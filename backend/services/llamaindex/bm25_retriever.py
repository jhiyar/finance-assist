"""
BM25 Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService

logger = logging.getLogger(__name__)

# Try to import BM25Retriever, fallback if not available
try:
    from llama_index.retrievers.bm25 import BM25Retriever
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("BM25Retriever not available. Install llama-index-retrievers-bm25 and PyStemmer")


def create_bm25_retriever(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 5,
    stemmer_language: str = "english"
) -> BM25Retriever:
    """
    Create a BM25 Retriever for keyword-based search.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of top similar documents to retrieve
        stemmer_language: Language for stemming (e.g., "english")
    
    Returns:
        BM25Retriever instance
    """
    if not BM25_AVAILABLE:
        raise ImportError(
            "BM25Retriever not available. Please install: "
            "pip install llama-index-retrievers-bm25 PyStemmer"
        )
    
    try:
        # Ensure nodes are created
        if not base_service.nodes:
            base_service.create_nodes()
        
        # Try to import Stemmer
        try:
            import Stemmer
            stemmer = Stemmer.Stemmer(stemmer_language)
        except ImportError:
            logger.warning("PyStemmer not available, using default stemmer")
            stemmer = None
        
        # Create BM25 retriever
        retriever = BM25Retriever.from_defaults(
            nodes=base_service.nodes,
            similarity_top_k=similarity_top_k,
            stemmer=stemmer,
            language=stemmer_language
        )
        
        logger.info(f"BM25 Retriever created with top_k={similarity_top_k}, language={stemmer_language}")
        return retriever
        
    except Exception as e:
        logger.error(f"Failed to create BM25 Retriever: {e}")
        raise


def create_bm25_query_engine(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 5,
    stemmer_language: str = "english"
) -> RetrieverQueryEngine:
    """
    Create a BM25 Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of top similar documents to retrieve
        stemmer_language: Language for stemming
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever
        retriever = create_bm25_retriever(
            base_service, similarity_top_k, stemmer_language
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info("BM25 Query Engine created")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create BM25 Query Engine: {e}")
        raise


def search_with_bm25_retriever(
    retriever: BM25Retriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using a BM25 Retriever.
    
    Args:
        retriever: The BM25 Retriever
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"BM25 retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"BM25 retrieval failed for query '{query}': {e}")
        raise


def get_bm25_retriever_info(retriever: BM25Retriever) -> Dict[str, Any]:
    """
    Get information about a BM25 Retriever.
    
    Args:
        retriever: The BM25 Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        return {
            "type": "BM25Retriever",
            "similarity_top_k": retriever.similarity_top_k,
            "language": getattr(retriever, 'language', 'unknown'),
            "stemmer_available": getattr(retriever, 'stemmer', None) is not None,
            "node_count": len(retriever.nodes) if hasattr(retriever, 'nodes') else 0
        }
    except Exception as e:
        logger.error(f"Failed to get BM25 retriever info: {e}")
        return {"error": str(e)}


def create_hybrid_retriever(
    base_service: LlamaIndexBaseService,
    vector_top_k: int = 3,
    bm25_top_k: int = 3,
    final_top_k: int = 5,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    stemmer_language: str = "english"
) -> 'HybridRetriever':
    """
    Create a hybrid retriever combining Vector and BM25 retrievers.
    
    Args:
        base_service: The base LlamaIndex service
        vector_top_k: Number of results from vector retriever
        bm25_top_k: Number of results from BM25 retriever
        final_top_k: Final number of results to return
        vector_weight: Weight for vector retriever scores
        bm25_weight: Weight for BM25 retriever scores
        stemmer_language: Language for BM25 stemming
    
    Returns:
        HybridRetriever instance
    """
    try:
        from .vector_retriever import create_vector_index_retriever
        
        # Create both retrievers
        vector_retriever = create_vector_index_retriever(
            base_service, vector_top_k, create_index=True
        )
        
        bm25_retriever = create_bm25_retriever(
            base_service, bm25_top_k, stemmer_language
        )
        
        # Create hybrid retriever
        hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            final_top_k=final_top_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )
        
        logger.info(f"Hybrid retriever created with weights: vector={vector_weight}, bm25={bm25_weight}")
        return hybrid_retriever
        
    except Exception as e:
        logger.error(f"Failed to create hybrid retriever: {e}")
        raise


class HybridRetriever:
    """
    Custom hybrid retriever combining Vector and BM25 retrievers.
    """
    
    def __init__(
        self,
        vector_retriever,
        bm25_retriever,
        final_top_k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ):
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.final_top_k = final_top_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
    
    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Retrieve documents using hybrid approach.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            # Get results from both retrievers
            vector_results = self.vector_retriever.retrieve(query_bundle)
            bm25_results = self.bm25_retriever.retrieve(query_bundle)
            
            # Create score dictionaries using text content as keys
            vector_scores = {}
            bm25_scores = {}
            all_nodes = {}
            
            # Normalize vector scores
            max_vector_score = max([r.score for r in vector_results]) if vector_results else 1
            for result in vector_results:
                text_key = result.text.strip()
                normalized_score = result.score / max_vector_score if max_vector_score > 0 else 0
                vector_scores[text_key] = normalized_score
                all_nodes[text_key] = result
            
            # Normalize BM25 scores
            max_bm25_score = max([r.score for r in bm25_results]) if bm25_results else 1
            for result in bm25_results:
                text_key = result.text.strip()
                normalized_score = result.score / max_bm25_score if max_bm25_score > 0 else 0
                bm25_scores[text_key] = normalized_score
                all_nodes[text_key] = result
            
            # Calculate hybrid scores
            hybrid_results = []
            for text_key in all_nodes:
                vector_score = vector_scores.get(text_key, 0)
                bm25_score = bm25_scores.get(text_key, 0)
                hybrid_score = (self.vector_weight * vector_score + 
                              self.bm25_weight * bm25_score)
                
                # Create new NodeWithScore with hybrid score
                original_node = all_nodes[text_key]
                hybrid_node = NodeWithScore(
                    node=original_node.node,
                    score=hybrid_score
                )
                hybrid_results.append(hybrid_node)
            
            # Sort by hybrid score and return top k
            hybrid_results.sort(key=lambda x: x.score, reverse=True)
            final_results = hybrid_results[:self.final_top_k]
            
            logger.info(f"Hybrid retriever found {len(final_results)} nodes for query")
            return final_results
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            raise


# Convenience function for quick setup
def setup_bm25_retriever(
    documents: List,
    collection_name: str = "bm25_documents",
    similarity_top_k: int = 5,
    stemmer_language: str = "english"
) -> tuple[BM25Retriever, LlamaIndexBaseService]:
    """
    Quick setup function for BM25 Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        similarity_top_k: Number of top similar documents to retrieve
        stemmer_language: Language for stemming
    
    Returns:
        Tuple of (retriever, base_service)
    """
    if not BM25_AVAILABLE:
        raise ImportError(
            "BM25Retriever not available. Please install: "
            "pip install llama-index-retrievers-bm25 PyStemmer"
        )
    
    try:
        # Create base service
        base_service = LlamaIndexBaseService(collection_name=collection_name)
        
        # Load documents
        base_service.load_documents(documents)
        
        # Create retriever
        retriever = create_bm25_retriever(
            base_service, similarity_top_k, stemmer_language
        )
        
        logger.info(f"BM25 retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup BM25 retriever: {e}")
        raise
