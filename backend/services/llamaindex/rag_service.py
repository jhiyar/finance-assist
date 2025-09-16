"""
Main RAG Service that combines all LlamaIndex retrievers.
"""
import logging
from typing import List, Optional, Dict, Any, Union
from llama_index.core.schema import NodeWithScore, QueryBundle, Document
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService
from .vector_retriever import create_vector_index_retriever, create_vector_query_engine
from .bm25_retriever import create_bm25_retriever, create_bm25_query_engine, BM25_AVAILABLE
from .document_summary_retriever import (
    create_llm_document_summary_retriever,
    create_embedding_document_summary_retriever,
    create_document_summary_query_engine
)
from .auto_merging_retriever import create_auto_merging_retriever, create_auto_merging_query_engine
from .recursive_retriever import create_recursive_retriever, create_recursive_query_engine
from .query_fusion_retriever import (
    create_query_fusion_retriever,
    create_query_fusion_query_engine,
    create_multi_mode_query_fusion_retriever,
    create_adaptive_query_fusion_retriever
)

logger = logging.getLogger(__name__)


class LlamaIndexRAGService:
    """
    Main RAG Service that provides access to all LlamaIndex retrievers.
    """
    
    def __init__(self, collection_name: str = "rag_documents"):
        self.collection_name = collection_name
        self.base_service = LlamaIndexBaseService(collection_name=collection_name)
        
        # Initialize retrievers cache
        self._retrievers = {}
        self._query_engines = {}
        
        logger.info(f"LlamaIndex RAG Service initialized with collection: {collection_name}")
    
    def load_documents(self, documents: List[Document]) -> None:
        """Load documents into the RAG service."""
        self.base_service.load_documents(documents)
        # Clear cached retrievers when new documents are loaded
        self._retrievers.clear()
        self._query_engines.clear()
        logger.info(f"Loaded {len(documents)} documents and cleared caches")
    
    def get_vector_retriever(self, similarity_top_k: int = 5) -> Any:
        """Get or create a Vector Index Retriever."""
        cache_key = f"vector_{similarity_top_k}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_vector_index_retriever(
                self.base_service, similarity_top_k, create_index=True
            )
        return self._retrievers[cache_key]
    
    def get_bm25_retriever(self, similarity_top_k: int = 5, stemmer_language: str = "english") -> Any:
        """Get or create a BM25 Retriever."""
        if not BM25_AVAILABLE:
            raise ImportError("BM25Retriever not available. Install llama-index-retrievers-bm25 and PyStemmer")
        
        cache_key = f"bm25_{similarity_top_k}_{stemmer_language}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_bm25_retriever(
                self.base_service, similarity_top_k, stemmer_language
            )
        return self._retrievers[cache_key]
    
    def get_document_summary_retriever(
        self, 
        retriever_type: str = "llm", 
        top_k: int = 3,
        summary_template: Optional[str] = None
    ) -> Any:
        """Get or create a Document Summary Retriever."""
        cache_key = f"doc_summary_{retriever_type}_{top_k}"
        if cache_key not in self._retrievers:
            if retriever_type.lower() == "llm":
                self._retrievers[cache_key] = create_llm_document_summary_retriever(
                    self.base_service, top_k, summary_template
                )
            elif retriever_type.lower() == "embedding":
                self._retrievers[cache_key] = create_embedding_document_summary_retriever(
                    self.base_service, top_k, summary_template
                )
            else:
                raise ValueError(f"Invalid retriever_type: {retriever_type}")
        return self._retrievers[cache_key]
    
    def get_auto_merging_retriever(
        self, 
        chunk_sizes: List[int] = [512, 256, 128], 
        similarity_top_k: int = 6,
        verbose: bool = True
    ) -> Any:
        """Get or create an Auto Merging Retriever."""
        cache_key = f"auto_merging_{similarity_top_k}_{str(chunk_sizes)}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_auto_merging_retriever(
                self.base_service, chunk_sizes, similarity_top_k, verbose
            )
        return self._retrievers[cache_key]
    
    def get_recursive_retriever(
        self, 
        reference_strategy: str = "cross_document", 
        similarity_top_k: int = 2,
        verbose: bool = True
    ) -> Any:
        """Get or create a Recursive Retriever."""
        cache_key = f"recursive_{reference_strategy}_{similarity_top_k}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_recursive_retriever(
                self.base_service, reference_strategy, similarity_top_k, verbose
            )
        return self._retrievers[cache_key]
    
    def get_query_fusion_retriever(
        self, 
        retrievers: Optional[List] = None,
        similarity_top_k: int = 3,
        num_queries: int = 4,
        mode: str = "reciprocal_rerank",
        use_async: bool = False,
        verbose: bool = True
    ) -> Any:
        """Get or create a Query Fusion Retriever."""
        cache_key = f"query_fusion_{mode}_{similarity_top_k}_{num_queries}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_query_fusion_retriever(
                self.base_service, retrievers, similarity_top_k, num_queries, mode, use_async, verbose
            )
        return self._retrievers[cache_key]
    
    def get_multi_mode_query_fusion_retriever(
        self, 
        similarity_top_k: int = 3,
        num_queries: int = 4,
        use_async: bool = False,
        verbose: bool = True
    ) -> Any:
        """Get or create a Multi-mode Query Fusion Retriever."""
        cache_key = f"multi_mode_fusion_{similarity_top_k}_{num_queries}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_multi_mode_query_fusion_retriever(
                self.base_service, similarity_top_k, num_queries, use_async, verbose
            )
        return self._retrievers[cache_key]
    
    def get_adaptive_query_fusion_retriever(
        self, 
        similarity_top_k: int = 3,
        num_queries: int = 4,
        use_async: bool = False,
        verbose: bool = True
    ) -> Any:
        """Get or create an Adaptive Query Fusion Retriever."""
        cache_key = f"adaptive_fusion_{similarity_top_k}_{num_queries}"
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = create_adaptive_query_fusion_retriever(
                self.base_service, similarity_top_k, num_queries, use_async, verbose
            )
        return self._retrievers[cache_key]
    
    # Query Engine methods
    def get_vector_query_engine(self, similarity_top_k: int = 5) -> RetrieverQueryEngine:
        """Get or create a Vector Index Query Engine."""
        cache_key = f"vector_qe_{similarity_top_k}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_vector_query_engine(
                self.base_service, similarity_top_k, create_index=True
            )
        return self._query_engines[cache_key]
    
    def get_bm25_query_engine(self, similarity_top_k: int = 5, stemmer_language: str = "english") -> RetrieverQueryEngine:
        """Get or create a BM25 Query Engine."""
        if not BM25_AVAILABLE:
            raise ImportError("BM25Retriever not available. Install llama-index-retrievers-bm25 and PyStemmer")
        
        cache_key = f"bm25_qe_{similarity_top_k}_{stemmer_language}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_bm25_query_engine(
                self.base_service, similarity_top_k, stemmer_language
            )
        return self._query_engines[cache_key]
    
    def get_document_summary_query_engine(
        self, 
        retriever_type: str = "llm", 
        top_k: int = 3,
        summary_template: Optional[str] = None
    ) -> RetrieverQueryEngine:
        """Get or create a Document Summary Query Engine."""
        cache_key = f"doc_summary_qe_{retriever_type}_{top_k}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_document_summary_query_engine(
                self.base_service, retriever_type, top_k, summary_template
            )
        return self._query_engines[cache_key]
    
    def get_auto_merging_query_engine(
        self, 
        chunk_sizes: List[int] = [512, 256, 128], 
        similarity_top_k: int = 6,
        verbose: bool = True
    ) -> RetrieverQueryEngine:
        """Get or create an Auto Merging Query Engine."""
        cache_key = f"auto_merging_qe_{similarity_top_k}_{str(chunk_sizes)}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_auto_merging_query_engine(
                self.base_service, chunk_sizes, similarity_top_k, verbose
            )
        return self._query_engines[cache_key]
    
    def get_recursive_query_engine(
        self, 
        reference_strategy: str = "cross_document", 
        similarity_top_k: int = 2,
        verbose: bool = True
    ) -> RetrieverQueryEngine:
        """Get or create a Recursive Query Engine."""
        cache_key = f"recursive_qe_{reference_strategy}_{similarity_top_k}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_recursive_query_engine(
                self.base_service, reference_strategy, similarity_top_k, verbose
            )
        return self._query_engines[cache_key]
    
    def get_query_fusion_query_engine(
        self, 
        retrievers: Optional[List] = None,
        similarity_top_k: int = 3,
        num_queries: int = 4,
        mode: str = "reciprocal_rerank",
        use_async: bool = False,
        verbose: bool = True
    ) -> RetrieverQueryEngine:
        """Get or create a Query Fusion Query Engine."""
        cache_key = f"query_fusion_qe_{mode}_{similarity_top_k}_{num_queries}"
        if cache_key not in self._query_engines:
            self._query_engines[cache_key] = create_query_fusion_query_engine(
                self.base_service, retrievers, similarity_top_k, num_queries, mode, use_async, verbose
            )
        return self._query_engines[cache_key]
    
    # Search methods
    def search_with_retriever(
        self, 
        retriever_type: str, 
        query: str, 
        **kwargs
    ) -> List[NodeWithScore]:
        """
        Search using a specific retriever type.
        
        Args:
            retriever_type: Type of retriever to use
            query: Search query
            **kwargs: Additional arguments for the retriever
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            if retriever_type == "vector":
                retriever = self.get_vector_retriever(kwargs.get('similarity_top_k', 5))
            elif retriever_type == "bm25":
                retriever = self.get_bm25_retriever(
                    kwargs.get('similarity_top_k', 5),
                    kwargs.get('stemmer_language', 'english')
                )
            elif retriever_type == "document_summary_llm":
                retriever = self.get_document_summary_retriever("llm", kwargs.get('top_k', 3))
            elif retriever_type == "document_summary_embedding":
                retriever = self.get_document_summary_retriever("embedding", kwargs.get('top_k', 3))
            elif retriever_type == "auto_merging":
                retriever = self.get_auto_merging_retriever(
                    kwargs.get('chunk_sizes', [512, 256, 128]),
                    kwargs.get('similarity_top_k', 6)
                )
            elif retriever_type == "recursive":
                retriever = self.get_recursive_retriever(
                    kwargs.get('reference_strategy', 'cross_document'),
                    kwargs.get('similarity_top_k', 2)
                )
            elif retriever_type == "query_fusion":
                retriever = self.get_query_fusion_retriever(
                    kwargs.get('retrievers'),
                    kwargs.get('similarity_top_k', 3),
                    kwargs.get('num_queries', 4),
                    kwargs.get('mode', 'reciprocal_rerank')
                )
            elif retriever_type == "adaptive_fusion":
                retriever = self.get_adaptive_query_fusion_retriever(
                    kwargs.get('similarity_top_k', 3),
                    kwargs.get('num_queries', 4)
                )
            else:
                raise ValueError(f"Unknown retriever type: {retriever_type}")
            
            query_bundle = QueryBundle(query_str=query)
            nodes = retriever.retrieve(query_bundle)
            
            logger.info(f"Search with {retriever_type} found {len(nodes)} nodes for query: {query}")
            return nodes
            
        except Exception as e:
            logger.error(f"Search with {retriever_type} failed for query '{query}': {e}")
            raise
    
    def query_with_engine(
        self, 
        engine_type: str, 
        query: str, 
        **kwargs
    ) -> str:
        """
        Query using a specific query engine type.
        
        Args:
            engine_type: Type of query engine to use
            query: Query string
            **kwargs: Additional arguments for the engine
        
        Returns:
            Response string
        """
        try:
            if engine_type == "vector":
                engine = self.get_vector_query_engine(kwargs.get('similarity_top_k', 5))
            elif engine_type == "bm25":
                engine = self.get_bm25_query_engine(
                    kwargs.get('similarity_top_k', 5),
                    kwargs.get('stemmer_language', 'english')
                )
            elif engine_type == "document_summary_llm":
                engine = self.get_document_summary_query_engine("llm", kwargs.get('top_k', 3))
            elif engine_type == "document_summary_embedding":
                engine = self.get_document_summary_query_engine("embedding", kwargs.get('top_k', 3))
            elif engine_type == "auto_merging":
                engine = self.get_auto_merging_query_engine(
                    kwargs.get('chunk_sizes', [512, 256, 128]),
                    kwargs.get('similarity_top_k', 6)
                )
            elif engine_type == "recursive":
                engine = self.get_recursive_query_engine(
                    kwargs.get('reference_strategy', 'cross_document'),
                    kwargs.get('similarity_top_k', 2)
                )
            elif engine_type == "query_fusion":
                engine = self.get_query_fusion_query_engine(
                    kwargs.get('retrievers'),
                    kwargs.get('similarity_top_k', 3),
                    kwargs.get('num_queries', 4),
                    kwargs.get('mode', 'reciprocal_rerank')
                )
            else:
                raise ValueError(f"Unknown engine type: {engine_type}")
            
            response = engine.query(query)
            
            logger.info(f"Query with {engine_type} completed for query: {query}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Query with {engine_type} failed for query '{query}': {e}")
            raise
    
    def get_available_retrievers(self) -> List[str]:
        """Get list of available retriever types."""
        retrievers = ["vector", "document_summary_llm", "document_summary_embedding", 
                     "auto_merging", "recursive", "query_fusion", "adaptive_fusion"]
        
        if BM25_AVAILABLE:
            retrievers.append("bm25")
        
        return retrievers
    
    def get_available_engines(self) -> List[str]:
        """Get list of available query engine types."""
        engines = ["vector", "document_summary_llm", "document_summary_embedding", 
                  "auto_merging", "recursive", "query_fusion"]
        
        if BM25_AVAILABLE:
            engines.append("bm25")
        
        return engines
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the RAG service."""
        return {
            "collection_name": self.collection_name,
            "document_count": len(self.base_service.documents),
            "node_count": len(self.base_service.nodes),
            "cached_retrievers": len(self._retrievers),
            "cached_query_engines": len(self._query_engines),
            "available_retrievers": self.get_available_retrievers(),
            "available_engines": self.get_available_engines(),
            "bm25_available": BM25_AVAILABLE,
            "collection_info": self.base_service.get_collection_info()
        }
    
    def clear_caches(self):
        """Clear all cached retrievers and query engines."""
        self._retrievers.clear()
        self._query_engines.clear()
        logger.info("Cleared all caches")
    
    def clear_collection(self):
        """Clear the current collection."""
        self.base_service.clear_collection()
        self.clear_caches()
        logger.info("Cleared collection and caches")


def get_llamaindex_rag_service(collection_name: str = "rag_documents") -> LlamaIndexRAGService:
    """Get a LlamaIndex RAG service instance."""
    return LlamaIndexRAGService(collection_name=collection_name)


# Convenience function for quick setup
def setup_llamaindex_rag_service(
    documents: List[Document],
    collection_name: str = "rag_documents"
) -> LlamaIndexRAGService:
    """
    Quick setup function for LlamaIndex RAG Service.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
    
    Returns:
        LlamaIndexRAGService instance
    """
    try:
        # Create RAG service
        rag_service = LlamaIndexRAGService(collection_name=collection_name)
        
        # Load documents
        rag_service.load_documents(documents)
        
        logger.info(f"LlamaIndex RAG service setup complete for {len(documents)} documents")
        return rag_service
        
    except Exception as e:
        logger.error(f"Failed to setup LlamaIndex RAG service: {e}")
        raise
