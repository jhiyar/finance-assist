from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Profile, Transaction, Balance
from .serializers import (
    ProfileSerializer, 
    TransactionSerializer, 
    BalanceSerializer,
    ChatMessageSerializer,
    ChatResponseSerializer,
    DeepAgentChatMessageSerializer,
    DeepAgentChatResponseSerializer
)
from .utils import detect_intent, format_minor_units_to_currency
from services.retriever_service import get_openai_retriever_service
from services.document_loader import get_document_loader
from services.agentic_rag.agentic_rag_service import get_agentic_rag_service, initialize_agentic_rag_service
from services.deep_agents.deep_agent_service import get_deep_agent_service, initialize_deep_agent_service
from services.agentic_rag.document_readers.agentic_document_reader import AgenticDocumentReader
from services.agentic_rag.document_readers.pdf_reader import PDFReader
from services.agentic_rag.document_readers.text_reader import TextReader
from langchain_core.documents import Document
import os
import sys


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    """Generic view for retrieving and updating profile information."""
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    
    def get_object(self):
        # Get the first profile or create one if none exists
        profile, created = Profile.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Alex Doe',
                'address': '1 High Street, London',
                'email': 'alex@example.com'
            }
        )
        return profile


class TransactionListView(generics.ListAPIView):
    """Generic view for listing transactions."""
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()


class BalanceDetailView(generics.RetrieveAPIView):
    """Generic view for retrieving balance information."""
    serializer_class = BalanceSerializer
    
    def get_object(self):
        # Get the first balance or create one if none exists
        balance, created = Balance.objects.get_or_create(
            id=1,
            defaults={'amount_minor': 120000}
        )
        return balance


