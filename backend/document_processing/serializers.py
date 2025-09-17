from rest_framework import serializers
from .models import (
    Document, ChunkingMethod, ProcessingJob, ChunkingResult, 
    Chunk, EvaluationMetric, ComparisonResult
)


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    file_size_mb = serializers.SerializerMethodField()
    processing_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'name', 'file', 'file_type', 'file_size', 'file_size_mb',
            'upload_date', 'processed', 'metadata', 'processing_status'
        ]
        read_only_fields = ['id', 'file_size', 'upload_date', 'processed']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB."""
        return round(obj.file_size / (1024 * 1024), 2)
    
    def get_processing_status(self, obj):
        """Get the latest processing job status."""
        latest_job = obj.processing_jobs.first()
        return latest_job.status if latest_job else 'not_started'


class ChunkingMethodSerializer(serializers.ModelSerializer):
    """Serializer for ChunkingMethod model."""
    
    class Meta:
        model = ChunkingMethod
        fields = [
            'id', 'name', 'method_type', 'description', 
            'parameters', 'is_active', 'created_at'
        ]


class ChunkSerializer(serializers.ModelSerializer):
    """Serializer for Chunk model."""
    
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Chunk
        fields = [
            'id', 'content', 'content_preview', 'chunk_type', 'chunk_index',
            'start_position', 'end_position', 'token_count', 'metadata',
            'parent_chunk'
        ]
    
    def get_content_preview(self, obj):
        """Get a preview of the chunk content."""
        return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content


class EvaluationMetricSerializer(serializers.ModelSerializer):
    """Serializer for EvaluationMetric model."""
    
    class Meta:
        model = EvaluationMetric
        fields = [
            'id', 'metric_type', 'metric_value', 'metric_details', 'calculated_at'
        ]


class ChunkingResultSerializer(serializers.ModelSerializer):
    """Serializer for ChunkingResult model."""
    
    chunking_method = ChunkingMethodSerializer(read_only=True)
    chunks = ChunkSerializer(many=True, read_only=True)
    evaluation_metrics = EvaluationMetricSerializer(many=True, read_only=True)
    avg_chunk_size = serializers.SerializerMethodField()
    processing_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ChunkingResult
        fields = [
            'id', 'chunking_method', 'total_chunks', 'processing_time',
            'processing_time_formatted', 'avg_chunk_size', 'created_at',
            'chunks', 'evaluation_metrics'
        ]
    
    def get_avg_chunk_size(self, obj):
        """Calculate average chunk size."""
        if obj.total_chunks > 0:
            total_tokens = sum(chunk.token_count for chunk in obj.chunks.all())
            return round(total_tokens / obj.total_chunks, 2)
        return 0
    
    def get_processing_time_formatted(self, obj):
        """Format processing time."""
        if obj.processing_time < 1:
            return f"{obj.processing_time * 1000:.0f}ms"
        else:
            return f"{obj.processing_time:.2f}s"


class ProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingJob model."""
    
    document = DocumentSerializer(read_only=True)
    chunking_methods = ChunkingMethodSerializer(many=True, read_only=True)
    chunking_results = ChunkingResultSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessingJob
        fields = [
            'id', 'document', 'chunking_methods', 'status', 'started_at',
            'completed_at', 'error_message', 'progress', 'configuration',
            'duration', 'chunking_results'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']

    def get_duration(self, obj):
        """Return duration in seconds (float) if started; includes running jobs."""
        try:
            from django.utils.timezone import now
            if obj.started_at and obj.completed_at:
                return (obj.completed_at - obj.started_at).total_seconds()
            if obj.started_at and not obj.completed_at:
                return (now() - obj.started_at).total_seconds()
            return None
        except Exception:
            return None


class ComparisonResultSerializer(serializers.ModelSerializer):
    """Serializer for ComparisonResult model."""
    
    compared_methods = ChunkingMethodSerializer(many=True, read_only=True)
    winner_method = ChunkingMethodSerializer(read_only=True)
    
    class Meta:
        model = ComparisonResult
        fields = [
            'id', 'processing_job', 'compared_methods', 'comparison_metrics',
            'winner_method', 'created_at'
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload."""
    
    class Meta:
        model = Document
        fields = ['name', 'file']
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 50MB.")
        
        # Check file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF, DOCX, and TXT files are allowed.")
        
        return value
    
    def create(self, validated_data):
        """Create document with additional metadata."""
        file = validated_data['file']
        
        # Determine file type
        content_type = file.content_type
        if content_type == 'application/pdf':
            file_type = 'pdf'
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            file_type = 'docx'
        elif content_type == 'text/plain':
            file_type = 'txt'
        else:
            file_type = 'txt'
        
        document = Document.objects.create(
            name=validated_data['name'],
            file=file,
            file_type=file_type,
            file_size=file.size,
            metadata={'content_type': content_type}
        )
        
        return document


class ProcessingJobCreateSerializer(serializers.Serializer):
    """Serializer for creating processing jobs."""
    
    chunking_method_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of chunking method IDs to use"
    )
    configuration = serializers.JSONField(
        default=dict,
        help_text="Job-specific configuration parameters"
    )
    
    def validate_chunking_method_ids(self, value):
        """Validate chunking method IDs."""
        if not value:
            raise serializers.ValidationError("At least one chunking method must be selected.")
        
        # Check if all methods exist and are active
        methods = ChunkingMethod.objects.filter(id__in=value, is_active=True)
        if len(methods) != len(value):
            raise serializers.ValidationError("One or more chunking methods are invalid or inactive.")
        
        return value


class ChunkingMethodConfigSerializer(serializers.Serializer):
    """Serializer for chunking method configuration."""
    
    chunk_size = serializers.IntegerField(min_value=100, max_value=4000, default=1000)
    chunk_overlap = serializers.IntegerField(min_value=0, max_value=500, default=200)
    semantic_threshold = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.7)
    preserve_structure = serializers.BooleanField(default=True)
    custom_separators = serializers.ListField(
        child=serializers.CharField(),
        default=list,
        required=False
    )
    table_aware = serializers.BooleanField(default=True)
    hierarchical_depth = serializers.IntegerField(min_value=1, max_value=10, default=3)
