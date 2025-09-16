"""
Auto Merging Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDocumentStore
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.node_parser import HierarchicalNodeParser

from .base_service import LlamaIndexBaseService

logger = logging.getLogger(__name__)


def create_auto_merging_retriever(
    base_service: LlamaIndexBaseService,
    chunk_sizes: List[int] = [512, 256, 128],
    similarity_top_k: int = 6,
    verbose: bool = True
) -> AutoMergingRetriever:
    """
    Create an Auto Merging Retriever for hierarchical context preservation.
    
    This retriever uses hierarchical chunking to break documents into parent and child nodes.
    If enough child nodes from the same parent are retrieved, it returns the parent node instead.
    
    Args:
        base_service: The base LlamaIndex service
        chunk_sizes: List of chunk sizes from largest to smallest
        similarity_top_k: Number of top similar documents to retrieve
        verbose: Whether to enable verbose logging
    
    Returns:
        AutoMergingRetriever instance
    """
    try:
        if not base_service.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        # Create hierarchical nodes
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=chunk_sizes
        )
        
        hierarchical_nodes = node_parser.get_nodes_from_documents(base_service.documents)
        logger.info(f"Created {len(hierarchical_nodes)} hierarchical nodes with chunk sizes: {chunk_sizes}")
        
        # Create storage context with docstore for parent documents
        docstore = SimpleDocumentStore()
        docstore.add_documents(hierarchical_nodes)
        
        storage_context = StorageContext.from_defaults(
            docstore=docstore,
            vector_store=base_service.get_vector_store()
        )
        
        # Create base vector index with hierarchical nodes
        base_index = VectorStoreIndex(
            hierarchical_nodes, 
            storage_context=storage_context
        )
        
        # Create base retriever
        base_retriever = base_index.as_retriever(similarity_top_k=similarity_top_k)
        
        # Create auto-merging retriever
        auto_merging_retriever = AutoMergingRetriever(
            base_retriever=base_retriever,
            storage_context=storage_context,
            verbose=verbose
        )
        
        logger.info(f"Auto Merging Retriever created with chunk_sizes={chunk_sizes}, top_k={similarity_top_k}")
        return auto_merging_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Auto Merging Retriever: {e}")
        raise


def create_auto_merging_query_engine(
    base_service: LlamaIndexBaseService,
    chunk_sizes: List[int] = [512, 256, 128],
    similarity_top_k: int = 6,
    verbose: bool = True
) -> RetrieverQueryEngine:
    """
    Create an Auto Merging Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        chunk_sizes: List of chunk sizes from largest to smallest
        similarity_top_k: Number of top similar documents to retrieve
        verbose: Whether to enable verbose logging
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever
        retriever = create_auto_merging_retriever(
            base_service, chunk_sizes, similarity_top_k, verbose
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info("Auto Merging Query Engine created")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create Auto Merging Query Engine: {e}")
        raise


def search_with_auto_merging_retriever(
    retriever: AutoMergingRetriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using an Auto Merging Retriever.
    
    Args:
        retriever: The Auto Merging Retriever
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"Auto merging retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"Auto merging retrieval failed for query '{query}': {e}")
        raise


def get_auto_merging_retriever_info(retriever: AutoMergingRetriever) -> Dict[str, Any]:
    """
    Get information about an Auto Merging Retriever.
    
    Args:
        retriever: The Auto Merging Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        return {
            "type": "AutoMergingRetriever",
            "base_retriever_type": type(retriever.base_retriever).__name__,
            "verbose": retriever.verbose,
            "similarity_top_k": getattr(retriever.base_retriever, 'similarity_top_k', 'unknown')
        }
    except Exception as e:
        logger.error(f"Failed to get auto merging retriever info: {e}")
        return {"error": str(e)}


def create_custom_auto_merging_retriever(
    base_service: LlamaIndexBaseService,
    chunk_sizes: List[int] = [1024, 512, 256],
    chunk_overlap: int = 50,
    similarity_top_k: int = 8,
    merge_threshold: float = 0.5,
    verbose: bool = True
) -> 'CustomAutoMergingRetriever':
    """
    Create a custom auto merging retriever with configurable merge logic.
    
    Args:
        base_service: The base LlamaIndex service
        chunk_sizes: List of chunk sizes from largest to smallest
        chunk_overlap: Overlap between chunks
        similarity_top_k: Number of top similar documents to retrieve
        merge_threshold: Threshold for merging child nodes (0.0 to 1.0)
        verbose: Whether to enable verbose logging
    
    Returns:
        CustomAutoMergingRetriever instance
    """
    try:
        # Create hierarchical nodes with custom overlap
        node_parser = HierarchicalNodeParser.from_defaults(
            chunk_sizes=chunk_sizes,
            chunk_overlap=chunk_overlap
        )
        
        hierarchical_nodes = node_parser.get_nodes_from_documents(base_service.documents)
        logger.info(f"Created {len(hierarchical_nodes)} hierarchical nodes with custom overlap")
        
        # Create storage context
        docstore = SimpleDocumentStore()
        docstore.add_documents(hierarchical_nodes)
        
        storage_context = StorageContext.from_defaults(
            docstore=docstore,
            vector_store=base_service.get_vector_store()
        )
        
        # Create base vector index
        base_index = VectorStoreIndex(
            hierarchical_nodes, 
            storage_context=storage_context
        )
        
        # Create base retriever
        base_retriever = base_index.as_retriever(similarity_top_k=similarity_top_k)
        
        # Create custom auto merging retriever
        custom_retriever = CustomAutoMergingRetriever(
            base_retriever=base_retriever,
            storage_context=storage_context,
            merge_threshold=merge_threshold,
            verbose=verbose
        )
        
        logger.info(f"Custom Auto Merging Retriever created with merge_threshold={merge_threshold}")
        return custom_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Custom Auto Merging Retriever: {e}")
        raise


class CustomAutoMergingRetriever:
    """
    Custom Auto Merging Retriever with configurable merge logic.
    """
    
    def __init__(
        self,
        base_retriever,
        storage_context: StorageContext,
        merge_threshold: float = 0.5,
        verbose: bool = True
    ):
        self.base_retriever = base_retriever
        self.storage_context = storage_context
        self.merge_threshold = merge_threshold
        self.verbose = verbose
    
    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Retrieve documents with custom auto merging logic.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            # Get initial results from base retriever
            initial_results = self.base_retriever.retrieve(query_bundle)
            
            if self.verbose:
                logger.info(f"Initial retrieval found {len(initial_results)} nodes")
            
            # Group results by parent document
            parent_groups = {}
            for result in initial_results:
                node = result.node
                # Check if this is a child node with a parent reference
                if hasattr(node, 'parent_node') and node.parent_node:
                    parent_id = node.parent_node.node_id
                    if parent_id not in parent_groups:
                        parent_groups[parent_id] = []
                    parent_groups[parent_id].append(result)
                else:
                    # This is a top-level node, add it directly
                    parent_groups[node.node_id] = [result]
            
            # Apply custom merge logic
            merged_results = []
            for parent_id, child_results in parent_groups.items():
                if len(child_results) >= 2:  # If we have multiple child results
                    # Calculate merge score based on number of children and their scores
                    total_score = sum(r.score for r in child_results)
                    avg_score = total_score / len(child_results)
                    merge_score = len(child_results) / 10.0  # Normalize by expected max children
                    
                    if merge_score >= self.merge_threshold:
                        # Merge: get the parent node
                        try:
                            parent_node = self.storage_context.docstore.get_document(parent_id)
                            if parent_node:
                                merged_result = NodeWithScore(
                                    node=parent_node,
                                    score=avg_score  # Use average score of children
                                )
                                merged_results.append(merged_result)
                                if self.verbose:
                                    logger.info(f"Merged {len(child_results)} children into parent {parent_id}")
                                continue
                        except Exception as e:
                            if self.verbose:
                                logger.warning(f"Could not retrieve parent {parent_id}: {e}")
                
                # If not merged, add individual results
                merged_results.extend(child_results)
            
            # Sort by score and return
            merged_results.sort(key=lambda x: x.score, reverse=True)
            
            if self.verbose:
                logger.info(f"Final merged results: {len(merged_results)} nodes")
            
            return merged_results
            
        except Exception as e:
            logger.error(f"Custom auto merging retrieval failed: {e}")
            raise


# Convenience function for quick setup
def setup_auto_merging_retriever(
    documents: List,
    collection_name: str = "auto_merging_documents",
    chunk_sizes: List[int] = [512, 256, 128],
    similarity_top_k: int = 6,
    verbose: bool = True
) -> tuple[AutoMergingRetriever, LlamaIndexBaseService]:
    """
    Quick setup function for Auto Merging Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        chunk_sizes: List of chunk sizes from largest to smallest
        similarity_top_k: Number of top similar documents to retrieve
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
        retriever = create_auto_merging_retriever(
            base_service, chunk_sizes, similarity_top_k, verbose
        )
        
        logger.info(f"Auto merging retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup auto merging retriever: {e}")
        raise
