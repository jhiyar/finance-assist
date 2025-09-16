"""
Workflow state definition for Enhanced Agentic-RAG LangGraph.

This module defines the state structure used throughout the LangGraph workflow.
"""

from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.documents import Document


class AgenticRAGState(TypedDict):
    """
    State structure for the Enhanced Agentic-RAG workflow.
    
    This state is passed between nodes in the LangGraph workflow and contains
    all the information needed for the agentic RAG pipeline.
    """
    
    # Input
    original_query: str
    user_context: Optional[str]
    
    # Query Optimization
    optimized_query: str
    sub_queries: List[str]
    query_optimization_reasoning: str
    query_optimization_confidence: float
    
    # Source Identification
    available_documents: List[Dict[str, Any]]
    selected_documents: List[Dict[str, Any]]
    source_selection_reasoning: str
    source_selection_confidence: float
    
    # Retrieval
    vector_search_results: List[Document]
    bm25_search_results: List[Document]
    hybrid_search_results: List[Document]
    hybrid_retrieval_reasoning: str
    
    # Post-Processing
    post_processed_documents: List[Document]
    duplicates_removed: int
    reordering_applied: bool
    quality_scores: List[float]
    post_processing_reasoning: str
    
    # Answer Generation
    generated_answer: str
    citations: List[Dict[str, Any]]
    answer_confidence: float
    answer_reasoning: str
    sources_used: List[str]
    
    # Evaluation (optional)
    golden_reference: Optional[str]
    evaluation_result: Optional[Dict[str, Any]]
    evaluation_scores: Optional[Dict[str, float]]
    
    # Metadata
    processing_timestamp: str
    workflow_version: str
    error_messages: List[str]
    debug_info: Dict[str, Any]
