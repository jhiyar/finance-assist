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
from .confluence_views import (
    confluence_documents_list,
    confluence_document_detail,
    confluence_fetch_documents,
    confluence_index_documents,
    confluence_document_chunks,
    confluence_document_delete
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
    
    # Confluence document endpoints
    path('confluence/documents', confluence_documents_list, name='confluence_documents_list'),
    path('confluence/documents/<int:document_id>', confluence_document_detail, name='confluence_document_detail'),
    path('confluence/documents/<int:document_id>/chunks', confluence_document_chunks, name='confluence_document_chunks'),
    path('confluence/fetch', confluence_fetch_documents, name='confluence_fetch_documents'),
    path('confluence/index', confluence_index_documents, name='confluence_index_documents'),
    path('confluence/documents/<int:document_id>/delete', confluence_document_delete, name='confluence_document_delete'),
]
