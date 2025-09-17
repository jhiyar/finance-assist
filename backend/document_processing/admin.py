from django.contrib import admin
from .models import (
    Document, ChunkingMethod, ProcessingJob, ChunkingResult, 
    Chunk, EvaluationMetric, ComparisonResult
)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_type', 'file_size', 'upload_date', 'processed']
    list_filter = ['file_type', 'processed', 'upload_date']
    search_fields = ['name']
    readonly_fields = ['id', 'file_size', 'upload_date']


@admin.register(ChunkingMethod)
class ChunkingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'method_type', 'is_active', 'created_at']
    list_filter = ['method_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = ['document__name']
    readonly_fields = ['id', 'started_at', 'completed_at']
    filter_horizontal = ['chunking_methods']


@admin.register(ChunkingResult)
class ChunkingResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'processing_job', 'chunking_method', 'total_chunks', 'processing_time', 'created_at']
    list_filter = ['chunking_method', 'created_at']
    search_fields = ['processing_job__document__name']
    readonly_fields = ['id', 'created_at']


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'chunking_result', 'chunk_type', 'chunk_index', 'token_count']
    list_filter = ['chunk_type', 'chunking_result__chunking_method']
    search_fields = ['content']
    readonly_fields = ['id']


@admin.register(EvaluationMetric)
class EvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ['id', 'chunking_result', 'metric_type', 'metric_value', 'calculated_at']
    list_filter = ['metric_type', 'calculated_at']
    search_fields = ['chunking_result__processing_job__document__name']
    readonly_fields = ['id', 'calculated_at']


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'processing_job', 'winner_method', 'created_at']
    list_filter = ['created_at', 'winner_method']
    search_fields = ['processing_job__document__name']
    readonly_fields = ['id', 'created_at']
    filter_horizontal = ['compared_methods']
