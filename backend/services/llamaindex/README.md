# LlamaIndex RAG Service

A comprehensive RAG (Retrieval-Augmented Generation) service built with LlamaIndex and ChromaDB, providing multiple advanced retrieval strategies for document-based question answering.

## Features

- **Multiple Retrievers**: Vector, BM25, Document Summary, Auto Merging, Recursive, and Query Fusion retrievers
- **OpenAI Integration**: Uses OpenAI LLM and embeddings
- **ChromaDB Storage**: Persistent vector storage with ChromaDB
- **Document Loading**: Support for various document formats
- **Caching**: Intelligent caching of retrievers and query engines
- **Flexible Configuration**: Easy to configure and extend

## Installation

The required dependencies are already added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:
- `llama-index==0.12.49`
- `llama-index-embeddings-openai==0.3.0`
- `llama-index-llms-openai==0.3.0`
- `llama-index-retrievers-bm25==0.5.2`
- `llama-index-vector-stores-chroma==0.3.0`
- `llama-index-embeddings-huggingface==0.5.5`
- `sentence-transformers==5.0.0`
- `rank-bm25==0.2.2`
- `PyStemmer==2.2.0.3`

## Configuration

Make sure you have the following environment variables set in your Django settings:

```python
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_MODEL_NAME = "gpt-3.5-turbo"  # or "gpt-4"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_TEMPERATURE = 0.1
OPENAI_MAX_TOKENS = 4096
```

## Quick Start

### Basic Usage

```python
from backend.services.llamaindex.rag_service import get_llamaindex_rag_service
from backend.services.llamaindex.document_loader import create_sample_documents

# Create sample documents
documents = create_sample_documents("ai")

# Create RAG service
rag_service = get_llamaindex_rag_service("my_collection")

# Load documents
rag_service.load_documents(documents)

# Search with vector retriever
results = rag_service.search_with_retriever("vector", "What is machine learning?", similarity_top_k=3)

# Query with vector engine
response = rag_service.query_with_engine("vector", "What is machine learning?", similarity_top_k=3)
print(response)
```

### Available Retrievers

1. **Vector Index Retriever**: Semantic search using embeddings
2. **BM25 Retriever**: Keyword-based search with advanced ranking
3. **Document Summary Retriever**: Uses document summaries for filtering
4. **Auto Merging Retriever**: Hierarchical context preservation
5. **Recursive Retriever**: Multi-level reference following
6. **Query Fusion Retriever**: Multi-query enhancement with fusion strategies

### Available Query Engines

All retrievers have corresponding query engines for end-to-end RAG:

- `vector`
- `bm25` (if BM25 dependencies are installed)
- `document_summary_llm`
- `document_summary_embedding`
- `auto_merging`
- `recursive`
- `query_fusion`

## Advanced Usage

### Using Different Retrievers

```python
# BM25 Retriever
results = rag_service.search_with_retriever("bm25", "machine learning algorithms", similarity_top_k=3)

# Document Summary Retriever
results = rag_service.search_with_retriever("document_summary_llm", "What is AI?", top_k=2)

# Auto Merging Retriever
results = rag_service.search_with_retriever("auto_merging", "How do neural networks work?", 
                                          chunk_sizes=[512, 256, 128], similarity_top_k=4)

# Query Fusion Retriever
results = rag_service.search_with_retriever("query_fusion", "What are ML approaches?", 
                                          mode="reciprocal_rerank", similarity_top_k=3, num_queries=4)
```

### Using Query Engines

```python
# Vector Query Engine
response = rag_service.query_with_engine("vector", "What is machine learning?", similarity_top_k=3)

# Document Summary Query Engine
response = rag_service.query_with_engine("document_summary_llm", "What is AI?", top_k=2)

# Query Fusion Query Engine
response = rag_service.query_with_engine("query_fusion", "What are ML approaches?", 
                                       mode="reciprocal_rerank", similarity_top_k=3, num_queries=4)
```

### Loading Custom Documents

