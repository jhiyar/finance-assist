"""
Context Pruning Service for Finance Assist

This service implements multiple context pruning strategies:
1. LLMChainExtractor for document compression
2. Relevance filtering with similarity thresholds
3. Metadata filtering for precise retrieval
4. Semantic chunking with relevance-based pruning

Based on latest research and best practices for RAG systems.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

import numpy as np
from langchain_core.documents import Document
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class PruningResult:
    """Result of context pruning operation."""
    pruned_documents: List[Document]
    original_documents: List[Document]  # Added to store original documents for comparison
    original_count: int
    pruned_count: int
    compression_ratio: float
    processing_time: float
    pruning_method: str
    metadata: Dict[str, Any]


@dataclass
class RelevanceScore:
    """Relevance score for a document chunk."""
    document: Document
    score: float
    reasoning: str
    metadata: Dict[str, Any]


class BaseContextPruner(ABC):
    """Abstract base class for context pruning strategies."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def prune(self, documents: List[Document], query: str, **kwargs) -> PruningResult:
        """Prune documents based on relevance to query."""
        pass


class LLMCompressionPruner(BaseContextPruner):
    """
    Context pruner using LLMChainExtractor for intelligent document compression.
    
    This pruner uses an LLM to extract only the most relevant parts of documents
    based on the query, significantly reducing context while maintaining relevance.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_name = kwargs.get('model_name', 'gpt-4o-mini')
        self.temperature = kwargs.get('temperature', 0.0)
        self.max_tokens = kwargs.get('max_tokens', 4000)
        
        # Initialize LLM and compressor
        self._initialize_compressor()
    
    def _initialize_compressor(self):
        """Initialize the LLM and compressor."""
        try:
            # Get OpenAI service
            openai_service = get_openai_service()
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                openai_api_key=openai_service.api_key
            )
            
            # Initialize compressor
            self.compressor = LLMChainExtractor.from_llm(self.llm)
            
            self.logger.info(f"LLMCompressionPruner initialized with model: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM compressor: {e}")
            raise
    
    def prune(self, documents: List[Document], query: str, **kwargs) -> PruningResult:
        """Prune documents using LLM-based compression."""
        start_time = time.time()
        
        try:
            # Create a mock retriever for the compressor
            class MockRetriever:
                def __init__(self, docs):
                    self.docs = docs
                
                def get_relevant_documents(self, query):
                    return self.docs
            
            mock_retriever = MockRetriever(documents)
            
            # Create compression retriever
            compression_retriever = ContextualCompressionRetriever(
                base_compressor=self.compressor,
                base_retriever=mock_retriever
            )
            
            # Get compressed documents
            pruned_docs = compression_retriever.get_relevant_documents(query)
            
            processing_time = time.time() - start_time
            compression_ratio = len(pruned_docs) / len(documents) if documents else 0
            
            return PruningResult(
                pruned_documents=pruned_docs,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(pruned_docs),
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                pruning_method='llm_compression',
                metadata={
                    'model_name': self.model_name,
                    'temperature': self.temperature,
                    'max_tokens': self.max_tokens,
                    'query': query
                }
            )
            
        except Exception as e:
            self.logger.error(f"LLM compression pruning failed: {e}")
            # Return original documents if compression fails
            return PruningResult(
                pruned_documents=documents,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(documents),
                compression_ratio=1.0,
                processing_time=time.time() - start_time,
                pruning_method='llm_compression_failed',
                metadata={'error': str(e)}
            )


class RelevanceFilterPruner(BaseContextPruner):
    """
    Context pruner using similarity thresholds to filter low-relevance chunks.
    
    This pruner calculates semantic similarity between query and documents,
    filtering out documents below a specified threshold.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.similarity_threshold = kwargs.get('similarity_threshold', 0.7)
        self.embedding_model = kwargs.get('embedding_model', 'all-MiniLM-L6-v2')
        self.top_k = kwargs.get('top_k', None)  # If None, use threshold filtering
        
        # Initialize embedding model
        self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model."""
        try:
            self.embedding_model_instance = SentenceTransformer(self.embedding_model)
            self.logger.info(f"RelevanceFilterPruner initialized with model: {self.embedding_model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def prune(self, documents: List[Document], query: str, **kwargs) -> PruningResult:
        """Prune documents based on similarity threshold."""
        start_time = time.time()
        
        try:
            if not documents:
                return PruningResult(
                    pruned_documents=[],
                    original_documents=documents,
                    original_count=0,
                    pruned_count=0,
                    compression_ratio=0.0,
                    processing_time=time.time() - start_time,
                    pruning_method='relevance_filter',
                    metadata={'error': 'No documents provided'}
                )
            
            # Calculate relevance scores
            relevance_scores = self._calculate_relevance_scores(documents, query)
            
            # Filter based on threshold or top_k
            if self.top_k:
                # Sort by score and take top_k
                sorted_scores = sorted(relevance_scores, key=lambda x: x.score, reverse=True)
                filtered_scores = sorted_scores[:self.top_k]
            else:
                # Filter by threshold
                filtered_scores = [score for score in relevance_scores if score.score >= self.similarity_threshold]
            
            pruned_docs = [score.document for score in filtered_scores]
            
            processing_time = time.time() - start_time
            compression_ratio = len(pruned_docs) / len(documents) if documents else 0
            
            return PruningResult(
                pruned_documents=pruned_docs,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(pruned_docs),
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                pruning_method='relevance_filter',
                metadata={
                    'similarity_threshold': self.similarity_threshold,
                    'top_k': self.top_k,
                    'embedding_model': self.embedding_model,
                    'query': query,
                    'relevance_scores': [score.score for score in relevance_scores],
                    'filtered_scores': [score.score for score in filtered_scores]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Relevance filtering failed: {e}")
            return PruningResult(
                pruned_documents=documents,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(documents),
                compression_ratio=1.0,
                processing_time=time.time() - start_time,
                pruning_method='relevance_filter_failed',
                metadata={'error': str(e)}
            )
    
    def _calculate_relevance_scores(self, documents: List[Document], query: str) -> List[RelevanceScore]:
        """Calculate relevance scores for documents."""
        try:
            # Generate embeddings
            query_embedding = self.embedding_model_instance.encode([query])
            doc_embeddings = self.embedding_model_instance.encode([doc.page_content for doc in documents])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            
            # Create relevance scores
            relevance_scores = []
            for i, (doc, similarity) in enumerate(zip(documents, similarities)):
                relevance_scores.append(RelevanceScore(
                    document=doc,
                    score=float(similarity),
                    reasoning=f"Semantic similarity: {similarity:.3f}",
                    metadata={
                        'document_index': i,
                        'content_length': len(doc.page_content),
                        'metadata': doc.metadata
                    }
                ))
            
            return relevance_scores
            
        except Exception as e:
            self.logger.error(f"Failed to calculate relevance scores: {e}")
            # Return all documents with low scores if calculation fails
            return [RelevanceScore(
                document=doc,
                score=0.0,
                reasoning=f"Error calculating similarity: {e}",
                metadata={'error': str(e)}
            ) for doc in documents]


class MetadataFilterPruner(BaseContextPruner):
    """
    Context pruner using metadata filtering for faster, more precise retrieval.
    
    This pruner filters documents based on metadata attributes before applying
    more computationally intensive processes.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metadata_filters = kwargs.get('metadata_filters', {})
        self.require_all_filters = kwargs.get('require_all_filters', True)
    
    def prune(self, documents: List[Document], query: str, **kwargs) -> PruningResult:
        """Prune documents based on metadata filters."""
        start_time = time.time()
        
        try:
            if not self.metadata_filters:
                # No filters specified, return all documents
                return PruningResult(
                    pruned_documents=documents,
                    original_documents=documents,
                    original_count=len(documents),
                    pruned_count=len(documents),
                    compression_ratio=1.0,
                    processing_time=time.time() - start_time,
                    pruning_method='metadata_filter',
                    metadata={'message': 'No metadata filters specified'}
                )
            
            # Apply metadata filters
            filtered_docs = []
            for doc in documents:
                if self._matches_metadata_filters(doc.metadata):
                    filtered_docs.append(doc)
            
            processing_time = time.time() - start_time
            compression_ratio = len(filtered_docs) / len(documents) if documents else 0
            
            return PruningResult(
                pruned_documents=filtered_docs,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(filtered_docs),
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                pruning_method='metadata_filter',
                metadata={
                    'metadata_filters': self.metadata_filters,
                    'require_all_filters': self.require_all_filters,
                    'query': query,
                    'filtered_metadata': [doc.metadata for doc in filtered_docs]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Metadata filtering failed: {e}")
            return PruningResult(
                pruned_documents=documents,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(documents),
                compression_ratio=1.0,
                processing_time=time.time() - start_time,
                pruning_method='metadata_filter_failed',
                metadata={'error': str(e)}
            )
    
    def _matches_metadata_filters(self, metadata: Dict[str, Any]) -> bool:
        """Check if document metadata matches the filters."""
        if self.require_all_filters:
            # All filters must match
            for key, value in self.metadata_filters.items():
                if key not in metadata or metadata[key] != value:
                    return False
            return True
        else:
            # At least one filter must match
            for key, value in self.metadata_filters.items():
                if key in metadata and metadata[key] == value:
                    return True
            return False


class HybridContextPruner(BaseContextPruner):
    """
    Hybrid context pruner that combines multiple pruning strategies.
    
    This pruner applies multiple pruning methods in sequence for optimal results:
    1. Metadata filtering (fastest)
    2. Relevance filtering (medium speed)
    3. LLM compression (slowest but most intelligent)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize individual pruners
        self.metadata_pruner = MetadataFilterPruner(
            metadata_filters=kwargs.get('metadata_filters', {}),
            require_all_filters=kwargs.get('require_all_filters', True)
        )
        
        self.relevance_pruner = RelevanceFilterPruner(
            similarity_threshold=kwargs.get('similarity_threshold', 0.7),
            embedding_model=kwargs.get('embedding_model', 'all-MiniLM-L6-v2'),
            top_k=kwargs.get('top_k', None)
        )
        
        self.llm_pruner = LLMCompressionPruner(
            model_name=kwargs.get('model_name', 'gpt-4o-mini'),
            temperature=kwargs.get('temperature', 0.0),
            max_tokens=kwargs.get('max_tokens', 4000)
        )
        
        # Pruning pipeline configuration
        self.use_metadata_filter = kwargs.get('use_metadata_filter', True)
        self.use_relevance_filter = kwargs.get('use_relevance_filter', True)
        self.use_llm_compression = kwargs.get('use_llm_compression', True)
    
    def prune(self, documents: List[Document], query: str, **kwargs) -> PruningResult:
        """Apply hybrid pruning pipeline."""
        start_time = time.time()
        
        try:
            current_docs = documents
            pruning_steps = []
            
            # Step 1: Metadata filtering
            if self.use_metadata_filter and current_docs:
                metadata_result = self.metadata_pruner.prune(current_docs, query, **kwargs)
                current_docs = metadata_result.pruned_documents
                pruning_steps.append({
                    'step': 'metadata_filter',
                    'original_count': metadata_result.original_count,
                    'pruned_count': metadata_result.pruned_count,
                    'compression_ratio': metadata_result.compression_ratio,
                    'processing_time': metadata_result.processing_time
                })
            
            # Step 2: Relevance filtering
            if self.use_relevance_filter and current_docs:
                relevance_result = self.relevance_pruner.prune(current_docs, query, **kwargs)
                current_docs = relevance_result.pruned_documents
                pruning_steps.append({
                    'step': 'relevance_filter',
                    'original_count': relevance_result.original_count,
                    'pruned_count': relevance_result.pruned_count,
                    'compression_ratio': relevance_result.compression_ratio,
                    'processing_time': relevance_result.processing_time
                })
            
            # Step 3: LLM compression
            if self.use_llm_compression and current_docs:
                llm_result = self.llm_pruner.prune(current_docs, query, **kwargs)
                current_docs = llm_result.pruned_documents
                pruning_steps.append({
                    'step': 'llm_compression',
                    'original_count': llm_result.original_count,
                    'pruned_count': llm_result.pruned_count,
                    'compression_ratio': llm_result.compression_ratio,
                    'processing_time': llm_result.processing_time
                })
            
            processing_time = time.time() - start_time
            compression_ratio = len(current_docs) / len(documents) if documents else 0
            
            return PruningResult(
                pruned_documents=current_docs,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(current_docs),
                compression_ratio=compression_ratio,
                processing_time=processing_time,
                pruning_method='hybrid',
                metadata={
                    'query': query,
                    'pruning_steps': pruning_steps,
                    'pipeline_config': {
                        'use_metadata_filter': self.use_metadata_filter,
                        'use_relevance_filter': self.use_relevance_filter,
                        'use_llm_compression': self.use_llm_compression
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Hybrid pruning failed: {e}")
            return PruningResult(
                pruned_documents=documents,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(documents),
                compression_ratio=1.0,
                processing_time=time.time() - start_time,
                pruning_method='hybrid_failed',
                metadata={'error': str(e)}
            )


class ContextPruningService:
    """
    Main service for context pruning operations.
    
    This service provides a unified interface for different context pruning strategies
    and can be integrated into both document processing and retrieval pipelines.
    """
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize default pruners
        self._initialize_pruners()
    
    def _initialize_pruners(self):
        """Initialize the available pruners."""
        try:
            self.llm_pruner = LLMCompressionPruner(**self.config)
            self.relevance_pruner = RelevanceFilterPruner(**self.config)
            self.metadata_pruner = MetadataFilterPruner(**self.config)
            self.hybrid_pruner = HybridContextPruner(**self.config)
            
            self.logger.info("ContextPruningService initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize context pruning service: {e}")
            raise
    
    def prune_context(
        self, 
        documents: List[Document], 
        query: str, 
        method: str = 'hybrid',
        **kwargs
    ) -> PruningResult:
        """
        Prune context using the specified method.
        
        Args:
            documents: List of documents to prune
            query: Query to determine relevance
            method: Pruning method ('llm_compression', 'relevance_filter', 'metadata_filter', 'hybrid')
            **kwargs: Additional parameters for the pruner
        
        Returns:
            PruningResult with pruned documents and metadata
        """
        try:
            if not documents:
                return PruningResult(
                    pruned_documents=[],
                    original_documents=documents,
                    original_count=0,
                    pruned_count=0,
                    compression_ratio=0.0,
                    processing_time=0.0,
                    pruning_method=method,
                    metadata={'error': 'No documents provided'}
                )
            
            # Select pruner based on method
            if method == 'llm_compression':
                pruner = self.llm_pruner
            elif method == 'relevance_filter':
                pruner = self.relevance_pruner
            elif method == 'metadata_filter':
                pruner = self.metadata_pruner
            elif method == 'hybrid':
                pruner = self.hybrid_pruner
            else:
                raise ValueError(f"Unknown pruning method: {method}")
            
            # Apply pruning
            result = pruner.prune(documents, query, **kwargs)
            
            self.logger.info(
                f"Context pruning completed: {result.original_count} -> {result.pruned_count} "
                f"documents (compression ratio: {result.compression_ratio:.2f}) "
                f"using method: {method}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Context pruning failed: {e}")
            # Return original documents if pruning fails
            return PruningResult(
                pruned_documents=documents,
                original_documents=documents,
                original_count=len(documents),
                pruned_count=len(documents),
                compression_ratio=1.0,
                processing_time=0.0,
                pruning_method=f"{method}_failed",
                metadata={'error': str(e)}
            )
    
    def get_pruning_stats(self, result: PruningResult) -> Dict[str, Any]:
        """Get statistics from a pruning result."""
        return {
            'original_count': result.original_count,
            'pruned_count': result.pruned_count,
            'compression_ratio': result.compression_ratio,
            'processing_time': result.processing_time,
            'pruning_method': result.pruning_method,
            'efficiency': f"{(1 - result.compression_ratio) * 100:.1f}% reduction"
        }


# Factory function for easy service creation
def get_context_pruning_service(**kwargs) -> ContextPruningService:
    """Get a configured context pruning service."""
    return ContextPruningService(**kwargs)


# Default configuration for different use cases
DEFAULT_CONFIGS = {
    'fast': {
        'method': 'relevance_filter',
        'similarity_threshold': 0.8,
        'top_k': 5,
        'embedding_model': 'all-MiniLM-L6-v2'
    },
    'balanced': {
        'method': 'hybrid',
        'use_metadata_filter': True,
        'use_relevance_filter': True,
        'use_llm_compression': False,
        'similarity_threshold': 0.7,
        'top_k': 10
    },
    'high_quality': {
        'method': 'hybrid',
        'use_metadata_filter': True,
        'use_relevance_filter': True,
        'use_llm_compression': True,
        'similarity_threshold': 0.6,
        'model_name': 'gpt-4o-mini',
        'temperature': 0.0
    }
}
