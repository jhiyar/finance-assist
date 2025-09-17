from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import tiktoken

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a document chunk."""
    content: str
    chunk_type: str
    chunk_index: int
    start_position: int
    end_position: int
    token_count: int
    metadata: Dict[str, Any]
    parent_chunk: Optional['Chunk'] = None
    child_chunks: List['Chunk'] = None
    
    def __post_init__(self):
        if self.child_chunks is None:
            self.child_chunks = []


@dataclass
class ChunkingResult:
    """Result of a chunking operation."""
    chunks: List[Chunk]
    total_chunks: int
    processing_time: float
    metadata: Dict[str, Any]


class BaseChunker(ABC):
    """Abstract base class for document chunkers."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        except Exception:
            self.logger.warning("Could not initialize tokenizer, using character count")
            self.tokenizer = None
    
    @abstractmethod
    def chunk(self, parsed_document, **kwargs) -> ChunkingResult:
        """
        Chunk a parsed document.
        
        Args:
            parsed_document: ParsedDocument object
            **kwargs: Additional chunking parameters
            
        Returns:
            ChunkingResult containing chunks and metadata
        """
        pass
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback to character count / 4 (rough approximation)
            return len(text) // 4
    
    def create_chunk(self, content: str, chunk_type: str, chunk_index: int, 
                    start_position: int, end_position: int, 
                    metadata: Dict[str, Any] = None) -> Chunk:
        """Create a chunk with proper token counting."""
        if metadata is None:
            metadata = {}
        
        return Chunk(
            content=content,
            chunk_type=chunk_type,
            chunk_index=chunk_index,
            start_position=start_position,
            end_position=end_position,
            token_count=self.count_tokens(content),
            metadata=metadata
        )
    
    def validate_chunk_size(self, chunk: Chunk, max_tokens: int = 4000) -> bool:
        """Validate if chunk size is within limits."""
        return chunk.token_count <= max_tokens
    
    def split_oversized_chunk(self, chunk: Chunk, max_tokens: int = 4000) -> List[Chunk]:
        """Split an oversized chunk into smaller ones."""
        if chunk.token_count <= max_tokens:
            return [chunk]
        
        # Simple splitting by sentences
        sentences = chunk.content.split('. ')
        new_chunks = []
        current_content = ""
        current_start = chunk.start_position
        chunk_index = chunk.chunk_index
        
        for i, sentence in enumerate(sentences):
            test_content = current_content + sentence + ('. ' if i < len(sentences) - 1 else '')
            test_tokens = self.count_tokens(test_content)
            
            if test_tokens > max_tokens and current_content:
                # Create chunk from current content
                new_chunk = self.create_chunk(
                    content=current_content.strip(),
                    chunk_type=chunk.chunk_type,
                    chunk_index=chunk_index,
                    start_position=current_start,
                    end_position=current_start + len(current_content),
                    metadata=chunk.metadata.copy()
                )
                new_chunks.append(new_chunk)
                chunk_index += 1
                
                # Reset for next chunk
                current_content = sentence + ('. ' if i < len(sentences) - 1 else '')
                current_start = new_chunk.end_position
            else:
                current_content = test_content
        
        # Add the last chunk
        if current_content:
            new_chunk = self.create_chunk(
                content=current_content.strip(),
                chunk_type=chunk.chunk_type,
                chunk_index=chunk_index,
                start_position=current_start,
                end_position=chunk.end_position,
                metadata=chunk.metadata.copy()
            )
            new_chunks.append(new_chunk)
        
        return new_chunks
