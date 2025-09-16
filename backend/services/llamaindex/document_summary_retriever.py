"""
Document Summary Index Retriever implementation using LlamaIndex.
"""
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import DocumentSummaryIndex
from llama_index.core.indices.document_summary import (
    DocumentSummaryIndexLLMRetriever,
    DocumentSummaryIndexEmbeddingRetriever,
)
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.query_engine import RetrieverQueryEngine

from .base_service import LlamaIndexBaseService

logger = logging.getLogger(__name__)


def create_document_summary_index(
    base_service: LlamaIndexBaseService,
    summary_template: Optional[str] = None
) -> DocumentSummaryIndex:
    """
    Create a Document Summary Index from documents.
    
    Args:
        base_service: The base LlamaIndex service
        summary_template: Custom template for document summaries
    
    Returns:
        DocumentSummaryIndex instance
    """
    try:
        if not base_service.documents:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        # Default summary template
        if summary_template is None:
            summary_template = (
                "Please provide a summary of the following document. "
                "Focus on the main topics, key concepts, and important information. "
                "Keep the summary concise but comprehensive.\n\n"
                "Document: {context_str}\n\n"
                "Summary:"
            )
        
        # Create document summary index
        doc_summary_index = DocumentSummaryIndex.from_documents(
            base_service.documents,
            llm=base_service.get_llm(),
            summary_template=summary_template
        )
        
        logger.info(f"Document Summary Index created for {len(base_service.documents)} documents")
        return doc_summary_index
        
    except Exception as e:
        logger.error(f"Failed to create Document Summary Index: {e}")
        raise


def create_llm_document_summary_retriever(
    base_service: LlamaIndexBaseService,
    choice_top_k: int = 3,
    summary_template: Optional[str] = None
) -> DocumentSummaryIndexLLMRetriever:
    """
    Create a Document Summary Index LLM Retriever.
    
    This retriever uses an LLM to analyze the query against document summaries
    and select the most relevant documents.
    
    Args:
        base_service: The base LlamaIndex service
        choice_top_k: Number of documents to select
        summary_template: Custom template for document summaries
    
    Returns:
        DocumentSummaryIndexLLMRetriever instance
    """
    try:
        # Create document summary index
        doc_summary_index = create_document_summary_index(
            base_service, summary_template
        )
        
        # Create LLM-based retriever
        retriever = DocumentSummaryIndexLLMRetriever(
            doc_summary_index,
            choice_top_k=choice_top_k
        )
        
        logger.info(f"Document Summary LLM Retriever created with choice_top_k={choice_top_k}")
        return retriever
        
    except Exception as e:
        logger.error(f"Failed to create Document Summary LLM Retriever: {e}")
        raise


def create_embedding_document_summary_retriever(
    base_service: LlamaIndexBaseService,
    similarity_top_k: int = 3,
    summary_template: Optional[str] = None
) -> DocumentSummaryIndexEmbeddingRetriever:
    """
    Create a Document Summary Index Embedding Retriever.
    
    This retriever uses semantic similarity between the query and summary embeddings
    to select the most relevant documents.
    
    Args:
        base_service: The base LlamaIndex service
        similarity_top_k: Number of documents to select
        summary_template: Custom template for document summaries
    
    Returns:
        DocumentSummaryIndexEmbeddingRetriever instance
    """
    try:
        # Create document summary index
        doc_summary_index = create_document_summary_index(
            base_service, summary_template
        )
        
        # Create embedding-based retriever
        retriever = DocumentSummaryIndexEmbeddingRetriever(
            doc_summary_index,
            similarity_top_k=similarity_top_k
        )
        
        logger.info(f"Document Summary Embedding Retriever created with similarity_top_k={similarity_top_k}")
        return retriever
        
    except Exception as e:
        logger.error(f"Failed to create Document Summary Embedding Retriever: {e}")
        raise


def create_document_summary_query_engine(
    base_service: LlamaIndexBaseService,
    retriever_type: str = "llm",
    top_k: int = 3,
    summary_template: Optional[str] = None
) -> RetrieverQueryEngine:
    """
    Create a Document Summary Query Engine for end-to-end RAG.
    
    Args:
        base_service: The base LlamaIndex service
        retriever_type: Type of retriever ("llm" or "embedding")
        top_k: Number of documents to select
        summary_template: Custom template for document summaries
    
    Returns:
        RetrieverQueryEngine instance
    """
    try:
        # Create retriever based on type
        if retriever_type.lower() == "llm":
            retriever = create_llm_document_summary_retriever(
                base_service, top_k, summary_template
            )
        elif retriever_type.lower() == "embedding":
            retriever = create_embedding_document_summary_retriever(
                base_service, top_k, summary_template
            )
        else:
            raise ValueError(f"Invalid retriever_type: {retriever_type}. Must be 'llm' or 'embedding'")
        
        # Create query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=base_service.get_llm()
        )
        
        logger.info(f"Document Summary Query Engine created with {retriever_type} retriever")
        return query_engine
        
    except Exception as e:
        logger.error(f"Failed to create Document Summary Query Engine: {e}")
        raise


