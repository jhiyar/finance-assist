# LangChain Retrievers Implementation

This backend implements all four types of retrievers from the LangChain notebook:

1. **Vector Store-Backed Retriever**
2. **Multi-Query Retriever**
3. **Self-Querying Retriever**
4. **Parent Document Retriever**

## Setup

### Dependencies
The implementation uses OpenAI for both LLM and embeddings:
- `openai` for LLM functionality
- `langchain-openai` for OpenAI embeddings
- `chromadb` for vector storage
- `langchain` for retriever implementations

### Environment
Make sure you have the RH-Bridging loans PDF file in the backend directory for testing.

## Services

### OpenAI Service
Handles LLM functionality using OpenAI models.

### OpenAI Embedding Service
Generates embeddings using OpenAI's text-embedding-3-small model.

### RetrieverService
Main service that implements all retriever types with the following methods:

- `text_splitter()` - Splits documents into chunks
- `create_vector_store()` - Creates ChromaDB vector store
- `vector_store_retriever()` - Creates vector store-backed retriever
- `multi_query_retriever()` - Creates multi-query retriever
- `self_query_retriever()` - Creates self-querying retriever
- `parent_document_retriever()` - Creates parent document retriever

### DocumentLoader
Utility for loading different document types (PDF, TXT) and creating sample data.

## API Endpoints

### 1. Retriever Demo
**POST** `/chat/retriever-demo`

Test any retriever type with the RH-Bridging loans PDF.

**Request Body:**
```json
{
    "retriever_type": "vector_store",
    "query": "bridging loans",
    "parameters": {
        "search_type": "similarity",
        "k": 3
    }
}
```

**Retriever Types:**
- `vector_store` - Vector Store-Backed Retriever
- `multi_query` - Multi-Query Retriever
- `self_query` - Self-Querying Retriever
- `parent_document` - Parent Document Retriever

### 2. Movies Retriever Demo
**POST** `/chat/movies-retriever-demo`

Test self-querying retriever with movie metadata.

**Request Body:**
```json
{
    "query": "I want to watch a movie rated higher than 8.5"
}
```

### 3. Retriever Examples
**GET** `/chat/retriever-examples`

Get example queries and parameters for all retriever types.

## Usage Examples

### 1. Vector Store-Backed Retriever

```python
from services.retriever_service import get_retriever_service

retriever_service = get_retriever_service()

# Basic similarity search
retriever = retriever_service.vector_store_retriever(search_kwargs={"k": 3})
docs = retriever_service.search_with_retriever(retriever, "bridging loans")

# MMR search
retriever = retriever_service.vector_store_retriever(search_type="mmr")
docs = retriever_service.search_with_retriever(retriever, "financial terms")

# Similarity with score threshold
retriever = retriever_service.vector_store_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.7}
)
docs = retriever_service.search_with_retriever(retriever, "loan requirements")
```

### 2. Multi-Query Retriever

```python
# Create base retriever
base_retriever = retriever_service.vector_store_retriever(search_kwargs={"k": 3})

# Create multi-query retriever
multi_retriever = retriever_service.multi_query_retriever(base_retriever)

# Search with multiple query variations
docs = retriever_service.search_with_retriever(multi_retriever, "What are bridging loans?")
```

### 3. Self-Querying Retriever

```python
from langchain.chains.query_constructor.base import AttributeInfo

# Define metadata fields
metadata_field_info = [
    AttributeInfo(
        name="page",
        description="The page number of the document",
        type="integer",
    ),
    AttributeInfo(
        name="source",
        description="The source file name",
        type="string",
    ),
]

document_content_description = "Financial document about bridging loans."

# Create self-querying retriever
retriever = retriever_service.self_query_retriever(
    metadata_field_info,
    document_content_description
)

# Search with natural language queries
docs = retriever_service.search_with_retriever(retriever, "Show me documents from page 1")
```

### 4. Parent Document Retriever

```python
# Create parent document retriever with custom chunk sizes
parent_retriever = retriever_service.parent_document_retriever(
    parent_chunk_size=1000,
    child_chunk_size=200,
    chunk_overlap=20
)

# Add documents
retriever_service.add_documents_to_parent_retriever(documents, parent_retriever)

# Search (returns parent documents)
docs = retriever_service.search_with_retriever(parent_retriever, "bridging loans overview")
```

## Testing

Run the test script to see all retrievers in action:

```bash
cd backend
python test_retrievers.py
```

This will test all retriever types with the RH-Bridging loans PDF and sample movie data.

## Sample Queries

### Vector Store Retriever
- "bridging loans"
- "financial terms"
- "loan requirements"
- "interest rates"

### Multi-Query Retriever
- "What are bridging loans?"
- "How do bridging loans work?"
- "Tell me about financial bridging"

### Self-Querying Retriever
- "Show me documents from page 1"
- "Find information about loans"
- "What is in the source document?"

### Parent Document Retriever
- "bridging loans overview"
- "loan terms and conditions"
- "financial requirements"

### Movies Self-Querying Retriever
- "I want to watch a movie rated higher than 8.5"
- "Has Greta Gerwig directed any movies about women?"
- "What is a highly rated science fiction film?"
- "Show me movies from the 1990s"
- "Find thrillers directed by Andrei Tarkovsky"

## Parameters

### Vector Store Retriever
- `search_type`: "similarity", "mmr", "similarity_score_threshold"
- `k`: Number of results to return
- `score_threshold`: Minimum similarity score (for similarity_score_threshold)

### Multi-Query Retriever
- `k`: Number of results per query variation

### Self-Querying Retriever
- `metadata_field_info`: List of AttributeInfo objects
- `document_content_description`: Description of document content

### Parent Document Retriever
- `parent_chunk_size`: Size of parent document chunks
- `child_chunk_size`: Size of child document chunks
- `chunk_overlap`: Overlap between chunks

## Notes

- The implementation uses OpenAI for both LLM and embeddings
- ChromaDB is used as the vector store backend
- All retrievers are implemented as per the LangChain notebook specifications
- The system automatically handles document loading, chunking, and vector store creation
- Error handling is implemented for all operations
- The test script provides comprehensive examples of all retriever types