class ChatView(APIView):
    """API view for handling chat messages and intent detection with Enhanced Agentic-RAG."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("✓ ChatView initialized", flush=True)
        self.retriever_service = get_openai_retriever_service()
        self.document_loader = get_document_loader()
        self.agentic_rag_service = None
        self._initialize_documents()
        self._initialize_agentic_rag()
    
    def _initialize_documents(self):
        """Initialize documents for retrieval if they haven't been loaded yet."""
        try:
            # Check if we already have a vector store
            if not hasattr(self, '_vector_store_initialized'):
                # Load the sample document
                pdf_path = os.path.join(os.path.dirname(__file__), '..', 'sample_documents', 'sampledoc.pdf')
                if os.path.exists(pdf_path):
                    documents = self.document_loader.load_pdf_file(pdf_path)
                    chunks = self.retriever_service.text_splitter(documents, chunk_size=1000, chunk_overlap=200)
                    self.retriever_service.create_vector_store(chunks, collection_name="chat_documents")
                    self._vector_store_initialized = True
                    print("✓ Documents initialized successfully", flush=True)
                    print(f"✓ Vector store initialized with provider: {self.retriever_service.get_service_provider()}", flush=True)
        except Exception as e:
            print(f"Warning: Could not initialize documents: {e}", flush=True)
    
    def _initialize_agentic_rag(self):
        """Initialize Enhanced Agentic-RAG service."""
        try:
            print("Initializing Enhanced Agentic-RAG service...", flush=True)
            self.agentic_rag_service = initialize_agentic_rag_service(
                documents_directory="sample_documents",
                model_name="gpt-4o-mini",
                enable_evaluation=False,
                force_reprocess=False
            )
            print("✓ Enhanced Agentic-RAG service initialized", flush=True)
        except Exception as e:
            print(f"Warning: Could not initialize Enhanced Agentic-RAG service: {e}", flush=True)
            # Set to None so we can handle gracefully in the chat method
            self.agentic_rag_service = None
    
    def post(self, request):
        # print(f"Request data: {request.data}", flush=True)
        serializer = ChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid message'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = serializer.validated_data['message']
        retriever_type = request.data.get('retriever_type', 'agentic_rag') #vector_store, self_query, agentic_rag


        
        # First check if this is a simple intent-based query that doesn't need document retrieval
        intent = detect_intent(message)

        print(f"Intent: {intent}", flush=True)
        print(f"Retriever type: {retriever_type}", flush=True)
        
        # Only use intent-based responses for specific banking actions
        if intent in ['get_balance', 'get_transactions', 'update_profile']:
            # Handle these specific banking intents
            pass
        else:
            # For all other queries (including 'help' and knowledge questions), try document retrieval first
            try:
                # Try Enhanced Agentic-RAG first if available
                if retriever_type == 'agentic_rag' and self.agentic_rag_service:
                    result = self._answer_with_agentic_rag(message)
                    
                    if result and result.get('answer'):
                        response_data = {
                            'type': 'text',
                            'text': result['answer'],
                            'source': 'agentic_rag',
                            'retriever_type': 'agentic_rag',
                            'confidence': result.get('confidence', 0.0),
                            'citations': result.get('citations', []),
                            'sources_used': result.get('sources_used', []),
                            'rag_details': {
                                'processing_info': result.get('processing_info', {}),
                                'reasoning': result.get('reasoning', {}),
                                'confidence_scores': result.get('confidence_scores', {}),
                                'timestamp': result.get('timestamp', ''),
                                'errors': result.get('errors', [])
                            }
                        }
                        response_serializer = ChatResponseSerializer(data=response_data)
                        response_serializer.is_valid(raise_exception=True)
                        return Response(response_serializer.validated_data)
                
                # Fallback to traditional retrievers
                elif hasattr(self, '_vector_store_initialized') and self._vector_store_initialized:
                    answer = self._answer_with_retriever(message, retriever_type)
                    
                    if answer:
                        response_data = {
                            'type': 'text',
                            'text': answer,
                            'source': 'document_retrieval',
                            'retriever_type': retriever_type
                        }
                        response_serializer = ChatResponseSerializer(data=response_data)
                        response_serializer.is_valid(raise_exception=True)
                        return Response(response_serializer.validated_data)
            except Exception as e:
                print(f"Document retrieval failed: {e}", flush=True)
                return Response({'message': 'Document retrieval failed'})
        
        # Handle intent-based responses (only for specific banking actions)
        
        if intent == 'get_balance':
            balance = get_object_or_404(Balance, id=1)
            human_balance = format_minor_units_to_currency(balance.amount_minor)
            response_data = {
                'type': 'text',
                'text': f'Your balance is {human_balance}.',
                'source': 'intent_detection'
            }
        
        elif intent == 'get_transactions':
            transactions = Transaction.objects.all()[:10]  # Show more transactions
            if transactions:
                lines = []
                total_amount = 0
                for t in transactions:
                    formatted_amount = format_minor_units_to_currency(t.amount_minor)
                    total_amount += t.amount_minor
                    lines.append(f"• {t.date} — {t.description}: {formatted_amount}")
                
                total_formatted = format_minor_units_to_currency(total_amount)
                response_text = f'Here are your last {len(lines)} transactions:\n\n' + '\n'.join(lines)
                response_text += f'\n\nTotal amount: {total_formatted}'
                
                response_data = {
                    'type': 'text',
                    'text': response_text,
                    'source': 'intent_detection'
                }
            else:
                response_data = {
                    'type': 'text',
                    'text': 'No transactions found.',
                    'source': 'intent_detection'
                }
        
        elif intent == 'update_profile':
            response_data = {
                'type': 'action',
                'actionType': 'open_widget',
                'widget': 'profile_update',
                'title': 'Update your profile information',
                'fields': ['name', 'address', 'email'],
                'source': 'intent_detection'
            }
        
        else:  # help or other queries
            # If we get here, it means document retrieval failed or wasn't attempted
            # Provide a helpful response that guides users
            response_data = {
                'type': 'text',
                'text': 'I can help with: checking your balance, showing recent transactions, updating your address, and answering questions about documents using Enhanced Agentic-RAG. Try: "What\'s my balance?", "Show my last transactions", "I want to change my address", or ask me about the documents in my knowledge base.',
                'source': 'intent_detection'
            }
        
        response_serializer = ChatResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        print(f"Response data: {response_serializer.validated_data}", flush=True)
        
        return Response(response_serializer.validated_data)
    
    def _answer_with_vector_store(self, query: str) -> str:
        """Answer using basic vector store similarity search."""
        results = self.retriever_service.similarity_search(query, k=3)
        if results:
            context = "\n\n".join([doc.page_content for doc in results])
            return f"Based on the documents, here's what I found:\n\n{context}\n\nThis information should help answer your question: {query}"
        return None

    def _answer_with_multi_query(self, query: str) -> str:
        """Answer using multi-query retriever for better results."""
        base_retriever = self.retriever_service.vector_store_retriever(search_kwargs={"k": 3})
        multi_retriever = self.retriever_service.multi_query_retriever(base_retriever)
        results = self.retriever_service.search_with_retriever(multi_retriever, query)
        if results:
            context = "\n\n".join([doc.page_content for doc in results])
            return f"Using multiple query variations, I found:\n\n{context}"
        return None

    def _answer_with_self_query(self, query: str) -> str:
        """Answer using self-query retriever for structured queries."""
        print("Using self-query retriever", flush=True)
        from langchain.chains.query_constructor.base import AttributeInfo
        metadata_field_info = [
            AttributeInfo(name="page", description="The page number", type="integer"),
            AttributeInfo(name="source", description="The source file", type="string")
        ]
        document_content_description = "Document content about various topics."
        
        self_query_retriever = self.retriever_service.self_query_retriever(
            metadata_field_info, document_content_description
        )
        results = self.retriever_service.search_with_retriever(self_query_retriever, query)
        if results:
            context = results[0].page_content if results else ""
            return context
        return None

    def _answer_with_parent_document(self, query: str) -> str:
        """Answer using parent document retriever for context-aware answers."""
        parent_retriever = self.retriever_service.parent_document_retriever(
            parent_chunk_size=1000, child_chunk_size=200, chunk_overlap=20
        )
        
        # Reload documents for parent retriever
        pdf_path = os.path.join(os.path.dirname(__file__), '..', 'sample_documents', 'sampledoc.pdf')
        if os.path.exists(pdf_path):
            documents = self.document_loader.load_pdf_file(pdf_path)
            self.retriever_service.add_documents_to_parent_retriever(documents, parent_retriever)
        
        results = self.retriever_service.search_with_retriever(parent_retriever, query)
        if results:
            context = "\n\n".join([doc.page_content for doc in results])
            return f"Based on context-aware document analysis:\n\n{context}\n\nThis provides context for: {query}"
        return None

    def _answer_with_retriever(self, query: str, retriever_type: str = 'vector_store') -> str:
        """Answer user questions using the specified retriever type."""
        try:
            if retriever_type == 'vector_store':
                return self._answer_with_vector_store(query)
            
            elif retriever_type == 'multi_query':
                return self._answer_with_multi_query(query)
            
            elif retriever_type == 'self_query':
                return self._answer_with_self_query(query)
            
            elif retriever_type == 'parent_document':
                return self._answer_with_parent_document(query)
            
            # If no results found or unsupported retriever type
            return None
            
        except Exception as e:
            print(f"Error in retriever-based answer: {e}")
            return None
    
    def _answer_with_agentic_rag(self, query: str) -> dict:
        """Answer user questions using Enhanced Agentic-RAG."""
        try:
            if not self.agentic_rag_service:
                print("Enhanced Agentic-RAG service not available", flush=True)
                return None
            
            # Process query with Enhanced Agentic-RAG
            result = self.agentic_rag_service.process_query(query)
            
            if result and result.get('answer'):
                print(f"Enhanced Agentic-RAG answer generated with confidence: {result.get('confidence', 0.0)}", flush=True)
                return result
            else:
                print("Enhanced Agentic-RAG failed to generate answer", flush=True)
                return None
                
        except Exception as e:
            print(f"Error in Enhanced Agentic-RAG: {e}")
            return None


