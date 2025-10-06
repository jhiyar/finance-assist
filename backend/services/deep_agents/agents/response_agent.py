"""
Response Agent for Deep Agents System.

This agent handles response generation, synthesis, and formatting.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import time

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


class ResponseAgent:
    """
    Agent responsible for response generation and synthesis.
    
    This agent:
    1. Synthesizes information from retrieved documents
    2. Generates coherent and accurate responses
    3. Provides confidence scoring
    4. Formats responses appropriately
    5. Handles different response types
    """
    
    def __init__(self):
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        
        # Initialize response generation prompts
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert assistant that provides accurate, helpful, and well-structured responses based on retrieved documents.

Guidelines:
1. Use only information from the provided documents
2. If information is insufficient, clearly state what's missing
3. Provide specific citations when possible
4. Structure your response clearly
5. Be concise but comprehensive
6. Maintain a helpful and professional tone

Format your response as JSON:
{
    "answer": "Your comprehensive answer",
    "confidence": 0.0-1.0,
    "citations": ["source1", "source2"],
    "reasoning": "Brief explanation of how you arrived at this answer",
    "missing_info": ["any missing information that would improve the answer"]
}"""),
            ("human", """Query: {query}

Retrieved Documents:
{documents}

Please provide a comprehensive answer based on the retrieved information.""")
        ])
        
        # Initialize confidence scoring prompt
        self.confidence_prompt = ChatPromptTemplate.from_messages([
            ("system", """Rate the confidence of this response on a scale of 0.0 to 1.0 based on:
1. Completeness of information (0.0-0.4)
2. Relevance to the query (0.0-0.3)
3. Source reliability (0.0-0.2)
4. Clarity of response (0.0-0.1)

Return only a number between 0.0 and 1.0."""),
            ("human", """Query: {query}
Response: {response}
Sources: {sources}""")
        ])
        
        logger.info("ResponseAgent initialized")
    
    def generate_response(
        self, 
        query: str, 
        retrieved_docs: List[Tuple[Document, float]],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a response based on retrieved documents and query analysis.
        
        Args:
            query: User's original query
            retrieved_docs: List of (Document, score) tuples
            query_analysis: Analysis of the user's query
            
        Returns:
            Dictionary with response information
        """
        start_time = time.time()
        
        try:
            if not retrieved_docs:
                return self._generate_no_results_response(query)
            
            # Prepare documents for response generation
            documents_text = self._prepare_documents_text(retrieved_docs)
            
            # Generate response based on query type
            response_type = query_analysis.get("response_format", "explanation")
            
            if response_type == "direct":
                response = self._generate_direct_response(query, documents_text)
            elif response_type == "step-by-step":
                response = self._generate_step_by_step_response(query, documents_text)
            else:  # explanation
                response = self._generate_explanation_response(query, documents_text)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(query, response, retrieved_docs)
            
            # Extract citations
            citations = self._extract_citations(retrieved_docs)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            return {
                "answer": response.get("answer", "I couldn't generate a proper response."),
                "confidence": confidence,
                "citations": citations,
                "sources_used": [doc.metadata.get("source", "Unknown") for doc, _ in retrieved_docs],
                "reasoning": response.get("reasoning", ""),
                "missing_info": response.get("missing_info", []),
                "processing_time": processing_time,
                "response_type": response_type,
                "document_count": len(retrieved_docs)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your query: '{query}'. Please try again.",
                "confidence": 0.0,
                "citations": [],
                "sources_used": [],
                "reasoning": f"Error occurred: {str(e)}",
                "missing_info": [],
                "processing_time": time.time() - start_time,
                "response_type": "error",
                "document_count": 0
            }
    
    def _prepare_documents_text(self, retrieved_docs: List[Tuple[Document, float]]) -> str:
        """Prepare documents text for response generation."""
        try:
            documents_text = ""
            for i, (doc, score) in enumerate(retrieved_docs, 1):
                source = doc.metadata.get("source", "Unknown")
                title = doc.metadata.get("document_title", "Unknown Title")
                
                documents_text += f"\n--- Document {i} (Score: {score:.3f}) ---\n"
                documents_text += f"Source: {source}\n"
                documents_text += f"Title: {title}\n"
                documents_text += f"Content: {doc.page_content}\n"
                
                # Add chunk metadata if available
                if "chunk_summary" in doc.metadata:
                    documents_text += f"Summary: {doc.metadata['chunk_summary']}\n"
                
                documents_text += "\n"
            
            return documents_text
            
        except Exception as e:
            logger.error(f"Failed to prepare documents text: {e}")
            return "Error preparing documents for response generation."
    
    def _generate_direct_response(self, query: str, documents_text: str) -> Dict[str, Any]:
        """Generate a direct, concise response."""
        try:
            direct_prompt = ChatPromptTemplate.from_messages([
                ("system", """Provide a direct, concise answer to the user's query based on the documents.
                Be specific and factual. If the answer isn't clear from the documents, say so.
                
                Format as JSON:
                {
                    "answer": "Direct answer",
                    "reasoning": "Brief reasoning",
                    "missing_info": ["any missing information"]
                }"""),
                ("human", "Query: {query}\n\nDocuments: {documents}")
            ])
            
            chain = direct_prompt | self.llm
            response = chain.invoke({"query": query, "documents": documents_text})
            
            import json
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"Failed to generate direct response: {e}")
            return {"answer": "Could not generate direct response.", "reasoning": str(e), "missing_info": []}
    
    def _generate_step_by_step_response(self, query: str, documents_text: str) -> Dict[str, Any]:
        """Generate a step-by-step response."""
        try:
            step_prompt = ChatPromptTemplate.from_messages([
                ("system", """Provide a step-by-step response to the user's query based on the documents.
                Break down the answer into clear, logical steps.
                
                Format as JSON:
                {
                    "answer": "Step 1: ...\nStep 2: ...\nStep 3: ...",
                    "reasoning": "Brief reasoning",
                    "missing_info": ["any missing information"]
                }"""),
                ("human", "Query: {query}\n\nDocuments: {documents}")
            ])
            
            chain = step_prompt | self.llm
            response = chain.invoke({"query": query, "documents": documents_text})
            
            import json
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"Failed to generate step-by-step response: {e}")
            return {"answer": "Could not generate step-by-step response.", "reasoning": str(e), "missing_info": []}
    
    def _generate_explanation_response(self, query: str, documents_text: str) -> Dict[str, Any]:
        """Generate a comprehensive explanation response."""
        try:
            chain = self.response_prompt | self.llm
            response = chain.invoke({"query": query, "documents": documents_text})
            
            import json
            return json.loads(response.content)
            
        except Exception as e:
            logger.error(f"Failed to generate explanation response: {e}")
            return {"answer": "Could not generate explanation response.", "reasoning": str(e), "missing_info": []}
    
    def _calculate_confidence(
        self, 
        query: str, 
        response: Dict[str, Any], 
        retrieved_docs: List[Tuple[Document, float]]
    ) -> float:
        """Calculate confidence score for the response."""
        try:
            # Base confidence from document scores
            if retrieved_docs:
                avg_doc_score = sum(score for _, score in retrieved_docs) / len(retrieved_docs)
            else:
                avg_doc_score = 0.0
            
            # Get LLM confidence assessment
            chain = self.confidence_prompt | self.llm
            llm_response = chain.invoke({
                "query": query,
                "response": response.get("answer", ""),
                "sources": [doc.metadata.get("source", "") for doc, _ in retrieved_docs]
            })
            
            try:
                llm_confidence = float(llm_response.content.strip())
            except:
                llm_confidence = 0.5
            
            # Combine scores (weighted average)
            final_confidence = (avg_doc_score * 0.3) + (llm_confidence * 0.7)
            
            # Adjust based on missing information
            missing_info = response.get("missing_info", [])
            if missing_info:
                final_confidence *= 0.8  # Reduce confidence if information is missing
            
            return min(max(final_confidence, 0.0), 1.0)  # Clamp between 0 and 1
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            return 0.5  # Default confidence
    
    def _extract_citations(self, retrieved_docs: List[Tuple[Document, float]]) -> List[str]:
        """Extract citations from retrieved documents."""
        try:
            citations = []
            for doc, score in retrieved_docs:
                source = doc.metadata.get("source", "Unknown")
                title = doc.metadata.get("document_title", "Unknown Title")
                chunk_id = doc.metadata.get("chunk_id", "")
                
                citation = f"{title} (Source: {source})"
                if chunk_id:
                    citation += f" [Chunk: {chunk_id}]"
                
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Failed to extract citations: {e}")
            return []
    
    def _generate_no_results_response(self, query: str) -> Dict[str, Any]:
        """Generate response when no documents are retrieved."""
        return {
            "answer": f"I couldn't find relevant information to answer your query: '{query}'. The document database might not contain information about this topic, or the query might need to be rephrased.",
            "confidence": 0.0,
            "citations": [],
            "sources_used": [],
            "reasoning": "No relevant documents were retrieved for this query.",
            "missing_info": ["Relevant documents for this query"],
            "processing_time": 0.0,
            "response_type": "no_results",
            "document_count": 0
        }
    
    def format_response_for_api(self, response_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Format response data for API consumption."""
        try:
            return {
                "type": "text",
                "text": response_data.get("answer", ""),
                "session_id": session_id,
                "confidence_score": response_data.get("confidence", 0.0),
                "sources_used": response_data.get("sources_used", []),
                "processing_time": response_data.get("processing_time", 0.0),
                "agent_type": "deep_agent",
                "reasoning": {
                    "reasoning": response_data.get("reasoning", ""),
                    "missing_info": response_data.get("missing_info", []),
                    "response_type": response_data.get("response_type", "explanation"),
                    "document_count": response_data.get("document_count", 0)
                },
                "citations": response_data.get("citations", []),
                "source": "deep_agent"
            }
            
        except Exception as e:
            logger.error(f"Failed to format response for API: {e}")
            return {
                "type": "text",
                "text": "Error formatting response.",
                "session_id": session_id,
                "confidence_score": 0.0,
                "sources_used": [],
                "processing_time": 0.0,
                "agent_type": "deep_agent",
                "reasoning": {"error": str(e)},
                "citations": [],
                "source": "deep_agent"
            }
