"""
PDF Reader for Enhanced Agentic-RAG.

Handles PDF document loading and content extraction with table processing.
"""

import logging
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import pandas as pd
from io import StringIO

logger = logging.getLogger(__name__)


class PDFReader:
    """
    PDF document reader with enhanced content extraction.
    
    Features:
    - Text extraction with formatting preservation
    - Table detection and conversion to markdown
    - Image and figure handling
    - Metadata extraction
    """
    
    def __init__(self):
        self.logger = logger
    
    def extract_content(self, file_path: str) -> str:
        """
        Extract content from PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted content as string
        """
        try:
            doc = fitz.open(file_path)
            content_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                text = page.get_text()
                if text.strip():
                    content_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                
                # Extract tables
                tables = self._extract_tables_from_page(page)
                for i, table in enumerate(tables):
                    if table:
                        content_parts.append(f"--- Table {i + 1} on Page {page_num + 1} ---\n{table}")
            
            doc.close()
            
            full_content = "\n\n".join(content_parts)
            self.logger.info(f"Extracted content from PDF: {len(full_content)} characters")
            
            return full_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from PDF {file_path}: {e}")
            raise
    
    def _extract_tables_from_page(self, page) -> List[str]:
        """
        Extract tables from a PDF page and convert to markdown.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of table markdown strings
        """
        try:
            tables = page.find_tables()
            table_markdowns = []
            
            for table in tables:
                try:
                    # Extract table data
                    table_data = table.extract()
                    
                    if table_data and len(table_data) > 1:  # At least header + 1 row
                        # Convert to DataFrame for easier processing
                        df = pd.DataFrame(table_data[1:], columns=table_data[0])
                        
                        # Convert to markdown
                        markdown_table = df.to_markdown(index=False)
                        table_markdowns.append(markdown_table)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to extract table: {e}")
                    continue
            
            return table_markdowns
            
        except Exception as e:
            self.logger.warning(f"Failed to extract tables from page: {e}")
            return []
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            
            # Add additional information
            metadata.update({
                "page_count": len(doc),
                "file_size": doc.stream.tell() if hasattr(doc, 'stream') else 0
            })
            
            doc.close()
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from PDF {file_path}: {e}")
            return {}
    
    def extract_images(self, file_path: str, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract images from PDF file.
        
        Args:
            file_path: Path to the PDF file
            output_dir: Directory to save images (optional)
            
        Returns:
            List of image information dictionaries
        """
        try:
            doc = fitz.open(file_path)
            images = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            img_info = {
                                "page": page_num + 1,
                                "index": img_index,
                                "width": pix.width,
                                "height": pix.height,
                                "colorspace": pix.colorspace.name if pix.colorspace else "unknown"
                            }
                            
                            if output_dir:
                                img_path = f"{output_dir}/page_{page_num + 1}_img_{img_index}.png"
                                pix.save(img_path)
                                img_info["saved_path"] = img_path
                            
                            images.append(img_info)
                        
                        pix = None
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
                        continue
            
            doc.close()
            return images
            
        except Exception as e:
            self.logger.error(f"Failed to extract images from PDF {file_path}: {e}")
            return []
