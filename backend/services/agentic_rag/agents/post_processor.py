"""
Post-Processor Agent for Enhanced Agentic-RAG.

This agent handles post-processing of retrieved documents, including
de-duplication, re-ordering, and quality assessment.
"""

import logging
from typing import List, Dict, Any, Optional
import json
from dataclasses import dataclass
from collections import defaultdict

from langchain_core.documents import Document

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class PostProcessingResult:
    """Result of post-processing."""
    original_documents: List[Document]
    processed_documents: List[Document]
    duplicates_removed: int
    reordering_applied: bool
    quality_scores: List[float]
    processing_reasoning: str


class PostProcessorAgent:
    """
    LLM-powered agent for post-processing retrieved documents.
    
    This agent:
    1. Removes duplicate content
    2. Re-orders documents by their original positional order
    3. Assesses document quality and relevance
    4. Provides reasoning for processing decisions
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        
        logger.info(f"PostProcessorAgent initialized with model: {model_name}")
    
    def process_documents(
        self, 
        documents: List[Document], 
        query: str,
        remove_duplicates: bool = True,
        reorder_by_position: bool = True,
        assess_quality: bool = True
    ) -> PostProcessingResult:
        """
        Post-process retrieved documents.
        
        Args:
            documents: List of retrieved documents
            query: Original user query
            remove_duplicates: Whether to remove duplicate content
            reorder_by_position: Whether to reorder by document position
            assess_quality: Whether to assess document quality
            
        Returns:
            PostProcessingResult with processing details
        """
        try:
            if not documents:
                return PostProcessingResult(
                    original_documents=[],
                    processed_documents=[],
                    duplicates_removed=0,
                    reordering_applied=False,
                    quality_scores=[],
                    processing_reasoning="No documents to process"
                )
            
            original_count = len(documents)
            processed_docs = documents.copy()
            duplicates_removed = 0
            reordering_applied = False
            quality_scores = []
            processing_steps = []
            
            # Step 1: Remove duplicates
            if remove_duplicates:
                processed_docs, removed_count = self._remove_duplicates(processed_docs)
                duplicates_removed = removed_count
                processing_steps.append(f"Removed {removed_count} duplicate documents")
            
            # Step 2: Reorder by position
            if reorder_by_position:
                processed_docs = self._reorder_by_position(processed_docs)
                reordering_applied = True
                processing_steps.append("Reordered documents by original position")
            
            # Step 3: Assess quality
            if assess_quality:
                quality_scores = self._assess_document_quality(processed_docs, query)
                processing_steps.append("Assessed document quality and relevance")
            
            processing_reasoning = "; ".join(processing_steps)
            
            result = PostProcessingResult(
                original_documents=documents,
                processed_documents=processed_docs,
                duplicates_removed=duplicates_removed,
                reordering_applied=reordering_applied,
                quality_scores=quality_scores,
                processing_reasoning=processing_reasoning
            )
            
            logger.info(f"Post-processing: {original_count} -> {len(processed_docs)} documents, {duplicates_removed} duplicates removed")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to post-process documents: {e}")
            # Return original documents as fallback
            return PostProcessingResult(
                original_documents=documents,
                processed_documents=documents,
                duplicates_removed=0,
                reordering_applied=False,
                quality_scores=[0.5] * len(documents),
                processing_reasoning=f"Post-processing failed: {str(e)}"
            )
    
    def _remove_duplicates(self, documents: List[Document]) -> tuple[List[Document], int]:
        """Remove duplicate documents based on content similarity."""
        try:
            if len(documents) <= 1:
                return documents, 0
            
            # Group documents by content similarity
            content_groups = defaultdict(list)
            
            for doc in documents:
                # Use first 100 characters as a simple content hash
                content_hash = doc.page_content[:100].strip().lower()
                content_groups[content_hash].append(doc)
            
            # Keep only the first document from each group
            unique_docs = []
            duplicates_removed = 0
            
            for group in content_groups.values():
                unique_docs.append(group[0])  # Keep first document
                duplicates_removed += len(group) - 1  # Count others as duplicates
            
            return unique_docs, duplicates_removed
            
        except Exception as e:
            logger.error(f"Failed to remove duplicates: {e}")
            return documents, 0
    
    def _reorder_by_position(self, documents: List[Document]) -> List[Document]:
        """Re-order documents by their original position in source documents."""
        try:
            # Extract position information from metadata
            docs_with_position = []
            
            for doc in documents:
                metadata = doc.metadata
                
                # Try to extract position information
                position = None
                
                # Check for page number
                if 'page' in metadata:
                    position = metadata['page']
                elif 'page_number' in metadata:
                    position = metadata['page_number']
                elif 'chunk_id' in metadata:
                    # Extract position from chunk_id if it contains position info
                    chunk_id = metadata['chunk_id']
                    if '_chunk_' in chunk_id:
                        try:
                            position = int(chunk_id.split('_chunk_')[1])
                        except (ValueError, IndexError):
                            pass
                
                # Use source path as secondary sort key
                source = metadata.get('source', '')
                
                docs_with_position.append((position, source, doc))
            
            # Sort by position, then by source
            docs_with_position.sort(key=lambda x: (x[0] if x[0] is not None else 999, x[1]))
            
            return [doc for position, source, doc in docs_with_position]
            
        except Exception as e:
            logger.error(f"Failed to reorder documents: {e}")
            return documents
    
    def _assess_document_quality(self, documents: List[Document], query: str) -> List[float]:
        """Assess the quality and relevance of documents using LLM."""
        try:
            if not documents:
                return []
            
            # Create quality assessment prompt
            prompt = self._create_quality_assessment_prompt(documents, query)
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            
            # Parse quality scores
            quality_scores = self._parse_quality_scores(response.content, len(documents))
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Failed to assess document quality: {e}")
            # Return default scores
            return [0.5] * len(documents)
    
    def _create_quality_assessment_prompt(self, documents: List[Document], query: str) -> str:
        """Create prompt for document quality assessment."""
        
        # Format documents for assessment
        docs_text = ""
        for i, doc in enumerate(documents):
            content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            docs_text += f"Document {i+1}:\n{content_preview}\n\n"
        
        prompt = f"""
