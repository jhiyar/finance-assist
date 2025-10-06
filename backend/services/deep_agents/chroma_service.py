"""
ChromaDB Service for Deep Agents.

This module provides persistent vector storage using ChromaDB for the deep agents system.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class ChromaService:
    """
    Service for managing ChromaDB vector storage with persistent collections.
    """
    
    def __init__(
        self,
        persist_directory: str = "chroma_db",
        collection_name: str = "deep_agent_documents",
        embedding_model: str = "text-embedding-3-small"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embeddings using the existing OpenAI service
        self.openai_service = get_openai_service()
        self.embeddings = self.openai_service.get_langchain_embeddings()
        
        # Initialize vector store
        self.vector_store = None
        self._initialize_vector_store()
        
        logger.info(f"ChromaService initialized with collection: {collection_name}")
    
    def _initialize_vector_store(self):
        """Initialize the Chroma vector store."""
        try:
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Check if collection exists and has documents
            collection = self.client.get_collection(self.collection_name)
            count = collection.count()
            logger.info(f"Vector store initialized with {count} documents")
            
        except Exception as e:
            logger.warning(f"Collection {self.collection_name} not found, will be created: {e}")
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
    
    def add_documents(self, documents: List[Document], metadatas: Optional[List[Dict]] = None) -> bool:
        """
        Add documents to the ChromaDB collection.
        
        Args:
            documents: List of Document objects
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not documents:
                logger.warning("No documents provided to add")
                return False
            
            # Prepare metadata
            if metadatas is None:
                metadatas = [doc.metadata for doc in documents]
            
            # Add documents to vector store
            self.vector_store.add_documents(documents, metadatas=metadatas)
            
            logger.info(f"Successfully added {len(documents)} documents to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            return False
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        filter: Optional[Dict] = None
    ) -> List[Document]:
        """
        Perform similarity search in ChromaDB.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of Document objects
        """
        try:
            results = self.vector_store.similarity_search(
                query, 
                k=k, 
                filter=filter
            )
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4, 
        filter: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Perform similarity search with scores.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (Document, score) tuples
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query, 
                k=k, 
                filter=filter
            )
            logger.info(f"Found {len(results)} similar documents with scores for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search with score failed: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            collection = self.client.get_collection(self.collection_name)
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_model,
                "status": "error",
                "error": str(e)
            }
    
    def delete_collection(self) -> bool:
        """Delete the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def reset_collection(self) -> bool:
        """Reset the collection (delete and recreate)."""
        try:
            self.delete_collection()
            self._initialize_vector_store()
            logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False


# Global ChromaService instance
_chroma_service = None


def get_chroma_service() -> ChromaService:
    """Get the global ChromaService instance."""
    global _chroma_service
    
    if _chroma_service is None:
        _chroma_service = ChromaService()
    
    return _chroma_service
