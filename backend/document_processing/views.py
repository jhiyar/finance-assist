import os
import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings

from .models import (
    Document, ChunkingMethod, ProcessingJob, ChunkingResult, 
    Chunk, EvaluationMetric, ComparisonResult
)
from .serializers import (
    DocumentSerializer, ChunkingMethodSerializer, ProcessingJobSerializer,
    ChunkingResultSerializer, DocumentUploadSerializer, ProcessingJobCreateSerializer,
    ChunkingMethodConfigSerializer
)
from .parsers.unstructured_parser import UnstructuredParser
from .parsers.llamaparse_parser import LlamaParseParser
from .chunkers.hierarchical_chunker import HierarchicalChunker
from .chunkers.semantic_chunker import SemanticChunker
from .chunkers.financial_chunker import FinancialChunker
from .evaluation.evaluator import ChunkEvaluator
from services.context_pruning_service import get_context_pruning_service

logger = logging.getLogger(__name__)


class DocumentUploadView(APIView):
    """API view for uploading documents."""
    
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Upload a new document."""
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            document = serializer.save()
            return Response(
                DocumentSerializer(document).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentParseView(APIView):
    """API view for parsing documents and extracting text content."""
    
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Parse a document and return extracted text content."""
        try:
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            
            # Validate file type
            if file.content_type != 'application/pdf':
                return Response(
                    {'error': 'Only PDF files are supported'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Parse document using available parsers
                parsed_document = self._parse_document(temp_file_path)
                
                # Extract text content
                text_content = self._extract_text_content(parsed_document)
                
                return Response({
                    'content': text_content,
                    'metadata': {
                        'filename': file.name,
                        'file_size': file.size,
                        'content_type': file.content_type,
                        'total_elements': len(parsed_document.elements),
                        'total_length': parsed_document.total_length
                    }
                })
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error parsing document: {e}")
            return Response(
                {'error': f'Failed to parse document: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _parse_document(self, file_path):
        """Parse document using appropriate parser."""
        # Try Unstructured.io first
        try:
            parser = UnstructuredParser()
            if parser.validate_file(file_path):
                return parser.parse(file_path)
        except Exception as e:
            logger.warning(f"Unstructured.io parsing failed: {e}")
        
        # Fallback to LlamaParse
        try:
            parser = LlamaParseParser()
            if parser.validate_file(file_path):
                return parser.parse(file_path)
        except Exception as e:
            logger.warning(f"LlamaParse parsing failed: {e}")
        
        # Fallback to basic text parsing
        return self._basic_text_parse(file_path)
    
    def _basic_text_parse(self, file_path):
        """Basic text parsing fallback."""
        try:
            import pypdf
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                from .parsers.base_parser import ParsedDocument, ParsedElement
                element = ParsedElement(
                    content=text_content,
                    element_type='text',
                    metadata={'source': 'basic_pdf_parser'},
                    start_position=0,
                    end_position=len(text_content)
                )
                
                return ParsedDocument(
                    elements=[element],
                    metadata={'parser': 'basic_pdf'},
                    total_length=len(text_content)
                )
        except Exception as e:
            logger.error(f"Basic text parsing failed: {e}")
            raise
    
    def _extract_text_content(self, parsed_document):
        """Extract plain text content from parsed document."""
        text_parts = []
        for element in parsed_document.elements:
            if element.content.strip():
                text_parts.append(element.content.strip())
        return '\n\n'.join(text_parts)


class ContextPruningView(APIView):
    """API view for context pruning operations."""
    
    def post(self, request):
        """Apply context pruning to documents."""
        try:
            # Get parameters from request
            documents_data = request.data.get('documents', [])
            query = request.data.get('query', '')
            method = request.data.get('method', 'hybrid')
            config = request.data.get('config', {})
            
            if not documents_data:
                return Response(
                    {'error': 'No documents provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert documents data to Document objects
            from langchain_core.documents import Document
            documents = []
            for doc_data in documents_data:
                doc = Document(
                    page_content=doc_data.get('content', ''),
                    metadata=doc_data.get('metadata', {})
                )
                documents.append(doc)
            
            # Initialize context pruning service
            pruning_service = get_context_pruning_service(**config)
            
            # Apply pruning
            result = pruning_service.prune_context(
                documents=documents,
                query=query,
                method=method,
                **config
            )
            
            # Convert result to response format
            response_data = {
                'pruned_documents': [
                    {
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    }
                    for doc in result.pruned_documents
                ],
                'original_documents': [
                    {
                        'content': doc.page_content,
                        'metadata': doc.metadata
                    }
                    for doc in result.original_documents
                ],
                'stats': {
                    'original_count': result.original_count,
                    'pruned_count': result.pruned_count,
                    'compression_ratio': result.compression_ratio,
                    'processing_time': result.processing_time,
                    'pruning_method': result.pruning_method,
                    'efficiency': f"{(1 - result.compression_ratio) * 100:.1f}% reduction"
                },
                'metadata': result.metadata
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Context pruning failed: {e}")
            return Response(
                {'error': f'Context pruning failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentListView(generics.ListAPIView):
    """API view for listing documents."""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """API view for retrieving and deleting documents."""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class ChunkingMethodListView(generics.ListAPIView):
    """API view for listing available chunking methods."""
    
    queryset = ChunkingMethod.objects.filter(is_active=True)
    serializer_class = ChunkingMethodSerializer


class ChunkingMethodDetailView(generics.RetrieveAPIView):
    """API view for retrieving chunking method details."""
    
    queryset = ChunkingMethod.objects.all()
    serializer_class = ChunkingMethodSerializer


class ProcessingJobCreateView(APIView):
    """API view for creating processing jobs."""
    
    def post(self, request, doc_id):
        """Create a new processing job for a document."""
        document = get_object_or_404(Document, id=doc_id)
        
        serializer = ProcessingJobCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        chunking_method_ids = serializer.validated_data['chunking_method_ids']
        configuration = serializer.validated_data['configuration']
        
        # Create processing job
        processing_job = ProcessingJob.objects.create(
            document=document,
            status='pending',
            configuration=configuration
        )
        
        # Add chunking methods
        chunking_methods = ChunkingMethod.objects.filter(id__in=chunking_method_ids)
        processing_job.chunking_methods.set(chunking_methods)
        
        # Start processing asynchronously (in a real implementation, use Celery)
        self._process_document_async(processing_job)
        
        return Response(
            ProcessingJobSerializer(processing_job).data,
            status=status.HTTP_201_CREATED
        )
    
    def _process_document_async(self, processing_job):
        """Process document asynchronously."""
        # In a real implementation, this would be a Celery task
        # For now, we'll process synchronously
        try:
            processing_job.status = 'processing'
            processing_job.save()
            
            # Parse document
            parsed_document = self._parse_document(processing_job.document)
            
            # Process with each chunking method
            for chunking_method in processing_job.chunking_methods.all():
                self._process_with_method(processing_job, chunking_method, parsed_document)
            
            processing_job.status = 'completed'
            processing_job.save()
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            processing_job.status = 'failed'
            processing_job.error_message = str(e)
            processing_job.save()
    
    def _parse_document(self, document):
        """Parse document using appropriate parser."""
        file_path = document.file.path
        
        # Try Unstructured.io first
        try:
            parser = UnstructuredParser()
            if parser.validate_file(file_path):
                return parser.parse(file_path)
        except Exception as e:
            logger.warning(f"Unstructured.io parsing failed: {e}")
        
        # Fallback to LlamaParse
        try:
            parser = LlamaParseParser()
            if parser.validate_file(file_path):
                return parser.parse(file_path)
        except Exception as e:
            logger.warning(f"LlamaParse parsing failed: {e}")
        
        # Fallback to basic text parsing
        return self._basic_text_parse(file_path)
    
    def _basic_text_parse(self, file_path):
        """Basic text parsing fallback."""
        from .parsers.base_parser import ParsedDocument, ParsedElement
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        element = ParsedElement(
            content=content,
            element_type='text',
            metadata={},
            start_position=0,
            end_position=len(content)
        )
        
        return ParsedDocument(
            elements=[element],
            metadata={'parser': 'basic_text'},
            total_length=len(content)
        )
    
    def _process_with_method(self, processing_job, chunking_method, parsed_document):
        """Process document with a specific chunking method."""
        # Get chunker based on method type
        chunker = self._get_chunker(chunking_method)
        
        # Get configuration
        config = processing_job.configuration.get(chunking_method.method_type, {})
        
        # Chunk the document
        chunking_result = chunker.chunk(parsed_document, **config)
        
        # Save chunking result
        db_result = ChunkingResult.objects.create(
            processing_job=processing_job,
            chunking_method=chunking_method,
            total_chunks=chunking_result.total_chunks,
            processing_time=chunking_result.processing_time
        )
        
        # Save chunks
        for chunk in chunking_result.chunks:
            Chunk.objects.create(
                chunking_result=db_result,
                content=chunk.content,
                chunk_type=chunk.chunk_type,
                chunk_index=chunk.chunk_index,
                start_position=chunk.start_position,
                end_position=chunk.end_position,
                token_count=chunk.token_count,
                metadata=chunk.metadata
            )
        
        # Evaluate the result
        evaluator = ChunkEvaluator()
        metrics = evaluator.evaluate_chunking_result(chunking_result)
        
        # Save evaluation metrics
        for metric in metrics:
            metric.chunking_result = db_result
            metric.save()
    
    def _get_chunker(self, chunking_method):
        """Get chunker instance based on method type."""
        method_type = chunking_method.method_type
        
        if method_type == 'hierarchical':
            return HierarchicalChunker(**chunking_method.parameters)
        elif method_type == 'semantic':
            return SemanticChunker(**chunking_method.parameters)
        elif method_type == 'financial':
            return FinancialChunker(**chunking_method.parameters)
        else:
            # Default to hierarchical
            return HierarchicalChunker(**chunking_method.parameters)


class ProcessingJobDetailView(generics.RetrieveAPIView):
    """API view for retrieving processing job details."""
    
    queryset = ProcessingJob.objects.all()
    serializer_class = ProcessingJobSerializer


class ProcessingJobListView(generics.ListAPIView):
    """API view for listing processing jobs."""
    
    queryset = ProcessingJob.objects.all()
    serializer_class = ProcessingJobSerializer


class ChunkingResultListView(generics.ListAPIView):
    """API view for listing chunking results."""
    
    queryset = ChunkingResult.objects.all()
    serializer_class = ChunkingResultSerializer


class ChunkingResultDetailView(generics.RetrieveAPIView):
    """API view for retrieving chunking result details."""
    
    queryset = ChunkingResult.objects.all()
    serializer_class = ChunkingResultSerializer


class ComparisonView(APIView):
    """API view for comparing chunking methods."""
    
    def post(self, request, doc_id):
        """Compare multiple chunking methods for a document."""
        document = get_object_or_404(Document, id=doc_id)
        
        # Get the latest processing job for this document
        processing_job = ProcessingJob.objects.filter(
            document=document,
            status='completed'
        ).first()
        
        if not processing_job:
            return Response(
                {'error': 'No completed processing job found for this document'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get chunking results
        chunking_results = processing_job.chunking_results.all()
        
        if len(chunking_results) < 2:
            return Response(
                {'error': 'At least 2 chunking results required for comparison'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform comparison
        comparison_metrics = self._compare_chunking_results(chunking_results)
        
        # Create comparison result
        comparison_result = ComparisonResult.objects.create(
            processing_job=processing_job,
            comparison_metrics=comparison_metrics
        )
        
        # Set winner method
        winner_method = self._determine_winner(chunking_results, comparison_metrics)
        if winner_method:
            comparison_result.winner_method = winner_method
            comparison_result.save()
        
        # Add compared methods
        comparison_result.compared_methods.set([cr.chunking_method for cr in chunking_results])
        
        return Response({
            'comparison_id': comparison_result.id,
            'comparison_metrics': comparison_metrics,
            'winner_method': ChunkingMethodSerializer(winner_method).data if winner_method else None,
            'compared_methods': ChunkingMethodSerializer(
                [cr.chunking_method for cr in chunking_results], many=True
            ).data
        })
    
    def _compare_chunking_results(self, chunking_results):
        """Compare chunking results and return metrics."""
        comparison_metrics = {}
        
        for result in chunking_results:
            method_name = result.chunking_method.name
            method_metrics = {}
            
            # Get evaluation metrics
            for metric in result.evaluation_metrics.all():
                method_metrics[metric.metric_type] = {
                    'value': metric.metric_value,
                    'details': metric.metric_details
                }
            
            # Add basic metrics
            method_metrics['total_chunks'] = result.total_chunks
            method_metrics['processing_time'] = result.processing_time
            
            comparison_metrics[method_name] = method_metrics
        
        return comparison_metrics
    
    def _determine_winner(self, chunking_results, comparison_metrics):
        """Determine the winning chunking method."""
        scores = {}
        
        for result in chunking_results:
            method_name = result.chunking_method.name
            method_metrics = comparison_metrics.get(method_name, {})
            
            # Calculate composite score
            score = 0
            weight_sum = 0
            
            # Weight different metrics
            weights = {
                'chunk_size_distribution': 0.2,
                'overlap_analysis': 0.15,
                'context_preservation': 0.2,
                'structure_retention': 0.2,
                'semantic_coherence': 0.15,
                'processing_efficiency': 0.1
            }
            
            for metric_type, weight in weights.items():
                if metric_type in method_metrics:
                    score += method_metrics[metric_type]['value'] * weight
                    weight_sum += weight
            
            if weight_sum > 0:
                scores[method_name] = score / weight_sum
        
        # Find the method with highest score
        if scores:
            winner_name = max(scores, key=scores.get)
            return next(
                (result.chunking_method for result in chunking_results 
                 if result.chunking_method.name == winner_name),
                None
            )
        
        return None


class ChunkingMethodConfigView(APIView):
    """API view for getting chunking method configuration options."""
    
    def get(self, request, method_id):
        """Get configuration options for a chunking method."""
        chunking_method = get_object_or_404(ChunkingMethod, id=method_id)
        
        # Get default configuration
        config = chunking_method.parameters.copy()
        
        # Add method-specific configuration options
        if chunking_method.method_type == 'hierarchical':
            config.update({
                'chunk_size': {'type': 'integer', 'min': 100, 'max': 4000, 'default': 1000},
                'chunk_overlap': {'type': 'integer', 'min': 0, 'max': 500, 'default': 200},
                'preserve_structure': {'type': 'boolean', 'default': True},
                'hierarchical_depth': {'type': 'integer', 'min': 1, 'max': 10, 'default': 3}
            })
        elif chunking_method.method_type == 'semantic':
            config.update({
                'chunk_size': {'type': 'integer', 'min': 1000, 'max': 30000, 'default': 15000},
                'semantic_threshold': {'type': 'float', 'min': 0.0, 'max': 1.0, 'default': 0.7},
                'min_chunk_size': {'type': 'integer', 'min': 500, 'max': 5000, 'default': 1500},
                'max_chunk_size': {'type': 'integer', 'min': 2000, 'max': 50000, 'default': 25000}
            })
        elif chunking_method.method_type == 'financial':
            config.update({
                'chunk_size': {'type': 'integer', 'min': 100, 'max': 4000, 'default': 1000},
                'chunk_overlap': {'type': 'integer', 'min': 0, 'max': 500, 'default': 200},
                'table_aware': {'type': 'boolean', 'default': True},
                'preserve_financial_structure': {'type': 'boolean', 'default': True}
            })
        
        return Response({
            'method': ChunkingMethodSerializer(chunking_method).data,
            'configuration_options': config
        })
