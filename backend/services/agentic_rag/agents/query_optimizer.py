"""
Query Optimizer Agent for Enhanced Agentic-RAG.

This agent refines ambiguous queries, adds context, and breaks complex queries
into sub-queries for better retrieval performance.
"""

import logging
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class QueryOptimizationResult:
    """Result of query optimization."""
    original_query: str
    optimized_query: str
    sub_queries: List[str]
    context_added: str
    optimization_reasoning: str
    confidence_score: float


class QueryOptimizerAgent:
    """
    LLM-powered agent for query optimization.
    
    This agent:
    1. Analyzes the input query for ambiguity
    2. Adds relevant context when needed
    3. Breaks complex queries into sub-queries
    4. Provides reasoning for optimization decisions
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        
        # Few-shot examples for query optimization
        self.few_shot_examples = [
            {
                "original": "What is the policy?",
                "optimized": "What are the company policies regarding employee benefits and vacation time?",
                "sub_queries": [
                    "What are the employee benefit policies?",
                    "What are the vacation time policies?"
                ],
                "context": "Company policies",
                "reasoning": "Original query was too vague. Added context about company policies and broke into specific sub-areas."
            },
            {
                "original": "How do I reset my password and what are the security requirements?",
                "optimized": "How do I reset my password and what are the security requirements for account access?",
                "sub_queries": [
                    "How do I reset my password?",
                    "What are the security requirements for account access?"
                ],
                "context": "Account security and password management",
                "reasoning": "Query was already specific but added context for better retrieval."
            }
        ]
        
        logger.info(f"QueryOptimizerAgent initialized with model: {model_name}")
    
    def optimize_query(
        self, 
        query: str, 
        available_documents: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None
    ) -> QueryOptimizationResult:
        """
        Optimize a query for better retrieval.
        
        Args:
            query: Original user query
            available_documents: List of available documents (for context)
            context: Additional context about the query domain
            
        Returns:
            QueryOptimizationResult with optimization details
        """
        try:
            # Prepare context information
            context_info = self._prepare_context(available_documents, context)
            
            # Create optimization prompt
            prompt = self._create_optimization_prompt(query, context_info)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse response
            result = self._parse_optimization_response(query, response.content)
            
            logger.info(f"Query optimized: '{query}' -> '{result.optimized_query}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize query '{query}': {e}")
            # Return original query as fallback
            return QueryOptimizationResult(
                original_query=query,
                optimized_query=query,
                sub_queries=[query],
                context_added="",
                optimization_reasoning=f"Optimization failed: {str(e)}",
                confidence_score=0.0
            )
    
    def _prepare_context(
        self, 
        available_documents: Optional[List[Dict[str, Any]]], 
        context: Optional[str]
    ) -> str:
        """Prepare context information for the optimization prompt."""
        context_parts = []
        
        if context:
            context_parts.append(f"Domain Context: {context}")
        
        if available_documents:
            doc_titles = [doc.get('title', 'Unknown') for doc in available_documents[:5]]
            context_parts.append(f"Available Documents: {', '.join(doc_titles)}")
        
        return "\n".join(context_parts) if context_parts else "No specific context available."
    
    def _create_optimization_prompt(self, query: str, context_info: str) -> str:
        """Create the optimization prompt with few-shot examples."""
        
        examples_text = "\n\n".join([
            f"Original: {ex['original']}\n"
            f"Optimized: {ex['optimized']}\n"
            f"Sub-queries: {ex['sub_queries']}\n"
            f"Context: {ex['context']}\n"
            f"Reasoning: {ex['reasoning']}"
            for ex in self.few_shot_examples
        ])
        
        prompt = f"""
You are a query optimization expert. Your task is to analyze user queries and optimize them for better document retrieval.

Context Information:
{context_info}

Few-shot Examples:
{examples_text}

Now optimize this query:
Original Query: {query}

Please provide your response in the following JSON format:
{{
    "optimized_query": "The improved version of the query",
    "sub_queries": ["List of sub-queries if the original is complex"],
    "context_added": "Any context that was added to make the query clearer",
    "reasoning": "Explanation of why these optimizations were made",
    "confidence_score": 0.85
}}

Guidelines:
1. If the query is too vague, add specific context
2. If the query is complex, break it into sub-queries
3. Maintain the original intent while improving clarity
4. Add relevant domain context when helpful
5. Provide a confidence score (0.0 to 1.0) for your optimization

Response:
"""
        return prompt
    
    def _parse_optimization_response(self, original_query: str, response: str) -> QueryOptimizationResult:
        """Parse the LLM response into a QueryOptimizationResult."""
        try:
            # Try to parse JSON response
            response_data = json.loads(response)
            
            return QueryOptimizationResult(
                original_query=original_query,
                optimized_query=response_data.get("optimized_query", original_query),
                sub_queries=response_data.get("sub_queries", [original_query]),
                context_added=response_data.get("context_added", ""),
                optimization_reasoning=response_data.get("reasoning", "No reasoning provided"),
                confidence_score=float(response_data.get("confidence_score", 0.5))
            )
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            logger.warning("Failed to parse JSON response, using fallback parsing")
            
            # Simple fallback: use the response as optimized query
            optimized_query = response.strip()
            if not optimized_query:
                optimized_query = original_query
            
            return QueryOptimizationResult(
                original_query=original_query,
                optimized_query=optimized_query,
                sub_queries=[optimized_query],
                context_added="",
                optimization_reasoning="Response parsing failed, used raw response",
                confidence_score=0.3
            )
    
    def batch_optimize_queries(
        self, 
        queries: List[str], 
        available_documents: Optional[List[Dict[str, Any]]] = None,
        context: Optional[str] = None
    ) -> List[QueryOptimizationResult]:
        """
        Optimize multiple queries in batch.
        
        Args:
            queries: List of queries to optimize
            available_documents: List of available documents
            context: Additional context
            
        Returns:
            List of QueryOptimizationResult objects
        """
        results = []
        
        for query in queries:
            try:
                result = self.optimize_query(query, available_documents, context)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to optimize query '{query}': {e}")
                # Add fallback result
                results.append(QueryOptimizationResult(
                    original_query=query,
                    optimized_query=query,
                    sub_queries=[query],
                    context_added="",
                    optimization_reasoning=f"Batch optimization failed: {str(e)}",
                    confidence_score=0.0
                ))
        
        return results
    
    def get_optimization_stats(self, results: List[QueryOptimizationResult]) -> Dict[str, Any]:
        """Get statistics about query optimization results."""
        if not results:
            return {"error": "No results provided"}
        
        total_queries = len(results)
        successful_optimizations = sum(1 for r in results if r.confidence_score > 0.5)
        avg_confidence = sum(r.confidence_score for r in results) / total_queries
        queries_with_sub_queries = sum(1 for r in results if len(r.sub_queries) > 1)
        
        return {
            "total_queries": total_queries,
            "successful_optimizations": successful_optimizations,
            "success_rate": successful_optimizations / total_queries,
            "average_confidence": avg_confidence,
            "queries_with_sub_queries": queries_with_sub_queries,
            "complex_query_rate": queries_with_sub_queries / total_queries
        }
