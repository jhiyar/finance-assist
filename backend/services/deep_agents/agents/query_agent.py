"""
Query Agent for Deep Agents System.

This agent handles query processing, intent detection, and retrieval orchestration.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from services.openai_service import get_openai_service
from services.deep_agents.chroma_service import get_chroma_service
from chat.utils import detect_intent

logger = logging.getLogger(__name__)


class QueryAgent:
    """
    Agent responsible for query processing and retrieval orchestration.
    
    This agent:
    1. Analyzes user queries and detects intent
    2. Determines the best retrieval strategy
    3. Orchestrates document retrieval
    4. Provides query optimization and expansion
    """
    
    def __init__(self):
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        self.chroma_service = get_chroma_service()
        
        # Initialize query analysis prompt
        self.query_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a query analysis expert. Analyze the user's query and determine:
1. Query type (factual, analytical, procedural, conversational)
2. Required information depth (surface, detailed, comprehensive)
3. Best retrieval strategy (semantic, keyword, hybrid)
4. Query complexity (simple, moderate, complex)
5. Expected response format (direct answer, explanation, step-by-step)

Respond in JSON format:
{
    "query_type": "factual|analytical|procedural|conversational",
    "information_depth": "surface|detailed|comprehensive",
    "retrieval_strategy": "semantic|keyword|hybrid",
    "complexity": "simple|moderate|complex",
    "response_format": "direct|explanation|step-by-step",
    "confidence": 0.0-1.0
}"""),
            ("human", "Query: {query}")
        ])
        
        logger.info("QueryAgent initialized")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a user query to determine processing strategy.
        
        Args:
            query: User's query string
            
        Returns:
            Dictionary with query analysis results
        """
        try:
            # Get LLM analysis
            chain = self.query_analysis_prompt | self.llm
            response = chain.invoke({"query": query})
            
            # Parse JSON response
            import json
            try:
                analysis = json.loads(response.content)
            except:
                # Fallback analysis
                analysis = self._fallback_query_analysis(query)
            
            # Add traditional intent detection
            intent = detect_intent(query)
            analysis["intent"] = intent
            
            # Add query complexity heuristics
            analysis["word_count"] = len(query.split())
            analysis["has_question_words"] = bool(re.search(r'\b(what|how|why|when|where|who|which)\b', query.lower()))
            analysis["has_technical_terms"] = self._has_technical_terms(query)
            
            logger.info(f"Query analyzed: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return self._fallback_query_analysis(query)
    
    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback query analysis using heuristics."""
        query_lower = query.lower()
        
        # Determine query type
        if any(word in query_lower for word in ['what', 'who', 'when', 'where']):
            query_type = "factual"
        elif any(word in query_lower for word in ['how', 'why']):
            query_type = "analytical"
        elif any(word in query_lower for word in ['step', 'process', 'procedure']):
            query_type = "procedural"
        else:
            query_type = "conversational"
        
        # Determine complexity
        word_count = len(query.split())
        if word_count <= 5:
            complexity = "simple"
        elif word_count <= 15:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        return {
            "query_type": query_type,
            "information_depth": "detailed",
            "retrieval_strategy": "hybrid",
            "complexity": complexity,
            "response_format": "explanation",
            "confidence": 0.7
        }
    
    def _has_technical_terms(self, query: str) -> bool:
        """Check if query contains technical terms."""
        technical_indicators = [
            'api', 'database', 'algorithm', 'function', 'method', 'class',
            'variable', 'parameter', 'configuration', 'implementation',
            'architecture', 'framework', 'library', 'module', 'component'
        ]
        
        query_lower = query.lower()
        return any(term in query_lower for term in technical_indicators)
    
    def retrieve_documents(
        self, 
        query: str, 
        analysis: Dict[str, Any],
        k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents based on query analysis.
        
        Args:
            query: User's query
            analysis: Query analysis results
            k: Number of documents to retrieve
            
        Returns:
            List of (Document, score) tuples
        """
        try:
            # Determine retrieval strategy
            strategy = analysis.get("retrieval_strategy", "hybrid")
            
            if strategy == "semantic":
                return self._semantic_retrieval(query, k)
            elif strategy == "keyword":
                return self._keyword_retrieval(query, k)
            else:  # hybrid
                return self._hybrid_retrieval(query, k)
                
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def _semantic_retrieval(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform semantic similarity search."""
        try:
            results = self.chroma_service.similarity_search_with_score(query, k=k)
            logger.info(f"Semantic retrieval found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []
    
    def _keyword_retrieval(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform keyword-based retrieval."""
        try:
            # Extract keywords from query
            keywords = self._extract_keywords(query)
            
            # Create keyword-based filter
            filter_dict = {}
            for keyword in keywords[:3]:  # Use top 3 keywords
                filter_dict[f"keywords_{keyword}"] = {"$contains": keyword}
            
            # Perform filtered search
            results = self.chroma_service.similarity_search_with_score(
                query, k=k, filter=filter_dict
            )
            
            logger.info(f"Keyword retrieval found {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Keyword retrieval failed: {e}")
            return []
    
    def _hybrid_retrieval(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform hybrid retrieval combining semantic and keyword approaches."""
        try:
            # Get semantic results
            semantic_results = self._semantic_retrieval(query, k=k*2)
            
            # Get keyword results
            keyword_results = self._keyword_retrieval(query, k=k*2)
            
            # Combine and deduplicate results
            combined_results = self._combine_results(semantic_results, keyword_results, k)
            
            logger.info(f"Hybrid retrieval found {len(combined_results)} documents")
            return combined_results
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Return top 10 keywords
    
    def _combine_results(
        self, 
        semantic_results: List[Tuple[Document, float]], 
        keyword_results: List[Tuple[Document, float]], 
        k: int
    ) -> List[Tuple[Document, float]]:
        """Combine and deduplicate retrieval results."""
        try:
            # Create a dictionary to store unique documents with best scores
            unique_docs = {}
            
            # Add semantic results with weight 0.7
            for doc, score in semantic_results:
                doc_id = doc.metadata.get('chunk_id', str(hash(doc.page_content)))
                if doc_id not in unique_docs or unique_docs[doc_id][1] < score * 0.7:
                    unique_docs[doc_id] = (doc, score * 0.7)
            
            # Add keyword results with weight 0.3
            for doc, score in keyword_results:
                doc_id = doc.metadata.get('chunk_id', str(hash(doc.page_content)))
                if doc_id not in unique_docs or unique_docs[doc_id][1] < score * 0.3:
                    unique_docs[doc_id] = (doc, score * 0.3)
            
            # Sort by score and return top k
            sorted_results = sorted(unique_docs.values(), key=lambda x: x[1], reverse=True)
            return sorted_results[:k]
            
        except Exception as e:
            logger.error(f"Failed to combine results: {e}")
            return semantic_results[:k]  # Fallback to semantic results
    
    def expand_query(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate query variations for better retrieval.
        
        Args:
            query: Original query
            analysis: Query analysis results
            
        Returns:
            List of expanded query variations
        """
        try:
            if analysis.get("complexity") == "simple":
                return [query]  # No expansion needed for simple queries
            
            # Create query expansion prompt
            expansion_prompt = ChatPromptTemplate.from_messages([
                ("system", """Generate 3 variations of the user's query that might help retrieve more relevant information. 
                Consider synonyms, related concepts, and different phrasings.
                
                Return as JSON array:
                ["variation1", "variation2", "variation3"]"""),
                ("human", "Original query: {query}\nQuery type: {query_type}")
            ])
            
            chain = expansion_prompt | self.llm
            response = chain.invoke({
                "query": query,
                "query_type": analysis.get("query_type", "factual")
            })
            
            import json
            try:
                variations = json.loads(response.content)
                return [query] + variations  # Include original query
            except:
                return [query]
                
        except Exception as e:
            logger.error(f"Failed to expand query: {e}")
            return [query]
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about retrieval performance."""
        try:
            chroma_info = self.chroma_service.get_collection_info()
            
            return {
                "chroma_collection": chroma_info,
                "retrieval_strategies": ["semantic", "keyword", "hybrid"],
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get retrieval stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
