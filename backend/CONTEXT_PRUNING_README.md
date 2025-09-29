# Context Pruning Service

A comprehensive context pruning service for the Finance Assist application that implements multiple strategies to remove irrelevant content and improve retrieval quality in RAG (Retrieval-Augmented Generation) systems.

## Overview

Context pruning is a critical component in modern RAG systems that helps:
- **Reduce noise**: Remove irrelevant content that can confuse the LLM
- **Improve efficiency**: Process only the most relevant information
- **Enhance accuracy**: Focus on content that directly relates to the query
- **Optimize costs**: Reduce token usage in LLM calls

## Features

### 1. Multiple Pruning Strategies

#### LLM Compression (`LLMCompressionPruner`)
- Uses LLMChainExtractor to intelligently extract only relevant parts
- Leverages GPT models to understand context and relevance
- Most intelligent but slower and more expensive
- Best for high-quality, precise pruning

#### Relevance Filtering (`RelevanceFilterPruner`)
- Uses semantic similarity to filter documents
- Configurable similarity thresholds
- Fast and efficient for large document sets
- Good balance of speed and quality

#### Metadata Filtering (`MetadataFilterPruner`)
- Filters based on document metadata attributes
- Fastest method for pre-filtering
- Useful for structured document collections
- Can be combined with other methods

#### Hybrid Pruning (`HybridContextPruner`)
- Combines multiple strategies in sequence
- Configurable pipeline: metadata → relevance → LLM compression
- Optimal balance of speed and quality
- Recommended for production use

### 2. Context-Aware Chunking

The `ContextAwareChunker` integrates pruning directly into the document chunking process:
- Creates semantic chunks based on content similarity
- Applies context pruning during chunking
- Optimizes chunk sizes based on relevance
- Maintains document structure while improving quality

### 3. Frontend Integration

- **Context Pruning Panel**: Interactive UI for configuring and running pruning
- **Real-time Results**: Live feedback on pruning efficiency and results
- **Multiple Methods**: Easy switching between different pruning strategies
- **Configuration Options**: Granular control over pruning parameters

## Installation

The context pruning service requires the following dependencies (already included in `requirements.txt`):

```bash
# Core dependencies
langchain>=0.3.27
langchain-openai>=0.2.14
sentence-transformers>=5.1.0
scikit-learn>=1.7.2
numpy>=2.3.2

# Optional for advanced features
tiktoken>=0.11.0  # For token counting
```

## Usage

### Backend API

#### Context Pruning Endpoint

```http
POST /api/document-processing/context-pruning/
Content-Type: application/json

{
  "documents": [
    {
      "content": "Document content here...",
      "metadata": {"type": "financial_report", "year": "2024"}
    }
  ],
  "query": "financial performance and revenue",
  "method": "hybrid",
  "config": {
    "similarity_threshold": 0.7,
    "top_k": 5,
    "use_metadata_filter": true,
    "use_relevance_filter": true,
    "use_llm_compression": false
  }
}
```

#### Response Format

```json
{
  "pruned_documents": [
    {
      "content": "Pruned document content...",
      "metadata": {"type": "financial_report", "year": "2024"}
    }
  ],
  "stats": {
    "original_count": 10,
    "pruned_count": 3,
    "compression_ratio": 0.3,
    "processing_time": 1.25,
    "pruning_method": "hybrid",
    "efficiency": "70.0% reduction"
  },
  "metadata": {
    "pruning_steps": [
      {
        "step": "metadata_filter",
        "original_count": 10,
        "pruned_count": 8,
        "compression_ratio": 0.8,
        "processing_time": 0.1
      }
    ]
  }
}
```

### Python Service Usage

```python
from services.context_pruning_service import get_context_pruning_service
from langchain_core.documents import Document

# Initialize service
service = get_context_pruning_service(
    similarity_threshold=0.7,
    model_name='gpt-4o-mini',
    temperature=0.0
)

# Create sample documents
documents = [
    Document(
        page_content="Financial report content...",
        metadata={"type": "financial_report"}
    )
]

# Apply pruning
result = service.prune_context(
    documents=documents,
    query="financial performance",
    method="hybrid"
)

print(f"Reduced from {result.original_count} to {result.pruned_count} documents")
print(f"Compression ratio: {result.compression_ratio:.2f}")
```

### Frontend Component Usage

```jsx
import { ContextPruningPanel } from '../components/ContextPruningPanel';
import { useContextPruning } from '../hooks/useContextPruning';

function DocumentProcessingPage() {
  const { pruneContext, isProcessing, pruningResult } = useContextPruning();
  
  const handlePruning = async (documents, query, method, config) => {
    const result = await pruneContext(documents, query, method, config);
    console.log('Pruning completed:', result);
  };

  return (
    <ContextPruningPanel
      documents={documents}
      onPruningComplete={handlePruning}
    />
  );
}
```

