# Document Management System with ChromaDB Integration

This document describes the document management system with automatic chunking, embedding generation, and hybrid search capabilities.

## Overview

The system provides:

1. **Document Upload & Processing**: Automatically chunks documents and stores embeddings in ChromaDB
2. **Hybrid Search**: Combines vector similarity search with BM25 keyword search for better retrieval
3. **Frontend Interface**: Browse documents, view chunks, and metadata
4. **Chat Integration**: Query documents using hybrid search via chat interface

## Architecture

### Backend Components

#### 1. ChromaDB Service (`services/chromadb_service.py`)

The core service that handles:
- Document loading and chunking
- Embedding generation using SentenceTransformers or OpenAI
- Storage in ChromaDB with persistent storage
- Hybrid search combining vector and BM25 retrieval

**Key Features:**
- Persistent ChromaDB storage at `./chroma_db`
- Automatic BM25 index building for keyword search
- Configurable chunk size and overlap
- Support for PDF, DOCX, TXT, and MD files

**Usage:**
```python
from services.chromadb_service import get_chromadb_service

# Get service instance
chromadb = get_chromadb_service()

# Add a document
result = chromadb.add_document(
    file_path="path/to/document.pdf",
    document_id="unique-id",
    document_name="My Document",
    metadata={"author": "John Doe"}
)

# Perform hybrid search
results = chromadb.hybrid_search(
    query="What is the refund policy?",
    k=5,
    vector_weight=0.7,
    bm25_weight=0.3
)

# Get document chunks
chunks = chromadb.get_document_chunks(document_id)
```

#### 2. Document Processing Views (`document_processing/views.py`)

Enhanced with ChromaDB integration:

- **DocumentUploadView**: Automatically processes uploads and stores in ChromaDB
- **DocumentChunksView**: Retrieves chunks for a specific document
- **DocumentDetailView**: Enhanced to delete from ChromaDB on document deletion

**API Endpoints:**
```
POST   /api/document-processing/documents/upload/
GET    /api/document-processing/documents/
GET    /api/document-processing/documents/<uuid:pk>/
DELETE /api/document-processing/documents/<uuid:pk>/
GET    /api/document-processing/documents/<uuid:doc_id>/chunks/
```

#### 3. Chat Integration (`chat/views.py`)

ChatView now supports hybrid search:

**Usage:**
```python
# In chat request
{
    "message": "What is the refund policy?",
    "retriever_type": "hybrid_search"  # Default, recommended
}
```

**Retriever Types:**
- `hybrid_search` (default): Vector + BM25 hybrid search
- `agentic_rag`: Enhanced Agentic-RAG with multi-agent pipeline
- `vector_store`: Simple vector similarity search
- `self_query`: Structured query retriever

### Frontend Components

#### 1. DocumentListPage

**Location:** `frontend/src/features/document-processing/components/DocumentListPage.jsx`

**Features:**
- Upload documents via drag-and-drop or file picker
- View all uploaded documents with metadata
- See processing status and chunk counts
- Navigate to document details
- Delete documents

**Route:** `/documents`

#### 2. DocumentDetailPage

**Location:** `frontend/src/features/document-processing/components/DocumentDetailPage.jsx`

**Features:**
- View document metadata (size, type, upload date, chunk count)
- Browse all chunks with search functionality
- Copy chunk content to clipboard
- View detailed chunk information (ID, metadata, content)
- Modal view for individual chunks

**Route:** `/documents/:documentId`

## Document Processing Pipeline

### Upload Flow

1. **User uploads document** via frontend
2. **Backend receives file** and creates Document record
3. **ChromaDB service processes document:**
   - Loads document using appropriate loader (PDF, DOCX, TXT)
   - Splits into chunks (default: 1000 chars with 200 overlap)
   - Generates embeddings for each chunk
   - Stores in ChromaDB collection
   - Builds/updates BM25 index
4. **Document metadata updated** with chunk count and processing status
5. **Frontend refreshes** to show processed document

### Query Flow (Hybrid Search)

1. **User sends query** via chat interface
2. **ChatView receives request** with `retriever_type: "hybrid_search"`
3. **ChromaDB service performs hybrid search:**
   - **Vector Search**: Generate query embedding, find top-k similar chunks
   - **BM25 Search**: Tokenize query, compute BM25 scores for all documents
   - **Combine Results**: Weighted combination of both scores
   - **Rank & Return**: Return top-k results by hybrid score
4. **Generate Answer**: LLM generates answer based on retrieved context
5. **Return Response** with answer, sources, and search statistics

## Hybrid Search Details

### How It Works

Hybrid search combines two complementary retrieval methods:

1. **Vector Search (Semantic)**
   - Uses embeddings to find semantically similar content
   - Good for conceptual matches and paraphrases
   - Weight: 0.7 (default)

2. **BM25 Search (Keyword)**
   - Traditional keyword-based search with TF-IDF weighting
   - Good for exact term matches and technical queries
   - Weight: 0.3 (default)

### Scoring

```python
hybrid_score = (vector_weight × normalized_vector_score) + 
               (bm25_weight × normalized_bm25_score)
```

Both scores are normalized to [0, 1] before combination.

### Configuration

You can adjust the weights in `ChromaDBService`:

