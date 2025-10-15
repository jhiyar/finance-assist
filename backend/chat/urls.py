from django.urls import path
from .views import (
    ProfileDetailView,
    TransactionListView,
    BalanceDetailView,
    ChatView,
    AgenticRAGTestView,
    ConversationListView,
    ConversationDetailView,
    ConversationMessagesView,
    ConversationChatView
)
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
    
    # Retriever demo endpoints
    path('retriever-demo', RetrieverDemoView.as_view(), name='retriever_demo'),
    path('movies-retriever-demo', MoviesRetrieverDemoView.as_view(), name='movies_retriever_demo'),
    path('retriever-examples', retriever_examples, name='retriever_examples'),
    
    # Conversation endpoints
    path('conversations', ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:conversation_id>/messages', ConversationMessagesView.as_view(), name='conversation_messages'),
    path('conversations/<int:conversation_id>/chat', ConversationChatView.as_view(), name='conversation_chat'),
]
