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


class Conversation(models.Model):
    """Store conversation sessions for chat functionality."""
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional: Link to a user profile if you have user authentication
    # profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Conversation {self.id}"

    def get_message_count(self):
        """Get the number of messages in this conversation."""
        return self.messages.count()

    def get_last_message(self):
        """Get the last message in this conversation."""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Store individual messages within conversations."""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store additional metadata for RAG responses
    retriever_type = models.CharField(max_length=50, blank=True, null=True)  # 'hybrid_search', 'agentic_rag', etc.
    source = models.CharField(max_length=50, blank=True, null=True)  # 'hybrid_search', 'agentic_rag', 'intent_detection'
    confidence = models.FloatField(blank=True, null=True)
    
    # Store sources and citations for RAG responses
    sources = models.JSONField(default=list, blank=True)  # List of source documents
    citations = models.JSONField(default=list, blank=True)  # List of citations
    search_stats = models.JSONField(default=dict, blank=True)  # Search statistics
    
    # Store processing details for agentic RAG
    rag_details = models.JSONField(default=dict, blank=True)  # Processing info, reasoning, etc.

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

    def get_conversation_title(self):
        """Get the conversation title this message belongs to."""
        return self.conversation.title or f"Conversation {self.conversation.id}"


class DeepAgentSession(models.Model):
    """Store sessions for deep agent interactions (legacy model - keeping for compatibility)."""
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Deep Agent Session"
        verbose_name_plural = "Deep Agent Sessions"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session {self.session_id}"


