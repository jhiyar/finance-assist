import os
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser, ParsedDocument, ParsedElement

logger = logging.getLogger(__name__)


class LlamaParseParser(BaseParser):
    """Parser using LlamaParse for GPT-4V powered document parsing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get('api_key', os.getenv('LLAMAPARSE_API_KEY'))
        if not self.api_key:
            raise ValueError("LLAMAPARSE_API_KEY environment variable is required")
        
        # Initialize LlamaParse
        try:
            from llama_parse import LlamaParse
            self.parser = LlamaParse(
                api_key=self.api_key,
                result_type="markdown",  # or "text"
                verbose=self.config.get('verbose', False),
                language=self.config.get('language', 'en')
            )
        except ImportError:
            logger.warning("LlamaParse not installed. Install with: pip install llama-parse")
            raise ImportError("LlamaParse library not found")
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse document using LlamaParse."""
        try:
            # Parse the document
            documents = self.parser.load_data(file_path)
            
            if not documents:
                raise ValueError("No content extracted from document")
            
            # Convert to our format
            parsed_elements = []
            current_position = 0
            
            for doc in documents:
                # Split the markdown content into elements
                elements = self._parse_markdown_content(doc.text)
                
                for element in elements:
                    parsed_element = ParsedElement(
                        content=element['content'],
                        element_type=element['type'],
                        metadata={
                            'llamaparse_metadata': doc.metadata,
                            'confidence': getattr(doc, 'confidence', None),
                            'page_number': getattr(doc, 'page_number', None),
                        },
                        start_position=current_position,
                        end_position=current_position + len(element['content'])
                    )
                    
                    parsed_elements.append(parsed_element)
                    current_position = parsed_element.end_position
            
            # Build hierarchical relationships
            self._build_hierarchical_relationships(parsed_elements)
            
            return ParsedDocument(
                elements=parsed_elements,
                metadata=self.extract_metadata(file_path),
                total_length=current_position
            )
            
        except Exception as e:
            logger.error(f"Error parsing document with LlamaParse: {e}")
            raise
    
    def _parse_markdown_content(self, markdown_text: str) -> List[Dict[str, Any]]:
        """Parse markdown content into structured elements."""
        import re
        
        elements = []
        lines = markdown_text.split('\n')
        current_element = {'content': '', 'type': 'text'}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_element['content']:
                    elements.append(current_element)
                    current_element = {'content': '', 'type': 'text'}
                continue
            
            # Detect element type
            if line.startswith('#'):
                # Header
                if current_element['content']:
                    elements.append(current_element)
                level = len(line) - len(line.lstrip('#'))
                elements.append({
                    'content': line,
                    'type': f'header_{level}'
                })
                current_element = {'content': '', 'type': 'text'}
            elif line.startswith('|') and '|' in line[1:]:
                # Table
                if current_element['content'] and current_element['type'] != 'table':
                    elements.append(current_element)
                    current_element = {'content': '', 'type': 'table'}
                current_element['content'] += line + '\n'
            elif line.startswith('- ') or line.startswith('* '):
                # List item
                if current_element['content'] and current_element['type'] != 'list':
                    elements.append(current_element)
                    current_element = {'content': '', 'type': 'list'}
                current_element['content'] += line + '\n'
            else:
                # Regular text
                if current_element['content'] and current_element['type'] != 'text':
                    elements.append(current_element)
                    current_element = {'content': '', 'type': 'text'}
                current_element['content'] += line + '\n'
        
        # Add the last element
        if current_element['content']:
            elements.append(current_element)
        
        return elements
    
    def _build_hierarchical_relationships(self, elements: List[ParsedElement]):
        """Build parent-child relationships between elements."""
        header_stack = []  # Stack to track header hierarchy
        
        for element in elements:
            if element.element_type.startswith('header_'):
                level = int(element.element_type.split('_')[1])
                
                # Pop headers with higher or equal level
                while header_stack and header_stack[-1][1] >= level:
                    header_stack.pop()
                
                # Set parent
                if header_stack:
                    element.parent_element = header_stack[-1][0]
                    header_stack[-1][0].child_elements.append(element)
                
                # Add to stack
                header_stack.append((element, level))
            else:
                # Set parent to the most recent header
                if header_stack:
                    element.parent_element = header_stack[-1][0]
                    header_stack[-1][0].child_elements.append(element)
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['.pdf', '.docx', '.doc', '.pptx', '.txt']
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract enhanced metadata using LlamaParse."""
        metadata = super().extract_metadata(file_path)
        metadata.update({
            'parser': 'LlamaParseParser',
            'api_version': 'llama-parse',
            'result_type': 'markdown',
            'language': self.config.get('language', 'en')
        })
        return metadata
