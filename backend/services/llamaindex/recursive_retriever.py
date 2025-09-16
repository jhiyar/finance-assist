"""
Recursive Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import RecursiveRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, Document
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService

logger = logging.getLogger(__name__)


def create_documents_with_references(
    base_service: LlamaIndexBaseService,
    reference_strategy: str = "cross_document"
) -> List[Document]:
    """
    Create documents with references for recursive retrieval.
    
    Args:
        base_service: The base LlamaIndex service
        reference_strategy: Strategy for creating references ("cross_document", "sequential", "topic_based")
    
    Returns:
        List of documents with reference metadata
    """
    try:
        if not base_service.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        docs_with_refs = []
        
        if reference_strategy == "cross_document":
            # Create cross-document references
            for i, doc in enumerate(base_service.documents):
                # Create references to other documents
                references = []
                for j in range(len(base_service.documents)):
                    if i != j:
                        references.append(f"doc_{j}")
                
                # Add reference metadata
                ref_doc = Document(
                    text=doc.text,
                    metadata={
                        "doc_id": f"doc_{i}",
                        "references": references[:3],  # Limit to 3 references
                        "original_index": i
                    }
                )
                docs_with_refs.append(ref_doc)
        
        elif reference_strategy == "sequential":
            # Create sequential references
            for i, doc in enumerate(base_service.documents):
                references = []
                if i > 0:
                    references.append(f"doc_{i-1}")  # Previous document
                if i < len(base_service.documents) - 1:
                    references.append(f"doc_{i+1}")  # Next document
                
                ref_doc = Document(
                    text=doc.text,
                    metadata={
                        "doc_id": f"doc_{i}",
                        "references": references,
                        "original_index": i
                    }
                )
                docs_with_refs.append(ref_doc)
        
        elif reference_strategy == "topic_based":
            # Create topic-based references (simplified)
            for i, doc in enumerate(base_service.documents):
                # Simple topic-based referencing based on document index
                references = []
                if i % 2 == 0 and i + 1 < len(base_service.documents):
                    references.append(f"doc_{i+1}")  # Pair with next document
                elif i % 2 == 1 and i - 1 >= 0:
                    references.append(f"doc_{i-1}")  # Pair with previous document
                
                ref_doc = Document(
                    text=doc.text,
                    metadata={
                        "doc_id": f"doc_{i}",
                        "references": references,
                        "original_index": i
                    }
                )
                docs_with_refs.append(ref_doc)
        
        else:
            raise ValueError(f"Unknown reference strategy: {reference_strategy}")
        
        logger.info(f"Created {len(docs_with_refs)} documents with {reference_strategy} references")
        return docs_with_refs
        
    except Exception as e:
        logger.error(f"Failed to create documents with references: {e}")
        raise


def create_recursive_retriever(
    base_service: LlamaIndexBaseService,
    reference_strategy: str = "cross_document",
    similarity_top_k: int = 2,
    verbose: bool = True
) -> RecursiveRetriever:
    """
    Create a Recursive Retriever for multi-level reference following.
    
    This retriever follows relationships between nodes using references,
    such as citations in academic papers or other metadata links.
    
    Args:
        base_service: The base LlamaIndex service
        reference_strategy: Strategy for creating references
        similarity_top_k: Number of top similar documents to retrieve
        verbose: Whether to enable verbose logging
    
    Returns:
        RecursiveRetriever instance
    """
    try:
        # Create documents with references
        docs_with_refs = create_documents_with_references(
            base_service, reference_strategy
        )
        
        # Create index with referenced documents
        ref_index = VectorStoreIndex.from_documents(
            docs_with_refs,
            storage_context=base_service.get_storage_context()
        )
        
        # Create retriever mapping for each document
        retriever_dict = {}
        for i in range(len(docs_with_refs)):
            doc_retriever = ref_index.as_retriever(similarity_top_k=1)
            retriever_dict[f"doc_{i}"] = doc_retriever
        
        # Create base retriever
        base_retriever = ref_index.as_retriever(similarity_top_k=similarity_top_k)
        
        # Add the root retriever to the dictionary
        retriever_dict["vector"] = base_retriever
        
        # Create recursive retriever
        recursive_retriever = RecursiveRetriever(
            "vector",  # Root retriever key
            retriever_dict=retriever_dict,
            query_engine_dict={},  # No query engines for this example
            verbose=verbose
        )
        
        logger.info(f"Recursive Retriever created with {reference_strategy} strategy")
        return recursive_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Recursive Retriever: {e}")
        raise


def create_recursive_query_engine(
    base_service: LlamaIndexBaseService,
    reference_strategy: str = "cross_document",
    similarity_top_k: int = 2,
    verbose: bool = True
) -> RetrieverQueryEngine:
    """
    Create a Recursive Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        reference_strategy: Strategy for creating references
        similarity_top_k: Number of top similar documents to retrieve
        verbose: Whether to enable verbose logging
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever
        retriever = create_recursive_retriever(
            base_service, reference_strategy, similarity_top_k, verbose
        )
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info("Recursive Query Engine created")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create Recursive Query Engine: {e}")
        raise


