"""
Document Agent for Deep Agents System.

This agent handles document processing, indexing, and metadata management.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.openai_service import get_openai_service
from services.deep_agents.chroma_service import get_chroma_service
from chat.models import DocumentMetadata, EnrichedChunk

logger = logging.getLogger(__name__)


class DocumentAgent:
    """
    Agent responsible for document processing and indexing.
    
    This agent:
    1. Processes documents from various sources
    2. Enriches content with LLM-generated metadata
    3. Chunks documents with semantic awareness
    4. Stores in ChromaDB with persistent metadata
    5. Manages document lifecycle
    """
    
    def __init__(self):
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        self.chroma_service = get_chroma_service()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        logger.info("DocumentAgent initialized")
    
    def process_documents_from_directory(
        self, 
        directory_path: str, 
        file_extensions: List[str] = ['.pdf', '.txt']
    ) -> Dict[str, Any]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to process
            
        Returns:
            Dictionary with processing results
        """
        try:
            docs_path = Path(directory_path)
            if not docs_path.exists():
                return {
                    "status": "error",
                    "error": f"Directory not found: {directory_path}",
                    "documents_processed": 0
                }
            
            processed_docs = []
            total_chunks = 0
            
            # Find all files with specified extensions
            for ext in file_extensions:
                for file_path in docs_path.glob(f"**/*{ext}"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        result = self.process_single_document(str(file_path))
                        if result["status"] == "success":
                            processed_docs.append(result)
                            total_chunks += result.get("chunk_count", 0)
            
            return {
                "status": "success",
                "documents_processed": len(processed_docs),
                "total_chunks": total_chunks,
                "timestamp": datetime.now().isoformat(),
                "processed_documents": processed_docs
            }
            
        except Exception as e:
            logger.error(f"Failed to process documents from directory: {e}")
            return {
                "status": "error",
                "error": str(e),
                "documents_processed": 0
            }
    
    def process_single_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Load document content
            content = self._load_document_content(file_path)
            if not content:
                return {
                    "status": "error",
                    "error": f"Could not load content from {file_path}",
                    "chunk_count": 0
                }
            
            # Generate document metadata
            doc_metadata = self._generate_document_metadata(content, file_path)
            
            # Chunk the document
            chunks = self._chunk_document(content, file_path)
            
            # Enrich chunks with LLM
            enriched_chunks = self._enrich_chunks(chunks, doc_metadata)
            
            # Store in ChromaDB
            self._store_documents_in_chroma(enriched_chunks)
            
            # Store metadata in MySQL
            db_metadata = self._store_metadata_in_db(doc_metadata, enriched_chunks)
            
            return {
                "status": "success",
                "file_path": file_path,
                "title": doc_metadata["title"],
                "chunk_count": len(enriched_chunks),
                "document_id": db_metadata.id if db_metadata else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path,
                "chunk_count": 0
            }
    
    def _load_document_content(self, file_path: str) -> Optional[str]:
        """Load content from a document file."""
        try:
            file_path_obj = Path(file_path)
            
            if file_path_obj.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path_obj.suffix.lower() == '.pdf':
                # Use existing PDF reader from the project
                from services.agentic_rag.document_readers.pdf_reader import PDFReader
                pdf_reader = PDFReader()
                documents = pdf_reader.load_pdf_file(file_path)
                if documents:
                    return "\n\n".join([doc.page_content for doc in documents])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load document content from {file_path}: {e}")
            return None
    
    def _generate_document_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Generate metadata for a document using LLM."""
        try:
            # Create a prompt for metadata generation
            prompt = f"""
            Analyze the following document and generate metadata:
            
            Document Content:
            {content[:2000]}...
            
            Please provide:
            1. A concise title (max 100 characters)
            2. A summary (max 300 characters)
            3. 5-10 relevant keywords
            4. 3-5 potential FAQ questions and answers
            
            Format your response as JSON:
            {{
                "title": "Document Title",
                "summary": "Brief summary of the document",
                "keywords": ["keyword1", "keyword2", ...],
                "faqs": [
                    {{"question": "Q1", "answer": "A1"}},
                    {{"question": "Q2", "answer": "A2"}}
                ]
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            # Parse JSON response
            import json
            try:
                metadata = json.loads(response.content)
            except:
                # Fallback if JSON parsing fails
                metadata = {
                    "title": Path(file_path).stem,
                    "summary": content[:200] + "..." if len(content) > 200 else content,
                    "keywords": ["document", "content"],
                    "faqs": []
                }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate document metadata: {e}")
            return {
                "title": Path(file_path).stem,
                "summary": content[:200] + "..." if len(content) > 200 else content,
                "keywords": ["document", "content"],
                "faqs": []
            }
    
    def _chunk_document(self, content: str, file_path: str) -> List[Document]:
        """Chunk a document into smaller pieces."""
        try:
            # Create initial document
            doc = Document(
                page_content=content,
                metadata={
                    "source": file_path,
                    "title": Path(file_path).stem
                }
            )
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_id": f"{Path(file_path).stem}_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document: {e}")
            return []
    
    def _enrich_chunks(self, chunks: List[Document], doc_metadata: Dict[str, Any]) -> List[Document]:
        """Enrich document chunks with LLM-generated content."""
        try:
            enriched_chunks = []
            
            for chunk in chunks:
                # Generate chunk-specific metadata
                chunk_metadata = self._generate_chunk_metadata(chunk.page_content, doc_metadata)
                
                # Create enriched chunk
                enriched_chunk = Document(
                    page_content=chunk.page_content,
                    metadata={
                        **chunk.metadata,
                        **chunk_metadata,
                        "document_title": doc_metadata["title"],
                        "document_summary": doc_metadata["summary"],
                        "document_keywords": doc_metadata["keywords"]
                    }
                )
                
                enriched_chunks.append(enriched_chunk)
            
            return enriched_chunks
            
        except Exception as e:
            logger.error(f"Failed to enrich chunks: {e}")
            return chunks  # Return original chunks if enrichment fails
    
    def _generate_chunk_metadata(self, content: str, doc_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for a specific chunk."""
        try:
            prompt = f"""
            Analyze this document chunk and generate metadata:
            
            Document Context:
            Title: {doc_metadata.get('title', 'Unknown')}
            Summary: {doc_metadata.get('summary', 'No summary available')}
            
            Chunk Content:
            {content[:1000]}
            
            Generate:
            1. A brief summary of this chunk (max 150 characters)
            2. 3-5 keywords specific to this chunk
            3. One potential FAQ question and answer based on this chunk
            
            Format as JSON:
            {{
                "chunk_summary": "Brief summary",
                "chunk_keywords": ["keyword1", "keyword2"],
                "chunk_faq": {{"question": "Q", "answer": "A"}}
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            import json
            try:
                chunk_metadata = json.loads(response.content)
            except:
                chunk_metadata = {
                    "chunk_summary": content[:100] + "..." if len(content) > 100 else content,
                    "chunk_keywords": ["content"],
                    "chunk_faq": None
                }
            
            return chunk_metadata
            
        except Exception as e:
            logger.error(f"Failed to generate chunk metadata: {e}")
            return {
                "chunk_summary": content[:100] + "..." if len(content) > 100 else content,
                "chunk_keywords": ["content"],
                "chunk_faq": None
            }
    
    def _store_documents_in_chroma(self, enriched_chunks: List[Document]) -> bool:
        """Store enriched chunks in ChromaDB."""
        try:
            return self.chroma_service.add_documents(enriched_chunks)
            
        except Exception as e:
            logger.error(f"Failed to store documents in ChromaDB: {e}")
            return False
    
    def _store_metadata_in_db(self, doc_metadata: Dict[str, Any], enriched_chunks: List[Document]) -> Optional[DocumentMetadata]:
        """Store document metadata in MySQL database."""
        try:
            # Create DocumentMetadata record
            db_metadata = DocumentMetadata.objects.create(
                title=doc_metadata["title"],
                summary=doc_metadata["summary"],
                keywords=doc_metadata["keywords"],
                faqs=[faq["question"] + ": " + faq["answer"] for faq in doc_metadata.get("faqs", [])],
                source_path=enriched_chunks[0].metadata.get("source", "") if enriched_chunks else "",
                chunk_count=len(enriched_chunks),
                processing_timestamp=datetime.now().isoformat()
            )
            
            # Create EnrichedChunk records
            for chunk in enriched_chunks:
                EnrichedChunk.objects.create(
                    document_metadata=db_metadata,
                    content=chunk.page_content,
                    summary=chunk.metadata.get("chunk_summary", ""),
                    keywords=chunk.metadata.get("chunk_keywords", []),
                    faq=chunk.metadata.get("chunk_faq", {}).get("question", "") + ": " + 
                        chunk.metadata.get("chunk_faq", {}).get("answer", "") if chunk.metadata.get("chunk_faq") else None,
                    chunk_id=chunk.metadata.get("chunk_id", ""),
                    document_id=str(db_metadata.id),
                    metadata=chunk.metadata
                )
            
            logger.info(f"Stored metadata for document: {doc_metadata['title']}")
            return db_metadata
            
        except Exception as e:
            logger.error(f"Failed to store metadata in database: {e}")
            return None
    
    def get_document_info(self) -> Dict[str, Any]:
        """Get information about processed documents."""
        try:
            # Get ChromaDB info
            chroma_info = self.chroma_service.get_collection_info()
            
            # Get database info
            db_docs = DocumentMetadata.objects.count()
            db_chunks = EnrichedChunk.objects.count()
            
            return {
                "chroma_info": chroma_info,
                "database_documents": db_docs,
                "database_chunks": db_chunks,
                "status": "active"
            }
            
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
