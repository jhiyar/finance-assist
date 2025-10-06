# Agentic Document Reader Setup

This document explains how to set up and use the new Agentic Document Reader that uses LandingAI's Agentic Document Extraction API.

## Overview

The Agentic Document Reader provides advanced document processing capabilities using LandingAI's API, including:

- Structured data extraction from complex documents
- Table, image, and chart processing
- Hierarchical JSON output with exact element locations
- Long document support (100+ pages)
- Auto-retry and paging for large documents
- Visual debugging with bounding box snippets

## Setup Instructions

### 1. Install Dependencies

The `agentic-doc` library has been added to `requirements.txt`. Install it with:

```bash
pip install agentic-doc==0.3.3
```

### 2. Get LandingAI API Key

1. Visit [LandingAI's website](https://landing.ai/agentic-document-extraction)
2. Sign up for an account
3. Get your API key from the dashboard

### 3. Set Environment Variable

Set your LandingAI API key as an environment variable:

```bash
export LANDINGAI_API_KEY="your_api_key_here"
```

Or add it to your `.env` file:

```
LANDINGAI_API_KEY=your_api_key_here
```

### 4. Test the Setup

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the Document Reader Comparison page in the frontend:
   ```
   http://localhost:3000/document-reader-comparison
   ```

3. Select a sample document and click "Compare Readers" to test the functionality.

## API Endpoints

### GET /api/chat/document-reader-comparison/

Returns information about available document readers and sample documents.

**Response:**
```json
{
  "status": "success",
  "readers": {
    "pdf_reader": {
      "name": "PDF Reader (PyMuPDF)",
      "available": true,
      "features": ["Text extraction", "Table detection", "Image extraction", "Metadata extraction"],
      "supported_formats": [".pdf"]
    },
    "agentic_reader": {
      "name": "Agentic Document Reader (LandingAI)",
      "available": true,
      "features": ["Structured data extraction", "Table/chart processing", "Visual element detection", "Hierarchical JSON output", "Long document support"],
      "supported_formats": [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"],
      "api_key_required": true
    }
  },
  "sample_documents": [
    {
      "filename": "sampledoc.pdf",
      "path": "/path/to/sampledoc.pdf",
      "type": "pdf"
    }
  ]
}
```

### POST /api/chat/document-reader-comparison/

Compares different document readers on the same document.

**Request:**
```json
{
  "file_path": "/path/to/document.pdf"
}
```

**Response:**
```json
{
  "status": "success",
  "file_path": "/path/to/document.pdf",
  "file_type": ".pdf",
  "comparison_results": {
    "pdf_reader": {
      "status": "success",
      "content_length": 1234,
      "content_preview": "Document content preview...",
      "metadata": {...},
      "processing_time": "N/A"
    },
    "agentic_reader": {
      "status": "success",
      "content_length": 1234,
      "content_preview": "Document content preview...",
      "structured_data_count": 5,
      "chunk_types": ["text", "table", "image"],
      "metadata": {...},
      "processing_time": "N/A"
    }
  }
}
```

## Usage Examples

### Using the AgenticDocumentReader Class Directly

```python
from services.agentic_rag.document_readers.agentic_document_reader import AgenticDocumentReader

# Initialize the reader
reader = AgenticDocumentReader(api_key="your_api_key")

# Extract content from a document
result = reader.extract_content("path/to/document.pdf")

# Extract with visualizations
result_with_viz = reader.extract_with_visualization(
    "path/to/document.pdf",
    output_dir="./visualizations"
)

# Extract with grounding images
result_with_groundings = reader.extract_groundings(
    "path/to/document.pdf",
    grounding_save_dir="./groundings"
)

# Batch process multiple documents
results = reader.batch_extract([
    "path/to/doc1.pdf",
    "path/to/doc2.pdf"
])
```

## Features Comparison

| Feature | PDF Reader (PyMuPDF) | Agentic Document Reader |
|---------|---------------------|------------------------|
| Text Extraction | ✅ | ✅ |
| Table Detection | ✅ | ✅ |
| Image Extraction | ✅ | ✅ |
| Structured Data | ❌ | ✅ |
| Visual Elements | ❌ | ✅ |
| Chart Processing | ❌ | ✅ |
| Long Documents | ✅ | ✅ |
| Multiple Formats | PDF only | PDF, Images |
| API Dependency | ❌ | ✅ |

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure `agentic-doc` is installed:
   ```bash
   pip install agentic-doc==0.3.3
   ```

2. **API Key Error**: Ensure your `LANDINGAI_API_KEY` environment variable is set correctly.

3. **Rate Limits**: The Agentic Document Reader automatically handles rate limits with retries.

4. **File Format Support**: Check that your file format is supported by the reader you're trying to use.

### Error Messages

- `"Agentic Document Reader not initialized (missing API key)"`: Set the `LANDINGAI_API_KEY` environment variable.
- `"File format .xyz not supported"`: Use a supported file format (PDF, PNG, JPG, etc.).
- `"No results returned from Agentic Document Extraction"`: Check your API key and file accessibility.

## Next Steps

1. Test the comparison page with different document types
2. Integrate the Agentic Document Reader into your document processing pipeline
3. Explore advanced features like visualizations and grounding images
4. Consider using batch processing for multiple documents

For more information about the LandingAI Agentic Document Extraction API, visit their [documentation](https://github.com/landing-ai/agentic-doc).