def search_with_recursive_retriever(
    retriever: RecursiveRetriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using a Recursive Retriever.
    
    Args:
        retriever: The Recursive Retriever
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"Recursive retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"Recursive retrieval failed for query '{query}': {e}")
        raise


def get_recursive_retriever_info(retriever: RecursiveRetriever) -> Dict[str, Any]:
    """
    Get information about a Recursive Retriever.
    
    Args:
        retriever: The Recursive Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        return {
            "type": "RecursiveRetriever",
            "root_retriever": retriever.root_retriever,
            "retriever_count": len(retriever.retriever_dict),
            "query_engine_count": len(retriever.query_engine_dict),
            "verbose": retriever.verbose
        }
    except Exception as e:
        logger.error(f"Failed to get recursive retriever info: {e}")
        return {"error": str(e)}


def create_advanced_recursive_retriever(
    base_service: LlamaIndexBaseService,
    reference_depth: int = 2,
    similarity_top_k: int = 3,
    verbose: bool = True
) -> 'AdvancedRecursiveRetriever':
    """
    Create an advanced recursive retriever with configurable depth and logic.
    
    Args:
        base_service: The base LlamaIndex service
        reference_depth: Maximum depth for following references
        similarity_top_k: Number of top similar documents to retrieve
        verbose: Whether to enable verbose logging
    
    Returns:
        AdvancedRecursiveRetriever instance
    """
    try:
        # Create documents with references
        docs_with_refs = create_documents_with_references(
            base_service, "cross_document"
        )
        
        # Create index
        ref_index = VectorStoreIndex.from_documents(
            docs_with_refs,
            storage_context=base_service.get_storage_context()
        )
        
        # Create base retriever
        base_retriever = ref_index.as_retriever(similarity_top_k=similarity_top_k)
        
        # Create advanced recursive retriever
        advanced_retriever = AdvancedRecursiveRetriever(
            base_retriever=base_retriever,
            documents=docs_with_refs,
            reference_depth=reference_depth,
            verbose=verbose
        )
        
        logger.info(f"Advanced Recursive Retriever created with depth={reference_depth}")
        return advanced_retriever
        
    except Exception as e:
        logger.error(f"Failed to create Advanced Recursive Retriever: {e}")
        raise


class AdvancedRecursiveRetriever:
    """
    Advanced Recursive Retriever with configurable depth and custom logic.
    """
    
    def __init__(
        self,
        base_retriever,
        documents: List[Document],
        reference_depth: int = 2,
        verbose: bool = True
    ):
        self.base_retriever = base_retriever
        self.documents = documents
        self.reference_depth = reference_depth
        self.verbose = verbose
        
        # Create document lookup
        self.doc_lookup = {doc.metadata.get("doc_id"): doc for doc in documents}
    
    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Retrieve documents with advanced recursive logic.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            # Get initial results
            initial_results = self.base_retriever.retrieve(query_bundle)
            
            if self.verbose:
                logger.info(f"Initial retrieval found {len(initial_results)} nodes")
            
            # Follow references recursively
            all_results = set()
            visited_docs = set()
            
            # Add initial results
            for result in initial_results:
                all_results.add(result.text.strip())
                doc_id = result.node.metadata.get("doc_id")
                if doc_id:
                    visited_docs.add(doc_id)
            
            # Follow references up to specified depth
            current_depth = 0
            current_docs = [result.node.metadata.get("doc_id") for result in initial_results if result.node.metadata.get("doc_id")]
            
            while current_depth < self.reference_depth and current_docs:
                next_docs = []
                
                for doc_id in current_docs:
                    if doc_id in self.doc_lookup:
                        doc = self.doc_lookup[doc_id]
                        references = doc.metadata.get("references", [])
                        
                        for ref_id in references:
                            if ref_id not in visited_docs and ref_id in self.doc_lookup:
                                # Add referenced document
                                ref_doc = self.doc_lookup[ref_id]
                                ref_result = NodeWithScore(
                                    node=ref_doc,
                                    score=0.8 - (current_depth * 0.1)  # Decreasing score with depth
                                )
                                all_results.add(ref_result.text.strip())
                                visited_docs.add(ref_id)
                                next_docs.append(ref_id)
                                
                                if self.verbose:
                                    logger.info(f"Followed reference from {doc_id} to {ref_id} at depth {current_depth + 1}")
                
                current_docs = next_docs
                current_depth += 1
            
            # Convert back to list of NodeWithScore
            final_results = []
            for result in initial_results:
                if result.text.strip() in all_results:
                    final_results.append(result)
            
            if self.verbose:
                logger.info(f"Advanced recursive retrieval found {len(final_results)} nodes with depth {current_depth}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Advanced recursive retrieval failed: {e}")
            raise


# Convenience function for quick setup
def setup_recursive_retriever(
    documents: List,
    collection_name: str = "recursive_documents",
    reference_strategy: str = "cross_document",
    similarity_top_k: int = 2,
    verbose: bool = True
) -> tuple[RecursiveRetriever, LlamaIndexBaseService]:
    """
    Quick setup function for Recursive Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        reference_strategy: Strategy for creating references
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
        retriever = create_recursive_retriever(
            base_service, reference_strategy, similarity_top_k, verbose
        )
        
        logger.info(f"Recursive retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup recursive retriever: {e}")
        raise