## Configuration Options

### Method-Specific Configuration

#### Relevance Filtering
```python
config = {
    "method": "relevance_filter",
    "similarity_threshold": 0.7,  # 0.0 to 1.0
    "top_k": 5,                   # Optional: limit results
    "embedding_model": "all-MiniLM-L6-v2"
}
```

#### LLM Compression
```python
config = {
    "method": "llm_compression",
    "model_name": "gpt-4o-mini",  # or "gpt-4o", "gpt-3.5-turbo"
    "temperature": 0.0,           # 0.0 to 2.0
    "max_tokens": 4000
}
```

#### Metadata Filtering
```python
config = {
    "method": "metadata_filter",
    "metadata_filters": {
        "document_type": "financial_report",
        "year": "2024"
    },
    "require_all_filters": True  # All filters must match
}
```

#### Hybrid Pruning
```python
config = {
    "method": "hybrid",
    "use_metadata_filter": True,
    "use_relevance_filter": True,
    "use_llm_compression": False,
    "similarity_threshold": 0.7,
    "top_k": 5,
    "model_name": "gpt-4o-mini"
}
```

### Context-Aware Chunker Configuration

```python
chunker_config = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "semantic_threshold": 0.7,
    "min_chunk_size": 200,
    "max_chunk_size": 2000,
    "enable_pruning": True,
    "pruning_method": "relevance_filter",
    "pruning_config": {
        "similarity_threshold": 0.7,
        "top_k": 5
    }
}
```

## Performance Characteristics

| Method | Speed | Quality | Cost | Use Case |
|--------|-------|---------|------|----------|
| Metadata Filter | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | Pre-filtering, structured data |
| Relevance Filter | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | General purpose, balanced |
| LLM Compression | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | High quality, precise pruning |
| Hybrid | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Production, optimal balance |

## Best Practices

### 1. Choose the Right Method
- **Fast filtering**: Use metadata filtering for initial document selection
- **Balanced approach**: Use relevance filtering for most use cases
- **High quality**: Use LLM compression for critical applications
- **Production**: Use hybrid method for optimal results

### 2. Optimize Parameters
- **Similarity threshold**: Start with 0.7, adjust based on results
- **Top K**: Use when you need a specific number of results
- **Chunk sizes**: Balance between context and efficiency
- **Model selection**: Use faster models for real-time applications

### 3. Monitor Performance
- Track compression ratios and processing times
- Monitor quality of pruned results
- Adjust parameters based on user feedback
- Use evaluation metrics to measure effectiveness

### 4. Error Handling
- Always provide fallback options
- Handle cases where pruning fails
- Log errors for debugging
- Return original documents if pruning fails

## Testing

Run the test suite to verify functionality:

```bash
cd backend
python test_context_pruning.py
```

The test suite includes:
- Relevance filtering with different thresholds
- Metadata filtering with various criteria
- Hybrid pruning pipeline
- Context-aware chunker integration
- Performance benchmarking

## Integration with Existing Systems

### Document Processing Pipeline
1. **Upload**: Document is uploaded and parsed
2. **Chunking**: Context-aware chunker creates semantic chunks
3. **Pruning**: Context pruning removes irrelevant content
4. **Storage**: Pruned chunks are stored in vector database
5. **Retrieval**: Only relevant chunks are retrieved for queries

### Chat System Integration
The context pruning service integrates with the existing chat system:
- Prunes retrieved documents before sending to LLM
- Improves response quality and reduces costs
- Maintains conversation context and relevance

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install sentence-transformers scikit-learn
   ```

2. **OpenAI API Errors**
   - Check API key configuration
   - Verify model availability
   - Monitor rate limits

3. **Memory Issues**
   - Reduce batch sizes for large documents
   - Use smaller embedding models
   - Enable garbage collection

4. **Performance Issues**
   - Use faster embedding models
   - Reduce similarity thresholds
   - Enable metadata pre-filtering

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('services.context_pruning_service').setLevel(logging.DEBUG)
```

## Future Enhancements

- [ ] **Adaptive Thresholds**: Automatically adjust thresholds based on query type
- [ ] **Multi-language Support**: Support for non-English documents
- [ ] **Custom Embeddings**: Integration with domain-specific embedding models
- [ ] **Batch Processing**: Efficient processing of large document collections
- [ ] **Caching**: Cache pruning results for repeated queries
- [ ] **Metrics Dashboard**: Real-time monitoring of pruning performance

## Contributing

When contributing to the context pruning service:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Consider performance implications
5. Maintain backward compatibility

## License

This context pruning service is part of the Finance Assist application and follows the same licensing terms.
