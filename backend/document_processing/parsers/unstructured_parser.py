import os
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser, ParsedDocument, ParsedElement

logger = logging.getLogger(__name__)


class UnstructuredParser(BaseParser):
    """Parser using Unstructured.io for structure-aware document parsing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get('api_key', os.getenv('UNSTRUCTURED_API_KEY'))
        if not self.api_key:
            raise ValueError("UNSTRUCTURED_API_KEY environment variable is required")
        
        # Initialize unstructured client
        try:
            from unstructured.partition.api import partition_via_api
            self.partition_func = partition_via_api
        except ImportError:
            logger.warning("Unstructured.io not installed. Install with: pip install unstructured[all-docs]")
            raise ImportError("Unstructured.io library not found")
    
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse document using Unstructured.io API."""
        try:
            # Configure partitioning strategy
            strategy = self.config.get('strategy', 'auto')
            include_page_breaks = self.config.get('include_page_breaks', True)
            
            # Partition the document
            elements = self.partition_func(
                filename=file_path,
                api_key=self.api_key,
                strategy=strategy,
                include_page_breaks=include_page_breaks
            )
            
            # Convert to our format
            parsed_elements = []
            current_position = 0
            
            for i, element in enumerate(elements):
                element_type = self._map_element_type(element.category)
                
                parsed_element = ParsedElement(
                    content=str(element),
                    element_type=element_type,
                    metadata={
                        'unstructured_category': element.category,
                        'page_number': getattr(element.metadata, 'page_number', None),
                        'coordinates': getattr(element.metadata, 'coordinates', None),
                        'parent_id': getattr(element.metadata, 'parent_id', None),
                        'element_id': getattr(element.metadata, 'element_id', None),
                    },
                    start_position=current_position,
                    end_position=current_position + len(str(element))
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
            logger.error(f"Error parsing document with Unstructured.io: {e}")
            raise
    
    def _map_element_type(self, unstructured_category: str) -> str:
        """Map Unstructured.io categories to our element types."""
        mapping = {
            'Title': 'header',
            'Header': 'header',
            'NarrativeText': 'text',
            'ListItem': 'list',
            'Table': 'table',
            'TableRow': 'table',
            'TableCell': 'table',
            'Footer': 'text',
            'PageBreak': 'page_break',
            'Image': 'image',
            'Formula': 'text',
        }
        return mapping.get(unstructured_category, 'text')
    
    def _build_hierarchical_relationships(self, elements: List[ParsedElement]):
        """Build parent-child relationships between elements."""
        # Simple hierarchical building based on element types and positions
        for i, element in enumerate(elements):
            if element.element_type == 'header':
                # Find the next non-header elements as children
                for j in range(i + 1, len(elements)):
                    if elements[j].element_type != 'header':
                        elements[j].parent_element = element
                        element.child_elements.append(elements[j])
                    else:
                        break
    
    def get_supported_formats(self) -> List[str]:
        """Get supported file formats."""
        return ['.pdf', '.docx', '.doc', '.txt', '.html', '.md']
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract enhanced metadata using Unstructured.io."""
        metadata = super().extract_metadata(file_path)
        metadata.update({
            'parser': 'UnstructuredParser',
            'api_version': 'unstructured.io',
            'strategy': self.config.get('strategy', 'auto')
        })
        return metadata
