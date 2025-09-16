"""
Enriched Document Processor for Enhanced Agentic-RAG.

This module handles the offline pipeline for document processing,
including content extraction, LLM enrichment, chunking, and embedding generation.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from services.openai_service import get_openai_service

logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """Metadata for enriched documents."""
    title: str
    summary: str
    keywords: List[str]
    faqs: List[str]
    source_path: str
    chunk_count: int
    processing_timestamp: str


@dataclass
class EnrichedChunk:
    """Enriched document chunk with LLM-generated content."""
    content: str
    summary: str
    keywords: List[str]
    faq: Optional[str]
    metadata: Dict[str, Any]
    chunk_id: str
    document_id: str


class EnrichedDocumentProcessor:
    """
    Processes documents with LLM enrichment for Enhanced Agentic-RAG.
    
    This class handles the offline pipeline:
    1. Load documents from various sources
    2. Extract and structure content
    3. Use LLM to enrich with summaries, keywords, and FAQs
    4. Chunk documents with metadata preservation
    5. Generate embeddings and store in vector store
    6. Save artifacts for online pipeline
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 10000,
        chunk_overlap: int = 200,
        collection_name: str = "agentic_rag_documents"
    ):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = collection_name
        
        # Initialize services
        self.llm_service = get_openai_service()
        self.llm = self.llm_service.get_langchain_llm()
        
        # Initialize embedding model
        self.embedding_model_instance = SentenceTransformer(embedding_model)
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Storage for processed documents
        self.documents_metadata: List[DocumentMetadata] = []
        self.enriched_chunks: List[EnrichedChunk] = []
        self.vector_store: Optional[FAISS] = None
        
        print(f"EnrichedDocumentProcessor initialized with model: {embedding_model}", flush=True)
    
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
        print(f"Processing documents from directory: {directory_path}", flush=True)
        # try:
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Find all documents
        documents = []
        for ext in file_extensions:
            documents.extend(directory.glob(f"*{ext}"))
        
        if not documents:
            print(f"No documents found in {directory_path}", flush=True)
            return {"status": "no_documents", "count": 0}
        
        print(f"Found {len(documents)} documents to process")
        
        # Process each document
        all_enriched_chunks = []
        all_metadata = []
        
        for doc_path in documents:
            try:
                enriched_chunks, metadata = self.process_single_document(str(doc_path))
                all_enriched_chunks.extend(enriched_chunks)
                all_metadata.append(metadata)
                print(f"Processed {doc_path.name}: {len(enriched_chunks)} chunks", flush=True)
            except Exception as e:
                print(f"Failed to process {doc_path}: {e}", flush=True)
                continue
        
        # Store results
        self.enriched_chunks = all_enriched_chunks
        self.documents_metadata = all_metadata
        
        # Create vector store
        self._create_vector_store()
        
        # Save artifacts
        self._save_artifacts(directory_path)
        
        return {
            "status": "success",
            "documents_processed": len(all_metadata),
            "total_chunks": len(all_enriched_chunks),
            "vector_store_created": self.vector_store is not None
        }
            
        # except Exception as e:
        #     logger.error(f"Failed to process documents from directory: {e}")
        #     raise
    
    def process_single_document(self, file_path: str) -> tuple[List[EnrichedChunk], DocumentMetadata]:
        """
        Process a single document with LLM enrichment.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (enriched_chunks, document_metadata)
        """
        # try:
        # Load document based on file type
        print(f"process_single_document: Loading document: {file_path}", flush=True)
        if file_path.endswith('.pdf'):
            from .pdf_reader import PDFReader
            reader = PDFReader()
            content = reader.extract_content(file_path)
            print(f"process_single_document: Extracted content from PDF: {len(content)} characters", flush=True)
        elif file_path.endswith('.txt'):
            from .text_reader import TextReader
            reader = TextReader()
            content = reader.extract_content(file_path)
            print(f"process_single_document: Extracted content from text file: {len(content)} characters", flush=True)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Extract title from filename
        title = Path(file_path).stem
        
        # Generate document-level enrichment
        doc_enrichment = self._enrich_document(content, title)
        
        # Create document for chunking
        doc = Document(
            page_content=content,
            metadata={
                "source": file_path,
                "title": title,
                "summary": doc_enrichment["summary"],
                "keywords": doc_enrichment["keywords"],
                "faqs": doc_enrichment["faqs"]
            }
        )
        
        # Chunk the document
        chunks = self.text_splitter.split_documents([doc])
        
        # Enrich each chunk
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_enrichment = self._enrich_chunk(chunk.page_content, title, i)
            
            enriched_chunk = EnrichedChunk(
                content=chunk.page_content,
                summary=chunk_enrichment["summary"],
                keywords=chunk_enrichment["keywords"],
                faq=chunk_enrichment.get("faq"),
                metadata=chunk.metadata,
                chunk_id=f"{title}_chunk_{i}",
                document_id=title
            )
            enriched_chunks.append(enriched_chunk)
        
        # Create document metadata
        metadata = DocumentMetadata(
            title=title,
            summary=doc_enrichment["summary"],
            keywords=doc_enrichment["keywords"],
            faqs=doc_enrichment["faqs"],
            source_path=file_path,
            chunk_count=len(enriched_chunks),
            processing_timestamp=str(pd.Timestamp.now())
        )
        
        return enriched_chunks, metadata
            
        # except Exception as e:
        #     logger.error(f"Failed to process document {file_path}: {e}")
        #     raise
    
    def _enrich_document(self, content: str, title: str) -> Dict[str, Any]:
        """Enrich document with LLM-generated summary, keywords, and FAQs."""
        try:
            # Truncate content if too long for LLM
            max_content_length = 8000  # Leave room for prompt and response
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            prompt = f"""
            Analyze the following document and provide enrichment information:
            
            Document Title: {title}
            Document Content: {content}
            
            Please provide:
            1. A 2-line summary of the document
            2. 5-10 relevant keywords
            3. 3-5 frequently asked questions that this document could answer
            
            Format your response as JSON:
            {{
                "summary": "2-line summary here",
                "keywords": ["keyword1", "keyword2", ...],
                "faqs": ["FAQ1?", "FAQ2?", ...]
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            # Parse JSON response
            try:
                import json
                enrichment = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                enrichment = {
                    "summary": "Document summary not available",
                    "keywords": ["document", "content"],
                    "faqs": ["What is this document about?"]
                }
            
            return enrichment
            
        except Exception as e:
            logger.error(f"Failed to enrich document {title}: {e}")
            return {
                "summary": "Document summary not available",
                "keywords": ["document", "content"],
                "faqs": ["What is this document about?"]
            }
    
    def _enrich_chunk(self, content: str, document_title: str, chunk_index: int) -> Dict[str, Any]:
        """Enrich individual chunk with summary, keywords, and optional FAQ."""
        # try:
            # Truncate content if too long
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        prompt = f"""
        Analyze this document chunk and provide enrichment:
        
        Document: {document_title}
        Chunk {chunk_index + 1}
        Content: {content}
        
        Provide:
        1. A 1-line summary of this chunk
        2. 3-5 relevant keywords
        3. One FAQ this chunk could answer (if applicable)
        
        Format as JSON:
        {{
            "summary": "1-line summary",
            "keywords": ["keyword1", "keyword2", ...],
            "faq": "FAQ question?" or null
        }}
        """
        
        response = self.llm.invoke(prompt)

        print(f"_enrich_chunk: Enrichment response: {response.content}", flush=True)
        
        try:
            import json
            enrichment = json.loads(response.content)
        except json.JSONDecodeError:
            enrichment = {
                "summary": "Chunk summary not available",
                "keywords": ["chunk", "content"],
                "faq": None
            }
        
        return enrichment
            
        # except Exception as e:
        #     logger.error(f"Failed to enrich chunk {chunk_index} of {document_title}: {e}")
        #     return {
        #         "summary": "Chunk summary not available",
        #         "keywords": ["chunk", "content"],
        #         "faq": None
        #     }
    
    def _create_vector_store(self):
        """Create FAISS vector store from enriched chunks."""
        try:
            if not self.enriched_chunks:
                raise ValueError("No enriched chunks available for vector store creation")
            
            # Prepare documents for FAISS
            documents = []
            metadatas = []
            
            for chunk in self.enriched_chunks:
                # Combine content with enrichment for better retrieval
                enriched_content = f"{chunk.content}\n\nSummary: {chunk.summary}\nKeywords: {', '.join(chunk.keywords)}"
                if chunk.faq:
                    enriched_content += f"\nFAQ: {chunk.faq}"
                
                doc = Document(
                    page_content=enriched_content,
                    metadata={
                        **chunk.metadata,
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "summary": chunk.summary,
                        "keywords": chunk.keywords,
                        "faq": chunk.faq
                    }
                )
                documents.append(doc)
                metadatas.append(doc.metadata)
            
            # Generate embeddings
            texts = [doc.page_content for doc in documents]
            embeddings = self.embedding_model_instance.encode(texts)
            
            # Create FAISS vector store
            self.vector_store = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, embeddings)),
                embedding=self.embedding_model_instance,
                metadatas=metadatas
            )
            
            logger.info(f"Created FAISS vector store with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            raise
    
    def _save_artifacts(self, output_directory: str):
        """Save processing artifacts for online pipeline."""
        try:
            output_path = Path(output_directory)
            artifacts_path = output_path / "agentic_rag_artifacts"
            artifacts_path.mkdir(exist_ok=True)
            
            # Save document metadata
            metadata_file = artifacts_path / "documents_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(meta) for meta in self.documents_metadata], f, indent=2)
            
            # Save enriched chunks
            chunks_file = artifacts_path / "enriched_chunks.json"
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(chunk) for chunk in self.enriched_chunks], f, indent=2)
            
            # Save vector store
            if self.vector_store:
                vector_store_path = artifacts_path / "vector_store"
                self.vector_store.save_local(str(vector_store_path))
            
            logger.info(f"Saved artifacts to {artifacts_path}")
            
        except Exception as e:
            logger.error(f"Failed to save artifacts: {e}")
            raise
    
    def load_artifacts(self, artifacts_directory: str):
        """Load previously saved artifacts."""
        try:
            artifacts_path = Path(artifacts_directory)
            
            # Load document metadata
            metadata_file = artifacts_path / "documents_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_data = json.load(f)
                    self.documents_metadata = [DocumentMetadata(**meta) for meta in metadata_data]
            
            # Load enriched chunks
            chunks_file = artifacts_path / "enriched_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks_data = json.load(f)
                    self.enriched_chunks = [EnrichedChunk(**chunk) for chunk in chunks_data]
            
            # Load vector store
            vector_store_path = artifacts_path / "vector_store"
            if vector_store_path.exists():
                self.vector_store = FAISS.load_local(
                    str(vector_store_path),
                    self.embedding_model_instance,
                    allow_dangerous_deserialization=True
                )
            
            logger.info(f"Loaded artifacts from {artifacts_path}")
            
        except Exception as e:
            logger.error(f"Failed to load artifacts: {e}")
            raise
    
    def get_document_list(self) -> List[Dict[str, Any]]:
        """Get list of processed documents for source identification."""
        return [
            {
                "title": meta.title,
                "summary": meta.summary,
                "keywords": meta.keywords,
                "faqs": meta.faqs,
                "chunk_count": meta.chunk_count
            }
            for meta in self.documents_metadata
        ]
    
    def search_vector_store(self, query: str, k: int = 5) -> List[Document]:
        """Search the vector store for relevant documents."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about the processing pipeline."""
        return {
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "documents_processed": len(self.documents_metadata),
            "total_chunks": len(self.enriched_chunks),
            "vector_store_available": self.vector_store is not None,
            "collection_name": self.collection_name
        }
