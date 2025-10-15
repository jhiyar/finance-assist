# Enhanced Agentic-RAG (EAg-RAG) Implementation

This implementation provides a comprehensive Enhanced Agentic-RAG workflow based on the Uber Engineering blog post "Enhanced Agentic-RAG: What If Chatbots Could Deliver Near-Human Precision?". The system combines enriched document processing, hybrid retrieval, and LLM-powered agents orchestrated via LangGraph.

## 🏗️ Architecture Overview

The Enhanced Agentic-RAG system consists of two main pipelines:

### 1. Offline Pipeline (Document Processing)
- **Document Loading**: Supports PDF and text files
- **Content Extraction**: Recursive extraction of paragraphs, tables, and structure
- **LLM Enrichment**: Generates summaries, keywords, and FAQs for each chunk
- **Chunking**: Intelligent chunking with metadata preservation
- **Embedding Generation**: Creates vector embeddings using SentenceTransformers
- **Vector Store**: Stores embeddings in ChromaDB for fast similarity search
- **Artifact Storage**: Saves processing results for online pipeline

### 2. Online Pipeline (Query Processing)
- **Query Optimization**: LLM agent refines ambiguous queries and breaks complex queries into sub-queries
- **Source Identification**: LLM agent selects relevant documents from available corpus
- **Hybrid Retrieval**: Combines vector search and BM25 keyword search
- **Post-Processing**: De-duplication, re-ordering, and quality assessment
- **Answer Generation**: LLM generates comprehensive answers with citations
- **Evaluation**: Optional LLM-as-Judge evaluation against golden references

## 📁 Project Structure

```
backend/services/agentic_rag/
├── __init__.py
├── agentic_rag_service.py          # Main service class
├── hybrid_retriever.py             # Hybrid retrieval implementation
├── document_readers/               # Document processing components
│   ├── __init__.py
│   ├── enriched_document_processor.py
│   ├── pdf_reader.py
│   └── text_reader.py
├── agents/                         # LLM-powered agents
│   ├── __init__.py
│   ├── query_optimizer.py
│   ├── source_identifier.py
│   ├── post_processor.py
│   ├── answer_generator.py
│   └── evaluator.py
└── langgraph/                      # LangGraph workflow
    ├── __init__.py
    ├── workflow_state.py
    └── agentic_rag_graph.py
```

## 🚀 Quick Start

### 1. Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `langgraph==0.2.60` - Workflow orchestration
- `faiss-cpu==1.8.0` - Vector similarity search
- `sentence-transformers==5.0.0` - Embedding generation
- `rank-bm25==0.2.2` - BM25 keyword search
- `PyMuPDF==1.25.2` - PDF processing
- `pandas` - Data processing

### 2. Basic Usage

```python
from services.agentic_rag.agentic_rag_service import AgenticRAGService

# Initialize the service
service = AgenticRAGService(
    documents_directory="sample_documents",
    model_name="gpt-4o-mini",
    enable_evaluation=False
)

# Process documents (offline pipeline)
result = service.initialize_documents()
print(f"Processing result: {result}")

# Process a query (online pipeline)
query_result = service.process_query("What are the main topics in the documents?")
print(f"Answer: {query_result['answer']}")
print(f"Confidence: {query_result['confidence']}")
print(f"Sources: {query_result['sources_used']}")
```

### 3. Integration with Django Views

The system is integrated with the Django chat view. To use Enhanced Agentic-RAG:

```python
# In your request, set retriever_type to 'agentic_rag'
response = requests.post('/chat/chat/', {
    'message': 'What are the company policies?',
    'retriever_type': 'agentic_rag'
})
```

## 🔧 Configuration

### Service Configuration

```python
service = AgenticRAGService(
    documents_directory="sample_documents",  # Path to documents
    model_name="gpt-4o-mini",               # OpenAI model
    enable_evaluation=False,                 # Enable LLM-as-Judge
    collection_name="agentic_rag_documents" # Vector store name
)
```

### Document Processor Configuration

