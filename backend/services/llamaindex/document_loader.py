"""
LlamaIndex Document Loader that integrates with existing document loading functionality.
"""
import os
import logging
from typing import List, Optional, Dict, Any
from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader

from ..document_loader import DocumentLoader as LangChainDocumentLoader

logger = logging.getLogger(__name__)


class LlamaIndexDocumentLoader:
    """
    Document loader for LlamaIndex that integrates with existing LangChain document loading.
    """
    
    def __init__(self):
        self.langchain_loader = LangChainDocumentLoader()
        logger.info("LlamaIndex Document Loader initialized")
    
    def load_text_file(self, file_path: str) -> List[Document]:
        """Load a text file and return as LlamaIndex Documents."""
        try:
            # Use existing LangChain loader
            langchain_docs = self.langchain_loader.load_text_file(file_path)
            
            # Convert to LlamaIndex Documents
            llamaindex_docs = []
            for doc in langchain_docs:
                llamaindex_doc = Document(
                    text=doc.page_content,
                    metadata=doc.metadata
                )
                llamaindex_docs.append(llamaindex_doc)
            
            logger.info(f"Loaded {len(llamaindex_docs)} LlamaIndex documents from text file: {file_path}")
            return llamaindex_docs
            
        except Exception as e:
            logger.error(f"Failed to load text file {file_path}: {e}")
            raise
    
    def load_pdf_file(self, file_path: str) -> List[Document]:
        """Load a PDF file and return as LlamaIndex Documents."""
        try:
            # Use existing LangChain loader
            langchain_docs = self.langchain_loader.load_pdf_file(file_path)
            
            # Convert to LlamaIndex Documents
            llamaindex_docs = []
            for doc in langchain_docs:
                llamaindex_doc = Document(
                    text=doc.page_content,
                    metadata=doc.metadata
                )
                llamaindex_docs.append(llamaindex_doc)
            
            logger.info(f"Loaded {len(llamaindex_docs)} LlamaIndex documents from PDF file: {file_path}")
            return llamaindex_docs
            
        except Exception as e:
            logger.error(f"Failed to load PDF file {file_path}: {e}")
            raise
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a document based on its file extension."""
        try:
            # Use existing LangChain loader
            langchain_docs = self.langchain_loader.load_document(file_path)
            
            # Convert to LlamaIndex Documents
            llamaindex_docs = []
            for doc in langchain_docs:
                llamaindex_doc = Document(
                    text=doc.page_content,
                    metadata=doc.metadata
                )
                llamaindex_docs.append(llamaindex_doc)
            
            logger.info(f"Loaded {len(llamaindex_docs)} LlamaIndex documents from: {file_path}")
            return llamaindex_docs
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            raise
    
    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        """Load all documents from a directory using LlamaIndex SimpleDirectoryReader."""
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Use LlamaIndex SimpleDirectoryReader
            reader = SimpleDirectoryReader(
                input_dir=directory_path,
                recursive=recursive
            )
            
            documents = reader.load_data()
            
            logger.info(f"Loaded {len(documents)} documents from directory: {directory_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load directory {directory_path}: {e}")
            raise
    
    def load_sample_documents(self) -> List[Document]:
        """Load sample documents from the sample_documents directory."""
        try:
            # Get the backend directory path
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            sample_dir = os.path.join(backend_dir, "sample_documents")
            
            if not os.path.exists(sample_dir):
                logger.warning(f"Sample documents directory not found: {sample_dir}")
                return []
            
            documents = self.load_directory(sample_dir)
            
            logger.info(f"Loaded {len(documents)} sample documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load sample documents: {e}")
            return []
    
    def create_sample_movies_documents(self) -> List[Document]:
        """Create sample movie documents with metadata for testing."""
        try:
            # Use existing LangChain loader
            langchain_docs = self.langchain_loader.create_sample_movies_documents()
            
            # Convert to LlamaIndex Documents
            llamaindex_docs = []
            for doc in langchain_docs:
                llamaindex_doc = Document(
                    text=doc.page_content,
                    metadata=doc.metadata
                )
                llamaindex_docs.append(llamaindex_doc)
            
            logger.info(f"Created {len(llamaindex_docs)} sample movie documents")
            return llamaindex_docs
            
        except Exception as e:
            logger.error(f"Failed to create sample movie documents: {e}")
            raise
    
    def create_sample_ai_documents(self) -> List[Document]:
        """Create sample AI/ML documents for testing retrievers."""
        try:
            sample_documents = [
                "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.",
                "Deep learning uses neural networks with multiple layers to model and understand complex patterns in data.",
                "Natural language processing enables computers to understand, interpret, and generate human language.",
                "Computer vision allows machines to interpret and understand visual information from the world.",
                "Reinforcement learning is a type of machine learning where agents learn to make decisions through rewards and penalties.",
                "Supervised learning uses labeled training data to learn a mapping from inputs to outputs.",
                "Unsupervised learning finds hidden patterns in data without labeled examples.",
                "Transfer learning leverages knowledge from pre-trained models to improve performance on new tasks.",
                "Generative AI can create new content including text, images, code, and more.",
                "Large language models are trained on vast amounts of text data to understand and generate human-like text."
            ]
            
            documents = []
            for i, text in enumerate(sample_documents):
                doc = Document(
                    text=text,
                    metadata={
                        "doc_id": f"ai_doc_{i}",
                        "category": "artificial_intelligence",
                        "topic": "machine_learning" if "learning" in text.lower() else "ai_concepts"
                    }
                )
                documents.append(doc)
            
            logger.info(f"Created {len(documents)} sample AI documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to create sample AI documents: {e}")
            raise
    
    def create_sample_finance_documents(self) -> List[Document]:
        """Create sample finance documents for testing."""
        try:
            sample_documents = [
                "Personal finance management involves budgeting, saving, investing, and planning for retirement.",
                "Investment strategies include diversification, asset allocation, and risk management techniques.",
                "Credit scores are calculated based on payment history, credit utilization, and length of credit history.",
                "Tax planning involves understanding deductions, credits, and optimizing your tax situation.",
                "Insurance is a key component of financial planning to protect against unexpected events.",
                "Retirement planning requires understanding 401(k)s, IRAs, and other retirement savings vehicles.",
                "Estate planning involves wills, trusts, and ensuring your assets are distributed according to your wishes.",
                "Financial markets include stocks, bonds, commodities, and other investment instruments.",
                "Economic indicators like GDP, inflation, and unemployment affect financial markets and personal finances.",
                "Banking services include checking accounts, savings accounts, loans, and credit cards."
            ]
            
            documents = []
            for i, text in enumerate(sample_documents):
                doc = Document(
                    text=text,
                    metadata={
                        "doc_id": f"finance_doc_{i}",
                        "category": "personal_finance",
                        "topic": "financial_planning"
                    }
                )
                documents.append(doc)
            
            logger.info(f"Created {len(documents)} sample finance documents")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to create sample finance documents: {e}")
            raise
    
    def load_multiple_files(self, file_paths: List[str]) -> List[Document]:
        """Load multiple files and return as a single list of LlamaIndex Documents."""
        try:
            all_documents = []
            
            for file_path in file_paths:
                try:
                    documents = self.load_document(file_path)
                    all_documents.extend(documents)
                except Exception as e:
                    logger.warning(f"Failed to load file {file_path}: {e}")
                    continue
            
            logger.info(f"Loaded {len(all_documents)} documents from {len(file_paths)} files")
            return all_documents
            
        except Exception as e:
            logger.error(f"Failed to load multiple files: {e}")
            raise
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types."""
        return ['.txt', '.pdf']
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if a file can be loaded."""
        try:
            if not os.path.exists(file_path):
                return False
            
            file_extension = os.path.splitext(file_path)[1].lower()
            return file_extension in self.get_supported_file_types()
            
        except Exception:
            return False


def get_llamaindex_document_loader() -> LlamaIndexDocumentLoader:
    """Get a LlamaIndex document loader instance."""
    return LlamaIndexDocumentLoader()


# Convenience functions for quick document loading
def load_sample_documents() -> List[Document]:
    """Quick function to load sample documents."""
    loader = get_llamaindex_document_loader()
    return loader.load_sample_documents()


def create_sample_documents(doc_type: str = "ai") -> List[Document]:
    """Quick function to create sample documents."""
    loader = get_llamaindex_document_loader()
    
    if doc_type == "ai":
        return loader.create_sample_ai_documents()
    elif doc_type == "finance":
        return loader.create_sample_finance_documents()
    elif doc_type == "movies":
        return loader.create_sample_movies_documents()
    else:
        raise ValueError(f"Unknown document type: {doc_type}")


def load_documents_from_path(file_path: str) -> List[Document]:
    """Quick function to load documents from a file path."""
    loader = get_llamaindex_document_loader()
    return loader.load_document(file_path)