class AgenticRAGTestView(APIView):
    """API view for testing Enhanced Agentic-RAG functionality."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agentic_rag_service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Enhanced Agentic-RAG service."""
        print("Initializing Enhanced Agentic-RAG service", flush=True)
        # try:
        from services.agentic_rag.agentic_rag_service import get_agentic_rag_service
        self.agentic_rag_service = get_agentic_rag_service()
        if not self.agentic_rag_service.documents_processed:
            print("Documents not processed, initializing documents", flush=True)
            result = self.agentic_rag_service.initialize_documents()
            print(f"Agentic RAG initialization result: {result}", flush=True)
        # except Exception as e:
            # print(f"Failed to initialize Agentic RAG service: {e}", flush=True)
    
    def get(self, request):
        """Get service information and available documents."""

        print("Getting service information and available documents", flush=True)
        # try:
        if not self.agentic_rag_service:
            print("Enhanced Agentic-RAG service not available", flush=True)
            return Response({
                'error': 'Enhanced Agentic-RAG service not available',
                'status': 'not_initialized'
            })
        
        service_info = self.agentic_rag_service.get_service_info()
        available_documents = self.agentic_rag_service.get_available_documents()
        
        return Response({
            'status': 'success',
            'service_info': service_info,
            'available_documents': available_documents,
            'document_count': len(available_documents)
        })
            
        # except Exception as e:
        #     return Response({
        #         'error': str(e),
        #         'status': 'error'
        #     })
    
    def post(self, request):
        """Test Enhanced Agentic-RAG with a query."""
        try:
            query = request.data.get('query', '')
            if not query:
                return Response({
                    'error': 'Query is required',
                    'status': 'error'
                })
            
            if not self.agentic_rag_service:
                return Response({
                    'error': 'Enhanced Agentic-RAG service not available',
                    'status': 'not_initialized'
                })
            
            # Process the query
            result = self.agentic_rag_service.process_query(query)
            
            return Response({
                'status': 'success',
                'query': query,
                'result': result
            })
            
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'error'
            })


