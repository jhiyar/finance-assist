"""
Query Fusion Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService
from .vector_retriever import create_vector_index_retriever
from .bm25_retriever import create_bm25_retriever, BM25_AVAILABLE

logger = logging.getLogger(__name__)


def create_query_fusion_retriever(
    base_service: LlamaIndexBaseService,
    retrievers: Optional[List] = None,
    similarity_top_k: int = 3,
    num_queries: int = 4,
    mode: str = "reciprocal_rerank",
    use_async: bool = False,
    verbose: bool = True
) -> QueryFusionRetriever:
    """
    Create a Query Fusion Retriever for multi-query enhancement.
    
    This retriever combines results from different retrievers and optionally
    generates multiple variations of a query using an LLM to improve coverage.
    
    Args:
        base_service: The base LlamaIndex service
        retrievers: List of retrievers to combine (if None, creates default set)
        similarity_top_k: Number of results to retrieve per query
        num_queries: Number of query variations to generate
        mode: Fusion strategy ("reciprocal_rerank", "relative_score", "dist_based_score")
        use_async: Whether to use async processing
        verbose: Whether to enable verbose logging
    
    Returns:
        QueryFusionRetriever instance
    """
    try:
        if retrievers is None:
            # Create default retrievers
            retrievers = []
            
            # Add vector retriever
            vector_retriever = create_vector_index_retriever(
                base_service, similarity_top_k, create_index=True
            )
            retrievers.append(vector_retriever)
            
            # Add BM25 retriever if available
            if BM25_AVAILABLE:
                try:
                    bm25_retriever = create_bm25_retriever(
                        base_service, similarity_top_k
                    )
                    retrievers.append(bm25_retriever)
                    logger.info("Added BM25 retriever to query fusion")
                except Exception as e:
                    logger.warning(f"Could not add BM25 retriever: {e}")
        
        # Create query fusion retriever
        query_fusion_retriever = QueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            mode=mode,
            use_async=use_async,
            verbose=verbose
        )
        
        logger.info(f"Query Fusion Retriever created with {len(retrievers)} retrievers, mode={mode}")
        return query_fusion_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Query Fusion Retriever: {e}")
        raise


def create_query_fusion_query_engine(
    base_service: LlamaIndexBaseService,
    retrievers: Optional[List] = None,
    similarity_top_k: int = 3,
    num_queries: int = 4,
    mode: str = "reciprocal_rerank",
    use_async: bool = False,
    verbose: bool = True
) -> RetrieverQueryEngine:
    """
    Create a Query Fusion Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        retrievers: List of retrievers to combine
        similarity_top_k: Number of results to retrieve per query
        num_queries: Number of query variations to generate
        mode: Fusion strategy
        use_async: Whether to use async processing
        verbose: Whether to enable verbose logging
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever
        retriever = create_query_fusion_retriever(
            base_service, retrievers, similarity_top_k, num_queries, mode, use_async, verbose
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info("Query Fusion Query Engine created")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create Query Fusion Query Engine: {e}")
        raise


def search_with_query_fusion_retriever(
    retriever: QueryFusionRetriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using a Query Fusion Retriever.
    
    Args:
        retriever: The Query Fusion Retriever
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"Query fusion retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"Query fusion retrieval failed for query '{query}': {e}")
        raise


def get_query_fusion_retriever_info(retriever: QueryFusionRetriever) -> Dict[str, Any]:
    """
    Get information about a Query Fusion Retriever.
    
    Args:
        retriever: The Query Fusion Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        return {
            "type": "QueryFusionRetriever",
            "num_retrievers": len(retriever.retrievers),
            "similarity_top_k": retriever.similarity_top_k,
            "num_queries": retriever.num_queries,
            "mode": retriever.mode,
            "use_async": retriever.use_async,
            "retriever_types": [type(r).__name__ for r in retriever.retrievers]
        }
    except Exception as e:
        logger.error(f"Failed to get query fusion retriever info: {e}")
        return {"error": str(e)}


def create_multi_mode_query_fusion_retriever(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 3,
    num_queries: int = 4,
    use_async: bool = False,
    verbose: bool = True
) -> 'MultiModeQueryFusionRetriever':
    """
    Create a multi-mode query fusion retriever that can switch between fusion strategies.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of results to retrieve per query
        num_queries: Number of query variations to generate
        use_async: Whether to use async processing
        verbose: Whether to enable verbose logging
    
    Returns:
        MultiModeQueryFusionRetriever instance
    """
    try:
        # Create retrievers
        retrievers = []
        
        # Add vector retriever
        vector_retriever = create_vector_index_retriever(
            base_service, similarity_top_k, create_index=True
        )
        retrievers.append(vector_retriever)
        
        # Add BM25 retriever if available
        if BM25_AVAILABLE:
            try:
                bm25_retriever = create_bm25_retriever(
                    base_service, similarity_top_k
                )
                retrievers.append(bm25_retriever)
            except Exception as e:
                logger.warning(f"Could not add BM25 retriever: {e}")
        
        # Create multi-mode retriever
        multi_mode_retriever = MultiModeQueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            use_async=use_async,
            verbose=verbose
        )
        
        logger.info("Multi-mode Query Fusion Retriever created")
        return multi_mode_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Multi-mode Query Fusion Retriever: {e}")
        raise


class MultiModeQueryFusionRetriever:
    """
    Multi-mode Query Fusion Retriever that can switch between fusion strategies.
    """
    
    def __init__(
        self,
        retrievers: List,
        similarity_top_k: int = 3,
        num_queries: int = 4,
        use_async: bool = False,
        verbose: bool = True
    ):
        self.retrievers = retrievers
        self.similarity_top_k = similarity_top_k
        self.num_queries = num_queries
        self.use_async = use_async
        self.verbose = verbose
        
        # Create retrievers for each mode
        self.rrf_retriever = QueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            mode="reciprocal_rerank",
            use_async=use_async,
            verbose=verbose
        )
        
        self.relative_retriever = QueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            mode="relative_score",
            use_async=use_async,
            verbose=verbose
        )
        
        self.dist_retriever = QueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            mode="dist_based_score",
            use_async=use_async,
            verbose=verbose
        )
    
    def retrieve(self, query_bundle: QueryBundle, mode: str = "reciprocal_rerank") -> List[NodeWithScore]:
        """
        Retrieve documents using specified fusion mode.
        
        Args:
            query_bundle: Query to search for
            mode: Fusion strategy ("reciprocal_rerank", "relative_score", "dist_based_score")
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            if mode == "reciprocal_rerank":
                retriever = self.rrf_retriever
            elif mode == "relative_score":
                retriever = self.relative_retriever
            elif mode == "dist_based_score":
                retriever = self.dist_retriever
            else:
                raise ValueError(f"Unknown mode: {mode}")
            
            nodes = retriever.retrieve(query_bundle)
            
            if self.verbose:
                logger.info(f"Multi-mode query fusion ({mode}) found {len(nodes)} nodes")
            
            return nodes
            
        except Exception as e:
            logger.error(f"Multi-mode query fusion retrieval failed: {e}")
            raise
    
    def retrieve_all_modes(self, query_bundle: QueryBundle) -> Dict[str, List[NodeWithScore]]:
        """
        Retrieve documents using all fusion modes for comparison.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            Dictionary with results for each mode
        """
        try:
            results = {}
            
            for mode in ["reciprocal_rerank", "relative_score", "dist_based_score"]:
                results[mode] = self.retrieve(query_bundle, mode)
            
            if self.verbose:
                logger.info(f"Retrieved results for all modes: {[(mode, len(nodes)) for mode, nodes in results.items()]}")
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-mode retrieval failed: {e}")
            raise


def create_adaptive_query_fusion_retriever(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 3,
    num_queries: int = 4,
    use_async: bool = False,
    verbose: bool = True
) -> 'AdaptiveQueryFusionRetriever':
    """
    Create an adaptive query fusion retriever that automatically selects the best fusion mode.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of results to retrieve per query
        num_queries: Number of query variations to generate
        use_async: Whether to use async processing
        verbose: Whether to enable verbose logging
    
    Returns:
        AdaptiveQueryFusionRetriever instance
    """
    try:
        # Create retrievers
        retrievers = []
        
        # Add vector retriever
        vector_retriever = create_vector_index_retriever(
            base_service, similarity_top_k, create_index=True
        )
        retrievers.append(vector_retriever)
        
        # Add BM25 retriever if available
        if BM25_AVAILABLE:
            try:
                bm25_retriever = create_bm25_retriever(
                    base_service, similarity_top_k
                )
                retrievers.append(bm25_retriever)
            except Exception as e:
                logger.warning(f"Could not add BM25 retriever: {e}")
        
        # Create adaptive retriever
        adaptive_retriever = AdaptiveQueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            use_async=use_async,
            verbose=verbose
        )
        
        logger.info("Adaptive Query Fusion Retriever created")
        return adaptive_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Adaptive Query Fusion Retriever: {e}")
        raise


class AdaptiveQueryFusionRetriever:
    """
    Adaptive Query Fusion Retriever that automatically selects the best fusion mode.
    """
    
    def __init__(
        self,
        retrievers: List,
        similarity_top_k: int = 3,
        num_queries: int = 4,
        use_async: bool = False,
        verbose: bool = True
    ):
        self.retrievers = retrievers
        self.similarity_top_k = similarity_top_k
        self.num_queries = num_queries
        self.use_async = use_async
        self.verbose = verbose
        
        # Create multi-mode retriever
        self.multi_mode_retriever = MultiModeQueryFusionRetriever(
            retrievers=retrievers,
            similarity_top_k=similarity_top_k,
            num_queries=num_queries,
            use_async=use_async,
            verbose=verbose
        )
    
    def _analyze_query(self, query: str) -> str:
        """
        Analyze query to determine best fusion mode.
        
        Args:
            query: Query to analyze
        
        Returns:
            Recommended fusion mode
        """
        query_lower = query.lower()
        
        # Simple heuristics for mode selection
        if any(word in query_lower for word in ["list", "types", "examples", "all"]):
            return "reciprocal_rerank"  # Good for comprehensive results
        elif any(word in query_lower for word in ["best", "top", "most", "highest"]):
            return "relative_score"  # Good for ranking
        elif len(query.split()) > 5:
            return "dist_based_score"  # Good for complex queries
        else:
            return "reciprocal_rerank"  # Default
    
    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Retrieve documents using adaptive fusion mode selection.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            # Analyze query to select best mode
            recommended_mode = self._analyze_query(query_bundle.query_str)
            
            if self.verbose:
                logger.info(f"Adaptive mode selection: {recommended_mode} for query: {query_bundle.query_str}")
            
            # Retrieve using recommended mode
            nodes = self.multi_mode_retriever.retrieve(query_bundle, recommended_mode)
            
            return nodes
            
        except Exception as e:
            logger.error(f"Adaptive query fusion retrieval failed: {e}")
            raise


# Convenience function for quick setup
def setup_query_fusion_retriever(
    documents: List,
    collection_name: str = "query_fusion_documents",
    similarity_top_k: int = 3,
    num_queries: int = 4,
    mode: str = "reciprocal_rerank",
    use_async: bool = False,
    verbose: bool = True
) -> tuple[QueryFusionRetriever, LlamaIndexBaseService]:
    """
    Quick setup function for Query Fusion Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        similarity_top_k: Number of results to retrieve per query
        num_queries: Number of query variations to generate
        mode: Fusion strategy
        use_async: Whether to use async processing
        verbose: Whether to enable verbose logging
    
    Returns:
        Tuple of (retriever, base_service)
    """
    try:
        # Create base service
        base_service = LlamaIndexBaseService(collection_name=collection_name)
        
        # Load documents
        base_service.load_documents(documents)
        
        # Create retriever
        retriever = create_query_fusion_retriever(
            base_service, None, similarity_top_k, num_queries, mode, use_async, verbose
        )
        
        logger.info(f"Query fusion retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup query fusion retriever: {e}")
        raise