```python
results = chromadb_service.hybrid_search(
    query="your query",
    k=5,                    # Number of results
    vector_weight=0.7,      # Weight for vector search
    bm25_weight=0.3,        # Weight for BM25 search
    filter_metadata={       # Optional metadata filters
        "document_id": "some-uuid"
    }
)
```

## Configuration

### Environment Variables

```env
# OpenAI (for embeddings fallback and LLM)
OPENAI_API_KEY=your_openai_api_key

# ChromaDB (optional, defaults shown)
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=finance_documents

# Document Processing
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
```

### ChromaDB Settings

Edit `services/chromadb_service.py`:

```python
def __init__(
    self,
    collection_name: str = "finance_documents",
    persist_directory: str = "./chroma_db",
    embedding_model: str = "all-MiniLM-L6-v2",  # SentenceTransformer model
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
```

## API Reference

### Upload Document

```http
POST /api/document-processing/documents/upload/
Content-Type: multipart/form-data

file: <file>
name: "document_name"
```

**Response:**
```json
{
  "id": "uuid",
  "name": "document_name",
  "file_type": "pdf",
  "file_size": 1234567,
  "file_size_mb": 1.18,
  "upload_date": "2025-01-01T12:00:00Z",
  "processed": true,
  "metadata": {
    "chunks_count": 15,
    "chromadb_processed": true
  }
}
```

### Get Document Chunks

```http
GET /api/document-processing/documents/<uuid>/chunks/
```

**Response:**
```json
{
  "document_id": "uuid",
  "document_name": "document_name",
  "total_chunks": 15,
  "chunks": [
    {
      "chunk_id": "uuid_chunk_0",
      "content": "chunk content...",
      "metadata": {
        "document_id": "uuid",
        "document_name": "document_name",
        "chunk_index": 0,
        "file_type": "pdf"
      },
      "chunk_index": 0
    }
  ]
}
```

### Chat with Hybrid Search

```http
POST /api/chat/
Content-Type: application/json

{
  "message": "What is the refund policy?",
  "retriever_type": "hybrid_search"
}
```

**Response:**
```json
{
  "type": "text",
  "text": "Based on the documents...",
  "source": "hybrid_search",
  "retriever_type": "hybrid_search",
  "sources": [
    {
      "rank": 1,
      "content_preview": "Our refund policy...",
      "document_name": "policy.pdf",
      "hybrid_score": 0.85,
      "vector_score": 0.82,
      "bm25_score": 0.91
    }
  ],
  "search_stats": {
    "total_results": 5,
    "results_used": 3,
    "search_type": "hybrid (vector + BM25)"
  }
}
```

## Performance Considerations

### Embedding Generation

- **SentenceTransformers** (default): Fast, runs locally, no API costs
- **OpenAI Embeddings** (fallback): High quality, requires API key, costs apply

### Index Building

- BM25 index is rebuilt after each document upload
- For large document sets, consider batch uploads and manual index rebuilding

### Search Performance

- Vector search: O(n) for brute force, O(log n) with HNSW index
- BM25 search: O(n × m) where n = docs, m = query terms
- Hybrid search: Both searches run, results are combined

### Optimization Tips

1. **Batch uploads**: Upload multiple documents before querying
2. **Adjust chunk size**: Larger chunks = fewer embeddings but less granular retrieval
3. **Tune weights**: Adjust vector/BM25 weights based on your use case
4. **Use filters**: Filter by metadata to reduce search space

## Testing

### Backend Testing

```bash
cd backend

# Test ChromaDB service
python manage.py shell
>>> from services.chromadb_service import get_chromadb_service
>>> service = get_chromadb_service()
>>> service.get_collection_stats()

# Test document upload
curl -X POST http://localhost:8000/api/document-processing/documents/upload/ \
  -F "file=@test.pdf" \
  -F "name=test.pdf"

# Test hybrid search via chat
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "test query", "retriever_type": "hybrid_search"}'
```

### Frontend Testing

1. Navigate to `/documents`
2. Upload a test document
3. Verify it appears in the list with processing status
4. Click to view document details
5. Verify chunks are displayed
6. Go to `/chat` and query the uploaded document

## Troubleshooting

### "No results from hybrid search"

- **Check**: Document has been processed (`processed: true`)
- **Check**: ChromaDB collection contains documents
- **Try**: Rebuild BM25 index by re-uploading a document

### "SSL certificate error" when initializing embeddings

- The system automatically falls back to OpenAI embeddings
- Set `OPENAI_API_KEY` in environment variables

### Chunks not appearing in UI

- **Check**: Document has `chromadb_processed: true` in metadata
- **Check**: API endpoint `/documents/<id>/chunks/` returns data
- **Check**: Console for JavaScript errors

### High memory usage

- **Reduce**: `chunk_size` to create fewer, larger chunks
- **Consider**: Using OpenAI embeddings instead of local SentenceTransformers
- **Implement**: Pagination for large document sets

## Future Enhancements

1. **Reranking**: Add cross-encoder reranking for improved accuracy
2. **Query expansion**: Automatic query expansion using LLM
3. **Document summarization**: Generate summaries for each document
4. **Multi-modal**: Support for images and tables in documents
5. **Incremental indexing**: Update index without full rebuild
6. **Analytics**: Track search quality and user queries

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Hybrid Search Paper](https://arxiv.org/abs/2104.08663)