def search_with_document_summary_retriever(
    retriever,
    query: str,
    **kwargs
) -> List[NodeWithScore]:
    """
    Search using a Document Summary Retriever.
    
    Args:
        retriever: The Document Summary Retriever (LLM or Embedding)
        query: Search query
        **kwargs: Additional arguments for retrieval
    
    Returns:
        List of NodeWithScore objects
    """
    try:
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        logger.info(f"Document summary retriever found {len(nodes)} nodes for query: {query}")
        return nodes
        
    except Exception as e:
        logger.error(f"Document summary retrieval failed for query '{query}': {e}")
        raise


def get_document_summary_retriever_info(retriever) -> Dict[str, Any]:
    """
    Get information about a Document Summary Retriever.
    
    Args:
        retriever: The Document Summary Retriever
    
    Returns:
        Dictionary with retriever information
    """
    try:
        info = {
            "type": type(retriever).__name__,
            "index_type": "DocumentSummaryIndex"
        }
        
        if hasattr(retriever, 'choice_top_k'):
            info["choice_top_k"] = retriever.choice_top_k
        if hasattr(retriever, 'similarity_top_k'):
            info["similarity_top_k"] = retriever.similarity_top_k
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get document summary retriever info: {e}")
        return {"error": str(e)}


def create_dual_document_summary_retriever(
    base_service: LlamaIndexBaseService,
    llm_top_k: int = 2,
    embedding_top_k: int = 2,
    final_top_k: int = 3,
    summary_template: Optional[str] = None
) -> 'DualDocumentSummaryRetriever':
    """
    Create a dual retriever combining both LLM and Embedding document summary retrievers.
    
    Args:
        base_service: The base LlamaIndex service
        llm_top_k: Number of documents from LLM retriever
        embedding_top_k: Number of documents from embedding retriever
        final_top_k: Final number of documents to return
        summary_template: Custom template for document summaries
    
    Returns:
        DualDocumentSummaryRetriever instance
    """
    try:
        # Create both retrievers
        llm_retriever = create_llm_document_summary_retriever(
            base_service, llm_top_k, summary_template
        )
        
        embedding_retriever = create_embedding_document_summary_retriever(
            base_service, embedding_top_k, summary_template
        )
        
        # Create dual retriever
        dual_retriever = DualDocumentSummaryRetriever(
            llm_retriever=llm_retriever,
            embedding_retriever=embedding_retriever,
            final_top_k=final_top_k
        )
        
        logger.info(f"Dual document summary retriever created")
        return dual_retriever
        
    except Exception as e:
        logger.error(f"Failed to create dual document summary retriever: {e}")
        raise


class DualDocumentSummaryRetriever:
    """
    Custom dual retriever combining LLM and Embedding document summary retrievers.
    """
    
    def __init__(
        self,
        llm_retriever: DocumentSummaryIndexLLMRetriever,
        embedding_retriever: DocumentSummaryIndexEmbeddingRetriever,
        final_top_k: int = 3
    ):
        self.llm_retriever = llm_retriever
        self.embedding_retriever = embedding_retriever
        self.final_top_k = final_top_k
    
    def retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        Retrieve documents using both LLM and embedding approaches.
        
        Args:
            query_bundle: Query to search for
        
        Returns:
            List of NodeWithScore objects
        """
        try:
            # Get results from both retrievers
            llm_results = self.llm_retriever.retrieve(query_bundle)
            embedding_results = self.embedding_retriever.retrieve(query_bundle)
            
            # Combine results, removing duplicates
            seen_texts = set()
            combined_results = []
            
            # Add LLM results first (they're typically more accurate)
            for result in llm_results:
                text_key = result.text.strip()
                if text_key not in seen_texts:
                    combined_results.append(result)
                    seen_texts.add(text_key)
            
            # Add embedding results that aren't already included
            for result in embedding_results:
                text_key = result.text.strip()
                if text_key not in seen_texts:
                    combined_results.append(result)
                    seen_texts.add(text_key)
            
            # Return top k results
            final_results = combined_results[:self.final_top_k]
            
            logger.info(f"Dual document summary retriever found {len(final_results)} nodes")
            return final_results
            
        except Exception as e:
            logger.error(f"Dual document summary retrieval failed: {e}")
            raise


# Convenience function for quick setup
def setup_document_summary_retriever(
    documents: List,
    collection_name: str = "doc_summary_documents",
    retriever_type: str = "llm",
    top_k: int = 3,
    summary_template: Optional[str] = None
) -> tuple:
    """
    Quick setup function for Document Summary Retriever.
    
    Args:
        documents: List of documents to index
        collection_name: Name for the collection
        retriever_type: Type of retriever ("llm" or "embedding")
        top_k: Number of documents to select
        summary_template: Custom template for document summaries
    
    Returns:
        Tuple of (retriever, base_service)
    """
    try:
        # Create base service
        base_service = LlamaIndexBaseService(collection_name=collection_name)
        
        # Load documents
        base_service.load_documents(documents)
        
        # Create retriever based on type
        if retriever_type.lower() == "llm":
            retriever = create_llm_document_summary_retriever(
                base_service, top_k, summary_template
            )
        elif retriever_type.lower() == "embedding":
            retriever = create_embedding_document_summary_retriever(
                base_service, top_k, summary_template
            )
        else:
            raise ValueError(f"Invalid retriever_type: {retriever_type}. Must be 'llm' or 'embedding'")
        
        logger.info(f"Document summary retriever setup complete for {len(documents)} documents")
        return retriever, base_service
        
    except Exception as e:
        logger.error(f"Failed to setup document summary retriever: {e}")
        raise
