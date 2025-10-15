import os
import logging
from typing import List, Dict, Any, Optional, Union
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.retrievers import MultiQueryRetriever
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import CharacterTextSplitter
from langchain.storage import InMemoryStore
from langchain_core.documents import Document
from django.conf import settings
# Watson services removed - using OpenAI only
from .openai_service import get_openai_service


class RetrieverService:
    """Comprehensive service for different types of retrievers using LangChain."""
    
    def __init__(self, collection_name: str = "documents", service_provider: Optional[str] = None):
        self.collection_name = collection_name
        
        # Using OpenAI as the only service provider
        self.service_provider = 'openai'
        
        # Initialize OpenAI services
        self.embedding_service = None
        self.llm_service = None
        
        try:
            self.embedding_service = get_openai_service()
            self.llm_service = get_openai_service()
            print(f"Initialized OpenAI services successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize OpenAI services: {e}")
            print("Please check your OpenAI API configuration")
        
        # Initialize vector store
        self.vectorstore = None
        self.parent_store = None
        
        # Set up logging
        logging.basicConfig()
        logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
    
    def text_splitter(self, data: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        """Split documents into chunks using RecursiveCharacterTextSplitter."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_documents(data)
        return chunks
    
    def create_vector_store(self, documents: List[Document], collection_name: Optional[str] = None) -> Chroma:
        """Create a vector store from documents."""
        if not self.embedding_service:
            raise Exception(f"Embedding service not available. Check {self.service_provider} configuration.")
        
        if collection_name:
            self.collection_name = collection_name
        
        # Get embeddings
        embeddings = self.embedding_service.get_langchain_embeddings()
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=self.collection_name
        )
        
        return self.vectorstore
    
    def vector_store_retriever(self, 
                              search_type: str = "similarity", 
                              search_kwargs: Optional[Dict[str, Any]] = None) -> Any:
        """Create a Vector Store-Backed Retriever."""
        if not self.vectorstore:
            raise Exception("Vector store not initialized. Call create_vector_store first.")
        
        if search_kwargs is None:
            search_kwargs = {}
        
        retriever = self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
        
        return retriever
    
    def multi_query_retriever(self, base_retriever: Optional[Any] = None) -> MultiQueryRetriever:
        """Create a Multi-Query Retriever."""
        if not self.llm_service:
            raise Exception(f"LLM service not available. Check {self.service_provider} configuration.")
        
        if not base_retriever:
            if not self.vectorstore:
                raise Exception("Vector store not initialized. Call create_vector_store first.")
            base_retriever = self.vectorstore.as_retriever()
        
        llm = self.llm_service.get_langchain_llm()
        
        retriever = MultiQueryRetriever.from_llm(
            retriever=base_retriever,
            llm=llm
        )
        
        return retriever
    
    def self_query_retriever(self, 
                            metadata_field_info: List[AttributeInfo],
                            document_content_description: str) -> SelfQueryRetriever:
        """Create a Self-Querying Retriever."""
        if not self.llm_service:
            raise Exception(f"LLM service not available. Check {self.service_provider} configuration.")
        
        if not self.vectorstore:
            raise Exception("Vector store not initialized. Call create_vector_store first.")
        
        llm = self.llm_service.get_langchain_llm()
        
        # Get document contents from the vector store for the document_contents parameter
        # This is required for newer versions of LangChain
        try:
            # For Chroma, we need to get documents differently
            if hasattr(self.vectorstore, '_collection'):
                # Get all documents from the collection
                all_docs = self.vectorstore._collection.get()
                if all_docs and 'documents' in all_docs:
                    # Limit to first 10 documents to avoid token limit issues
                    limited_docs = all_docs['documents'][:10]
                    document_contents = "\n\n".join(limited_docs)
                    print(f"Using {len(limited_docs)} documents for SelfQueryRetriever", flush=True)
                else:
                    document_contents = ""
            else:
                # Fallback: try to get documents using similarity search with a broad query
                sample_docs = self.vectorstore.similarity_search("", k=10)  # Reduced from 100 to 10
                document_contents = "\n\n".join([doc.page_content for doc in sample_docs]) if sample_docs else ""
                print(f"Using {len(sample_docs)} sample docs for SelfQueryRetriever", flush=True)
        except Exception as e:
            print(f"Warning: Could not retrieve document contents for SelfQueryRetriever: {e}")
            document_contents = ""
        
        retriever = SelfQueryRetriever.from_llm(
            llm=llm,
            vectorstore=self.vectorstore,
            document_contents=document_contents,
            document_content_description=document_content_description,
            metadata_field_info=metadata_field_info,
            search_kwargs={"k": 5},  # Limit results to avoid token issues
            verbose=True,  # Enable verbose mode for debugging
        )
        
        return retriever
    
    def parent_document_retriever(self,
                                 parent_chunk_size: int = 1000,
                                 child_chunk_size: int = 200,
                                 chunk_overlap: int = 20) -> ParentDocumentRetriever:
        """Create a Parent Document Retriever."""
        if not self.vectorstore:
            raise Exception("Vector store not initialized. Call create_vector_store first.")
        
        # Set up splitters
        parent_splitter = CharacterTextSplitter(
            chunk_size=parent_chunk_size, 
            chunk_overlap=chunk_overlap, 
            separator='\n'
        )
        child_splitter = CharacterTextSplitter(
            chunk_size=child_chunk_size, 
            chunk_overlap=chunk_overlap, 
            separator='\n'
        )
        
        # Set up storage for parent documents
        self.parent_store = InMemoryStore()
        
        # Create parent document retriever
        retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.parent_store,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
        )
        
        return retriever
    
    def add_documents_to_parent_retriever(self, documents: List[Document], retriever: ParentDocumentRetriever):
        """Add documents to the parent document retriever."""
        retriever.add_documents(documents)
    
    def search_with_retriever(self, 
                             retriever: Any, 
                             query: str, 
                             **kwargs) -> List[Document]:
        """Search using any retriever."""
        try:
            docs = retriever.invoke(query, **kwargs)
            # print(f"Docs: {docs}", flush=True)
            return docs
        except Exception as e:
            raise Exception(f"Retrieval failed: {str(e)}")
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 8, 
                         search_type: str = "similarity") -> List[Document]:
        """Perform similarity search using the vector store."""
        if not self.vectorstore:
            raise Exception("Vector store not initialized. Call create_vector_store first.")
        
        if search_type == "mmr":
            return self.vectorstore.max_marginal_relevance_search(query, k=k)
        elif search_type == "similarity_score_threshold":
            # This would need to be implemented with a custom retriever
            # For now, use regular similarity search
            return self.vectorstore.similarity_search(query, k=k)
        else:
            return self.vectorstore.similarity_search(query, k=k)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        if not self.vectorstore:
            return {"error": "Vector store not initialized"}
        
        try:
            count = self.vectorstore._collection.count()
            return {
                'name': self.collection_name,
                'document_count': count,
                'collection_id': str(self.vectorstore._collection.id)
            }
        except Exception as e:
            return {"error": f"Failed to get collection info: {str(e)}"}
    
    def clear_vector_store(self):
        """Clear the current vector store."""
        if self.vectorstore:
            try:
                ids = self.vectorstore.get()["ids"]
                if ids:
                    self.vectorstore.delete(ids)
            except Exception as e:
                print(f"Warning: Could not clear vector store: {e}")
    
    def delete_collection(self):
        """Delete the current collection."""
        if self.vectorstore:
            try:
                self.vectorstore._client.delete_collection(self.collection_name)
                self.vectorstore = None
            except Exception as e:
                print(f"Warning: Could not delete collection: {e}")
    
    def get_service_provider(self) -> str:
        """Get the current service provider."""
        return self.service_provider


def get_retriever_service(service_provider: Optional[str] = None) -> RetrieverService:
    """Get a retriever service instance (OpenAI only)."""
    return RetrieverService(service_provider=service_provider)


def get_openai_retriever_service() -> RetrieverService:
    """Get a retriever service instance configured for OpenAI."""
    return RetrieverService(service_provider='openai')

