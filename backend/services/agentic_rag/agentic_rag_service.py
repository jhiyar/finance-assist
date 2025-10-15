"""
Main Enhanced Agentic-RAG Service.

This module provides the main service class that orchestrates the complete
Enhanced Agentic-RAG workflow for the Django application.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .document_readers.enriched_document_processor import EnrichedDocumentProcessor
from .langgraph.agentic_rag_graph import AgenticRAGGraph
from .hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class AgenticRAGService:
    """
    Main service class for Enhanced Agentic-RAG.
    
    This service provides a high-level interface for:
    1. Document processing and indexing
    2. Query processing with agentic workflow
    3. Integration with Django views
    """
    
    def __init__(
        self,
        documents_directory: str = "sample_documents",
        model_name: str = "gpt-4o-mini",
        enable_evaluation: bool = False,
        collection_name: str = "finance_documents",
        max_tokens: int = 4000
    ):
        self.documents_directory = documents_directory
        self.model_name = model_name
        self.enable_evaluation = enable_evaluation
        self.collection_name = collection_name
        self.max_tokens = max_tokens
        
        # Initialize components
        self.document_processor = EnrichedDocumentProcessor(
            collection_name=collection_name
        )
        self.hybrid_retriever = HybridRetriever()
        self.agentic_graph = None
        
        # Processing status
        self.documents_processed = False
        self.processing_timestamp = None
        
        print(f"AgenticRAGService initialized with model: {model_name}")
    
    def initialize_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Initialize and process documents for the agentic RAG system.
        
        Args:
            force_reprocess: Whether to force reprocessing even if artifacts exist
            
        Returns:
            Dictionary with initialization results
        """
        # try:
        # Get the full path to documents directory
        base_dir = Path(__file__).parent.parent.parent  # Go up to backend/
        docs_path = base_dir / self.documents_directory
        
        if not docs_path.exists():
            raise FileNotFoundError(f"Documents directory not found: {docs_path}")
        
        # Check if artifacts already exist
        artifacts_path = docs_path / "agentic_rag_artifacts"
        
        if artifacts_path.exists() and not force_reprocess:
            print("Loading existing artifacts...")
            self.document_processor.load_artifacts(str(artifacts_path))
            self.documents_processed = True
            self.processing_timestamp = "loaded_from_artifacts"
            
            # Build hybrid retriever index
            self._build_hybrid_retriever_index()
            
            # Initialize agentic graph
            self._initialize_agentic_graph()
            
            return {
                "status": "loaded_existing",
                "documents_processed": len(self.document_processor.documents_metadata),
                "total_chunks": len(self.document_processor.enriched_chunks),
                "vector_store_available": self.document_processor.vector_store is not None
            }
        
        # Process documents
        print("Processing documents...")
        result = self.document_processor.process_documents_from_directory(
            directory_path=str(docs_path),
            file_extensions=['.pdf', '.txt']
        )

        print(f"Document processing result: {result}", flush=True)
        
        if result["status"] == "success":
            self.documents_processed = True
            self.processing_timestamp = result.get("timestamp", "unknown")
            
            # Build hybrid retriever index
            self._build_hybrid_retriever_index()
            
            # Initialize agentic graph
            self._initialize_agentic_graph()
            
            print("Document processing completed successfully")
        
        return result
            
        # except Exception as e:
        #     print(f"Failed to initialize documents: {e}", flush=True)
        #     return {
        #         "status": "error",
        #         "error": str(e),
        #         "documents_processed": False
        #     }
    
    def _build_hybrid_retriever_index(self):
        """Build the hybrid retriever index from processed documents."""
        # try:
        if not self.document_processor.enriched_chunks:
            raise ValueError("No enriched chunks available for hybrid retriever")
        
        # Convert enriched chunks to documents
        from langchain_core.documents import Document
        documents = []
        
        for chunk in self.document_processor.enriched_chunks:
            # Ensure metadata is a dictionary
            chunk_metadata = chunk.metadata if isinstance(chunk.metadata, dict) else {}
            
            # Ensure keywords is a list
            keywords = chunk.keywords if isinstance(chunk.keywords, list) else []
            
            doc = Document(
                page_content=chunk.content,
                metadata={
                    **chunk_metadata,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "summary": chunk.summary,
                    "keywords": keywords,
                    "faq": chunk.faq
                }
            )
            documents.append(doc)
        
        # Build hybrid retriever index
        self.hybrid_retriever.build_index(documents)
        
        print(f"Built hybrid retriever index with {len(documents)} documents")
        
        # except Exception as e:
        #     logger.error(f"Failed to build hybrid retriever index: {e}")
        #     raise
    
    def _initialize_agentic_graph(self):
        """Initialize the agentic RAG graph."""
        try:
            self.agentic_graph = AgenticRAGGraph(
                document_processor=self.document_processor,
                hybrid_retriever=self.hybrid_retriever,
                model_name=self.model_name,
                enable_evaluation=self.enable_evaluation,
                max_tokens=self.max_tokens
            )
            
            print("Initialized agentic RAG graph")
            
        except Exception as e:
            logger.error(f"Failed to initialize agentic graph: {e}")
            raise
    
    def process_query(
        self, 
        query: str, 
        user_context: Optional[str] = None,
        golden_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using the Enhanced Agentic-RAG workflow.
        
        Args:
            query: User query
            user_context: Additional user context (optional)
            golden_reference: Golden reference for evaluation (optional)
            
        Returns:
            Dictionary with query processing results
        """
        try:
            if not self.documents_processed:
                return {
                    "error": "Documents not processed. Call initialize_documents() first.",
                    "answer": "I apologize, but the document processing system is not ready. Please try again later.",
                    "confidence": 0.0
                }
            
            if not self.agentic_graph:
                return {
                    "error": "Agentic graph not initialized.",
                    "answer": "I apologize, but the query processing system is not ready. Please try again later.",
                    "confidence": 0.0
                }
            
            # Run the agentic workflow
            result = self.agentic_graph.run_workflow(
                query=query,
                user_context=user_context,
                golden_reference=golden_reference
            )
            
            print(f"Processed query: '{query}' with confidence: {result.get('confidence', 0.0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process query '{query}': {e}")
            return {
                "error": str(e),
                "answer": f"I apologize, but I encountered an error while processing your query: '{query}'. Please try again.",
                "confidence": 0.0,
                "citations": [],
                "sources_used": []
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service status and configuration."""
        return {
            "model_name": self.model_name,
            "enable_evaluation": self.enable_evaluation,
            "collection_name": self.collection_name,
            "max_tokens": self.max_tokens,
            "documents_processed": self.documents_processed,
            "processing_timestamp": self.processing_timestamp,
            "documents_directory": self.documents_directory,
            "document_processor_info": self.document_processor.get_processing_info() if self.document_processor else None,
            "hybrid_retriever_info": self.hybrid_retriever.get_retrieval_stats() if self.hybrid_retriever else None,
            "agentic_graph_info": self.agentic_graph.get_workflow_info() if self.agentic_graph else None
        }
    
    def get_available_documents(self) -> List[Dict[str, Any]]:
        """Get list of available documents."""
        if not self.document_processor:
            return []
        
        return self.document_processor.get_document_list()
    
    def clear_cache(self):
        """Clear all caches and reset the service."""
        try:
            self.documents_processed = False
            self.processing_timestamp = None
            self.agentic_graph = None
            
            # Clear document processor
            if self.document_processor:
                self.document_processor.documents_metadata = []
                self.document_processor.enriched_chunks = []
                self.document_processor.vector_store = None
            
            # Clear hybrid retriever
            if self.hybrid_retriever:
                self.hybrid_retriever.bm25_index = None
                self.hybrid_retriever.bm25_documents = []
                self.hybrid_retriever.document_texts = []
            
            print("Cleared all caches and reset service")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


# Global service instance
_agentic_rag_service = None


def get_agentic_rag_service() -> AgenticRAGService:
    """Get the global agentic RAG service instance."""
    global _agentic_rag_service
    
    if _agentic_rag_service is None:
        _agentic_rag_service = AgenticRAGService(max_tokens=4000)
    
    return _agentic_rag_service


def initialize_agentic_rag_service(
    documents_directory: str = "sample_documents",
    model_name: str = "gpt-4o-mini",
    enable_evaluation: bool = False,
    force_reprocess: bool = False,
    max_tokens: int = 4000
) -> AgenticRAGService:
    """Initialize the global agentic RAG service."""
    global _agentic_rag_service
    
    _agentic_rag_service = AgenticRAGService(
        documents_directory=documents_directory,
        model_name=model_name,
        enable_evaluation=enable_evaluation,
        max_tokens=max_tokens
    )
    
    # Initialize documents
    result = _agentic_rag_service.initialize_documents(force_reprocess=force_reprocess)
    
    if result["status"] in ["success", "loaded_existing"]:
        print("Agentic RAG service initialized successfully")
    else:
        logger.error(f"Failed to initialize agentic RAG service: {result}")
    
    return _agentic_rag_service
