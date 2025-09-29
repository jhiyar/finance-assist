import time
import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from .base_chunker import BaseChunker, Chunk, ChunkingResult
from ..parsers.base_parser import ParsedDocument, ParsedElement

logger = logging.getLogger(__name__)


class SemanticChunker(BaseChunker):
    """Chunker that uses semantic similarity to determine chunk boundaries."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = kwargs.get('chunk_size', 15000)  # ~3000 words - increased for better context
        self.semantic_threshold = kwargs.get('semantic_threshold', 0.7)
        self.min_chunk_size = kwargs.get('min_chunk_size', 1500)  # ~300 words - increased proportionally
        self.max_chunk_size = kwargs.get('max_chunk_size', 25000)  # ~5000 words - increased proportionally
        
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model for semantic similarity."""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            return SentenceTransformer(model_name)
        except ImportError:
            logger.warning("SentenceTransformers not available. Install with: pip install sentence-transformers")
            return None
    
    def chunk(self, parsed_document: ParsedDocument, **kwargs) -> ChunkingResult:
        """Chunk document using semantic similarity."""
        start_time = time.time()
        
        # Override config with kwargs if provided
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        semantic_threshold = kwargs.get('semantic_threshold', self.semantic_threshold)
        min_chunk_size = kwargs.get('min_chunk_size', self.min_chunk_size)
        max_chunk_size = kwargs.get('max_chunk_size', self.max_chunk_size)
        
        if not self.embedding_model:
            # Fallback to hierarchical chunking if no embedding model
            logger.warning("No embedding model available, falling back to hierarchical chunking")
            from .hierarchical_chunker import HierarchicalChunker
            fallback_chunker = HierarchicalChunker(chunk_size=chunk_size)
            return fallback_chunker.chunk(parsed_document, **kwargs)
        
        chunks = []
        chunk_index = 0
        
        # Process each element type separately
        for element_type in ['header', 'text', 'table', 'list']:
            elements = [elem for elem in parsed_document.elements if elem.element_type == element_type]
            if elements:
                element_chunks = self._chunk_elements_semantically(
                    elements, semantic_threshold, min_chunk_size, max_chunk_size, chunk_index
                )
                chunks.extend(element_chunks)
                chunk_index += len(element_chunks)
        
        # Process remaining elements
        remaining_elements = [elem for elem in parsed_document.elements 
                            if elem.element_type not in ['header', 'text', 'table', 'list']]
        if remaining_elements:
            remaining_chunks = self._chunk_elements_semantically(
                remaining_elements, semantic_threshold, min_chunk_size, max_chunk_size, chunk_index
            )
            chunks.extend(remaining_chunks)
        
        processing_time = time.time() - start_time
        
        return ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            processing_time=processing_time,
            metadata={
                'chunker': 'SemanticChunker',
                'chunk_size': chunk_size,
                'semantic_threshold': semantic_threshold,
                'min_chunk_size': min_chunk_size,
                'max_chunk_size': max_chunk_size,
                'embedding_model': self.config.get('embedding_model', 'all-MiniLM-L6-v2'),
                'document_elements': len(parsed_document.elements)
            }
        )
    
    def _chunk_elements_semantically(self, elements: List[ParsedElement], 
                                   semantic_threshold: float, min_chunk_size: int, 
                                   max_chunk_size: int, start_index: int) -> List[Chunk]:
        """Chunk elements using semantic similarity."""
        if not elements:
            return []
        
        chunks = []
        chunk_index = start_index
        
        # Split elements into sentences for better semantic analysis
        sentences = []
        sentence_positions = []
        
        for element in elements:
            element_sentences = self._split_into_sentences(element.content)
            for sentence in element_sentences:
                sentences.append(sentence)
                sentence_positions.append({
                    'element': element,
                    'start': element.start_position + element.content.find(sentence),
                    'end': element.start_position + element.content.find(sentence) + len(sentence)
                })
        
        if not sentences:
            return []
        
        # Calculate embeddings
        embeddings = self.embedding_model.encode(sentences)
        
        # Find semantic boundaries
        boundaries = self._find_semantic_boundaries(embeddings, semantic_threshold)
        
        # Create chunks based on boundaries
        current_chunk_sentences = []
        current_start_pos = sentence_positions[0]['start']
        current_element_type = sentence_positions[0]['element'].element_type
        
        for i, sentence in enumerate(sentences):
            current_chunk_sentences.append(sentence)
            
            # Check if we should create a chunk
            should_chunk = (
                i in boundaries or  # Semantic boundary
                len(' '.join(current_chunk_sentences)) >= max_chunk_size or  # Size limit
                i == len(sentences) - 1  # Last sentence
            )
            
            if should_chunk and len(' '.join(current_chunk_sentences)) >= min_chunk_size:
                chunk_content = ' '.join(current_chunk_sentences)
                current_end_pos = sentence_positions[i]['end']
                
                chunk = self.create_chunk(
                    content=chunk_content,
                    chunk_type=current_element_type,
                    chunk_index=chunk_index,
                    start_position=current_start_pos,
                    end_position=current_end_pos,
                    metadata={
                        'chunking_method': 'semantic',
                        'semantic_threshold': semantic_threshold,
                        'sentence_count': len(current_chunk_sentences),
                        'boundary_type': 'semantic' if i in boundaries else 'size_limit'
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Reset for next chunk
                current_chunk_sentences = []
                if i < len(sentences) - 1:
                    current_start_pos = sentence_positions[i + 1]['start']
                    current_element_type = sentence_positions[i + 1]['element'].element_type
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # If no sentences found, split by paragraphs
        if not sentences:
            sentences = [p.strip() for p in text.split('\n') if p.strip()]
        
        # If still no sentences, return the whole text
        if not sentences:
            sentences = [text]
        
        return sentences
    
    def _find_semantic_boundaries(self, embeddings: np.ndarray, threshold: float) -> List[int]:
        """Find semantic boundaries based on embedding similarity."""
        boundaries = []
        
        for i in range(1, len(embeddings)):
            # Calculate cosine similarity between consecutive sentences
            similarity = np.dot(embeddings[i-1], embeddings[i]) / (
                np.linalg.norm(embeddings[i-1]) * np.linalg.norm(embeddings[i])
            )
            
            # If similarity is below threshold, it's a boundary
            if similarity < threshold:
                boundaries.append(i)
        
        return boundaries
    
    def _calculate_semantic_coherence(self, chunks: List[Chunk]) -> float:
        """Calculate semantic coherence score for chunks."""
        if len(chunks) < 2:
            return 1.0
        
        if not self.embedding_model:
            return 0.5  # Default score if no embedding model
        
        # Calculate average similarity between consecutive chunks
        similarities = []
        for i in range(1, len(chunks)):
            emb1 = self.embedding_model.encode([chunks[i-1].content])
            emb2 = self.embedding_model.encode([chunks[i].content])
            
            similarity = np.dot(emb1[0], emb2[0]) / (
                np.linalg.norm(emb1[0]) * np.linalg.norm(emb2[0])
            )
            similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0
