from django.urls import path
from .views import (
    ProfileDetailView,
    TransactionListView,
    BalanceDetailView,
    ChatView,
    AgenticRAGTestView,
    DeepAgentChatView,
    DeepAgentTestView
)
from .document_reader_views import DocumentReaderComparisonView
from .retriever_views import (
    RetrieverDemoView,
    MoviesRetrieverDemoView,
    retriever_examples
)

app_name = 'chat'

urlpatterns = [
    path('chat', ChatView.as_view(), name='chat'),
    path('profile', ProfileDetailView.as_view(), name='profile'),
    path('transactions', TransactionListView.as_view(), name='transactions'),
    path('balance', BalanceDetailView.as_view(), name='balance'),
    
    # Enhanced Agentic-RAG endpoints
    path('agentic-rag-test', AgenticRAGTestView.as_view(), name='agentic_rag_test'),
    
    # Deep Agent endpoints
    path('deep-agent-chat', DeepAgentChatView.as_view(), name='deep_agent_chat'),
    path('deep-agent-test', DeepAgentTestView.as_view(), name='deep_agent_test'),
    
    # Retriever demo endpoints
    path('retriever-demo', RetrieverDemoView.as_view(), name='retriever_demo'),
    path('movies-retriever-demo', MoviesRetrieverDemoView.as_view(), name='movies_retriever_demo'),
    path('retriever-examples', retriever_examples, name='retriever_examples'),
    
    # Document reader comparison endpoints
    path('document-reader-comparison', DocumentReaderComparisonView.as_view(), name='document_reader_comparison'),
]
