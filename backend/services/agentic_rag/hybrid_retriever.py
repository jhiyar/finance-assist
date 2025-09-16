"""
Hybrid Retriever for Enhanced Agentic-RAG.

This module implements hybrid retrieval combining vector search and BM25
for improved document retrieval performance.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class HybridRetrievalResult:
    """Result of hybrid retrieval."""
    vector_results: List[Document]
    bm25_results: List[Document]
    hybrid_results: List[Document]
    vector_scores: List[float]
    bm25_scores: List[float]
    hybrid_scores: List[float]
    retrieval_reasoning: str


class HybridRetriever:
    """
    Hybrid retriever combining vector search and BM25.
    
    This retriever:
    1. Performs vector similarity search using embeddings
    2. Performs BM25 keyword-based search
    3. Combines results using configurable weighting
    4. Returns ranked hybrid results
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        top_k: int = 5
    ):
        self.embedding_model = embedding_model
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.top_k = top_k
        
        # Initialize embedding model
        self.embedding_model_instance = SentenceTransformer(embedding_model)
        
        # Initialize BM25
        self.bm25_index = None
        self.bm25_documents = []
        self.document_texts = []
        
        logger.info(f"HybridRetriever initialized with model: {embedding_model}")
    
    def build_index(self, documents: List[Document]):
        """
        Build both vector and BM25 indices from documents.
        
        Args:
            documents: List of documents to index
        """
        try:
            if not documents:
                raise ValueError("No documents provided for indexing")
            
            # Prepare document texts
            self.document_texts = [doc.page_content for doc in documents]
            self.bm25_documents = documents
            
            # Build BM25 index
            tokenized_docs = [self._tokenize_text(text) for text in self.document_texts]
            self.bm25_index = BM25Okapi(tokenized_docs)
            
            logger.info(f"Built hybrid index with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to build hybrid index: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        vector_documents: Optional[List[Document]] = None,
        filter_documents: Optional[List[str]] = None
    ) -> HybridRetrievalResult:
        """
        Perform hybrid search combining vector and BM25 retrieval.
        
        Args:
            query: Search query
            vector_documents: Documents for vector search (if different from indexed)
            filter_documents: List of document titles to filter by
            
        Returns:
            HybridRetrievalResult with combined results
        """
        try:
            if not self.bm25_index:
                raise ValueError("BM25 index not built. Call build_index first.")
            
            # Vector search
            vector_results, vector_scores = self._vector_search(query, vector_documents, filter_documents)
            
            # BM25 search
            bm25_results, bm25_scores = self._bm25_search(query, filter_documents)
            
            # Combine results
            hybrid_results, hybrid_scores = self._combine_results(
                vector_results, vector_scores,
                bm25_results, bm25_scores
            )
            
            # Create reasoning
            reasoning = self._create_retrieval_reasoning(
                len(vector_results), len(bm25_results), len(hybrid_results)
            )
            
            result = HybridRetrievalResult(
                vector_results=vector_results,
                bm25_results=bm25_results,
                hybrid_results=hybrid_results,
                vector_scores=vector_scores,
                bm25_scores=bm25_scores,
                hybrid_scores=hybrid_scores,
                retrieval_reasoning=reasoning
            )
            
            logger.info(f"Hybrid search: {len(hybrid_results)} results for query '{query}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Hybrid search failed for query '{query}': {e}")
            raise
    
    def _vector_search(
        self, 
        query: str, 
        vector_documents: Optional[List[Document]] = None,
        filter_documents: Optional[List[str]] = None
    ) -> Tuple[List[Document], List[float]]:
        """Perform vector similarity search."""
        try:
            # Use provided documents or indexed documents
            search_documents = vector_documents if vector_documents else self.bm25_documents
            
            if not search_documents:
                return [], []
            
            # Filter documents if specified
            if filter_documents:
                search_documents = [
                    doc for doc in search_documents
                    if any(title in doc.metadata.get("title", "") for title in filter_documents)
                ]
            
            # Generate embeddings
            query_embedding = self.embedding_model_instance.encode([query])
            doc_embeddings = self.embedding_model_instance.encode([doc.page_content for doc in search_documents])
            
            # Calculate similarities
            similarities = np.dot(query_embedding, doc_embeddings.T).flatten()
            
            # Sort by similarity
            sorted_indices = np.argsort(similarities)[::-1]
            
            # Get top results
            top_indices = sorted_indices[:self.top_k]
            results = [search_documents[i] for i in top_indices]
            scores = [float(similarities[i]) for i in top_indices]
            
            return results, scores
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return [], []
    
    def _bm25_search(
        self, 
        query: str, 
        filter_documents: Optional[List[str]] = None
    ) -> Tuple[List[Document], List[float]]:
        """Perform BM25 keyword search."""
        try:
            # Tokenize query
            query_tokens = self._tokenize_text(query)
            
            # Get BM25 scores
            bm25_scores = self.bm25_index.get_scores(query_tokens)
            
            # Sort by score
            sorted_indices = np.argsort(bm25_scores)[::-1]
            
            # Filter documents if specified
            if filter_documents:
                filtered_indices = []
                for idx in sorted_indices:
                    doc_title = self.bm25_documents[idx].metadata.get("title", "")
                    if any(title in doc_title for title in filter_documents):
                        filtered_indices.append(idx)
                sorted_indices = filtered_indices
            
            # Get top results
            top_indices = sorted_indices[:self.top_k]
            results = [self.bm25_documents[i] for i in top_indices]
            scores = [float(bm25_scores[i]) for i in top_indices]
            
            return results, scores
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return [], []
    
    def _combine_results(
        self,
        vector_results: List[Document],
        vector_scores: List[float],
        bm25_results: List[Document],
        bm25_scores: List[float]
    ) -> Tuple[List[Document], List[float]]:
        """Combine vector and BM25 results using weighted scoring."""
        try:
            # Create document to score mapping
            doc_scores = defaultdict(lambda: {"vector": 0.0, "bm25": 0.0, "doc": None})
            
            # Add vector results
            for doc, score in zip(vector_results, vector_scores):
                doc_key = self._get_doc_key(doc)
                doc_scores[doc_key]["vector"] = score
                doc_scores[doc_key]["doc"] = doc
            
            # Add BM25 results
            for doc, score in zip(bm25_results, bm25_scores):
                doc_key = self._get_doc_key(doc)
                doc_scores[doc_key]["bm25"] = score
                if doc_scores[doc_key]["doc"] is None:
                    doc_scores[doc_key]["doc"] = doc
            
            # Calculate hybrid scores
            hybrid_results = []
            hybrid_scores = []
            
            for doc_key, scores in doc_scores.items():
                if scores["doc"] is not None:
                    # Normalize scores
                    norm_vector_score = self._normalize_score(scores["vector"], vector_scores)
                    norm_bm25_score = self._normalize_score(scores["bm25"], bm25_scores)
                    
                    # Calculate hybrid score
                    hybrid_score = (
                        self.vector_weight * norm_vector_score + 
                        self.bm25_weight * norm_bm25_score
                    )
                    
                    hybrid_results.append(scores["doc"])
                    hybrid_scores.append(hybrid_score)
            
            # Sort by hybrid score
            sorted_pairs = sorted(zip(hybrid_results, hybrid_scores), key=lambda x: x[1], reverse=True)
            hybrid_results, hybrid_scores = zip(*sorted_pairs)
            
            return list(hybrid_results), list(hybrid_scores)
            
        except Exception as e:
            logger.error(f"Failed to combine results: {e}")
            # Fallback: return vector results
            return vector_results, vector_scores
    
    def _get_doc_key(self, doc: Document) -> str:
        """Get a unique key for a document."""
        # Use content hash as key
        return doc.page_content[:100].strip()
    
    def _normalize_score(self, score: float, all_scores: List[float]) -> float:
        """Normalize a score to [0, 1] range."""
        if not all_scores or max(all_scores) == min(all_scores):
            return 0.5
        
        return (score - min(all_scores)) / (max(all_scores) - min(all_scores))
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Basic tokenization - in production, you might want to use more sophisticated tokenization
        return text.lower().split()
    
    def _create_retrieval_reasoning(
        self, 
        vector_count: int, 
        bm25_count: int, 
        hybrid_count: int
    ) -> str:
        """Create reasoning for retrieval results."""
        return (
            f"Retrieved {vector_count} documents via vector search, "
            f"{bm25_count} documents via BM25 search, "
            f"combined into {hybrid_count} unique documents using "
            f"weights: vector={self.vector_weight}, bm25={self.bm25_weight}"
        )
    
    def update_weights(self, vector_weight: float, bm25_weight: float):
        """Update the weighting for hybrid scoring."""
        if abs(vector_weight + bm25_weight - 1.0) > 0.01:
            logger.warning("Weights don't sum to 1.0, normalizing...")
            total = vector_weight + bm25_weight
            vector_weight = vector_weight / total
            bm25_weight = bm25_weight / total
        
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        logger.info(f"Updated hybrid weights: vector={vector_weight}, bm25={bm25_weight}")
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retriever."""
        return {
            "embedding_model": self.embedding_model,
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "top_k": self.top_k,
            "indexed_documents": len(self.bm25_documents),
            "bm25_index_built": self.bm25_index is not None
        }
