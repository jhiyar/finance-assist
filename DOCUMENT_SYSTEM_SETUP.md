# Document Management System - Quick Setup Guide

## 🎉 What's New

Your finance-assist application now has a complete document management system with:

✅ **Document Upload & Management** - Upload PDFs, DOCX, TXT files via beautiful UI  
✅ **Automatic Chunking** - Documents are automatically split into optimized chunks  
✅ **ChromaDB Integration** - All chunks stored with embeddings in ChromaDB  
✅ **Hybrid Search** - Combines vector similarity + BM25 keyword search  
✅ **Document Viewer** - Browse documents and view individual chunks  
✅ **Chat Integration** - Query uploaded documents via chat interface  

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key new dependencies:
- `chromadb==1.0.20` - Vector database
- `sentence-transformers==5.1.0` - Local embeddings
- `rank-bm25==0.2.2` - BM25 search
- `python-docx==1.1.2` - DOCX file support

### 2. Run Migrations (if needed)

```bash
python manage.py migrate
```

### 3. Start Backend

```bash
python manage.py runserver
```

The ChromaDB storage will be automatically created at `backend/chroma_db/`

### 4. Start Frontend

```bash
cd ../frontend
npm install  # if you haven't already
npm run dev
```

## 📝 How to Use

### Upload Documents

