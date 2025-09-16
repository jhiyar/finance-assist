"""
Vector Index Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService

logger = logging.getLogger(__name__)


def create_vector_index_retriever(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 5,
    create_index: bool = True
) -> VectorIndexRetriever:
    """
    Create a Vector Index Retriever for semantic search.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of top similar documents to retrieve
        create_index: Whether to create a new index from documents
    
    Returns:
        VectorIndexRetriever instance
    """
    try:
        if create_index and base_service.documents:
            # Create nodes if not already created
            if not base_service.nodes:
                base_service.create_nodes()
            
            # Create vector index
            vector_index = VectorStoreIndex.from_documents(
                base_service.documents,
                storage_context=base_service.get_storage_context()
            )
            logger.info("Created new VectorStoreIndex from documents")
        else:
            # Load existing index
            vector_index = VectorStoreIndex.from_vector_store(
                base_service.get_vector_store(),
                storage_context=base_service.get_storage_context()
            )
            logger.info("Loaded existing VectorStoreIndex from vector store")
        
        # Create retriever
        retriever = VectorIndexRetriever(
            index=vector_index,
            similarity_top_k=similarity_top_k
        )
        
        logger.info(f"Vector Index Retriever created with top_k={similarity_top_k}")
        return retriever
        
    except Exception as e:
        logger.error(f"Failed to create Vector Index Retriever: {e}")
        raise


def create_vector_query_engine(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 5,
    create_index: bool = True
) -> RetrieverQueryEngine:
    """
    Create a Vector Index Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of top similar documents to retrieve
        create_index: Whether to create a new index from documents
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever
        retriever = create_vector_index_retriever(
            base_service, similarity_top_k, create_index
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info("Vector Index Query Engine created")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create Vector Index Query Engine: {e}")
        raise


def search_with_vector_retriever(
    retriever: VectorIndexRetriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using a Vector Index Retriever.
    
    Args:
        retriever: The Vector Index Retriever
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"Vector retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"Vector retrieval failed for query '{query}': {e}")
        raise


def get_vector_retriever_info(retriever: VectorIndexRetriever) -> Dict[str, Any]:
    """
    Get information about a Vector Index Retriever.
    
    Args:
        retriever: The Vector Index Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        return {
            "type": "VectorIndexRetriever",
            "similarity_top_k": retriever.similarity_top_k,
            "index_type": type(retriever.index).__name__,
            "embed_model": type(retriever.index._embed_model).__name__ if hasattr(retriever.index, '_embed_model') else "Unknown"
        }
    except Exception as e:
        logger.error(f"Failed to get retriever info: {e}")
        return {"error": str(e)}


# Convenience function for quick setup
def setup_vector_retriever(
    documents: List,
    collection_name: str = "vector_documents",
    similarity_top_k: int = 5
) -> tuple[VectorIndexRetriever, LlamaIndexBaseService]:
    """
    Quick setup function for Vector Index Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        similarity_top_k: Number of top similar documents to retrieve
    
    Returns:
        Tuple of (retriever, base_service)
    """
    try:
        # Create base service
        base_service = LlamaIndexBaseService(collection_name=collection_name)
        
        # Load documents
        base_service.load_documents(documents)
        
        # Create retriever
        retriever = create_vector_index_retriever(
            base_service, similarity_top_k, create_index=True
        )
        
        logger.info(f"Vector retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup vector retriever: {e}")
        raise
