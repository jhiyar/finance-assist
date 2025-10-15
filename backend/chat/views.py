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
    ChatResponseSerializer
)
from .utils import detect_intent, format_minor_units_to_currency
from services.agentic_rag.agentic_rag_service import get_agentic_rag_service, initialize_agentic_rag_service
from services.chromadb_service import get_chromadb_service
import os


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
        # Use the same ChromaDB collection that document processing uses
        self.chromadb_service = get_chromadb_service(collection_name="finance_documents")
        self.agentic_rag_service = None
        self._initialize_agentic_rag()
    
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
        retriever_type = request.data.get('retriever_type', 'hybrid_search') #hybrid_search, agentic_rag
        
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
                # Try hybrid search first (recommended) - uses existing ChromaDB collection
                if retriever_type == 'hybrid_search':
                    result = self._answer_with_hybrid_search(message)
                    
                    if result:
                        response_data = {
                            'type': 'text',
                            'text': result['answer'],
                            'source': 'hybrid_search',
                            'retriever_type': 'hybrid_search',
                            'sources': result.get('sources', []),
                            'search_stats': result.get('search_stats', {})
                        }
                        response_serializer = ChatResponseSerializer(data=response_data)
                        response_serializer.is_valid(raise_exception=True)
                        return Response(response_serializer.validated_data)
                
                # Try Enhanced Agentic-RAG if specified
                elif retriever_type == 'agentic_rag' and self.agentic_rag_service:
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
            except Exception as e:
                print(f"Document retrieval failed: {e}", flush=True)
                # Continue to intent-based fallback instead of returning error
        
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
                'text': 'I can help with: checking your balance, showing recent transactions, updating your address, and answering questions about documents using hybrid search (vector + BM25) on your uploaded documents. Try: "What\'s my balance?", "Show my last transactions", "I want to change my address", or ask me about the documents in your knowledge base.',
                'source': 'intent_detection'
            }
        
        response_serializer = ChatResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        print(f"Response data: {response_serializer.validated_data}", flush=True)
        
        return Response(response_serializer.validated_data)
    
    
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
    
    def _answer_with_hybrid_search(self, query: str) -> dict:
        """Answer user questions using ChromaDB hybrid search."""
        try:
            # Perform hybrid search
            search_results = self.chromadb_service.hybrid_search(
                query=query,
                k=5,
                vector_weight=0.7,
                bm25_weight=0.3
            )
            
            if not search_results:
                print("No results found from hybrid search", flush=True)
                return None
            
            # Extract context from search results
            context_parts = []
            sources = []
            
            for i, result in enumerate(search_results[:3]):  # Use top 3 results
                context_parts.append(f"[Source {i+1}] {result['content']}")
                sources.append({
                    "rank": result.get("rank", i+1),
                    "content_preview": result['content'][:200] + "...",
                    "document_name": result['metadata'].get('document_name', 'Unknown'),
                    "hybrid_score": result.get("hybrid_score", 0),
                    "vector_score": result.get("vector_score", 0),
                    "bm25_score": result.get("bm25_score", 0)
                })
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using LLM
            from services.openai_service import get_openai_service
            openai_service = get_openai_service()
            llm = openai_service.get_langchain_llm()
            
            prompt = f"""Based on the following context from our documents, please answer the user's question.

Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context provided. If the context doesn't contain enough information to answer the question, say so."""

            answer = llm.invoke(prompt).content
            
            return {
                "answer": answer,
                "sources": sources,
                "search_stats": {
                    "total_results": len(search_results),
                    "results_used": len(sources),
                    "search_type": "hybrid (vector + BM25)"
                }
            }
            
        except Exception as e:
            print(f"Error in hybrid search: {e}", flush=True)
            import traceback
            traceback.print_exc()
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