1. Navigate to **Documents** page (http://localhost:5173/documents)
2. Click "Choose File" or drag & drop
3. Supported formats: PDF, DOCX, TXT, MD
4. Click "Upload"
5. Wait for processing (automatic chunking + embedding generation)

### View Document Details

1. From Documents page, click the eye icon (👁️) on any document
2. See document metadata (size, type, upload date, chunk count)
3. Browse all chunks with search functionality
4. Click on any chunk to view full details
5. Copy chunk content to clipboard

### Query Documents via Chat

1. Navigate to **Chat** page (http://localhost:5173/chat)
2. Type your question
3. The system automatically uses **hybrid search** (vector + BM25)
4. Get answers with source citations and relevance scores

**Example queries:**
- "What is the refund policy?"
- "Tell me about payment methods"
- "What are the company's privacy practices?"

### Available Retriever Types

In the chat, you can specify the retriever type (default is `hybrid_search`):

```javascript
// Frontend chat component can set retriever_type
{
  message: "your question",
  retriever_type: "hybrid_search"  // Options: hybrid_search, agentic_rag, vector_store
}
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Frontend (React) │
│  - DocumentListPage     │
│  - DocumentDetailPage   │
│  - ChatInterface        │
└─────────┬───────┘
          │
          │ HTTP API
          │
┌─────────▼───────┐
│  Backend (Django) │
│  - Document Upload API  │
│  - Chunks API           │
│  - Chat API (hybrid)    │
└─────────┬───────┘
          │
          │
┌─────────▼───────────────┐
│  ChromaDB Service       │
│  - Document Loading     │
│  - Chunking             │
│  - Embedding Generation │
│  - Vector Search        │
│  - BM25 Search          │
│  - Hybrid Ranking       │
└─────────────────────────┘
          │
          │
┌─────────▼───────────────┐
│  ChromaDB Storage       │
│  (./chroma_db/)         │
│  - Embeddings           │
│  - Metadata             │
│  - Persistent Index     │
└─────────────────────────┘
```

## 📁 File Structure

### Backend Files Added/Modified

```
backend/
├── services/
│   └── chromadb_service.py          # NEW - ChromaDB integration
├── document_processing/
│   ├── views.py                      # MODIFIED - Added ChromaDB processing
│   └── urls.py                       # MODIFIED - Added chunks endpoint
├── chat/
│   └── views.py                      # MODIFIED - Added hybrid search
├── requirements.txt                  # MODIFIED - Added dependencies
├── chroma_db/                        # NEW - ChromaDB storage (auto-created)
└── DOCUMENT_MANAGEMENT_README.md     # NEW - Comprehensive docs
```

### Frontend Files Added/Modified

```
frontend/src/
├── features/document-processing/components/
│   ├── DocumentListPage.jsx         # NEW - Document list with upload
│   ├── DocumentDetailPage.jsx       # NEW - Document details with chunks
│   └── index.js                     # MODIFIED - Export new components
├── mainRoutes.jsx                   # MODIFIED - Added new routes
└── features/chat/components/
    └── ChatInterface.jsx            # Uses hybrid search by default
```

## 🔧 Configuration

### Environment Variables

Create/update `backend/.env`:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (defaults shown)
CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=finance_documents
DEFAULT_CHUNK_SIZE=1000
DEFAULT_CHUNK_OVERLAP=200
```

### Hybrid Search Weights

Edit `backend/services/chromadb_service.py` to adjust:

```python
def hybrid_search(
    self,
    query: str,
    k: int = 5,
    vector_weight: float = 0.7,    # Adjust this (semantic similarity)
    bm25_weight: float = 0.3,      # Adjust this (keyword matching)
    ...
):
```

**Recommendations:**
- **General queries**: 70% vector, 30% BM25 (default)
- **Technical/keyword queries**: 40% vector, 60% BM25
- **Conceptual queries**: 90% vector, 10% BM25

## 🧪 Testing

### 1. Test Document Upload

```bash
# Using curl
curl -X POST http://localhost:8000/api/document-processing/documents/upload/ \
  -F "file=@path/to/test.pdf" \
  -F "name=test.pdf"

# Or use the frontend at /documents
```

### 2. Test Chunks Retrieval

```bash
# Get document chunks
curl http://localhost:8000/api/document-processing/documents/<DOCUMENT_ID>/chunks/

# Or click on document in frontend
```

### 3. Test Hybrid Search

```bash
# Via chat API
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the return policy?", "retriever_type": "hybrid_search"}'

# Or use the chat interface at /chat
```

### 4. Verify ChromaDB Storage

```bash
# Python shell
python manage.py shell

>>> from services.chromadb_service import get_chromadb_service
>>> service = get_chromadb_service()
>>> stats = service.get_collection_stats()
>>> print(stats)
{
  'collection_name': 'finance_documents',
  'total_chunks': 42,
  'embedding_model': 'SentenceTransformer(...)',
  'chunk_size': 1000,
  'chunk_overlap': 200,
  'bm25_enabled': True
}
```

## 🎯 API Endpoints

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/document-processing/documents/upload/` | Upload document |
| GET | `/api/document-processing/documents/` | List all documents |
| GET | `/api/document-processing/documents/<id>/` | Get document details |
| DELETE | `/api/document-processing/documents/<id>/` | Delete document |
| GET | `/api/document-processing/documents/<id>/chunks/` | Get document chunks |

### Chat with Hybrid Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/` | Send message with hybrid search |

Request body:
```json
{
  "message": "your question",
  "retriever_type": "hybrid_search"
}
```

## 📊 Features Breakdown

### Hybrid Search Explained

**Vector Search (70% weight)**
- Uses SentenceTransformers to encode query and documents
- Finds semantically similar content
- Good for: paraphrases, conceptual matches

**BM25 Search (30% weight)**  
- Traditional keyword-based ranking (TF-IDF variant)
- Finds exact term matches with importance weighting
- Good for: technical terms, specific phrases

**Hybrid Combination**
- Normalizes both scores to [0, 1]
- Combines with weighted sum
- Returns top-k results by combined score

### Document Processing Pipeline

1. **Upload** → Document saved to media storage
2. **Load** → Content extracted (PDF/DOCX/TXT parser)
3. **Chunk** → Split into 1000-char chunks with 200 overlap
4. **Embed** → Generate embeddings (SentenceTransformers or OpenAI)
5. **Store** → Save to ChromaDB with metadata
6. **Index** → Build/update BM25 index
7. **Ready** → Document available for hybrid search

## 🐛 Troubleshooting

### ChromaDB directory not created
```bash
# Manually create
mkdir backend/chroma_db
```

### "No module named chromadb"
```bash
pip install chromadb==1.0.20
```

### "SSL certificate error" with SentenceTransformers
- The system automatically falls back to OpenAI embeddings
- Make sure `OPENAI_API_KEY` is set in `.env`

### Documents not appearing after upload
- Check Django logs for errors
- Verify ChromaDB service initialized correctly
- Check `document.processed` is `True` in database

### Hybrid search returns no results
- Ensure document has been processed
- Check ChromaDB collection: `service.get_collection_stats()`
- Try uploading a simple text file first

## 📚 Additional Resources

- **Full Documentation**: `backend/DOCUMENT_MANAGEMENT_README.md`
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Sentence Transformers**: https://www.sbert.net/
- **BM25 Algorithm**: https://en.wikipedia.org/wiki/Okapi_BM25

## 🎓 Next Steps

1. **Upload test documents** via `/documents`
2. **View chunks** by clicking on a document
3. **Query via chat** at `/chat`
4. **Adjust weights** in `chromadb_service.py` for your use case
5. **Add more documents** to build your knowledge base

## 💡 Pro Tips

- **Upload PDFs** for best extraction quality
- **Use descriptive filenames** - they're used as document names
- **Test queries** with both technical and conceptual terms
- **Monitor chunk counts** - 10-50 chunks per document is ideal
- **Tune hybrid weights** based on your document types

---

**Ready to go!** 🚀 Start by uploading your first document at `/documents`

