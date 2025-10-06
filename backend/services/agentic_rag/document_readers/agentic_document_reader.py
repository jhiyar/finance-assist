"""
Agentic Document Reader for Enhanced Agentic-RAG.

Uses LandingAI's Agentic Document Extraction API to extract structured data
from visually complex documents with tables, pictures, and charts.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json

try:
    from agentic_doc.parse import parse
    from agentic_doc.utils import viz_parsed_document
    from agentic_doc.config import VisualizationConfig
    AGENTIC_DOC_AVAILABLE = True
except ImportError:
    AGENTIC_DOC_AVAILABLE = False
    logging.warning("agentic-doc library not available. Install with: pip install agentic-doc")

logger = logging.getLogger(__name__)


class AgenticDocumentReader:
    """
    Agentic document reader using LandingAI's Agentic Document Extraction API.
    
    Features:
    - Structured data extraction from complex documents
    - Table, image, and chart processing
    - Hierarchical JSON output with exact element locations
    - Long document support (100+ pages)
    - Auto-retry and paging for large documents
    - Visual debugging with bounding box snippets
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Agentic Document Reader.
        
        Args:
            api_key: LandingAI API key. If not provided, will use LANDINGAI_API_KEY env var.
        """
        if not AGENTIC_DOC_AVAILABLE:
            raise ImportError("agentic-doc library is not installed. Install with: pip install agentic-doc")
        
        self.logger = logger
        self.api_key = api_key or os.getenv('LANDINGAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("LandingAI API key is required. Set LANDINGAI_API_KEY environment variable or pass api_key parameter.")
        
        # Set the API key for the agentic-doc library
        os.environ['LANDINGAI_API_KEY'] = self.api_key
        
        self.logger.info("AgenticDocumentReader initialized with LandingAI API")
    
    def extract_content(self, file_path: str, include_marginalia: bool = True, 
                       include_metadata_in_markdown: bool = True) -> Dict[str, Any]:
        """
        Extract structured content from document using Agentic Document Extraction.
        
        Args:
            file_path: Path to the document file (PDF, image, or URL)
            include_marginalia: Whether to include marginalia (footer notes, page numbers)
            include_metadata_in_markdown: Whether to include metadata in markdown output
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            self.logger.info(f"Extracting content from {file_path} using Agentic Document Extraction")
            
            # Parse the document
            results = parse(
                file_path,
                include_marginalia=include_marginalia,
                include_metadata_in_markdown=include_metadata_in_markdown
            )
            
            if not results:
                raise ValueError(f"No results returned from Agentic Document Extraction for {file_path}")
            
            # Get the first (and typically only) result
            parsed_doc = results[0]
            
            # Extract structured content
            extracted_content = self._process_parsed_document(parsed_doc, file_path)
            
            self.logger.info(f"Successfully extracted content from {file_path}: {len(extracted_content.get('content', ''))} characters")
            
            return extracted_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content from {file_path}: {e}")
            raise
    
    def _process_parsed_document(self, parsed_doc, file_path: str) -> Dict[str, Any]:
        """
        Process the parsed document from Agentic Document Extraction.
        
        Args:
            parsed_doc: Parsed document object from agentic-doc
            file_path: Original file path
            
        Returns:
            Processed content dictionary
        """
        try:
            # Extract basic content
            content_parts = []
            structured_data = []
            
            # Process chunks
            for chunk in parsed_doc.chunks:
                chunk_data = {
                    "type": chunk.type.value if hasattr(chunk.type, 'value') else str(chunk.type),
                    "content": chunk.content,
                    "page": getattr(chunk, 'page', None),
                    "grounding": []
                }
                
                # Add content to text
                content_parts.append(chunk.content)
                
                # Process grounding information
                for grounding in chunk.grounding:
                    grounding_data = {
                        "page": getattr(grounding, 'page', None),
                        "bbox": getattr(grounding, 'bbox', None),
                        "image_path": getattr(grounding, 'image_path', None)
                    }
                    chunk_data["grounding"].append(grounding_data)
                
                structured_data.append(chunk_data)
            
            # Combine all content
            full_content = "\n\n".join(content_parts)
            
            # Extract metadata
            metadata = {
                "source": file_path,
                "total_chunks": len(parsed_doc.chunks),
                "chunk_types": list(set([chunk.type.value if hasattr(chunk.type, 'value') else str(chunk.type) 
                                       for chunk in parsed_doc.chunks])),
                "pages": list(set([getattr(chunk, 'page', 1) for chunk in parsed_doc.chunks if hasattr(chunk, 'page')])),
                "extraction_method": "agentic_document_extraction"
            }
            
            return {
                "content": full_content,
                "structured_data": structured_data,
                "metadata": metadata,
                "raw_result": parsed_doc
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process parsed document: {e}")
            raise
    
    def extract_with_visualization(self, file_path: str, output_dir: str = "./visualizations",
                                 include_marginalia: bool = True, 
                                 include_metadata_in_markdown: bool = True) -> Dict[str, Any]:
        """
        Extract content and create visualizations showing extraction results.
        
        Args:
            file_path: Path to the document file
            output_dir: Directory to save visualization images
            include_marginalia: Whether to include marginalia
            include_metadata_in_markdown: Whether to include metadata in markdown
            
        Returns:
            Dictionary containing extracted content and visualization paths
        """
        try:
            # First extract the content
            extracted_content = self.extract_content(
                file_path, 
                include_marginalia=include_marginalia,
                include_metadata_in_markdown=include_metadata_in_markdown
            )
            
            # Create visualizations
            parsed_doc = extracted_content["raw_result"]
            visualization_images = viz_parsed_document(
                file_path,
                parsed_doc,
                output_dir=output_dir
            )
            
            # Add visualization paths to metadata
            extracted_content["metadata"]["visualization_images"] = [
                str(img) for img in visualization_images
            ]
            extracted_content["metadata"]["visualization_output_dir"] = output_dir
            
            self.logger.info(f"Created {len(visualization_images)} visualization images in {output_dir}")
            
            return extracted_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content with visualization: {e}")
            raise
    
    def extract_groundings(self, file_path: str, grounding_save_dir: str = "./groundings",
                          include_marginalia: bool = True, 
                          include_metadata_in_markdown: bool = True) -> Dict[str, Any]:
        """
        Extract content and save grounding images (bounding box snippets).
        
        Args:
            file_path: Path to the document file
            grounding_save_dir: Directory to save grounding images
            include_marginalia: Whether to include marginalia
            include_metadata_in_markdown: Whether to include metadata in markdown
            
        Returns:
            Dictionary containing extracted content and grounding information
        """
        try:
            # Parse document with grounding save directory
            results = parse(
                file_path,
                grounding_save_dir=grounding_save_dir,
                include_marginalia=include_marginalia,
                include_metadata_in_markdown=include_metadata_in_markdown
            )
            
            if not results:
                raise ValueError(f"No results returned from Agentic Document Extraction for {file_path}")
            
            parsed_doc = results[0]
            extracted_content = self._process_parsed_document(parsed_doc, file_path)
            
            # Collect grounding image paths
            grounding_paths = []
            for chunk in parsed_doc.chunks:
                for grounding in chunk.grounding:
                    if hasattr(grounding, 'image_path') and grounding.image_path:
                        grounding_paths.append(grounding.image_path)
            
            extracted_content["metadata"]["grounding_images"] = grounding_paths
            extracted_content["metadata"]["grounding_save_dir"] = grounding_save_dir
            
            self.logger.info(f"Saved {len(grounding_paths)} grounding images in {grounding_save_dir}")
            
            return extracted_content
            
        except Exception as e:
            self.logger.error(f"Failed to extract content with groundings: {e}")
            raise
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document metadata
        """
        try:
            # Extract content to get metadata
            extracted_content = self.extract_content(file_path)
            
            # Get file information
            path_obj = Path(file_path)
            file_stats = path_obj.stat() if path_obj.exists() else {}
            
            metadata = {
                "filename": path_obj.name,
                "file_size": file_stats.get('st_size', 0),
                "file_extension": path_obj.suffix,
                "extraction_method": "agentic_document_extraction",
                **extracted_content["metadata"]
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return {
                "filename": Path(file_path).name,
                "file_extension": Path(file_path).suffix,
                "extraction_method": "agentic_document_extraction",
                "error": str(e)
            }
    
    def batch_extract(self, file_paths: List[str], include_marginalia: bool = True,
                     include_metadata_in_markdown: bool = True) -> List[Dict[str, Any]]:
        """
        Extract content from multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process
            include_marginalia: Whether to include marginalia
            include_metadata_in_markdown: Whether to include metadata in markdown
            
        Returns:
            List of extracted content dictionaries
        """
        try:
            self.logger.info(f"Batch extracting content from {len(file_paths)} documents")
            
            # Use agentic-doc's batch processing
            results = parse(
                file_paths,
                include_marginalia=include_marginalia,
                include_metadata_in_markdown=include_metadata_in_markdown
            )
            
            extracted_contents = []
            for i, parsed_doc in enumerate(results):
                file_path = file_paths[i] if i < len(file_paths) else f"document_{i}"
                extracted_content = self._process_parsed_document(parsed_doc, file_path)
                extracted_contents.append(extracted_content)
            
            self.logger.info(f"Successfully batch extracted content from {len(extracted_contents)} documents")
            
            return extracted_contents
            
        except Exception as e:
            self.logger.error(f"Failed to batch extract content: {e}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
    
    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file format is supported
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.get_supported_formats()