```python
from llama_index.core import Document
from backend.services.llamaindex.document_loader import get_llamaindex_document_loader

# Load from file
loader = get_llamaindex_document_loader()
documents = loader.load_document("path/to/your/document.pdf")

# Load from directory
documents = loader.load_directory("path/to/documents/")

# Create custom documents
custom_docs = [
    Document(
        text="Your document content here",
        metadata={"source": "custom", "type": "example"}
    )
]

rag_service.load_documents(custom_docs)
```

## Service Management

### Getting Service Information

```python
info = rag_service.get_service_info()
print(f"Document count: {info['document_count']}")
print(f"Available retrievers: {info['available_retrievers']}")
print(f"Available engines: {info['available_engines']}")
```

### Cache Management

```python
# Clear caches
rag_service.clear_caches()

# Clear collection
rag_service.clear_collection()
```

## Retriever Types and Use Cases

### Vector Index Retriever
- **Best for**: General semantic search, finding conceptually related content
- **Use case**: "What is machine learning?" → finds documents about ML concepts

### BM25 Retriever
- **Best for**: Exact keyword matching, technical documentation
- **Use case**: "neural networks deep learning" → finds documents with these exact terms

### Document Summary Retriever
- **Best for**: Large document collections, efficient document filtering
- **Use case**: "What are the different types of learning?" → filters relevant documents first

### Auto Merging Retriever
- **Best for**: Long documents, context preservation
- **Use case**: "How do neural networks work?" → retrieves larger context chunks

### Recursive Retriever
- **Best for**: Documents with references, citations, interconnected content
- **Use case**: "What are AI applications?" → follows document references

### Query Fusion Retriever
- **Best for**: Complex queries, multiple query formulations
- **Use case**: "What are the main approaches to machine learning?" → generates multiple query variations

## Fusion Strategies

The Query Fusion Retriever supports three fusion strategies:

1. **Reciprocal Rank Fusion (RRF)**: Most robust, rank-based, scale-invariant
2. **Relative Score**: Preserves confidence information, normalizes by max score
3. **Distribution-Based**: Most sophisticated, statistical normalization

## Testing

Run the test suite:

```python
from backend.services.llamaindex.test_rag_service import main
main()
```

Run examples:

```python
from backend.services.llamaindex.example_usage import main
main()
```

## File Structure

```
backend/services/llamaindex/
├── __init__.py
├── base_service.py              # Base service with OpenAI integration
├── vector_retriever.py          # Vector Index Retriever
├── bm25_retriever.py            # BM25 Retriever
├── document_summary_retriever.py # Document Summary Retriever
├── auto_merging_retriever.py    # Auto Merging Retriever
├── recursive_retriever.py       # Recursive Retriever
├── query_fusion_retriever.py    # Query Fusion Retriever
├── rag_service.py               # Main RAG service
├── document_loader.py           # Document loading utilities
├── test_rag_service.py          # Test suite
├── example_usage.py             # Usage examples
└── README.md                    # This file
```

## Error Handling

The service includes comprehensive error handling:

- Missing dependencies (BM25, PyStemmer)
- Invalid retriever types
- Document loading failures
- OpenAI API errors
- ChromaDB connection issues

## Performance Considerations

- **Caching**: Retrievers and query engines are cached for better performance
- **Chunk Sizes**: Adjust chunk sizes based on your document types
- **Top-K Values**: Balance between recall and precision
- **Async Processing**: Available for Query Fusion Retriever

## Troubleshooting

### Common Issues

1. **BM25 Not Available**: Install `llama-index-retrievers-bm25` and `PyStemmer`
2. **OpenAI API Errors**: Check your API key and model configuration
3. **ChromaDB Issues**: Ensure the `chroma_db` directory is writable
4. **Memory Issues**: Reduce chunk sizes or document count

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Contributing

To add new retrievers:

1. Create a new retriever file following the existing pattern
2. Add the retriever to the main RAG service
3. Update the test suite
4. Add documentation

## License

This service is part of the finance-assist project and follows the same license terms.
