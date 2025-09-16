"""
Base LlamaIndex service with OpenAI LLM and embedding integration.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings

# LlamaIndex core imports
from llama_index.core import (
    VectorStoreIndex,
    Document,
    Settings,
    StorageContext,
    SimpleDocumentStore,
    SimpleVectorStore
)
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.llms import LLM
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser
from llama_index.core.schema import NodeWithScore, QueryBundle

# OpenAI integrations
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

# ChromaDB integration
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

logger = logging.getLogger(__name__)


class LlamaIndexBaseService:
    """Base service for LlamaIndex with OpenAI integration."""
    
    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.llm = None
        self.embed_model = None
        self.vector_store = None
        self.storage_context = None
        self.documents = []
        self.nodes = []
        
        # Initialize services
        self._initialize_openai_services()
        self._setup_global_settings()
        self._initialize_chroma_store()
    
    def _initialize_openai_services(self):
        """Initialize OpenAI LLM and embedding services."""
        try:
            # Get OpenAI API key from Django settings
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in Django settings")
            
            # Initialize LLM
            model_name = getattr(settings, 'OPENAI_MODEL_NAME', 'gpt-3.5-turbo')
            temperature = float(getattr(settings, 'OPENAI_TEMPERATURE', '0.1'))
            max_tokens = int(getattr(settings, 'OPENAI_MAX_TOKENS', '4096'))
            
            self.llm = OpenAI(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                api_key=api_key
            )
            
            # Initialize embeddings
            embedding_model = getattr(settings, 'OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
            self.embed_model = OpenAIEmbedding(
                model=embedding_model,
                api_key=api_key
            )
            
            logger.info(f"OpenAI services initialized - Model: {model_name}, Embedding: {embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI services: {e}")
            raise
    
    def _setup_global_settings(self):
        """Set up global LlamaIndex settings."""
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        logger.info("Global LlamaIndex settings configured")
    
    def _initialize_chroma_store(self):
        """Initialize ChromaDB vector store."""
        try:
            # Initialize ChromaDB client
            chroma_client = chromadb.PersistentClient(path="./chroma_db")
            
            # Get or create collection
            chroma_collection = chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            
            # Create LlamaIndex ChromaVectorStore
            self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            
            # Create storage context
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            logger.info(f"ChromaDB vector store initialized - Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def load_documents(self, documents: List[Document]) -> None:
        """Load documents into the service."""
        self.documents = documents
        logger.info(f"Loaded {len(documents)} documents")
    
    def create_nodes(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> List:
        """Create nodes from documents using text splitter."""
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.nodes = text_splitter.get_nodes_from_documents(self.documents)
        logger.info(f"Created {len(self.nodes)} nodes from documents")
        return self.nodes
    
    def create_hierarchical_nodes(self, chunk_sizes: List[int] = [512, 256, 128]) -> List:
        """Create hierarchical nodes for auto-merging retriever."""
        if not self.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=chunk_sizes
        )
        
        hierarchical_nodes = node_parser.get_nodes_from_documents(self.documents)
        logger.info(f"Created {len(hierarchical_nodes)} hierarchical nodes")
        return hierarchical_nodes
    
    def get_llm(self) -> LLM:
        """Get the configured LLM."""
        return self.llm
    
    def get_embed_model(self) -> BaseEmbedding:
        """Get the configured embedding model."""
        return self.embed_model
    
    def get_vector_store(self):
        """Get the vector store."""
        return self.vector_store
    
    def get_storage_context(self) -> StorageContext:
        """Get the storage context."""
        return self.storage_context
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            if self.vector_store and hasattr(self.vector_store, '_collection'):
                count = self.vector_store._collection.count()
                return {
                    'name': self.collection_name,
                    'document_count': count,
                    'collection_id': str(self.vector_store._collection.id)
                }
            else:
                return {"error": "Vector store not properly initialized"}
        except Exception as e:
            return {"error": f"Failed to get collection info: {str(e)}"}
    
    def clear_collection(self):
        """Clear the current collection."""
        try:
            if self.vector_store and hasattr(self.vector_store, '_collection'):
                # Delete all documents in the collection
                self.vector_store._collection.delete()
                logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
    
    def delete_collection(self):
        """Delete the current collection."""
        try:
            if self.vector_store and hasattr(self.vector_store, '_collection'):
                # Get the client and delete the collection
                client = self.vector_store._collection._client
                client.delete_collection(self.collection_name)
                logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")


def get_llamaindex_base_service(collection_name: str = "documents") -> LlamaIndexBaseService:
    """Get a LlamaIndex base service instance."""
    return LlamaIndexBaseService(collection_name=collection_name)
