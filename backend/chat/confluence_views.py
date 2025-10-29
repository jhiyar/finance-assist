"""
API views for Confluence document management
"""

import logging
from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import ConfluenceDocument
from .serializers import (
    ConfluenceDocumentSerializer, 
    ConfluenceFetchSerializer, 
    ConfluenceIndexSerializer
)
from services.confluence_service import get_confluence_service
from services.chromadb_service import get_chromadb_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def confluence_documents_list(request):
    """
    List all Confluence documents with optional filtering.
    """
    try:
        documents = ConfluenceDocument.objects.all()
        
        # Apply filters if provided
        if request.GET.get('indexed_only'):
            documents = documents.filter(is_indexed=True)
        if request.GET.get('outdated_only'):
            documents = documents.filter(is_outdated=True)
        if request.GET.get('space_key'):
            documents = documents.filter(space_key=request.GET.get('space_key'))
        
        # Serialize documents
        serializer = ConfluenceDocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'documents': serializer.data,
            'total': documents.count()
        })
        
    except Exception as e:
        logger.error(f"Error listing Confluence documents: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def confluence_document_detail(request, document_id):
    """
    Get details of a specific Confluence document.
    """
    try:
        document = ConfluenceDocument.objects.get(id=document_id)
        serializer = ConfluenceDocumentSerializer(document)
        
        return Response({
            'success': True,
            'document': serializer.data
        })
        
    except ConfluenceDocument.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def confluence_fetch_documents(request):
    """
    Fetches documents from Confluence, updates existing ones, and adds new ones.
    """
    serializer = ConfluenceFetchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    parent_id = serializer.validated_data['parent_id']
    force_refresh = serializer.validated_data['force_refresh']
    
    try:
        # Get Confluence service
        confluence_service = get_confluence_service()
        
        # Fetch documents from Confluence
        logger.info(f"Fetching Confluence documents from parent ID: {parent_id}")
        
        # Track processing progress
        processed_pages = []
        total_pages = 0
        
        def progress_callback(current, total, page_title):
            nonlocal total_pages
            total_pages = total
            processed_pages.append({
                'current': current,
                'total': total,
                'title': page_title,
                'status': 'Processing...'
            })
            logger.info(f"Processing page {current}/{total}: {page_title}")
        
        fetch_result = confluence_service.fetch_confluence_documents(parent_id, progress_callback=progress_callback)
        
        if not fetch_result['success']:
            return Response({
                'success': False,
                'error': fetch_result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Process and store documents
        stored_documents = []
        updated_documents = []
        errors = []
        
        with transaction.atomic():
            for page_data in fetch_result['pages']:
                try:
                    confluence_id = page_data['id']
                    
                    # Check if document already exists
                    existing_doc = ConfluenceDocument.objects.filter(
                        confluence_id=confluence_id
                    ).first()
                    
                    # Parse timestamps
                    confluence_created = None
                    confluence_modified = None
                    
                    if page_data.get('created'):
                        try:
                            confluence_created = parse_datetime(page_data['created'])
                            # Ensure timezone-aware
                            if confluence_created and confluence_created.tzinfo is None:
                                confluence_created = timezone.make_aware(confluence_created, timezone.utc)
                        except:
                            pass
                    
                    if page_data.get('last_modified'):
                        try:
                            confluence_modified = parse_datetime(page_data['last_modified'])
                            # Ensure timezone-aware
                            if confluence_modified and confluence_modified.tzinfo is None:
                                confluence_modified = timezone.make_aware(confluence_modified, timezone.utc)
                        except:
                            pass
                    
                    document_data = {
                        'confluence_id': confluence_id,
                        'title': page_data['title'],
                        'content': page_data['content'],
                        'html_content': page_data['html_content'],
                        'space_key': page_data['space_key'],
                        'space_name': page_data['space_name'],
                        'version': page_data['version'],
                        'url': page_data['url'],
                        'ancestors': page_data['ancestors'],
                        'parent_id': page_data['parent_id'],
                        'confluence_created': confluence_created,
                        'confluence_modified': confluence_modified,
                    }
                    
                    if existing_doc:
                        # Update existing document if force_refresh or outdated
                        if force_refresh or existing_doc.is_outdated:
                            for key, value in document_data.items():
                                setattr(existing_doc, key, value)
                            existing_doc.is_indexed = False # Mark for re-indexing
                            existing_doc.indexing_error = ""
                            existing_doc.save()
                            updated_documents.append(existing_doc)
                            logger.info(f"Updated Confluence document: {existing_doc.title} (ID: {existing_doc.confluence_id})")
                    else:
                        # Create new document
                        new_doc = ConfluenceDocument.objects.create(**document_data)
                        stored_documents.append(new_doc)
                        logger.info(f"Created new Confluence document: {new_doc.title} (ID: {new_doc.confluence_id})")
                
                except Exception as e:
                    error_msg = f"Error processing page {page_data.get('title', 'Unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        return Response({
            'success': True,
            'message': f"Successfully processed {len(stored_documents + updated_documents)} documents",
            'stats': {
                'total_fetched': fetch_result['total_pages'],
                'new_documents': len(stored_documents),
                'updated_documents': len(updated_documents),
                'errors': len(errors)
            },
            'processing_details': {
                'total_pages_processed': len(processed_pages),
                'pages_processed': processed_pages[-10:] if len(processed_pages) > 10 else processed_pages,  # Last 10 pages
                'total_pages_found': total_pages
            },
            'new_documents': ConfluenceDocumentSerializer(stored_documents, many=True).data,
            'updated_documents': ConfluenceDocumentSerializer(updated_documents, many=True).data,
            'errors': errors,
            'fetched_at': fetch_result['fetched_at']
        })
        
    except Exception as e:
        logger.error(f"Error in confluence_fetch_documents: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def confluence_index_documents(request):
    """
    Index Confluence documents in ChromaDB.
    """
    serializer = ConfluenceIndexSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    document_ids = serializer.validated_data.get('document_ids', [])
    force_reindex = serializer.validated_data.get('force_reindex', False)
    
    try:
        # Get documents to index
        if document_ids:
            documents = ConfluenceDocument.objects.filter(id__in=document_ids)
        else:
            documents = ConfluenceDocument.objects.all()
        
        if not documents.exists():
            return Response({
                'success': False,
                'error': 'No documents found to index'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get ChromaDB service
        chromadb_service = get_chromadb_service()
        
        # Index documents
        successfully_indexed = 0
        errors = []
        
        for document in documents:
            try:
                # Skip if already indexed and not forcing reindex
                if document.is_indexed and not force_reindex:
                    logger.info(f"Skipping already indexed document: {document.title}")
                    continue
                
                # Prepare document for indexing
                # Convert ancestors list to string for ChromaDB compatibility
                ancestors_str = ', '.join(document.ancestors) if document.ancestors else ''
                
                doc_data = {
                    'content': document.content,
                    'metadata': {
                        'title': document.title,
                        'confluence_id': document.confluence_id,
                        'space_key': document.space_key,
                        'space_name': document.space_name,
                        'url': document.url,
                        'version': str(document.version),  # Ensure version is string
                        'ancestors': ancestors_str,  # Convert list to string
                        'source': 'confluence',
                        'document_type': 'confluence_page'
                    }
                }
                
                # Index document in ChromaDB
                chromadb_service.add_content_document(
                    content=doc_data['content'],
                    document_id=f"confluence_{document.confluence_id}",
                    metadata=doc_data['metadata']
                )
                
                # Update document status
                document.is_indexed = True
                document.last_indexed = timezone.now()
                document.indexing_error = ''
                document.save()
                
                successfully_indexed += 1
                logger.info(f"Successfully indexed document: {document.title}")
                
            except Exception as e:
                error_msg = f"Error indexing document {document.title}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Update document with error
                document.indexing_error = str(e)
                document.save()
        
        return Response({
            'success': True,
            'message': f"Successfully indexed {successfully_indexed} documents",
            'stats': {
                'successfully_indexed': successfully_indexed,
                'errors': len(errors),
                'total_processed': documents.count()
            },
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error in confluence_index_documents: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def confluence_document_chunks(request, document_id):
    """
    Get chunks for a Confluence document from ChromaDB.
    """
    try:
        document = ConfluenceDocument.objects.get(id=document_id)
        
        # Get chunks from ChromaDB
        chromadb_service = get_chromadb_service()
        chunks = chromadb_service.get_document_chunks(f"confluence_{document.confluence_id}")
        
        return Response({
            'success': True,
            'document_id': document_id,
            'confluence_id': document.confluence_id,
            'title': document.title,
            'chunks': chunks,
            'total_chunks': len(chunks)
        })
        
    except ConfluenceDocument.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error getting chunks for document {document_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def confluence_document_delete(request, document_id):
    """Delete a Confluence document from database and ChromaDB"""
    try:
        document = ConfluenceDocument.objects.get(id=document_id)
        
        # Remove from ChromaDB if indexed
        if document.is_indexed:
            try:
                chromadb_service = get_chromadb_service()
                chromadb_service.delete_document(f"confluence_{document.confluence_id}")
                logger.info(f"Removed document from ChromaDB: {document.title}")
            except Exception as e:
                logger.warning(f"Error removing document from ChromaDB: {e}")
        
        # Delete from database
        document.delete()
        
        return Response({
            'success': True,
            'message': f"Successfully deleted document: {document.title}"
        })
        
    except ConfluenceDocument.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Document not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting Confluence document {document_id}: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
