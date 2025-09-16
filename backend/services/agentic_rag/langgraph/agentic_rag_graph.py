"""
Enhanced Agentic-RAG LangGraph workflow implementation.

This module implements the main LangGraph workflow that orchestrates all
the agentic components in the Enhanced Agentic-RAG pipeline.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.documents import Document

from .workflow_state import AgenticRAGState
from ..agents.query_optimizer import QueryOptimizerAgent
from ..agents.source_identifier import SourceIdentifierAgent
from ..agents.post_processor import PostProcessorAgent
from ..agents.answer_generator import AnswerGeneratorAgent
from ..agents.evaluator import EvaluatorAgent
from ..document_readers.enriched_document_processor import EnrichedDocumentProcessor

logger = logging.getLogger(__name__)


class AgenticRAGGraph:
    """
    Enhanced Agentic-RAG workflow implemented as a LangGraph.
    
    This workflow orchestrates the following steps:
    1. Query Optimization
    2. Source Identification
    3. Hybrid Retrieval (Vector + BM25)
    4. Post-Processing
    5. Answer Generation
    6. Evaluation (optional)
    """
    
    def __init__(
        self,
        document_processor: EnrichedDocumentProcessor,
        hybrid_retriever,
        model_name: str = "gpt-4o-mini",
        enable_evaluation: bool = False,
        max_tokens: int = 4000
    ):
        self.document_processor = document_processor
        self.hybrid_retriever = hybrid_retriever
        self.model_name = model_name
        self.enable_evaluation = enable_evaluation
        self.max_tokens = max_tokens
        
        # Initialize agents
        self.query_optimizer = QueryOptimizerAgent(model_name)
        self.source_identifier = SourceIdentifierAgent(model_name)
        self.post_processor = PostProcessorAgent(model_name)
        self.answer_generator = AnswerGeneratorAgent(model_name, max_tokens=max_tokens)
        
        if enable_evaluation:
            self.evaluator = EvaluatorAgent(model_name)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        logger.info(f"AgenticRAGGraph initialized with model: {model_name}, evaluation: {enable_evaluation}")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create the state graph
        workflow = StateGraph(AgenticRAGState)
        
        # Add nodes
        workflow.add_node("query_optimizer", self._query_optimizer_node)
        workflow.add_node("source_identifier", self._source_identifier_node)
        workflow.add_node("hybrid_retriever", self._hybrid_retriever_node)
        workflow.add_node("post_processor", self._post_processor_node)
        workflow.add_node("answer_generator", self._answer_generator_node)
        
        if self.enable_evaluation:
            workflow.add_node("evaluator", self._evaluator_node)
        
        # Define the workflow edges
        workflow.set_entry_point("query_optimizer")
        
        workflow.add_edge("query_optimizer", "source_identifier")
        workflow.add_edge("source_identifier", "hybrid_retriever")
        workflow.add_edge("hybrid_retriever", "post_processor")
        workflow.add_edge("post_processor", "answer_generator")
        
        if self.enable_evaluation:
            workflow.add_edge("answer_generator", "evaluator")
            workflow.add_edge("evaluator", END)
        else:
            workflow.add_edge("answer_generator", END)
        
        # Compile the workflow
        return workflow.compile()
    
    def _query_optimizer_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Query optimization node."""
        try:
            logger.info("Starting query optimization")
            
            # Get available documents for context
            available_docs = self.document_processor.get_document_list()
            
            # Optimize the query
            optimization_result = self.query_optimizer.optimize_query(
                query=state["original_query"],
                available_documents=available_docs,
                context=state.get("user_context")
            )
            
            # Update state
            state["optimized_query"] = optimization_result.optimized_query
            state["sub_queries"] = optimization_result.sub_queries
            state["query_optimization_reasoning"] = optimization_result.optimization_reasoning
            state["query_optimization_confidence"] = optimization_result.confidence_score
            state["available_documents"] = available_docs
            
            logger.info(f"Query optimized: '{state['original_query']}' -> '{state['optimized_query']}'")
            
        except Exception as e:
            error_msg = f"Query optimization failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: use original query
            state["optimized_query"] = state["original_query"]
            state["sub_queries"] = [state["original_query"]]
            state["query_optimization_reasoning"] = "Query optimization failed, using original query"
            state["query_optimization_confidence"] = 0.0
        
        return state
    
    def _source_identifier_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Source identification node."""
        try:
            logger.info("Starting source identification")
            
            # Identify relevant sources
            source_result = self.source_identifier.identify_sources(
                query=state["optimized_query"],
                available_documents=state["available_documents"],
                max_documents=3
            )
            
            # Update state
            state["selected_documents"] = source_result.selected_documents
            state["source_selection_reasoning"] = source_result.selection_reasoning
            state["source_selection_confidence"] = source_result.confidence_score
            
            logger.info(f"Source identification: selected {len(source_result.selected_documents)} documents")
            
        except Exception as e:
            error_msg = f"Source identification failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: use all available documents
            state["selected_documents"] = state["available_documents"][:5]
            state["source_selection_reasoning"] = "Source identification failed, using all available documents"
            state["source_selection_confidence"] = 0.0
        
        return state
    
    def _hybrid_retriever_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Hybrid retrieval node (Vector + BM25)."""
        try:
            logger.info("Starting hybrid retrieval")
            
            # Get selected document titles for filtering
            selected_titles = [doc["title"] for doc in state["selected_documents"]]
            
            # Use the hybrid retriever to perform search
            hybrid_result = self.hybrid_retriever.search(
                query=state["optimized_query"],
                filter_documents=selected_titles
            )
            
            # Update state with hybrid retrieval results
            state["vector_search_results"] = hybrid_result.vector_results
            state["bm25_search_results"] = hybrid_result.bm25_results
            state["hybrid_search_results"] = hybrid_result.hybrid_results
            state["hybrid_retrieval_reasoning"] = hybrid_result.retrieval_reasoning
            
            logger.info(f"Hybrid retrieval: found {len(hybrid_result.hybrid_results)} documents")
            
        except Exception as e:
            error_msg = f"Hybrid retrieval failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: empty results
            state["vector_search_results"] = []
            state["bm25_search_results"] = []
            state["hybrid_search_results"] = []
            state["hybrid_retrieval_reasoning"] = "Hybrid retrieval failed"
        
        return state
    
    def _post_processor_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Post-processing node."""
        try:
            logger.info("Starting post-processing")
            
            # Post-process the retrieved documents
            post_processing_result = self.post_processor.process_documents(
                documents=state["hybrid_search_results"],
                query=state["optimized_query"],
                remove_duplicates=True,
                reorder_by_position=True,
                assess_quality=True
            )
            
            # Update state
            state["post_processed_documents"] = post_processing_result.processed_documents
            state["duplicates_removed"] = post_processing_result.duplicates_removed
            state["reordering_applied"] = post_processing_result.reordering_applied
            state["quality_scores"] = post_processing_result.quality_scores
            state["post_processing_reasoning"] = post_processing_result.processing_reasoning
            
            logger.info(f"Post-processing: {len(post_processing_result.processed_documents)} documents processed")
            
        except Exception as e:
            error_msg = f"Post-processing failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: use original results
            state["post_processed_documents"] = state["hybrid_search_results"]
            state["duplicates_removed"] = 0
            state["reordering_applied"] = False
            state["quality_scores"] = [0.5] * len(state["hybrid_search_results"])
            state["post_processing_reasoning"] = "Post-processing failed, using original results"
        
        return state
    
    def _answer_generator_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Answer generation node."""
        try:
            logger.info("Starting answer generation")
            
            # Generate the final answer
            answer_result = self.answer_generator.generate_answer(
                original_query=state["original_query"],
                optimized_queries=state["sub_queries"],
                context_documents=state["post_processed_documents"],
                query_optimization_reasoning=state["query_optimization_reasoning"],
                source_selection_reasoning=state["source_selection_reasoning"],
                post_processing_reasoning=state["post_processing_reasoning"]
            )
            
            # Update state
            state["generated_answer"] = answer_result.generated_answer
            state["citations"] = answer_result.citations
            state["answer_confidence"] = answer_result.confidence_score
            state["answer_reasoning"] = answer_result.reasoning
            state["sources_used"] = answer_result.sources_used
            
            logger.info(f"Answer generated with confidence: {answer_result.confidence_score}")
            
        except Exception as e:
            error_msg = f"Answer generation failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: simple error message
            state["generated_answer"] = f"I apologize, but I encountered an error while generating an answer for your query: '{state['original_query']}'. Please try again or rephrase your question."
            state["citations"] = []
            state["answer_confidence"] = 0.0
            state["answer_reasoning"] = "Answer generation failed due to error"
            state["sources_used"] = []
        
        return state
    
    def _evaluator_node(self, state: AgenticRAGState) -> AgenticRAGState:
        """Evaluation node (optional)."""
        try:
            logger.info("Starting evaluation")
            
            if not state.get("golden_reference"):
                logger.warning("No golden reference provided for evaluation")
                state["evaluation_result"] = {"error": "No golden reference provided"}
                return state
            
            # Evaluate the generated answer
            evaluation_result = self.evaluator.evaluate_answer(
                generated_answer=state["generated_answer"],
                golden_reference=state["golden_reference"],
                original_query=state["original_query"],
                context_documents=state["post_processed_documents"]
            )
            
            # Update state
            state["evaluation_result"] = {
                "overall_score": evaluation_result.overall_score,
                "accuracy_score": evaluation_result.accuracy_score,
                "completeness_score": evaluation_result.completeness_score,
                "relevance_score": evaluation_result.relevance_score,
                "clarity_score": evaluation_result.clarity_score,
                "reasoning": evaluation_result.reasoning,
                "strengths": evaluation_result.strengths,
                "weaknesses": evaluation_result.weaknesses,
                "suggestions": evaluation_result.suggestions
            }
            
            state["evaluation_scores"] = {
                "overall": evaluation_result.overall_score,
                "accuracy": evaluation_result.accuracy_score,
                "completeness": evaluation_result.completeness_score,
                "relevance": evaluation_result.relevance_score,
                "clarity": evaluation_result.clarity_score
            }
            
            logger.info(f"Evaluation completed with overall score: {evaluation_result.overall_score}")
            
        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}"
            logger.error(error_msg)
            state["error_messages"].append(error_msg)
            
            # Fallback: no evaluation
            state["evaluation_result"] = {"error": "Evaluation failed"}
            state["evaluation_scores"] = {}
        
        return state
    
    def run_workflow(
        self,
        query: str,
        user_context: Optional[str] = None,
        golden_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete Enhanced Agentic-RAG workflow.
        
        Args:
            query: User query
            user_context: Additional user context (optional)
            golden_reference: Golden reference for evaluation (optional)
            
        Returns:
            Dictionary with workflow results
        """
        try:
            # Initialize state
            initial_state: AgenticRAGState = {
                "original_query": query,
                "user_context": user_context,
                "optimized_query": "",
                "sub_queries": [],
                "query_optimization_reasoning": "",
                "query_optimization_confidence": 0.0,
                "available_documents": [],
                "selected_documents": [],
                "source_selection_reasoning": "",
                "source_selection_confidence": 0.0,
                "vector_search_results": [],
                "bm25_search_results": [],
                "hybrid_search_results": [],
                "hybrid_retrieval_reasoning": "",
                "post_processed_documents": [],
                "duplicates_removed": 0,
                "reordering_applied": False,
                "quality_scores": [],
                "post_processing_reasoning": "",
                "generated_answer": "",
                "citations": [],
                "answer_confidence": 0.0,
                "answer_reasoning": "",
                "sources_used": [],
                "golden_reference": golden_reference,
                "evaluation_result": None,
                "evaluation_scores": None,
                "processing_timestamp": datetime.now().isoformat(),
                "workflow_version": "1.0",
                "error_messages": [],
                "debug_info": {}
            }
            
            # Run the workflow
            logger.info(f"Starting Enhanced Agentic-RAG workflow for query: '{query}'")
            final_state = self.workflow.invoke(initial_state)
            
            # Prepare result
            result = {
                "query": query,
                "answer": final_state["generated_answer"],
                "confidence": final_state["answer_confidence"],
                "citations": final_state["citations"],
                "sources_used": final_state["sources_used"],
                "processing_info": {
                    "optimized_query": final_state["optimized_query"],
                    "sub_queries": final_state["sub_queries"],
                    "documents_selected": len(final_state["selected_documents"]),
                    "documents_retrieved": len(final_state["hybrid_search_results"]),
                    "documents_processed": len(final_state["post_processed_documents"]),
                    "duplicates_removed": final_state["duplicates_removed"],
                    "reordering_applied": final_state["reordering_applied"]
                },
                "reasoning": {
                    "query_optimization": final_state["query_optimization_reasoning"],
                    "source_selection": final_state["source_selection_reasoning"],
                    "post_processing": final_state["post_processing_reasoning"],
                    "answer_generation": final_state["answer_reasoning"]
                },
                "confidence_scores": {
                    "query_optimization": final_state["query_optimization_confidence"],
                    "source_selection": final_state["source_selection_confidence"],
                    "answer_generation": final_state["answer_confidence"]
                },
                "evaluation": final_state.get("evaluation_result"),
                "errors": final_state["error_messages"],
                "timestamp": final_state["processing_timestamp"]
            }
            
            logger.info(f"Enhanced Agentic-RAG workflow completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                "query": query,
                "answer": f"I apologize, but I encountered an error while processing your query: '{query}'. Please try again.",
                "confidence": 0.0,
                "citations": [],
                "sources_used": [],
                "processing_info": {},
                "reasoning": {},
                "confidence_scores": {},
                "evaluation": None,
                "errors": [error_msg],
                "timestamp": datetime.now().isoformat()
            }
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow configuration."""
        return {
            "model_name": self.model_name,
            "enable_evaluation": self.enable_evaluation,
            "max_tokens": self.max_tokens,
            "document_processor_info": self.document_processor.get_processing_info(),
            "workflow_version": "1.0",
            "nodes": [
                "query_optimizer",
                "source_identifier", 
                "hybrid_retriever",
                "post_processor",
                "answer_generator"
            ] + (["evaluator"] if self.enable_evaluation else [])
        }
