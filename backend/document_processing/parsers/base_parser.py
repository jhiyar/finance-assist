from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedElement:
    """Represents a parsed element from a document."""
    content: str
    element_type: str  # 'text', 'table', 'header', 'list', etc.
    metadata: Dict[str, Any]
    start_position: int
    end_position: int
    parent_element: Optional['ParsedElement'] = None
    child_elements: List['ParsedElement'] = None
    
    def __post_init__(self):
        if self.child_elements is None:
            self.child_elements = []


@dataclass
class ParsedDocument:
    """Represents a fully parsed document."""
    elements: List[ParsedElement]
    metadata: Dict[str, Any]
    total_length: int
    
    def get_elements_by_type(self, element_type: str) -> List[ParsedElement]:
        """Get all elements of a specific type."""
        return [elem for elem in self.elements if elem.element_type == element_type]
    
    def get_hierarchical_structure(self) -> List[ParsedElement]:
        """Get elements organized in hierarchical structure."""
        return [elem for elem in self.elements if elem.parent_element is None]


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    def __init__(self, **kwargs):
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse a document and return structured elements.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            ParsedDocument containing structured elements
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if the file can be parsed by this parser."""
        import os
        if not os.path.exists(file_path):
            return False
        
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in self.get_supported_formats()
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from the file."""
        import os
        from datetime import datetime
        
        stat = os.stat(file_path)
        return {
            'file_name': os.path.basename(file_path),
            'file_size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime),
            'parser': self.__class__.__name__
        }
