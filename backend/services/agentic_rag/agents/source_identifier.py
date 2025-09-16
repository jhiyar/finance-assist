"""
Source Identifier Agent for Enhanced Agentic-RAG.

This agent selects a subset of relevant documents from the available document list
using titles, summaries, FAQs, and keywords as context for better retrieval performance.
"""

import logging
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class SourceIdentificationResult:
    """Result of source identification."""
    query: str
    selected_documents: List[Dict[str, Any]]
    selection_reasoning: str
    confidence_score: float
    total_documents_available: int
    documents_selected: int


class SourceIdentifierAgent:
    """
    LLM-powered agent for source identification.
    
    This agent:
    1. Analyzes the query and available documents
    2. Selects the most relevant documents based on titles, summaries, FAQs, and keywords
    3. Provides reasoning for document selection
    4. Returns a focused subset for retrieval
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        
        # Few-shot examples for source identification
        self.few_shot_examples = [
            {
                "query": "What are the company policies on remote work?",
                "available_docs": [
                    {"title": "Employee Handbook", "summary": "Comprehensive guide to company policies", "keywords": ["policies", "employee", "handbook"], "faqs": ["What are the work hours?", "What is the dress code?"]},
                    {"title": "IT Security Guidelines", "summary": "Security protocols and best practices", "keywords": ["security", "IT", "protocols"], "faqs": ["How to secure passwords?", "What is VPN policy?"]},
                    {"title": "Remote Work Policy", "summary": "Guidelines for working from home", "keywords": ["remote", "work", "home", "telecommuting"], "faqs": ["Who can work remotely?", "What equipment is provided?"]}
                ],
                "selected_docs": ["Employee Handbook", "Remote Work Policy"],
                "reasoning": "Selected Employee Handbook for general policy context and Remote Work Policy for specific remote work information."
            },
            {
                "query": "How do I reset my password?",
                "available_docs": [
                    {"title": "Employee Handbook", "summary": "General company information", "keywords": ["company", "general"], "faqs": ["What are the work hours?"]},
                    {"title": "IT Security Guidelines", "summary": "Security protocols and password policies", "keywords": ["security", "passwords", "authentication"], "faqs": ["How to reset passwords?", "Password requirements?"]},
                    {"title": "Benefits Guide", "summary": "Employee benefits and perks", "keywords": ["benefits", "health", "vacation"], "faqs": ["What health insurance is available?"]}
                ],
                "selected_docs": ["IT Security Guidelines"],
                "reasoning": "Selected IT Security Guidelines as it specifically covers password policies and reset procedures."
            }
        ]
        
        logger.info(f"SourceIdentifierAgent initialized with model: {model_name}")
    
    def identify_sources(
        self, 
        query: str, 
        available_documents: List[Dict[str, Any]],
        max_documents: int = 5
    ) -> SourceIdentificationResult:
        """
        Identify relevant documents for the given query.
        
        Args:
            query: User query
            available_documents: List of available documents with metadata
            max_documents: Maximum number of documents to select
            
        Returns:
            SourceIdentificationResult with selected documents
        """
        try:
            if not available_documents:
                return SourceIdentificationResult(
                    query=query,
                    selected_documents=[],
                    selection_reasoning="No documents available",
                    confidence_score=0.0,
                    total_documents_available=0,
                    documents_selected=0
                )
            
            # Create identification prompt
            prompt = self._create_identification_prompt(query, available_documents, max_documents)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse response
            result = self._parse_identification_response(query, available_documents, response.content)
            
            logger.info(f"Source identification: selected {result.documents_selected} out of {result.total_documents_available} documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to identify sources for query '{query}': {e}")
            # Return all documents as fallback
            return SourceIdentificationResult(
                query=query,
                selected_documents=available_documents[:max_documents],
                selection_reasoning=f"Source identification failed: {str(e)}. Using all available documents.",
                confidence_score=0.1,
                total_documents_available=len(available_documents),
                documents_selected=min(len(available_documents), max_documents)
            )
    
    def _create_identification_prompt(
        self, 
        query: str, 
        available_documents: List[Dict[str, Any]], 
        max_documents: int
    ) -> str:
        """Create the source identification prompt with few-shot examples."""
        
        # Format available documents
        docs_text = "\n".join([
            f"Document {i+1}: {doc.get('title', 'Unknown')}\n"
            f"  Summary: {doc.get('summary', 'No summary')}\n"
            f"  Keywords: {', '.join(doc.get('keywords', []))}\n"
            f"  FAQs: {', '.join(doc.get('faqs', []))}\n"
            for i, doc in enumerate(available_documents)
        ])
        
        # Format few-shot examples
        examples_text = "\n\n".join([
            f"Query: {ex['query']}\n"
            f"Available Documents: {len(ex['available_docs'])} documents\n"
            f"Selected: {ex['selected_docs']}\n"
            f"Reasoning: {ex['reasoning']}"
            for ex in self.few_shot_examples
        ])
        
        prompt = f"""
You are a document source identification expert. Your task is to select the most relevant documents for answering a user query.

Few-shot Examples:
{examples_text}

Current Task:
Query: {query}

Available Documents ({len(available_documents)} total):
{docs_text}

Please select the most relevant documents (maximum {max_documents}) for answering this query.

