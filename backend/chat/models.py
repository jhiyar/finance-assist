from django.db import models
import json


class Profile(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=255)
    amount_minor = models.IntegerField()  # Amount in minor units (pennies)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def __str__(self):
        return f"{self.date} - {self.description}"


class Balance(models.Model):
    amount_minor = models.IntegerField(default=0)  # Balance in minor units (pennies)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balance"
        verbose_name_plural = "Balances"

    def __str__(self):
        return f"Balance: {self.amount_minor} minor units"


class DocumentMetadata(models.Model):
    """Store document metadata from the enriched document processor."""
    title = models.CharField(max_length=500)
    summary = models.TextField()
    keywords = models.JSONField(default=list)  # Store as JSON array
    faqs = models.JSONField(default=list)  # Store as JSON array
    source_path = models.CharField(max_length=1000)
    chunk_count = models.IntegerField(default=0)
    processing_timestamp = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document Metadata"
        verbose_name_plural = "Document Metadata"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.chunk_count} chunks)"


class EnrichedChunk(models.Model):
    """Store enriched document chunks with LLM-generated content."""
    document_metadata = models.ForeignKey(DocumentMetadata, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    summary = models.TextField()
    keywords = models.JSONField(default=list)
    faq = models.TextField(blank=True, null=True)
    chunk_id = models.CharField(max_length=100, unique=True)
    document_id = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)  # Store additional metadata as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Enriched Chunk"
        verbose_name_plural = "Enriched Chunks"
        ordering = ['document_metadata', 'chunk_id']

    def __str__(self):
        return f"Chunk {self.chunk_id} from {self.document_metadata.title}"


class DeepAgentSession(models.Model):
    """Track deep agent chat sessions."""
    session_id = models.CharField(max_length=100, unique=True)
    user_query = models.TextField()
    agent_response = models.TextField()
    confidence_score = models.FloatField(default=0.0)
    sources_used = models.JSONField(default=list)
    processing_time = models.FloatField(default=0.0)  # in seconds
    agent_type = models.CharField(max_length=50, default='deep_agent')  # deep_agent, document_agent, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Deep Agent Session"
        verbose_name_plural = "Deep Agent Sessions"
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id} - {self.user_query[:50]}..."
