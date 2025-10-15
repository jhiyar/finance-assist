from rest_framework import serializers
from .models import Profile, Transaction, Balance, DocumentMetadata, EnrichedChunk


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


