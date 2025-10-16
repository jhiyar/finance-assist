"""
New Planner-Orchestrator Agentic RAG Service.

This module provides the main service class that orchestrates the complete
Planner-Orchestrator Agentic RAG workflow for the Django application.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .document_readers.enriched_document_processor import EnrichedDocumentProcessor
from .planner_orchestrator_graph import PlannerOrchestratorGraph
from .hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class AgenticRAGService:
    """
    Main service class for the new Planner-Orchestrator Agentic RAG.
    
    This service provides a high-level interface for:
    1. Document processing and indexing
    2. Query processing with planner-orchestrator workflow
    3. Integration with Django views
    """
    
    def __init__(
        self,
        documents_directory: str = "sample_documents",
        model_name: str = "gpt-4o-mini",
        collection_name: str = "finance_documents",
        max_tokens: int = 4000,
        enable_reflection: bool = False,
        max_iterations: int = 3
    ):
        self.documents_directory = documents_directory
        self.model_name = model_name
        self.collection_name = collection_name
        self.max_tokens = max_tokens
        self.enable_reflection = enable_reflection
        self.max_iterations = max_iterations
        
        # Initialize components
        self.document_processor = EnrichedDocumentProcessor(
            collection_name=collection_name
        )
        self.hybrid_retriever = HybridRetriever()
        self.planner_orchestrator_graph = None
        self.available_documents = []
        
        # Processing status
        self.documents_processed = False
        self.processing_timestamp = None
        
        print(f"New AgenticRAGService initialized with model: {model_name}, reflection: {enable_reflection}")
    
    def initialize_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Initialize and process documents for the agentic RAG system.
        
        Args:
            force_reprocess: Whether to force reprocessing even if artifacts exist
            
        Returns:
            Dictionary with initialization results
        """
        try:
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
                
                # Get available documents list
                self._load_available_documents()
                
                # Initialize planner-orchestrator graph
                self._initialize_planner_orchestrator_graph()
                
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
                
                # Get available documents list
                self._load_available_documents()
                
                # Initialize planner-orchestrator graph
                self._initialize_planner_orchestrator_graph()
                
                print("Document processing completed successfully")
            
            return result
                
        except Exception as e:
            print(f"Failed to initialize documents: {e}", flush=True)
            return {
                "status": "error",
                "error": str(e),
                "documents_processed": False
            }
    
    def _build_hybrid_retriever_index(self):
        """Build the hybrid retriever index from processed documents."""
        try:
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
            
        except Exception as e:
            logger.error(f"Failed to build hybrid retriever index: {e}")
            raise
    
    def _load_available_documents(self):
        """Load list of available documents for planning."""
        try:
            self.available_documents = self.document_processor.get_document_list()
            print(f"Loaded {len(self.available_documents)} available documents")
        except Exception as e:
            logger.error(f"Failed to load available documents: {e}")
            self.available_documents = []
    
    def _initialize_planner_orchestrator_graph(self):
        """Initialize the planner-orchestrator graph."""
        try:
            self.planner_orchestrator_graph = PlannerOrchestratorGraph(
                model_name=self.model_name,
                available_documents=self.available_documents,
                enable_reflection=self.enable_reflection,
                max_iterations=self.max_iterations
            )
            
            print("Initialized planner-orchestrator graph")
            
        except Exception as e:
            logger.error(f"Failed to initialize planner-orchestrator graph: {e}")
            raise
    
    def process_query(
        self, 
        query: str, 
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using the new Planner-Orchestrator workflow.
        
        Args:
            query: User query
            user_context: Additional user context (optional)
            
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
            
            if not self.planner_orchestrator_graph:
                return {
                    "error": "Planner-orchestrator graph not initialized.",
                    "answer": "I apologize, but the query processing system is not ready. Please try again later.",
                    "confidence": 0.0
                }
            
            # Run the planner-orchestrator workflow
            result = self.planner_orchestrator_graph.run_workflow(
                query=query,
                user_context=user_context
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
                "sources_used": [],
                "execution_summary": f"Query processing failed: {str(e)}",
                # Backward compatibility fields
                "reasoning": {
                    "planning": "Planning failed",
                    "execution_summary": f"Query processing failed: {str(e)}"
                },
                "confidence_scores": {
                    "final_confidence": 0.0,
                    "planning_confidence": 0.0
                },
                "processing_info": {},
                "errors": [str(e)],
                "timestamp": datetime.now().isoformat()
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service status and configuration."""
        return {
            "model_name": self.model_name,
            "collection_name": self.collection_name,
            "max_tokens": self.max_tokens,
            "enable_reflection": self.enable_reflection,
            "max_iterations": self.max_iterations,
            "documents_processed": self.documents_processed,
            "processing_timestamp": self.processing_timestamp,
            "documents_directory": self.documents_directory,
            "available_documents_count": len(self.available_documents),
            "document_processor_info": self.document_processor.get_processing_info() if self.document_processor else None,
            "hybrid_retriever_info": self.hybrid_retriever.get_retrieval_stats() if self.hybrid_retriever else None,
            "planner_orchestrator_info": self.planner_orchestrator_graph.get_workflow_info() if self.planner_orchestrator_graph else None
        }
    
    def get_available_documents(self) -> List[Dict[str, Any]]:
        """Get list of available documents."""
        return self.available_documents
    
    def get_execution_report(self, query: str, user_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a detailed execution report for a query without processing it.
        This is useful for debugging and monitoring.
        """
        try:
            if not self.planner_orchestrator_graph:
                return {"error": "Planner-orchestrator graph not initialized"}
            
            # Get workflow info
            workflow_info = self.planner_orchestrator_graph.get_workflow_info()
            
            return {
                "query": query,
                "user_context": user_context,
                "workflow_info": workflow_info,
                "available_documents": len(self.available_documents),
                "service_status": {
                    "documents_processed": self.documents_processed,
                    "processing_timestamp": self.processing_timestamp
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get execution report: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear all caches and reset the service."""
        try:
            self.documents_processed = False
            self.processing_timestamp = None
            self.planner_orchestrator_graph = None
            self.available_documents = []
            
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
        _agentic_rag_service = AgenticRAGService(max_tokens=4000, enable_reflection=False)
    
    return _agentic_rag_service


def initialize_agentic_rag_service(
    documents_directory: str = "sample_documents",
    model_name: str = "gpt-4o-mini",
    force_reprocess: bool = False,
    max_tokens: int = 4000,
    enable_reflection: bool = False,
    max_iterations: int = 3
) -> AgenticRAGService:
    """Initialize the global agentic RAG service."""
    global _agentic_rag_service
    
    _agentic_rag_service = AgenticRAGService(
        documents_directory=documents_directory,
        model_name=model_name,
        max_tokens=max_tokens,
        enable_reflection=enable_reflection,
        max_iterations=max_iterations
    )
    
    # Initialize documents
    result = _agentic_rag_service.initialize_documents(force_reprocess=force_reprocess)
    
    if result["status"] in ["success", "loaded_existing"]:
        print("New Planner-Orchestrator Agentic RAG service initialized successfully")
    else:
        logger.error(f"Failed to initialize agentic RAG service: {result}")
    
    return _agentic_rag_service