class DeepAgentChatView(APIView):
    """API view for handling chat messages with Deep Agents using LangGraph and ChromaDB."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("✓ DeepAgentChatView initialized", flush=True)
        self.deep_agent_service = None
        self._initialize_deep_agent_service()
    
    def _initialize_deep_agent_service(self):
        """Initialize the Deep Agent service."""
        try:
            print("Initializing Deep Agent service...", flush=True)
            self.deep_agent_service = initialize_deep_agent_service(
                documents_directory="sample_documents",
                collection_name="deep_agent_documents",
                enable_evaluation=False,
                force_reprocess=False
            )
            print("✓ Deep Agent service initialized", flush=True)
        except Exception as e:
            print(f"Warning: Could not initialize Deep Agent service: {e}", flush=True)
            # Set to None so we can handle gracefully in the chat method
            self.deep_agent_service = None
    
    def post(self, request):
        """Handle chat messages with Deep Agent processing."""
        serializer = DeepAgentChatMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid message'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        agent_type = serializer.validated_data.get('agent_type', 'deep_agent')
        
        print(f"Processing message with Deep Agent: {message[:50]}...", flush=True)
        print(f"Session ID: {session_id}", flush=True)
        print(f"Agent type: {agent_type}", flush=True)
        
        # Check if this is a simple intent-based query that doesn't need document retrieval
        intent = detect_intent(message)
        print(f"Intent detected: {intent}", flush=True)
        
        # Handle specific banking intents directly
        if intent in ['get_balance', 'get_transactions', 'update_profile']:
            return self._handle_banking_intent(intent)
        
        # Use Deep Agent for all other queries
        try:
            if not self.deep_agent_service:
                return Response({
                    'error': 'Deep Agent service not available',
                    'message': 'I apologize, but the Deep Agent system is not ready. Please try again later.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Process query with Deep Agent
            result = self.deep_agent_service.process_query(
                query=message,
                session_id=session_id
            )
            
            if result and result.get('answer'):
                # Format response for API
                response_data = {
                    'type': 'text',
                    'text': result['answer'],
                    'session_id': result.get('session_id', session_id or 'unknown'),
                    'confidence_score': result.get('confidence', 0.0),
                    'sources_used': result.get('sources_used', []),
                    'processing_time': result.get('processing_time', 0.0),
                    'agent_type': agent_type,
                    'reasoning': result.get('reasoning', {}),
                    'citations': result.get('citations', []),
                    'source': 'deep_agent'
                }
                
                response_serializer = DeepAgentChatResponseSerializer(data=response_data)
                response_serializer.is_valid(raise_exception=True)
                
                print(f"Deep Agent response generated with confidence: {result.get('confidence', 0.0)}", flush=True)
                return Response(response_serializer.validated_data)
            else:
                return Response({
                    'error': 'Failed to generate response',
                    'message': 'I apologize, but I couldn\'t generate a proper response to your query. Please try rephrasing your question.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            print(f"Deep Agent processing failed: {e}", flush=True)
            return Response({
                'error': 'Processing failed',
                'message': f'I apologize, but I encountered an error while processing your query: "{message}". Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_banking_intent(self, intent: str) -> Response:
        """Handle specific banking intents."""
        if intent == 'get_balance':
            balance = get_object_or_404(Balance, id=1)
            human_balance = format_minor_units_to_currency(balance.amount_minor)
            response_data = {
                'type': 'text',
                'text': f'Your balance is {human_balance}.',
                'session_id': 'banking_intent',
                'confidence_score': 1.0,
                'sources_used': ['database'],
                'processing_time': 0.0,
                'agent_type': 'banking_intent',
                'reasoning': {'intent': 'get_balance'},
                'citations': [],
                'source': 'banking_intent'
            }
        
        elif intent == 'get_transactions':
            transactions = Transaction.objects.all()[:10]
            if transactions:
                lines = []
                total_amount = 0
                for t in transactions:
                    formatted_amount = format_minor_units_to_currency(t.amount_minor)
                    total_amount += t.amount_minor
                    lines.append(f"• {t.date} — {t.description}: {formatted_amount}")
                
                total_formatted = format_minor_units_to_currency(total_amount)
                response_text = f'Here are your last {len(lines)} transactions:\n\n' + '\n'.join(lines)
                response_text += f'\n\nTotal amount: {total_formatted}'
                
                response_data = {
                    'type': 'text',
                    'text': response_text,
                    'session_id': 'banking_intent',
                    'confidence_score': 1.0,
                    'sources_used': ['database'],
                    'processing_time': 0.0,
                    'agent_type': 'banking_intent',
                    'reasoning': {'intent': 'get_transactions'},
                    'citations': [],
                    'source': 'banking_intent'
                }
            else:
                response_data = {
                    'type': 'text',
                    'text': 'No transactions found.',
                    'session_id': 'banking_intent',
                    'confidence_score': 1.0,
                    'sources_used': ['database'],
                    'processing_time': 0.0,
                    'agent_type': 'banking_intent',
                    'reasoning': {'intent': 'get_transactions'},
                    'citations': [],
                    'source': 'banking_intent'
                }
        
        elif intent == 'update_profile':
            response_data = {
                'type': 'action',
                'text': 'Profile update widget opened',
                'session_id': 'banking_intent',
                'confidence_score': 1.0,
                'sources_used': ['database'],
                'processing_time': 0.0,
                'agent_type': 'banking_intent',
                'reasoning': {'intent': 'update_profile'},
                'citations': [],
                'source': 'banking_intent',
                'actionType': 'open_widget',
                'widget': 'profile_update',
                'title': 'Update your profile information',
                'fields': ['name', 'address', 'email']
            }
        
        response_serializer = DeepAgentChatResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.validated_data)


class DeepAgentTestView(APIView):
    """API view for testing Deep Agent functionality."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deep_agent_service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the Deep Agent service."""
        print("Initializing Deep Agent service for testing", flush=True)
        try:
            self.deep_agent_service = get_deep_agent_service()
            if not self.deep_agent_service.documents_processed:
                print("Documents not processed, initializing documents", flush=True)
                result = self.deep_agent_service.initialize_documents()
                print(f"Deep Agent initialization result: {result}", flush=True)
        except Exception as e:
            print(f"Failed to initialize Deep Agent service: {e}", flush=True)
    
    def get(self, request):
        """Get service information and available documents."""
        print("Getting Deep Agent service information", flush=True)
        
        if not self.deep_agent_service:
            print("Deep Agent service not available", flush=True)
            return Response({
                'error': 'Deep Agent service not available',
                'status': 'not_initialized'
            })
        
        service_info = self.deep_agent_service.get_service_info()
        available_documents = self.deep_agent_service.get_available_documents()
        
        return Response({
            'status': 'success',
            'service_info': service_info,
            'available_documents': available_documents,
            'document_count': len(available_documents)
        })
    
    def post(self, request):
        """Test Deep Agent with a query."""
        try:
            query = request.data.get('query', '')
            if not query:
                return Response({
                    'error': 'Query is required',
                    'status': 'error'
                })
            
            if not self.deep_agent_service:
                return Response({
                    'error': 'Deep Agent service not available',
                    'status': 'not_initialized'
                })
            
            # Process the query
            result = self.deep_agent_service.process_query(query)
            
            return Response({
                'status': 'success',
                'query': query,
                'result': result
            })
            
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'error'
            })