```python
processor = EnrichedDocumentProcessor(
    embedding_model="all-MiniLM-L6-v2",  # SentenceTransformer model
    chunk_size=1000,                     # Chunk size
    chunk_overlap=200,                   # Chunk overlap
    collection_name="documents"          # Collection name
)
```

### Hybrid Retriever Configuration

```python
retriever = HybridRetriever(
    embedding_model="all-MiniLM-L6-v2",  # Embedding model
    vector_weight=0.7,                   # Vector search weight
    bm25_weight=0.3,                     # BM25 search weight
    top_k=10                             # Number of results
)
```

## 📊 API Endpoints

### Chat Endpoint
- **URL**: `/chat/chat/`
- **Method**: POST
- **Parameters**:
  - `message`: User query
  - `retriever_type`: Set to `'agentic_rag'` for Enhanced Agentic-RAG

### Test Endpoint
- **URL**: `/chat/agentic-rag-test/`
- **Method**: GET/POST
- **GET**: Returns service information and available documents
- **POST**: Test query processing

## 🧪 Testing

Run the test script to verify the implementation:

```bash
cd backend
python test_agentic_rag.py
```

The test script will:
1. Initialize the Enhanced Agentic-RAG service
2. Process sample documents
3. Test individual components
4. Run sample queries
5. Display results and statistics

## 🔍 Workflow Details

### LangGraph Workflow

The system uses LangGraph to orchestrate the following nodes:

1. **Query Optimizer**: Refines user queries
2. **Source Identifier**: Selects relevant documents
3. **Hybrid Retriever**: Performs vector + BM25 search
4. **Post-Processor**: Cleans and ranks results
5. **Answer Generator**: Creates final answer
6. **Evaluator**: Optional quality assessment

### State Management

The workflow state includes:
- Original and optimized queries
- Selected documents and retrieval results
- Processing reasoning and confidence scores
- Generated answers and citations
- Evaluation results (if enabled)

## 📈 Performance Features

### Hybrid Retrieval
- Combines semantic (vector) and keyword (BM25) search
- Configurable weighting between retrieval methods
- Automatic score normalization and ranking

### Document Enrichment
- LLM-generated summaries for each chunk
- Keyword extraction for better retrieval
- FAQ generation for improved matching

### Quality Assessment
- Post-processing with duplicate removal
- Document reordering by original position
- Quality scoring for retrieved documents

## 🛠️ Customization

### Adding New Document Types

Extend the document readers:

```python
class CustomReader:
    def extract_content(self, file_path: str) -> str:
        # Implement custom extraction logic
        pass
```

### Custom Agents

Create new agents by extending the base classes:

```python
class CustomAgent:
    def __init__(self, model_name: str):
        self.llm = get_openai_service().get_langchain_llm()
    
    def process(self, input_data: Any) -> Any:
        # Implement custom processing logic
        pass
```

### Custom Workflow Nodes

Add new nodes to the LangGraph workflow:

```python
def custom_node(state: AgenticRAGState) -> AgenticRAGState:
    # Implement custom processing
    return state

# Add to workflow
workflow.add_node("custom_node", custom_node)
```

## 🔒 Security Considerations

- API keys are managed through environment variables
- Document processing is done locally
- No sensitive data is sent to external services (except OpenAI)
- Vector stores are stored locally

## 📝 Logging

The system provides comprehensive logging:

```python
import logging
logging.getLogger("services.agentic_rag").setLevel(logging.INFO)
```

Log levels:
- `INFO`: General workflow progress
- `WARNING`: Non-critical issues
- `ERROR`: Critical failures

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key**: Ensure `OPENAI_API_KEY` is set
2. **Document Processing**: Check file permissions and formats
3. **Memory Issues**: Reduce chunk size or document count
4. **Import Errors**: Verify all dependencies are installed

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 References

- [Uber Engineering Blog: Enhanced Agentic-RAG](https://www.uber.com/en-GB/blog/enhanced-agentic-rag/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [SentenceTransformers Documentation](https://www.sbert.net/)

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility

## 📄 License

This implementation is part of the finance-assist project and follows the same licensing terms.