Provide your response in the following JSON format:
{{
    "selected_document_indices": [0, 2, 4],
    "reasoning": "Explanation of why these documents were selected",
    "confidence_score": 0.85
}}

Guidelines:
1. Select documents that are most likely to contain information relevant to the query
2. Consider document titles, summaries, keywords, and FAQs
3. Prioritize documents with direct relevance over general documents
4. Limit selection to {max_documents} documents maximum
5. Provide clear reasoning for your selection
6. Give a confidence score (0.0 to 1.0) for your selection

Response:
"""
        return prompt
    
    def _parse_identification_response(
        self, 
        query: str, 
        available_documents: List[Dict[str, Any]], 
        response: str
    ) -> SourceIdentificationResult:
        """Parse the LLM response into a SourceIdentificationResult."""
        try:
            # Try to parse JSON response
            response_data = json.loads(response)
            
            selected_indices = response_data.get("selected_document_indices", [])
            reasoning = response_data.get("reasoning", "No reasoning provided")
            confidence_score = float(response_data.get("confidence_score", 0.5))
            
            # Validate indices
            valid_indices = [
                idx for idx in selected_indices 
                if isinstance(idx, int) and 0 <= idx < len(available_documents)
            ]
            
            # Get selected documents
            selected_documents = [available_documents[idx] for idx in valid_indices]
            
            return SourceIdentificationResult(
                query=query,
                selected_documents=selected_documents,
                selection_reasoning=reasoning,
                confidence_score=confidence_score,
                total_documents_available=len(available_documents),
                documents_selected=len(selected_documents)
            )
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            logger.warning("Failed to parse JSON response, using fallback selection")
            
            # Simple keyword-based fallback selection
            selected_documents = self._fallback_keyword_selection(query, available_documents)
            
            return SourceIdentificationResult(
                query=query,
                selected_documents=selected_documents,
                selection_reasoning="JSON parsing failed, used keyword-based fallback selection",
                confidence_score=0.3,
                total_documents_available=len(available_documents),
                documents_selected=len(selected_documents)
            )
    
    def _fallback_keyword_selection(
        self, 
        query: str, 
        available_documents: List[Dict[str, Any]], 
        max_documents: int = 3
    ) -> List[Dict[str, Any]]:
        """Fallback keyword-based document selection."""
        try:
            query_words = set(query.lower().split())
            
            # Score documents based on keyword matches
            scored_docs = []
            for doc in available_documents:
                score = 0
                
                # Check title matches
                title_words = set(doc.get('title', '').lower().split())
                score += len(query_words.intersection(title_words)) * 3
                
                # Check keyword matches
                keywords = [kw.lower() for kw in doc.get('keywords', [])]
                score += len(query_words.intersection(keywords)) * 2
                
                # Check summary matches
                summary_words = set(doc.get('summary', '').lower().split())
                score += len(query_words.intersection(summary_words))
                
                # Check FAQ matches
                faqs = [faq.lower() for faq in doc.get('faqs', [])]
                for faq in faqs:
                    faq_words = set(faq.split())
                    score += len(query_words.intersection(faq_words)) * 1.5
                
                scored_docs.append((score, doc))
            
            # Sort by score and return top documents
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            return [doc for score, doc in scored_docs[:max_documents] if score > 0]
            
        except Exception as e:
            logger.error(f"Fallback keyword selection failed: {e}")
            return available_documents[:max_documents]
    
    def batch_identify_sources(
        self, 
        queries: List[str], 
        available_documents: List[Dict[str, Any]],
        max_documents: int = 5
    ) -> List[SourceIdentificationResult]:
        """
        Identify sources for multiple queries in batch.
        
        Args:
            queries: List of queries
            available_documents: List of available documents
            max_documents: Maximum documents per query
            
        Returns:
            List of SourceIdentificationResult objects
        """
        results = []
        
        for query in queries:
            try:
                result = self.identify_sources(query, available_documents, max_documents)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to identify sources for query '{query}': {e}")
                # Add fallback result
                results.append(SourceIdentificationResult(
                    query=query,
                    selected_documents=available_documents[:max_documents],
                    selection_reasoning=f"Batch source identification failed: {str(e)}",
                    confidence_score=0.0,
                    total_documents_available=len(available_documents),
                    documents_selected=min(len(available_documents), max_documents)
                ))
        
        return results
    
    def get_identification_stats(self, results: List[SourceIdentificationResult]) -> Dict[str, Any]:
        """Get statistics about source identification results."""
        if not results:
            return {"error": "No results provided"}
        
        total_queries = len(results)
        successful_identifications = sum(1 for r in results if r.confidence_score > 0.5)
        avg_confidence = sum(r.confidence_score for r in results) / total_queries
        avg_documents_selected = sum(r.documents_selected for r in results) / total_queries
        avg_documents_available = sum(r.total_documents_available for r in results) / total_queries
        
        return {
            "total_queries": total_queries,
            "successful_identifications": successful_identifications,
            "success_rate": successful_identifications / total_queries,
            "average_confidence": avg_confidence,
            "average_documents_selected": avg_documents_selected,
            "average_documents_available": avg_documents_available,
            "selection_ratio": avg_documents_selected / avg_documents_available if avg_documents_available > 0 else 0
        }
