import time
import logging
import re
from typing import List, Dict, Any, Tuple
from .base_chunker import BaseChunker, Chunk, ChunkingResult
from ..parsers.base_parser import ParsedDocument, ParsedElement

logger = logging.getLogger(__name__)


class FinancialChunker(BaseChunker):
    """Specialized chunker for financial documents with table and structure awareness."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chunk_size = kwargs.get('chunk_size', 5000)  # ~1000 words
        self.chunk_overlap = kwargs.get('chunk_overlap', 500)  # ~100 words
        self.table_aware = kwargs.get('table_aware', True)
        self.preserve_financial_structure = kwargs.get('preserve_financial_structure', True)
        
        # Financial document patterns
        self.financial_patterns = {
            'balance_sheet': r'(?i)(balance\s+sheet|statement\s+of\s+financial\s+position)',
            'income_statement': r'(?i)(income\s+statement|profit\s+and\s+loss|p&l)',
            'cash_flow': r'(?i)(cash\s+flow|statement\s+of\s+cash\s+flows)',
            'financial_ratios': r'(?i)(ratios?|financial\s+ratios?)',
            'notes': r'(?i)(notes?\s+to\s+financial\s+statements?|accounting\s+policies)',
            'audit': r'(?i)(audit|auditor|independent\s+auditor)',
            'revenue': r'(?i)(revenue|sales|income)',
            'expenses': r'(?i)(expenses?|costs?|operating\s+expenses?)',
            'assets': r'(?i)(assets?|current\s+assets?|fixed\s+assets?)',
            'liabilities': r'(?i)(liabilities?|current\s+liabilities?|long.term\s+liabilities?)',
            'equity': r'(?i)(equity|shareholders?\s+equity|stockholders?\s+equity)',
        }
    
    def chunk(self, parsed_document: ParsedDocument, **kwargs) -> ChunkingResult:
        """Chunk financial document with specialized awareness."""
        start_time = time.time()
        
        # Override config with kwargs if provided
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        table_aware = kwargs.get('table_aware', self.table_aware)
        preserve_financial_structure = kwargs.get('preserve_financial_structure', self.preserve_financial_structure)
        
        chunks = []
        chunk_index = 0
        
        if preserve_financial_structure:
            # Identify financial document sections
            sections = self._identify_financial_sections(parsed_document)
            
            # Chunk each section appropriately
            for section in sections:
                section_chunks = self._chunk_financial_section(
                    section, chunk_size, chunk_overlap, table_aware, chunk_index
                )
                chunks.extend(section_chunks)
                chunk_index += len(section_chunks)
        else:
            # Standard chunking with financial awareness
            chunks = self._chunk_with_financial_awareness(
                parsed_document, chunk_size, chunk_overlap, table_aware, chunk_index
            )
        
        processing_time = time.time() - start_time
        
        return ChunkingResult(
            chunks=chunks,
            total_chunks=len(chunks),
            processing_time=processing_time,
            metadata={
                'chunker': 'FinancialChunker',
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'table_aware': table_aware,
                'preserve_financial_structure': preserve_financial_structure,
                'document_elements': len(parsed_document.elements),
                'financial_sections': len(self._identify_financial_sections(parsed_document))
            }
        )
    
    def _identify_financial_sections(self, parsed_document: ParsedDocument) -> List[Dict[str, Any]]:
        """Identify financial document sections."""
        sections = []
        current_section = None
        
        for element in parsed_document.elements:
            section_type = self._classify_financial_section(element.content)
            
            if section_type and section_type != 'unknown':
                # Start new section
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    'type': section_type,
                    'title': element.content[:100] if element.element_type == 'header' else '',
                    'elements': [element],
                    'start_position': element.start_position,
                    'end_position': element.end_position
                }
            else:
                # Add to current section
                if current_section:
                    current_section['elements'].append(element)
                    current_section['end_position'] = element.end_position
                else:
                    # Create a general section
                    current_section = {
                        'type': 'general',
                        'title': 'General Content',
                        'elements': [element],
                        'start_position': element.start_position,
                        'end_position': element.end_position
                    }
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _classify_financial_section(self, content: str) -> str:
        """Classify content as a financial section type."""
        content_lower = content.lower()
        
        for section_type, pattern in self.financial_patterns.items():
            if re.search(pattern, content_lower):
                return section_type
        
        return 'unknown'
    
    def _chunk_financial_section(self, section: Dict[str, Any], chunk_size: int, 
                               chunk_overlap: int, table_aware: bool, 
                               start_index: int) -> List[Chunk]:
        """Chunk a financial section with appropriate strategy."""
        chunks = []
        chunk_index = start_index
        
        # Handle tables separately if table_aware
        if table_aware:
            table_elements = [elem for elem in section['elements'] if elem.element_type == 'table']
            non_table_elements = [elem for elem in section['elements'] if elem.element_type != 'table']
            
            # Chunk tables as complete units
            for table_element in table_elements:
                chunk = self.create_chunk(
                    content=table_element.content,
                    chunk_type='table',
                    chunk_index=chunk_index,
                    start_position=table_element.start_position,
                    end_position=table_element.end_position,
                    metadata={
                        'chunking_method': 'financial_table',
                        'section_type': section['type'],
                        'section_title': section['title'],
                        'table_aware': True,
                        'financial_entity_count': self._count_financial_entities(table_element.content)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Chunk non-table elements
            if non_table_elements:
                non_table_chunks = self._chunk_elements_standard(
                    non_table_elements, chunk_size, chunk_overlap, chunk_index
                )
                chunks.extend(non_table_chunks)
        else:
            # Standard chunking for all elements
            standard_chunks = self._chunk_elements_standard(
                section['elements'], chunk_size, chunk_overlap, chunk_index
            )
            chunks.extend(standard_chunks)
        
        return chunks
    
    def _chunk_elements_standard(self, elements: List[ParsedElement], chunk_size: int, 
                               chunk_overlap: int, start_index: int) -> List[Chunk]:
        """Standard chunking for elements."""
        chunks = []
        chunk_index = start_index
        
        # Combine content from elements
        combined_content = ""
        element_metadata = []
        
        for element in elements:
            combined_content += element.content + "\n\n"
            element_metadata.append({
                'type': element.element_type,
                'start': element.start_position,
                'end': element.end_position
            })
        
        # Split into chunks
        start_pos = 0
        while start_pos < len(combined_content):
            end_pos = min(start_pos + chunk_size, len(combined_content))
            
            # Find a good split point
            if end_pos < len(combined_content):
                end_pos = self._find_financial_split_point(combined_content[start_pos:], chunk_size) + start_pos
            
            chunk_content = combined_content[start_pos:end_pos].strip()
            if chunk_content:
                chunk = self.create_chunk(
                    content=chunk_content,
                    chunk_type='mixed',
                    chunk_index=chunk_index,
                    start_position=start_pos,
                    end_position=end_pos,
                    metadata={
                        'chunking_method': 'financial_standard',
                        'element_count': len(element_metadata),
                        'financial_entity_count': self._count_financial_entities(chunk_content)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start_pos = end_pos - chunk_overlap
        
        return chunks
    
    def _chunk_with_financial_awareness(self, parsed_document: ParsedDocument, 
                                      chunk_size: int, chunk_overlap: int, 
                                      table_aware: bool, start_index: int) -> List[Chunk]:
        """Chunk with financial awareness but without strict section preservation."""
        chunks = []
        chunk_index = start_index
        
        # Separate tables and other content
        if table_aware:
            table_elements = [elem for elem in parsed_document.elements if elem.element_type == 'table']
            other_elements = [elem for elem in parsed_document.elements if elem.element_type != 'table']
            
            # Process tables as complete units
            for table_element in table_elements:
                chunk = self.create_chunk(
                    content=table_element.content,
                    chunk_type='table',
                    chunk_index=chunk_index,
                    start_position=table_element.start_position,
                    end_position=table_element.end_position,
                    metadata={
                        'chunking_method': 'financial_table_aware',
                        'table_aware': True,
                        'financial_entity_count': self._count_financial_entities(table_element.content)
                    }
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Process other elements
            if other_elements:
                other_chunks = self._chunk_elements_standard(
                    other_elements, chunk_size, chunk_overlap, chunk_index
                )
                chunks.extend(other_chunks)
        else:
            # Process all elements together
            all_chunks = self._chunk_elements_standard(
                parsed_document.elements, chunk_size, chunk_overlap, chunk_index
            )
            chunks.extend(all_chunks)
        
        return chunks
    
    def _find_financial_split_point(self, text: str, max_length: int) -> int:
        """Find a good split point for financial content."""
        if len(text) <= max_length:
            return len(text)
        
        # Look for financial statement boundaries (search backwards from max_length)
        financial_boundaries = [
            r'(?i)(balance\s+sheet|income\s+statement|cash\s+flow)',
            r'(?i)(notes?\s+to\s+financial\s+statements?)',
            r'(?i)(audit\s+report|independent\s+auditor)',
            r'(?i)(revenue|expenses|assets|liabilities|equity)',
            r'(?i)(quarterly|annual|yearly|monthly)',
        ]
        
        # Search in a reasonable range (last 20% of max_length)
        search_start = max_length
        search_end = max(0, max_length - int(max_length * 0.2))
        
        for i in range(search_start, search_end, -1):
            for pattern in financial_boundaries:
                if re.search(pattern, text[:i]):
                    return i
        
        # Look for sentence boundaries (search in last 10% of max_length)
        sentence_end = max(0, max_length - int(max_length * 0.1))
        for i in range(max_length, sentence_end, -1):
            if text[i] in '.!?' and i + 1 < len(text) and text[i + 1] in ' \n':
                return i + 1
        
        # Look for paragraph boundaries (search in last 5% of max_length)
        para_end = max(0, max_length - int(max_length * 0.05))
        for i in range(max_length, para_end, -1):
            if text[i] == '\n' and (i + 1 >= len(text) or text[i + 1] == '\n'):
                return i + 1
        
        # Look for word boundaries (search in last 2% of max_length)
        word_end = max(0, max_length - int(max_length * 0.02))
        for i in range(max_length, word_end, -1):
            if text[i] == ' ':
                return i + 1
        
        # Fallback to max_length
        return max_length
    
    def _count_financial_entities(self, content: str) -> int:
        """Count financial entities in content."""
        financial_terms = [
            r'\$[\d,]+\.?\d*',  # Dollar amounts
            r'\b\d+\.?\d*\s*(?:million|billion|thousand)\b',  # Large numbers
            r'\b(?:revenue|income|profit|loss|assets|liabilities|equity)\b',  # Financial terms
            r'\b(?:Q[1-4]|quarter|annual|yearly)\b',  # Time periods
        ]
        
        count = 0
        for pattern in financial_terms:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count
