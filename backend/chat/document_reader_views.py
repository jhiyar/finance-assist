"""
Document Reader Comparison Views for Enhanced Agentic-RAG.

Views for comparing different document readers on the same document.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from services.agentic_rag.document_readers.agentic_document_reader import AgenticDocumentReader
from services.agentic_rag.document_readers.pdf_reader import PDFReader
from services.agentic_rag.document_readers.text_reader import TextReader
import os


class DocumentReaderComparisonView(APIView):
    """API view for comparing different document readers on the same document."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agentic_reader = None
        self.pdf_reader = PDFReader()
        self.text_reader = TextReader()
        self._initialize_agentic_reader()
    
    def _initialize_agentic_reader(self):
        """Initialize the Agentic Document Reader."""
        try:
            # Check if API key is available
            api_key = os.getenv('LANDINGAI_API_KEY')
            if api_key:
                self.agentic_reader = AgenticDocumentReader(api_key=api_key)
                print("✓ Agentic Document Reader initialized", flush=True)
            else:
                print("Warning: LANDINGAI_API_KEY not found. Agentic Document Reader will not be available.", flush=True)
        except Exception as e:
            print(f"Warning: Could not initialize Agentic Document Reader: {e}", flush=True)
            self.agentic_reader = None
    
    def get(self, request):
        """Get information about available document readers."""
        readers_info = {
            'pdf_reader': {
                'name': 'PDF Reader (PyMuPDF)',
                'available': True,
                'features': ['Text extraction', 'Table detection', 'Image extraction', 'Metadata extraction'],
                'supported_formats': ['.pdf']
            },
            'text_reader': {
                'name': 'Text Reader',
                'available': True,
                'features': ['Multiple encoding support', 'Content cleaning', 'Section detection', 'Language detection'],
                'supported_formats': ['.txt']
            },
            'agentic_reader': {
                'name': 'Agentic Document Reader (LandingAI)',
                'available': self.agentic_reader is not None,
                'features': ['Structured data extraction', 'Table/chart processing', 'Visual element detection', 'Hierarchical JSON output', 'Long document support'],
                'supported_formats': ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'],
                'api_key_required': True
            }
        }
        
        return Response({
            'status': 'success',
            'readers': readers_info,
            'sample_documents': self._get_sample_documents()
        })
    
    def _get_sample_documents(self):
        """Get list of available sample documents."""
        sample_docs = []
        sample_dir = os.path.join(os.path.dirname(__file__), '..', 'sample_documents')
        
        if os.path.exists(sample_dir):
            for file in os.listdir(sample_dir):
                if file.endswith(('.pdf', '.txt')):
                    sample_docs.append({
                        'filename': file,
                        'path': os.path.join(sample_dir, file),
                        'type': 'pdf' if file.endswith('.pdf') else 'text'
                    })
        
        return sample_docs
    
    def post(self, request):
        """Compare document readers on the same document."""
        try:
            file_path = request.data.get('file_path', '')
            if not file_path:
                return Response({
                    'error': 'file_path is required',
                    'status': 'error'
                })
            
            if not os.path.exists(file_path):
                return Response({
                    'error': f'File not found: {file_path}',
                    'status': 'error'
                })
            
            file_ext = os.path.splitext(file_path)[1].lower()
            results = {}
            
            # Test PDF Reader for PDF files
            if file_ext == '.pdf':
                try:
                    pdf_result = self.pdf_reader.extract_content(file_path)
                    pdf_metadata = self.pdf_reader.extract_metadata(file_path)
                    
                    results['pdf_reader'] = {
                        'status': 'success',
                        'content_length': len(pdf_result),
                        'content_preview': pdf_result[:500] + '...' if len(pdf_result) > 500 else pdf_result,
                        'metadata': pdf_metadata,
                        'processing_time': 'N/A'  # Could add timing if needed
                    }
                except Exception as e:
                    results['pdf_reader'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Test Text Reader for text files
            if file_ext == '.txt':
                try:
                    text_result = self.text_reader.extract_content(file_path)
                    text_metadata = self.text_reader.extract_metadata(file_path)
                    
                    results['text_reader'] = {
                        'status': 'success',
                        'content_length': len(text_result),
                        'content_preview': text_result[:500] + '...' if len(text_result) > 500 else text_result,
                        'metadata': text_metadata,
                        'processing_time': 'N/A'
                    }
                except Exception as e:
                    results['text_reader'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # Test Agentic Document Reader (if available and file is supported)
            if self.agentic_reader and self.agentic_reader.is_supported(file_path):
                try:
                    agentic_result = self.agentic_reader.extract_content(file_path)
                    
                    results['agentic_reader'] = {
                        'status': 'success',
                        'content_length': len(agentic_result.get('content', '')),
                        'content_preview': agentic_result.get('content', '')[:500] + '...' if len(agentic_result.get('content', '')) > 500 else agentic_result.get('content', ''),
                        'structured_data_count': len(agentic_result.get('structured_data', [])),
                        'chunk_types': agentic_result.get('metadata', {}).get('chunk_types', []),
                        'metadata': agentic_result.get('metadata', {}),
                        'processing_time': 'N/A'
                    }
                except Exception as e:
                    results['agentic_reader'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            elif self.agentic_reader:
                results['agentic_reader'] = {
                    'status': 'skipped',
                    'reason': f'File format {file_ext} not supported by Agentic Document Reader'
                }
            else:
                results['agentic_reader'] = {
                    'status': 'unavailable',
                    'reason': 'Agentic Document Reader not initialized (missing API key)'
                }
            
            return Response({
                'status': 'success',
                'file_path': file_path,
                'file_type': file_ext,
                'comparison_results': results
            })
            
        except Exception as e:
            return Response({
                'error': str(e),
                'status': 'error'
            })
