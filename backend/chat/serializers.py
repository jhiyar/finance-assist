from rest_framework import serializers
from .models import Profile, Transaction, Balance, DocumentMetadata, EnrichedChunk, Conversation, Message, ConfluenceDocument


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'name', 'address', 'email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'date', 'description', 'amount_minor', 'created_at']
        read_only_fields = ['id', 'created_at']


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ['id', 'amount_minor', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    retriever_type = serializers.CharField(max_length=20, required=False, default='vector_store')


class ChatResponseSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=20)
    text = serializers.CharField(required=False, allow_blank=True)
    actionType = serializers.CharField(required=False, allow_blank=True)
    widget = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    fields = serializers.ListField(child=serializers.CharField(), required=False)
    source = serializers.CharField(required=False, allow_blank=True)
    retriever_type = serializers.CharField(required=False, allow_blank=True)
    confidence = serializers.FloatField(required=False)
    citations = serializers.ListField(required=False)
    sources_used = serializers.ListField(required=False)
    rag_details = serializers.DictField(required=False)


class DocumentMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentMetadata
        fields = ['id', 'title', 'summary', 'keywords', 'faqs', 'source_path', 
                 'chunk_count', 'processing_timestamp', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EnrichedChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnrichedChunk
        fields = ['id', 'document_metadata', 'content', 'summary', 'keywords', 
                 'faq', 'chunk_id', 'document_id', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    message_type_display = serializers.CharField(source='get_message_type_display', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'content', 'message_type', 'message_type_display',
            'created_at', 'retriever_type', 'source', 'confidence',
            'sources', 'citations', 'search_stats', 'rag_details'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        """Create a new message and update conversation timestamp."""
        message = Message.objects.create(**validated_data)
        # Update conversation's updated_at timestamp
        message.conversation.save()
        return message


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversations with summary info."""
    message_count = serializers.IntegerField(source='get_message_count', read_only=True)
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'message_count', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the last message preview."""
        last_message = obj.get_last_message()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
            }
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation details with all messages."""
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='get_message_count', read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'is_active', 'message_count', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create a new conversation."""
        # Generate title from first message if not provided
        if not validated_data.get('title'):
            validated_data['title'] = 'New Conversation'
        return Conversation.objects.create(**validated_data)


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new conversations."""
    
    class Meta:
        model = Conversation
        fields = ['title']
        
    def create(self, validated_data):
        """Create a new conversation."""
        if not validated_data.get('title'):
            validated_data['title'] = 'New Conversation'
        return Conversation.objects.create(**validated_data)


class ConversationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating conversation properties."""
    
    class Meta:
        model = Conversation
        fields = ['title', 'is_active']


class ConfluenceDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Confluence documents."""
    is_outdated = serializers.ReadOnlyField()
    
    class Meta:
        model = ConfluenceDocument
        fields = [
            'id', 'confluence_id', 'title', 'content', 'html_content',
            'space_key', 'space_name', 'version', 'url', 'ancestors',
            'parent_id', 'confluence_created', 'confluence_modified',
            'created_at', 'updated_at', 'is_indexed', 'last_indexed',
            'indexing_error', 'is_outdated'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_outdated']


class ConfluenceFetchSerializer(serializers.Serializer):
    """Serializer for Confluence fetch requests."""
    parent_id = serializers.CharField(max_length=50, default="27394188")
    force_refresh = serializers.BooleanField(default=False)


class ConfluenceIndexSerializer(serializers.Serializer):
    """Serializer for Confluence indexing requests."""
    document_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of document IDs to index. If empty, indexes all documents."
    )
    force_reindex = serializers.BooleanField(default=False)

