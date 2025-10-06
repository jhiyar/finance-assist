"""
Deep Agent Service - Main orchestrator for the deep agents system.

This service coordinates document processing, query handling, and response generation
using LangGraph workflow and ChromaDB for persistent storage.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime

from deepagents import create_deep_agent

from .chroma_service import get_chroma_service
from .agents.document_agent import DocumentAgent
from .agents.query_agent import QueryAgent
from .agents.response_agent import ResponseAgent
from .prompts import DEEP_AGENT_INSTRUCTIONS, ERROR_MESSAGES, RESPONSE_TEMPLATES
from chat.models import DeepAgentSession

logger = logging.getLogger(__name__)


# Remove the custom state class - we'll use the built-in deep agent state


class DeepAgentService:
    """
    Main service for the deep agents system.
    
    This service orchestrates:
    1. Document processing and indexing
    2. Query analysis and retrieval
    3. Response generation and synthesis
    4. Session management
    5. LangGraph workflow execution
    """
    
    def __init__(
        self,
        documents_directory: str = "sample_documents",
        collection_name: str = "deep_agent_documents",
        enable_evaluation: bool = False
    ):
        self.documents_directory = documents_directory
        self.collection_name = collection_name
        self.enable_evaluation = enable_evaluation
        
        # Initialize agents
        self.document_agent = DocumentAgent()
        self.query_agent = QueryAgent()
        self.response_agent = ResponseAgent()
        self.chroma_service = get_chroma_service()
        
        # Initialize deep agent
        self.deep_agent = self._create_deep_agent()
        
        # Processing status
        self.documents_processed = False
        self.processing_timestamp = None
        
        logger.info("DeepAgentService initialized")
    
    def _create_deep_agent(self):
        """Create the deep agent with tools and instructions."""
        try:
            # Define tools for the deep agent
            tools = [
                self._document_search_tool,
                self._query_analysis_tool,
                self._response_generation_tool
            ]
            
            # Define instructions for the deep agent
            instructions = DEEP_AGENT_INSTRUCTIONS
            
            # Create the deep agent
            agent = create_deep_agent(
                tools=tools,
                instructions=instructions
            )
            
            logger.info("Deep agent created successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create deep agent: {e}")
            raise
    
    def _document_search_tool(self, query: str) -> str:
        """Tool for searching documents."""
        try:
            # Analyze the query first
            analysis = self.query_agent.analyze_query(query)
            
            # Retrieve documents
            retrieved_docs = self.query_agent.retrieve_documents(query, analysis, k=5)
            
            if not retrieved_docs:
                return ERROR_MESSAGES["no_documents_found"]
            
            # Format the retrieved documents
            results = []
            for i, (doc, score) in enumerate(retrieved_docs, 1):
                source = doc.metadata.get("source", "Unknown")
                title = doc.metadata.get("document_title", "Unknown Title")
                content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                
                results.append(RESPONSE_TEMPLATES["document_result_format"].format(
                    index=i, score=score, source=source, title=title, content=content
                ))
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return RESPONSE_TEMPLATES["error_response_format"].format(
                operation="searching documents", error_message=str(e)
            )
    
    def _query_analysis_tool(self, query: str) -> str:
        """Tool for analyzing queries."""
        try:
            analysis = self.query_agent.analyze_query(query)
            
            return RESPONSE_TEMPLATES["query_analysis_format"].format(
                query_type=analysis.get('query_type', 'Unknown'),
                information_depth=analysis.get('information_depth', 'Unknown'),
                retrieval_strategy=analysis.get('retrieval_strategy', 'Unknown'),
                complexity=analysis.get('complexity', 'Unknown'),
                response_format=analysis.get('response_format', 'Unknown'),
                confidence=analysis.get('confidence', 0.0),
                intent=analysis.get('intent', 'Unknown'),
                word_count=analysis.get('word_count', 0),
                has_question_words=analysis.get('has_question_words', False),
                has_technical_terms=analysis.get('has_technical_terms', False)
            )
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return RESPONSE_TEMPLATES["error_response_format"].format(
                operation="analyzing query", error_message=str(e)
            )
    
    def _response_generation_tool(self, query: str, context: str) -> str:
        """Tool for generating responses."""
        try:
            # This would be called by the deep agent with context from document search
            # For now, return a simple response
            return f"Based on the query '{query}' and the provided context, I can help you with that information."
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return RESPONSE_TEMPLATES["error_response_format"].format(
                operation="generating response", error_message=str(e)
            )
    
    def initialize_documents(self, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Initialize and process documents for the deep agent system.
        
        Args:
            force_reprocess: Whether to force reprocessing even if documents exist
            
        Returns:
            Dictionary with initialization results
        """
        try:
            # Get the full path to documents directory
            base_dir = Path(__file__).parent.parent.parent  # Go up to backend/
            docs_path = base_dir / self.documents_directory
            
            if not docs_path.exists():
                return {
                    "status": "error",
                    "error": f"Documents directory not found: {docs_path}",
                    "documents_processed": 0
                }
            
            # Check if documents are already processed
            chroma_info = self.chroma_service.get_collection_info()
            
            if chroma_info.get("document_count", 0) > 0 and not force_reprocess:
                self.documents_processed = True
                self.processing_timestamp = "loaded_from_chroma"
                
                return {
                    "status": "loaded_existing",
                    "documents_processed": chroma_info.get("document_count", 0),
                    "collection_info": chroma_info,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process documents
            logger.info("Processing documents for deep agent system...")
            result = self.document_agent.process_documents_from_directory(
                directory_path=str(docs_path),
                file_extensions=['.pdf', '.txt']
            )
            
            if result["status"] == "success":
                self.documents_processed = True
                self.processing_timestamp = result.get("timestamp", "unknown")
                
                logger.info("Document processing completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to initialize documents: {e}")
            return {
                "status": "error",
                "error": str(e),
                "documents_processed": False
            }
    
    def process_query(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using the deep agent.
        
        Args:
            query: User's query
            session_id: Optional session ID
            user_context: Optional user context
            
        Returns:
            Dictionary with query processing results
        """
        try:
            if not self.documents_processed:
                return {
                    "error": "Documents not processed. Call initialize_documents() first.",
                    "answer": ERROR_MESSAGES["documents_not_processed"],
                    "confidence": 0.0
                }
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Run the deep agent
            logger.info(f"Running deep agent for query: {query}")
            result = self.deep_agent.invoke({
                "messages": [{"role": "user", "content": query}]
            })
            
            # Extract the response from the deep agent result
            if result and "messages" in result:
                # Get the last message from the agent
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    if "content" in last_message:
                        answer = last_message["content"]
                    else:
                        answer = ERROR_MESSAGES["response_generation_failed"]
                else:
                    answer = ERROR_MESSAGES["response_generation_failed"]
            else:
                answer = ERROR_MESSAGES["response_generation_failed"]
            
            # Create response data
            response_data = {
                "answer": answer,
                "confidence": 0.8,  # Default confidence for deep agent responses
                "citations": [],
                "sources_used": [],
                "reasoning": "Generated using LangChain Deep Agent",
                "missing_info": [],
                "processing_time": 0.0,
                "response_type": "deep_agent",
                "document_count": 0,
                "session_id": session_id
            }
            
            # Store session in database
            self._store_session(session_id, query, response_data)
            
            logger.info(f"Query processed successfully with deep agent")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to process query '{query}': {e}")
            return {
                "error": str(e),
                "answer": f"{ERROR_MESSAGES['processing_error']} Query: '{query}'",
                "confidence": 0.0,
                "citations": [],
                "sources_used": []
            }
    
    def _store_session(
        self, 
        session_id: str, 
        query: str, 
        response_data: Dict[str, Any]
    ) -> None:
        """Store session data in the database."""
        try:
            DeepAgentSession.objects.create(
                session_id=session_id,
                user_query=query,
                agent_response=response_data.get("answer", ""),
                confidence_score=response_data.get("confidence", 0.0),
                sources_used=response_data.get("sources_used", []),
                processing_time=response_data.get("processing_time", 0.0),
                agent_type="deep_agent"
            )
            
            logger.info(f"Session stored: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store session: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service status and configuration."""
        try:
            chroma_info = self.chroma_service.get_collection_info()
            document_info = self.document_agent.get_document_info()
            retrieval_stats = self.query_agent.get_retrieval_stats()
            
            return {
                "service_name": "DeepAgentService",
                "documents_directory": self.documents_directory,
                "collection_name": self.collection_name,
                "enable_evaluation": self.enable_evaluation,
                "documents_processed": self.documents_processed,
                "processing_timestamp": self.processing_timestamp,
                "chroma_info": chroma_info,
                "document_info": document_info,
                "retrieval_stats": retrieval_stats,
                "deep_agent_status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get service info: {e}")
            return {
                "service_name": "DeepAgentService",
                "status": "error",
                "error": str(e)
            }
    
    def get_available_documents(self) -> List[Dict[str, Any]]:
        """Get list of available documents."""
        try:
            from chat.models import DocumentMetadata
            
            documents = DocumentMetadata.objects.all()
            return [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "summary": doc.summary,
                    "keywords": doc.keywords,
                    "source_path": doc.source_path,
                    "chunk_count": doc.chunk_count,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Failed to get available documents: {e}")
            return []
    
    def clear_cache(self):
        """Clear all caches and reset the service."""
        try:
            self.documents_processed = False
            self.processing_timestamp = None
            
            # Clear ChromaDB collection
            self.chroma_service.reset_collection()
            
            logger.info("Cleared all caches and reset service")
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


# Global service instance
_deep_agent_service = None


def get_deep_agent_service() -> DeepAgentService:
    """Get the global deep agent service instance."""
    global _deep_agent_service
    
    if _deep_agent_service is None:
        _deep_agent_service = DeepAgentService()
    
    return _deep_agent_service


def initialize_deep_agent_service(
    documents_directory: str = "sample_documents",
    collection_name: str = "deep_agent_documents",
    enable_evaluation: bool = False,
    force_reprocess: bool = False
) -> DeepAgentService:
    """Initialize the global deep agent service."""
    global _deep_agent_service
    
    _deep_agent_service = DeepAgentService(
        documents_directory=documents_directory,
        collection_name=collection_name,
        enable_evaluation=enable_evaluation
    )
    
    # Initialize documents
    result = _deep_agent_service.initialize_documents(force_reprocess=force_reprocess)
    
    if result["status"] in ["success", "loaded_existing"]:
        logger.info("Deep agent service initialized successfully")
    else:
        logger.error(f"Failed to initialize deep agent service: {result}")
    
    return _deep_agent_service
