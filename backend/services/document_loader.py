import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader


class DocumentLoader:
    """Utility class for loading different types of documents."""
    
    @staticmethod
    def load_text_file(file_path: str) -> List[Document]:
        """Load a text file and return as a list of documents."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            loader = TextLoader(file_path)
            documents = loader.load()
            return documents
            
        except Exception as e:
            raise Exception(f"Failed to load text file {file_path}: {str(e)}")
    
    @staticmethod
    def load_pdf_file(file_path: str) -> List[Document]:
        """Load a PDF file and return as a list of documents."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return documents
            
        except Exception as e:
            raise Exception(f"Failed to load PDF file {file_path}: {str(e)}")
    
    @staticmethod
    def load_document(file_path: str) -> List[Document]:
        """Load a document based on its file extension."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.txt':
                return DocumentLoader.load_text_file(file_path)
            elif file_extension == '.pdf':
                return DocumentLoader.load_pdf_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
                
        except Exception as e:
            raise Exception(f"Failed to load document {file_path}: {str(e)}")
    
    @staticmethod
    def create_sample_movies_documents() -> List[Document]:
        """Create sample movie documents with metadata for testing self-querying retriever."""
        movies_data = [
            {
                "page_content": "A bunch of scientists bring back dinosaurs and mayhem breaks loose",
                "metadata": {"year": 1993, "rating": 7.7, "genre": "science fiction", "director": "Steven Spielberg"}
            },
            {
                "page_content": "Leo DiCaprio gets lost in a dream within a dream within a dream within a ...",
                "metadata": {"year": 2010, "director": "Christopher Nolan", "rating": 8.2, "genre": "science fiction"}
            },
            {
                "page_content": "A psychologist / detective gets lost in a series of dreams within dreams within dreams and Inception reused the idea",
                "metadata": {"year": 2006, "director": "Satoshi Kon", "rating": 8.6, "genre": "science fiction"}
            },
            {
                "page_content": "A bunch of normal-sized women are supremely wholesome and some men pine after them",
                "metadata": {"year": 2019, "director": "Greta Gerwig", "rating": 8.3, "genre": "drama"}
            },
            {
                "page_content": "Toys come alive and have a blast doing so",
                "metadata": {"year": 1995, "genre": "animated", "director": "John Lasseter", "rating": 8.3}
            },
            {
                "page_content": "Three men walk into the Zone, three men walk out of the Zone",
                "metadata": {
                    "year": 1979,
                    "director": "Andrei Tarkovsky",
                    "genre": "thriller",
                    "rating": 9.9,
                }
            }
        ]
        
        documents = []
        for movie in movies_data:
            doc = Document(
                page_content=movie["page_content"],
                metadata=movie["metadata"]
            )
            documents.append(doc)
        
        return documents


def get_document_loader() -> DocumentLoader:
    """Get a default document loader instance."""
    return DocumentLoader()
