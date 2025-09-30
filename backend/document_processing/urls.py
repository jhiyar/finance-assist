from django.urls import path
from .views import (
    DocumentUploadView, DocumentListView, DocumentDetailView,
    ChunkingMethodListView, ChunkingMethodDetailView,
    ProcessingJobCreateView, ProcessingJobDetailView, ProcessingJobListView,
    ChunkingResultListView, ChunkingResultDetailView,
    ComparisonView, ChunkingMethodConfigView, ContextPruningView,
    DocumentParseView
)

app_name = 'document_processing'

urlpatterns = [
    # Document endpoints
    path('documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('parse-document/', DocumentParseView.as_view(), name='parse_document'),
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('documents/<uuid:pk>/', DocumentDetailView.as_view(), name='document_detail'),
    
    # Chunking method endpoints
    path('chunking-methods/', ChunkingMethodListView.as_view(), name='chunking_method_list'),
    path('chunking-methods/<int:pk>/', ChunkingMethodDetailView.as_view(), name='chunking_method_detail'),
    path('chunking-methods/<int:method_id>/config/', ChunkingMethodConfigView.as_view(), name='chunking_method_config'),
    
    # Processing job endpoints
    path('documents/<uuid:doc_id>/process/', ProcessingJobCreateView.as_view(), name='process_document'),
    path('processing-jobs/', ProcessingJobListView.as_view(), name='processing_job_list'),
    path('processing-jobs/<uuid:pk>/', ProcessingJobDetailView.as_view(), name='processing_job_detail'),
    
    # Chunking result endpoints
    path('chunking-results/', ChunkingResultListView.as_view(), name='chunking_result_list'),
    path('chunking-results/<uuid:pk>/', ChunkingResultDetailView.as_view(), name='chunking_result_detail'),
    
    # Comparison endpoint
    path('documents/<uuid:doc_id>/compare/', ComparisonView.as_view(), name='compare_methods'),
    
    # Context pruning endpoint
    path('context-pruning/', ContextPruningView.as_view(), name='context_pruning'),
]
