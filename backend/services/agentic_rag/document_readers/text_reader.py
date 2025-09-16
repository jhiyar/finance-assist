"""
Text Reader for Enhanced Agentic-RAG.

Handles plain text document loading and content extraction.
"""

import logging
from typing import List, Dict, Any, Optional
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class TextReader:
    """
    Text document reader with content preprocessing.
    
    Features:
    - Multiple encoding support
    - Content cleaning and formatting
    - Section detection
    - Metadata extraction
    """
    
    def __init__(self):
        self.logger = logger
        self.encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    def extract_content(self, file_path: str) -> str:
        """
        Extract content from text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted content as string
        """
        try:
            content = self._read_file_with_encoding(file_path)
            
            if not content:
                raise ValueError(f"File appears to be empty: {file_path}")
            
            # Clean and format content
            cleaned_content = self._clean_content(content)
            
            self.logger.info(f"Extracted content from text file: {len(cleaned_content)} characters")
            
            return cleaned_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from text file {file_path}: {e}")
            raise
    
    def _read_file_with_encoding(self, file_path: str) -> str:
        """
        Read file with multiple encoding attempts.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content as string
        """
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    self.logger.debug(f"Successfully read file with encoding: {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.warning(f"Failed to read file with encoding {encoding}: {e}")
                continue
        
        raise ValueError(f"Could not read file with any of the attempted encodings: {self.encodings}")
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and format text content.
        
        Args:
            content: Raw text content
            
        Returns:
            Cleaned content
        """
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive spaces
        content = re.sub(r'[ \t]+', ' ', content)
        
        # Clean up bullet points and lists
        content = re.sub(r'^\s*[-*•]\s+', '• ', content, flags=re.MULTILINE)
        
        # Clean up numbered lists
        content = re.sub(r'^\s*(\d+\.)\s+', r'\1 ', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract sections from text content.
        
        Args:
            content: Text content
            
        Returns:
            List of section dictionaries
        """
        try:
            sections = []
            
            # Common section patterns
            section_patterns = [
                r'^#+\s+(.+)$',  # Markdown headers
                r'^[A-Z][A-Z\s]+$',  # ALL CAPS headers
                r'^\d+\.\s+([A-Z][^.\n]+)',  # Numbered sections
                r'^[A-Z][^.\n]+:$',  # Title with colon
            ]
            
            lines = content.split('\n')
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_content:
                        current_content.append('')
                    continue
                
                # Check if line matches any section pattern
                is_section_header = False
                for pattern in section_patterns:
                    if re.match(pattern, line, re.MULTILINE):
                        # Save previous section
                        if current_section:
                            sections.append({
                                "title": current_section,
                                "content": '\n'.join(current_content).strip(),
                                "line_count": len(current_content)
                            })
                        
                        # Start new section
                        current_section = line
                        current_content = []
                        is_section_header = True
                        break
                
                if not is_section_header:
                    current_content.append(line)
            
            # Add final section
            if current_section:
                sections.append({
                    "title": current_section,
                    "content": '\n'.join(current_content).strip(),
                    "line_count": len(current_content)
                })
            
            return sections
            
        except Exception as e:
            self.logger.error(f"Failed to extract sections: {e}")
            return []
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            path_obj = Path(file_path)
            content = self._read_file_with_encoding(file_path)
            
            metadata = {
                "filename": path_obj.name,
                "file_size": path_obj.stat().st_size,
                "line_count": len(content.split('\n')),
                "word_count": len(content.split()),
                "character_count": len(content),
                "sections_count": len(self.extract_sections(content))
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from text file {file_path}: {e}")
            return {}
    
    def detect_language(self, content: str) -> str:
        """
        Simple language detection based on common words.
        
        Args:
            content: Text content
            
        Returns:
            Detected language code
        """
        try:
            # Simple word-based language detection
            english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            spanish_words = ['el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le']
            french_words = ['le', 'la', 'de', 'et', 'à', 'un', 'il', 'que', 'ne', 'se', 'ce', 'pas', 'tout']
            
            content_lower = content.lower()
            
            english_count = sum(1 for word in english_words if word in content_lower)
            spanish_count = sum(1 for word in spanish_words if word in content_lower)
            french_count = sum(1 for word in french_words if word in content_lower)
            
            if english_count > spanish_count and english_count > french_count:
                return 'en'
            elif spanish_count > french_count:
                return 'es'
            elif french_count > 0:
                return 'fr'
            else:
                return 'unknown'
                
        except Exception as e:
            self.logger.warning(f"Failed to detect language: {e}")
            return 'unknown'
