from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.http import JsonResponse
from langchain.chains.query_constructor.base import AttributeInfo
from services.retriever_service import get_openai_retriever_service
from services.document_loader import get_document_loader
from django.conf import settings
import os


class RetrieverDemoView(APIView):
    """Demo view for showcasing different types of retrievers."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever_service = get_openai_retriever_service()
        self.document_loader = get_document_loader()
    
    def post(self, request):
        """Handle retriever demo requests."""
        try:
            retriever_type = request.data.get('retriever_type', 'vector_store')
            query = request.data.get('query', '')
            parameters = request.data.get('parameters', {})
            
            if not query:
                return Response(
                    {'error': 'Query is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Load the RH-Bridging loans PDF
            pdf_path = os.path.join(os.path.dirname(__file__), '..', 'sample_documents', 'sampledoc.pdf')
            
            if not os.path.exists(pdf_path):
                return Response(
                    {'error': 'PDF file not found. Please ensure the RH-Bridging loans PDF is in the correct location.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Load documents
            documents = self.document_loader.load_pdf_file(pdf_path)
            
            # Split documents into chunks
            chunks = self.retriever_service.text_splitter(documents, chunk_size=500, chunk_overlap=50)
            
            # Create vector store
            self.retriever_service.create_vector_store(chunks, collection_name="bridging_loans")
            
            # Process based on retriever type
            if retriever_type == 'vector_store':
                result = self._demo_vector_store_retriever(query, parameters)
            elif retriever_type == 'multi_query':
                result = self._demo_multi_query_retriever(query, parameters)
            elif retriever_type == 'self_query':
                result = self._demo_self_query_retriever(query, parameters)
            elif retriever_type == 'parent_document':
                result = self._demo_parent_document_retriever(query, parameters)
            else:
                return Response(
                    {'error': f'Unknown retriever type: {retriever_type}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'retriever_type': retriever_type,
                'query': query,
                'parameters': parameters,
                'result': result
            })
            
        except Exception as e:
            return Response(
                {'error': f'Retriever demo failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _demo_vector_store_retriever(self, query: str, parameters: dict):
        """Demonstrate Vector Store-Backed Retriever."""
        # Get search parameters
        search_type = parameters.get('search_type', 'similarity')
        k = parameters.get('k', 4)
        score_threshold = parameters.get('score_threshold', None)
        
        # Create retriever
        if search_type == 'mmr':
            retriever = self.retriever_service.vector_store_retriever(search_type="mmr")
        elif search_type == 'similarity_score_threshold' and score_threshold:
            retriever = self.retriever_service.vector_store_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"score_threshold": score_threshold}
            )
        else:
            retriever = self.retriever_service.vector_store_retriever(
                search_kwargs={"k": k}
            )
        
        # Search
        docs = self.retriever_service.search_with_retriever(retriever, query)
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                'metadata': doc.metadata
            })
        
        return {
            'search_type': search_type,
            'parameters': parameters,
            'documents_found': len(results),
            'results': results
        }
    
    def _demo_multi_query_retriever(self, query: str, parameters: dict):
        """Demonstrate Multi-Query Retriever."""
        # Create base retriever
        base_retriever = self.retriever_service.vector_store_retriever(
            search_kwargs={"k": parameters.get('k', 3)}
        )
        
        # Create multi-query retriever
        multi_retriever = self.retriever_service.multi_query_retriever(base_retriever)
        
        # Search
        docs = self.retriever_service.search_with_retriever(multi_retriever, query)
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                'metadata': doc.metadata
            })
        
        return {
            'retriever_type': 'multi_query',
            'documents_found': len(results),
            'results': results
        }
    
    def _demo_self_query_retriever(self, query: str, parameters: dict):
        """Demonstrate Self-Querying Retriever."""
        # Define metadata field info for the PDF documents
        metadata_field_info = [
            AttributeInfo(
                name="page",
                description="The page number of the document",
                type="integer",
            ),
            AttributeInfo(
                name="source",
                description="The source file name",
                type="string",
            ),
        ]
        
        document_content_description = "Financial document about bridging loans and related information."
        
        # Create self-querying retriever
        self_query_retriever = self.retriever_service.self_query_retriever(
            metadata_field_info,
            document_content_description
        )
        
        # Search
        docs = self.retriever_service.search_with_retriever(self_query_retriever, query)
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                'metadata': doc.metadata
            })
        
        return {
            'retriever_type': 'self_query',
            'documents_found': len(results),
            'results': results
        }
    
    def _demo_parent_document_retriever(self, query: str, parameters: dict):
        """Demonstrate Parent Document Retriever."""
        # Get chunk size parameters
        parent_chunk_size = parameters.get('parent_chunk_size', 1000)
        child_chunk_size = parameters.get('child_chunk_size', 200)
        chunk_overlap = parameters.get('chunk_overlap', 20)
        
        # Create parent document retriever
        parent_retriever = self.retriever_service.parent_document_retriever(
            parent_chunk_size=parent_chunk_size,
            child_chunk_size=child_chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Add documents to the retriever
        self.retriever_service.add_documents_to_parent_retriever(
            self.document_loader.load_pdf_file(
                os.path.join(os.path.dirname(__file__), '..', 'sample_documents', 'sampledoc.pdf')
            ),
            parent_retriever
        )
        
        # Search
        docs = self.retriever_service.search_with_retriever(parent_retriever, query)
        
        # Format results
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                'metadata': doc.metadata
            })
        
        return {
            'retriever_type': 'parent_document',
            'parent_chunk_size': parent_chunk_size,
            'child_chunk_size': child_chunk_size,
            'chunk_overlap': chunk_overlap,
            'documents_found': len(results),
            'results': results
        }


class MoviesRetrieverDemoView(APIView):
    """Demo view for showcasing self-querying retriever with movies data."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.retriever_service = get_openai_retriever_service()
        self.document_loader = get_document_loader()
    
    def post(self, request):
        """Handle movies retriever demo requests."""
        try:
            query = request.data.get('query', '')
            
            if not query:
                return Response(
                    {'error': 'Query is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create sample movies documents
            movies_docs = self.document_loader.create_sample_movies_documents()
            
            # Create vector store for movies
            self.retriever_service.create_vector_store(movies_docs, collection_name="movies")
            
            # Define metadata field info for movies
            metadata_field_info = [
                AttributeInfo(
                    name="genre",
                    description="The genre of the movie. One of ['science fiction', 'comedy', 'drama', 'thriller', 'romance', 'action', 'animated']",
                    type="string",
                ),
                AttributeInfo(
                    name="year",
                    description="The year the movie was released",
                    type="integer",
                ),
                AttributeInfo(
                    name="director",
                    description="The name of the movie director",
                    type="string",
                ),
                AttributeInfo(
                    name="rating", 
                    description="A 1-10 rating for the movie", 
                    type="float"
                ),
            ]
            
            document_content_description = "Brief summary of a movie."
            
            # Create self-querying retriever
            retriever = self.retriever_service.self_query_retriever(
                metadata_field_info,
                document_content_description
            )
            
            # Search
            docs = self.retriever_service.search_with_retriever(retriever, query)
            
            # Format results
            results = []
            for doc in docs:
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata
                })
            
            return Response({
                'retriever_type': 'self_query_movies',
                'query': query,
                'documents_found': len(results),
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': f'Movies retriever demo failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def retriever_examples(request):
    """Provide example queries and parameters for different retrievers."""
    examples = {
        'vector_store': {
            'description': 'Vector Store-Backed Retriever for similarity search',
            'example_queries': [
                'bridging loans',
                'financial terms',
                'loan requirements',
                'interest rates'
            ],
            'example_parameters': [
                {'search_type': 'similarity', 'k': 3},
                {'search_type': 'mmr', 'k': 5},
                {'search_type': 'similarity_score_threshold', 'score_threshold': 0.7}
            ]
        },
        'multi_query': {
            'description': 'Multi-Query Retriever that generates multiple query variations',
            'example_queries': [
                'What are bridging loans?',
                'How do bridging loans work?',
                'Tell me about financial bridging'
            ],
            'example_parameters': [
                {'k': 3},
                {'k': 5}
            ]
        },
        'self_query': {
            'description': 'Self-Querying Retriever that can filter by metadata',
            'example_queries': [
                'Show me documents from page 1',
                'Find information about loans',
                'What is in the source document?'
            ],
            'example_parameters': [
                {},
                {}
            ]
        },
        'parent_document': {
            'description': 'Parent Document Retriever that maintains context',
            'example_queries': [
                'bridging loans overview',
                'loan terms and conditions',
                'financial requirements'
            ],
            'example_parameters': [
                {'parent_chunk_size': 1000, 'child_chunk_size': 200, 'chunk_overlap': 20},
                {'parent_chunk_size': 800, 'child_chunk_size': 150, 'chunk_overlap': 30}
            ]
        },
        'movies_self_query': {
            'description': 'Self-Querying Retriever with movie metadata examples',
            'example_queries': [
                'I want to watch a movie rated higher than 8.5',
                'Has Greta Gerwig directed any movies about women?',
                'What is a highly rated science fiction film?',
                'Show me movies from the 1990s',
                'Find thrillers directed by Andrei Tarkovsky'
            ],
            'example_parameters': [
                {},
                {}
            ]
        }
    }
    
    return JsonResponse(examples)
