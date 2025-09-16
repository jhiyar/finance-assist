"""
Answer Generator Agent for Enhanced Agentic-RAG.

This agent generates final answers using the original query, optimized sub-queries,
and post-processed context with proper citations.
"""

import logging
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass

from langchain_core.documents import Document

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class AnswerGenerationResult:
    """Result of answer generation."""
    original_query: str
    optimized_queries: List[str]
    generated_answer: str
    citations: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str
    sources_used: List[str]


class AnswerGeneratorAgent:
    """
    LLM-powered agent for generating final answers.
    
    This agent:
    1. Combines original query with optimized sub-queries
    2. Uses post-processed context to generate comprehensive answers
    3. Includes proper citations and source references
    4. Provides confidence scoring and reasoning
    """
    
    def __init__(self, model_name: str = "gpt-4o", max_tokens: int = 4000):
        self.model_name = model_name
        print(f"AnswerGeneratorAgent initialized with model: {model_name}, max_tokens: {max_tokens}")
        self.max_tokens = max_tokens
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm(max_tokens=max_tokens)
        
        logger.info(f"AnswerGeneratorAgent initialized with model: {model_name}, max_tokens: {max_tokens}")
    
    def generate_answer(
        self,
        original_query: str,
        optimized_queries: List[str],
        context_documents: List[Document],
        query_optimization_reasoning: str = "",
        source_selection_reasoning: str = "",
        post_processing_reasoning: str = ""
    ) -> AnswerGenerationResult:
        """
        Generate a comprehensive answer using all available context.
        
        Args:
            original_query: Original user query
            optimized_queries: List of optimized sub-queries
            context_documents: Post-processed context documents
            query_optimization_reasoning: Reasoning from query optimization
            source_selection_reasoning: Reasoning from source selection
            post_processing_reasoning: Reasoning from post-processing
            
        Returns:
            AnswerGenerationResult with generated answer and citations
        """
        try:
            if not context_documents:
                return AnswerGenerationResult(
                    original_query=original_query,
                    optimized_queries=optimized_queries,
                    generated_answer="I apologize, but I couldn't find any relevant information to answer your question. Please try rephrasing your query or check if the relevant documents are available.",
                    citations=[],
                    confidence_score=0.0,
                    reasoning="No context documents available",
                    sources_used=[]
                )
            
            # Prepare context and citations
            context_text, citations, sources_used = self._prepare_context_and_citations(context_documents)
            
            # Create answer generation prompt
            prompt = self._create_answer_generation_prompt(
                original_query,
                optimized_queries,
                context_text,
                query_optimization_reasoning,
                source_selection_reasoning,
                post_processing_reasoning
            )
            
            # Generate answer
            response = self.llm.invoke(prompt)
            
            # Parse response
            result = self._parse_answer_response(
                original_query,
                optimized_queries,
                response.content,
                citations,
                sources_used
            )
            
            logger.info(f"Generated answer for query: '{original_query}' (confidence: {result.confidence_score})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate answer for query '{original_query}': {e}")
            # Return fallback answer
            return AnswerGenerationResult(
                original_query=original_query,
                optimized_queries=optimized_queries,
                generated_answer=f"I encountered an error while generating an answer for your query: '{original_query}'. Please try again or rephrase your question.",
                citations=[],
                confidence_score=0.0,
                reasoning=f"Answer generation failed for {self.model_name}: {str(e)}",
                sources_used=[]
            )
    
    def _prepare_context_and_citations(
        self, 
        documents: List[Document]
    ) -> tuple[str, List[Dict[str, Any]], List[str]]:
        """Prepare context text and citations from documents with length management."""
        try:
            # Limit documents to prevent token limit exceeded
            limited_documents = self._limit_context_length(documents)
            
            context_parts = []
            citations = []
            sources_used = []
            
            for i, doc in enumerate(limited_documents):
                # Add document content to context
                context_parts.append(f"[Document {i+1}]\n{doc.page_content}")
                
                # Create citation
                citation = {
                    "id": i + 1,
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get('source', 'Unknown source'),
                    "title": doc.metadata.get('title', 'Unknown title'),
                    "page": doc.metadata.get('page', 'Unknown page')
                }
                citations.append(citation)
                
                # Track sources
                source = doc.metadata.get('source', 'Unknown')
                if source not in sources_used:
                    sources_used.append(source)
            
            context_text = "\n\n".join(context_parts)
            
            return context_text, citations, sources_used
            
        except Exception as e:
            logger.error(f"Failed to prepare context and citations: {e}")
            return "", [], []
    
    def _limit_context_length(self, documents: List[Document]) -> List[Document]:
        """Limit the number of documents and their content to prevent token limit exceeded."""
        try:
            # Rough estimation: 1 token ≈ 4 characters for English text
            # Reserve some tokens for the prompt and response
            max_context_tokens = self.max_tokens - 1000  # Reserve 1000 tokens for prompt and response
            max_context_chars = max_context_tokens * 4
            
            limited_documents = []
            current_chars = 0
            
            for doc in documents:
                # Truncate document content if it's too long
                doc_content = doc.page_content
                if len(doc_content) > 2000:  # Limit individual document to 2000 chars
                    doc_content = doc_content[:2000] + "..."
                
                # Check if adding this document would exceed the limit
                if current_chars + len(doc_content) > max_context_chars:
                    # If we have at least one document, stop here
                    if limited_documents:
                        break
                    # If this is the first document and it's too long, truncate it
                    if not limited_documents:
                        doc_content = doc_content[:max_context_chars - 100] + "..."
                
                # Create a new document with truncated content
                truncated_doc = Document(
                    page_content=doc_content,
                    metadata=doc.metadata
                )
                limited_documents.append(truncated_doc)
                current_chars += len(doc_content)
                
                # Limit to maximum 5 documents to prevent too many documents
                if len(limited_documents) >= 5:
                    break
            
            logger.info(f"Limited context from {len(documents)} to {len(limited_documents)} documents, ~{current_chars} characters")
            return limited_documents
            
        except Exception as e:
            logger.error(f"Failed to limit context length: {e}")
            # Fallback: return first 3 documents with truncated content
            return documents[:3]
    
    def _create_answer_generation_prompt(
        self,
        original_query: str,
        optimized_queries: List[str],
        context_text: str,
        query_optimization_reasoning: str,
        source_selection_reasoning: str,
        post_processing_reasoning: str
    ) -> str:
        """Create the answer generation prompt."""
        
        prompt = f"""
You are an expert answer generator for a RAG (Retrieval-Augmented Generation) system. Your task is to generate a comprehensive, accurate, and well-cited answer based on the provided context.

Original Query: {original_query}

Optimized Queries: {', '.join(optimized_queries)}

Processing Reasoning:
- Query Optimization: {query_optimization_reasoning}
- Source Selection: {source_selection_reasoning}
- Post-Processing: {post_processing_reasoning}

Context Documents:
{context_text}

Instructions:
1. Generate a comprehensive answer that directly addresses the original query
2. Use information from the context documents to support your answer
3. Include proper citations using [Document X] format where X is the document number
4. If the context doesn't contain enough information, clearly state this
5. Be accurate and avoid hallucination - only use information from the provided context
6. CRITICAL: Structure your answer using MARKDOWN formatting. You MUST use:
   - ## Main Headers for primary topics
   - ### Subheaders for subtopics
   - **Bold text** for important terms, concepts, and key points
   - *Italic text* for emphasis
   - Bullet points (-) for ALL lists, features, types, and key information
   - Numbered lists (1., 2., 3.) for step-by-step processes
   - `Code formatting` for technical terms, product names, or specific values
   - Blockquotes (>) for important notes or warnings
7. When listing types, features, or categories, ALWAYS use bullet points
8. When explaining processes or steps, use numbered lists
9. Make the answer visually structured and easy to scan
10. Provide a confidence score (0.0 to 1.0) for your answer
11. Explain your reasoning for the answer quality

Example of proper markdown formatting:
## What are Bridging Loans?

**Bridging loans** are specialist short-term loans that provide immediate cash flow.

### Key Features:
- **Duration**: Typically 3-12 months
- **Purpose**: Bridge immediate financial needs
- **Security**: Usually secured against properties

### Types of Bridging Loans:
- **Full Serviced Loans**: Regular interest payments
- **Fully Retained Loans**: Interest rolled up
- **Partially Retained Loans**: Mixed payment structure
- **Roll-up Loans**: Interest added to principal
- **Deferred Loans**: Payment deferral options

Provide your response in the following JSON format:
{{
    "answer": "Your comprehensive answer here with [Document X] citations using proper markdown formatting",
    "confidence_score": 0.85,
    "reasoning": "Explanation of answer quality and confidence level"
}}

Response:
"""
        return prompt
    
    def _parse_answer_response(
        self,
        original_query: str,
        optimized_queries: List[str],
        response: str,
        citations: List[Dict[str, Any]],
        sources_used: List[str]
    ) -> AnswerGenerationResult:
        """Parse the LLM response into an AnswerGenerationResult."""
        try:
            # Try to parse JSON response
            response_data = json.loads(response)
            
            answer = response_data.get("answer", "No answer generated")
            confidence_score = float(response_data.get("confidence_score", 0.5))
            reasoning = response_data.get("reasoning", "No reasoning provided")
            
            return AnswerGenerationResult(
                original_query=original_query,
                optimized_queries=optimized_queries,
                generated_answer=answer,
                citations=citations,
                confidence_score=confidence_score,
                reasoning=reasoning,
                sources_used=sources_used
            )
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            logger.warning("Failed to parse JSON response, using raw response as answer")
            
            return AnswerGenerationResult(
                original_query=original_query,
                optimized_queries=optimized_queries,
                generated_answer=response.strip(),
                citations=citations,
                confidence_score=0.3,
                reasoning="JSON parsing failed, used raw response",
                sources_used=sources_used
            )
    
    def format_answer_with_citations(self, result: AnswerGenerationResult) -> str:
        """Format the answer with proper citations display."""
        try:
            formatted_answer = result.generated_answer
            
            # Add citations section
            if result.citations:
                formatted_answer += "\n\n**Sources:**\n"
                for citation in result.citations:
                    formatted_answer += f"[{citation['id']}] {citation['title']} - {citation['source']}\n"
            
            # Add confidence and reasoning
            formatted_answer += f"\n\n**Confidence:** {result.confidence_score:.2f}\n"
            formatted_answer += f"**Reasoning:** {result.reasoning}\n"
            
            return formatted_answer
            
        except Exception as e:
            logger.error(f"Failed to format answer with citations: {e}")
            return result.generated_answer
    
    def batch_generate_answers(
        self,
        queries_data: List[Dict[str, Any]]
    ) -> List[AnswerGenerationResult]:
        """
        Generate answers for multiple queries in batch.
        
        Args:
            queries_data: List of dictionaries containing query information
            
        Returns:
            List of AnswerGenerationResult objects
        """
        results = []
        
        for query_data in queries_data:
            try:
                result = self.generate_answer(
                    original_query=query_data.get('original_query', ''),
                    optimized_queries=query_data.get('optimized_queries', []),
                    context_documents=query_data.get('context_documents', []),
                    query_optimization_reasoning=query_data.get('query_optimization_reasoning', ''),
                    source_selection_reasoning=query_data.get('source_selection_reasoning', ''),
                    post_processing_reasoning=query_data.get('post_processing_reasoning', '')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate answer for query data: {e}")
                # Add fallback result
                results.append(AnswerGenerationResult(
                    original_query=query_data.get('original_query', ''),
                    optimized_queries=query_data.get('optimized_queries', []),
                    generated_answer="Failed to generate answer",
                    citations=[],
                    confidence_score=0.0,
                    reasoning=f"Batch answer generation failed: {str(e)}",
                    sources_used=[]
                ))
        
        return results
    
    def get_generation_stats(self, results: List[AnswerGenerationResult]) -> Dict[str, Any]:
        """Get statistics about answer generation results."""
        if not results:
            return {"error": "No results provided"}
        
        total_queries = len(results)
        successful_generations = sum(1 for r in results if r.confidence_score > 0.5)
        avg_confidence = sum(r.confidence_score for r in results) / total_queries
        avg_sources_used = sum(len(r.sources_used) for r in results) / total_queries
        avg_citations = sum(len(r.citations) for r in results) / total_queries
        
        return {
            "total_queries": total_queries,
            "successful_generations": successful_generations,
            "success_rate": successful_generations / total_queries,
            "average_confidence": avg_confidence,
            "average_sources_used": avg_sources_used,
            "average_citations": avg_citations
        }