You are a document quality assessment expert. Your task is to evaluate the quality and relevance of retrieved documents for answering a specific query.

Query: {query}

Retrieved Documents:
{docs_text}

For each document, assess:
1. Relevance to the query (0.0 to 1.0)
2. Information completeness (0.0 to 1.0)
3. Content quality (0.0 to 1.0)

Provide your response as a JSON array of quality scores:
[
    {{"relevance": 0.8, "completeness": 0.7, "quality": 0.9}},
    {{"relevance": 0.6, "completeness": 0.8, "quality": 0.7}},
    ...
]

Calculate an overall score for each document as the average of the three metrics.

Response:
"""
        return prompt
    
    def _parse_quality_scores(self, response: str, expected_count: int) -> List[float]:
        """Parse quality scores from LLM response."""
        try:
            # Try to parse JSON response
            scores_data = json.loads(response)
            
            if isinstance(scores_data, list):
                quality_scores = []
                for score_obj in scores_data:
                    if isinstance(score_obj, dict):
                        # Calculate overall score
                        relevance = score_obj.get('relevance', 0.5)
                        completeness = score_obj.get('completeness', 0.5)
                        quality = score_obj.get('quality', 0.5)
                        overall_score = (relevance + completeness + quality) / 3
                        quality_scores.append(overall_score)
                    else:
                        quality_scores.append(0.5)
                
                # Ensure we have the right number of scores
                while len(quality_scores) < expected_count:
                    quality_scores.append(0.5)
                
                return quality_scores[:expected_count]
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse quality scores JSON, using default scores")
        
        # Return default scores
        return [0.5] * expected_count
    
    def filter_by_quality_threshold(
        self, 
        documents: List[Document], 
        quality_scores: List[float], 
        threshold: float = 0.6
    ) -> List[Document]:
        """Filter documents by quality threshold."""
        try:
            if len(documents) != len(quality_scores):
                logger.warning("Document count doesn't match quality scores count")
                return documents
            
            filtered_docs = [
                doc for doc, score in zip(documents, quality_scores)
                if score >= threshold
            ]
            
            logger.info(f"Filtered {len(documents)} documents to {len(filtered_docs)} with quality >= {threshold}")
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Failed to filter documents by quality: {e}")
            return documents
    
    def get_processing_stats(self, result: PostProcessingResult) -> Dict[str, Any]:
        """Get statistics about post-processing results."""
        return {
            "original_count": len(result.original_documents),
            "processed_count": len(result.processed_documents),
            "duplicates_removed": result.duplicates_removed,
            "reordering_applied": result.reordering_applied,
            "quality_assessed": len(result.quality_scores) > 0,
            "average_quality": sum(result.quality_scores) / len(result.quality_scores) if result.quality_scores else 0,
            "high_quality_docs": sum(1 for score in result.quality_scores if score >= 0.7) if result.quality_scores else 0
        }
