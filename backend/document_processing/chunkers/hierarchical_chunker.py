import time
import logging
from typing import List, Dict, Any
from .base_chunker import BaseChunker, Chunk, ChunkingResult
from ..parsers.base_parser import ParsedDocument, ParsedElement

logger = logging.getLogger(__name__)


class HierarchicalChunker(BaseChunker):
    """Chunker that maintains document structure and hierarchical relationships."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = kwargs.get('chunk_size', 5000)  # ~1000 words
        self.chunk_overlap = kwargs.get('chunk_overlap', 500)  # ~100 words
        self.preserve_structure = kwargs.get('preserve_structure', True)
        self.hierarchical_depth = kwargs.get('hierarchical_depth', 3)
    
    def chunk(self, parsed_document: ParsedDocument, **kwargs) -> ChunkingResult:
        """Chunk document while preserving hierarchical structure."""
        start_time = time.time()
        
        # Override config with kwargs if provided
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        preserve_structure = kwargs.get('preserve_structure', self.preserve_structure)
        
        chunks = []
        chunk_index = 0
        
        if preserve_structure:
            # Build hierarchical chunks
            chunks = self._build_hierarchical_chunks(
                parsed_document, chunk_size, chunk_overlap, chunk_index
            )
        else:
            # Simple sequential chunking
            chunks = self._build_sequential_chunks(
                parsed_document, chunk_size, chunk_overlap, chunk_index
            )
        
        processing_time = time.time() - start_time
        
        return ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            processing_time=processing_time,
            metadata={
                'chunker': 'HierarchicalChunker',
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'preserve_structure': preserve_structure,
                'hierarchical_depth': self.hierarchical_depth,
                'document_elements': len(parsed_document.elements)
            }
        )
    
    def _build_hierarchical_chunks(self, parsed_document: ParsedDocument, 
                                 chunk_size: int, chunk_overlap: int, 
                                 start_index: int) -> List[Chunk]:
        """Build chunks that preserve hierarchical structure."""
        chunks = []
        chunk_index = start_index
        
        # Get root elements (elements without parents)
        root_elements = [elem for elem in parsed_document.elements if elem.parent_element is None]
        
        for root_element in root_elements:
            element_chunks = self._chunk_element_hierarchically(
                root_element, chunk_size, chunk_overlap, chunk_index
            )
            chunks.extend(element_chunks)
            chunk_index += len(element_chunks)
        
        return chunks
    
    def _chunk_element_hierarchically(self, element: ParsedElement, chunk_size: int, 
                                    chunk_overlap: int, start_index: int) -> List[Chunk]:
        """Chunk a single element and its children hierarchically."""
        chunks = []
        chunk_index = start_index
        
        # If element is small enough, create a single chunk
        if len(element.content) <= chunk_size:
            chunk = self.create_chunk(
                content=element.content,
                chunk_type=element.element_type,
                chunk_index=chunk_index,
                start_position=element.start_position,
                end_position=element.end_position,
                metadata={
                    'element_type': element.element_type,
                    'hierarchical_level': self._get_hierarchical_level(element),
                    'has_children': len(element.child_elements) > 0,
                    'child_count': len(element.child_elements)
                }
            )
            chunks.append(chunk)
            chunk_index += 1
        else:
            # Split large element into smaller chunks
            element_chunks = self._split_large_element(element, chunk_size, chunk_overlap, chunk_index)
            chunks.extend(element_chunks)
            chunk_index += len(element_chunks)
        
        # Process child elements
        for child in element.child_elements:
            child_chunks = self._chunk_element_hierarchically(
                child, chunk_size, chunk_overlap, chunk_index
            )
            chunks.extend(child_chunks)
            chunk_index += len(child_chunks)
        
        return chunks
    
    def _split_large_element(self, element: ParsedElement, chunk_size: int, 
                           chunk_overlap: int, start_index: int) -> List[Chunk]:
        """Split a large element into smaller chunks with overlap."""
        chunks = []
        chunk_index = start_index
        content = element.content
        start_pos = element.start_position
        
        while len(content) > chunk_size:
            # Find a good split point (prefer sentence boundaries)
            split_point = self._find_split_point(content, chunk_size)
            
            chunk_content = content[:split_point]
            chunk = self.create_chunk(
                content=chunk_content,
                chunk_type=element.element_type,
                chunk_index=chunk_index,
                start_position=start_pos,
                end_position=start_pos + len(chunk_content),
                metadata={
                    'element_type': element.element_type,
                    'hierarchical_level': self._get_hierarchical_level(element),
                    'is_split': True,
                    'split_index': chunk_index - start_index
                }
            )
            chunks.append(chunk)
            chunk_index += 1
            
            # Move to next chunk with overlap
            overlap_start = max(0, split_point - chunk_overlap)
            content = content[overlap_start:]
            start_pos += overlap_start
        
        # Add remaining content as final chunk
        if content:
            chunk = self.create_chunk(
                content=content,
                chunk_type=element.element_type,
                chunk_index=chunk_index,
                start_position=start_pos,
                end_position=element.end_position,
                metadata={
                    'element_type': element.element_type,
                    'hierarchical_level': self._get_hierarchical_level(element),
                    'is_split': True,
                    'split_index': chunk_index - start_index,
                    'is_final': True
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _build_sequential_chunks(self, parsed_document: ParsedDocument, 
                               chunk_size: int, chunk_overlap: int, 
                               start_index: int) -> List[Chunk]:
        """Build chunks sequentially without preserving structure."""
        chunks = []
        chunk_index = start_index
        
        # Combine all content
        full_content = ""
        for element in parsed_document.elements:
            full_content += element.content + "\n\n"
        
        # Split into chunks
        start_pos = 0
        while start_pos < len(full_content):
            end_pos = min(start_pos + chunk_size, len(full_content))
            
            # Find a good split point
            if end_pos < len(full_content):
                end_pos = self._find_split_point(full_content[start_pos:], chunk_size) + start_pos
            
            chunk_content = full_content[start_pos:end_pos].strip()
            if chunk_content:
                chunk = self.create_chunk(
                    content=chunk_content,
                    chunk_type='mixed',
                    chunk_index=chunk_index,
                    start_position=start_pos,
                    end_position=end_pos,
                    metadata={
                        'chunking_method': 'sequential',
                        'preserve_structure': False
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start_pos = max(start_pos + 1, end_pos - chunk_overlap)
        
        return chunks
    
    def _find_split_point(self, text: str, max_length: int) -> int:
        """Find a good split point in text."""
        if len(text) <= max_length:
            return len(text)
        
        # Look for sentence boundaries
        for i in range(max_length, max(0, max_length - 200), -1):
            if text[i] in '.!?':
                return i + 1
        
        # Look for paragraph boundaries
        for i in range(max_length, max(0, max_length - 100), -1):
            if text[i] == '\n':
                return i + 1
        
        # Look for word boundaries
        for i in range(max_length, max(0, max_length - 50), -1):
            if text[i] == ' ':
                return i + 1
        
        # Fallback to max_length
        return max_length
    
    def _get_hierarchical_level(self, element: ParsedElement) -> int:
        """Get the hierarchical level of an element."""
        level = 0
        current = element
        while current.parent_element:
            level += 1
            current = current.parent_element
            if level > self.hierarchical_depth:
                break
        return level
