from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
import json


class Document(models.Model):
    """Model for storing uploaded documents and their metadata."""
    
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
        ('md', 'Markdown'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'txt', 'md'])]
    )
    file_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    file_size = models.BigIntegerField()  # Size in bytes
    upload_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Document"
        verbose_name_plural = "Documents"
    
    def __str__(self):
        return f"{self.name} ({self.file_type})"


class ChunkingMethod(models.Model):
    """Model for storing available chunking methods and their configurations."""
    
    METHOD_TYPES = [
        ('unstructured', 'Unstructured.io'),
        ('llamaparse', 'LlamaParse'),
        ('hierarchical', 'Hierarchical Chunking'),
        ('semantic', 'Semantic Chunking'),
        ('recursive', 'Recursive Character Splitting'),
        ('sentence', 'Sentence-based Splitting'),
        ('token', 'Token-based Splitting'),
        ('financial', 'Financial Document Splitting'),
        ('hybrid', 'Hybrid Chunking'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    description = models.TextField()
    parameters = models.JSONField(default=dict)  # Default parameters for this method
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Chunking Method"
        verbose_name_plural = "Chunking Methods"
    
    def __str__(self):
        return f"{self.name} ({self.method_type})"


class ProcessingJob(models.Model):
    """Model for tracking document processing jobs."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='processing_jobs')
    chunking_methods = models.ManyToManyField(ChunkingMethod, related_name='processing_jobs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    progress = models.IntegerField(default=0)  # Progress percentage
    configuration = models.JSONField(default=dict)  # Job-specific configuration
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Processing Job"
        verbose_name_plural = "Processing Jobs"
    
    def __str__(self):
        return f"Job {self.id} - {self.document.name}"


class ChunkingResult(models.Model):
    """Model for storing results of chunking operations."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='chunking_results')
    chunking_method = models.ForeignKey(ChunkingMethod, on_delete=models.CASCADE, related_name='chunking_results')
    total_chunks = models.IntegerField()
    processing_time = models.FloatField()  # Time in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chunking Result"
        verbose_name_plural = "Chunking Results"
    
    def __str__(self):
        return f"Result {self.id} - {self.chunking_method.name}"


class Chunk(models.Model):
    """Model for storing individual document chunks."""
    
    CHUNK_TYPES = [
        ('text', 'Text'),
        ('table', 'Table'),
        ('header', 'Header'),
        ('list', 'List'),
        ('paragraph', 'Paragraph'),
        ('mixed', 'Mixed Content'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chunking_result = models.ForeignKey(ChunkingResult, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_type = models.CharField(max_length=20, choices=CHUNK_TYPES, default='text')
    chunk_index = models.IntegerField()  # Order within the document
    start_position = models.IntegerField()  # Character position in original document
    end_position = models.IntegerField()
    token_count = models.IntegerField()
    metadata = models.JSONField(default=dict)  # Additional chunk metadata
    parent_chunk = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_chunks')
    
    class Meta:
        ordering = ['chunking_result', 'chunk_index']
        verbose_name = "Chunk"
        verbose_name_plural = "Chunks"
    
    def __str__(self):
        return f"Chunk {self.chunk_index} - {self.chunking_result.chunking_method.name}"


class EvaluationMetric(models.Model):
    """Model for storing evaluation metrics for chunking results."""
    
    METRIC_TYPES = [
        ('chunk_size_distribution', 'Chunk Size Distribution'),
        ('overlap_analysis', 'Overlap Analysis'),
        ('context_preservation', 'Context Preservation Score'),
        ('structure_retention', 'Structure Retention Rate'),
        ('semantic_coherence', 'Semantic Coherence Score'),
        ('processing_efficiency', 'Processing Efficiency'),
        ('table_detection', 'Table Detection Rate'),
        ('hierarchical_preservation', 'Hierarchical Preservation'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chunking_result = models.ForeignKey(ChunkingResult, on_delete=models.CASCADE, related_name='evaluation_metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    metric_value = models.FloatField()
    metric_details = models.JSONField(default=dict)  # Additional metric details
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-calculated_at']
        verbose_name = "Evaluation Metric"
        verbose_name_plural = "Evaluation Metrics"
    
    def __str__(self):
        return f"{self.metric_type} - {self.chunking_result.chunking_method.name}"


class ComparisonResult(models.Model):
    """Model for storing comparison results between different chunking methods."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='comparison_results')
    compared_methods = models.ManyToManyField(ChunkingMethod, related_name='comparison_results')
    comparison_metrics = models.JSONField(default=dict)  # Comparison results
    winner_method = models.ForeignKey(ChunkingMethod, on_delete=models.CASCADE, null=True, blank=True, related_name='winning_comparisons')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Comparison Result"
        verbose_name_plural = "Comparison Results"
    
    def __str__(self):
        return f"Comparison {self.id} - {self.processing_job.document.name}"
