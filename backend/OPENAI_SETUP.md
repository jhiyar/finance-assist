# OpenAI Integration Setup

This document explains how to set up and use OpenAI models and embeddings in the Finance Assist retriever service.

## Overview

The retriever service uses OpenAI services for both LLM and embeddings.

## Configuration

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# OpenAI Configuration (default provider)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4096

# AI Service Provider Configuration
# Using OpenAI only
AI_SERVICE_PROVIDER=openai
```

### 2. API Key Setup

1. Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add it to your `.env` file as `OPENAI_API_KEY`

## Usage

### Basic Usage

The retriever service will automatically use OpenAI by default:

```python
from services.retriever_service import get_retriever_service

# This will use OpenAI by default
retriever_service = get_retriever_service()

# Create vector store with OpenAI embeddings
vectorstore = retriever_service.create_vector_store(documents)

# Perform similarity search
results = retriever_service.similarity_search("your query")
```

### Explicit Provider Selection

You can explicitly choose which provider to use:

```python
from services.retriever_service import (
    get_openai_retriever_service,
    get_openai_retriever_service
)

# Use OpenAI specifically
openai_service = get_openai_retriever_service()

# Use OpenAI specifically
openai_service = get_openai_retriever_service()

# Or specify provider when creating service
from services.retriever_service import get_retriever_service
service = get_retriever_service(service_provider='openai')
```

### Switching Providers

You can switch between providers at runtime:

```python
retriever_service = get_retriever_service()  # Uses default (OpenAI)

# Service provider is now fixed to OpenAI

# Switch back to OpenAI
openai_service = retriever_service.switch_service_provider('openai')
```

## Available Models

### OpenAI Models

- **LLM Models**: `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo-preview`
- **Embedding Models**: `text-embedding-3-small`, `text-embedding-3-large`

### Configuration Options

You can customize the models and parameters:

```bash
# LLM Configuration
OPENAI_MODEL_NAME=gpt-4
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=8192

# Embedding Configuration
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

## Testing

Run the test script to verify your OpenAI integration:

```bash
cd backend
python test_openai_retriever.py
```

This will test:
- Service initialization
- Document processing
- Vector store creation
- Similarity search
- Multi-query retrieval

## Features

### Supported Retriever Types

All retriever types work with OpenAI:

1. **Vector Store Retriever**: Basic similarity search
2. **Multi-Query Retriever**: Generates multiple queries for better retrieval
3. **Self-Query Retriever**: Uses LLM to parse natural language queries
4. **Parent Document Retriever**: Hierarchical document retrieval

### Example Usage

```python
from services.retriever_service import get_openai_retriever_service
from services.document_loader import get_document_loader

# Initialize services
retriever_service = get_openai_retriever_service()
document_loader = get_document_loader()

# Load and process documents
documents = document_loader.load_pdf_file("path/to/document.pdf")
chunks = retriever_service.text_splitter(documents)

# Create vector store
vectorstore = retriever_service.create_vector_store(chunks)

# Use different retriever types
# 1. Basic similarity search
results = retriever_service.similarity_search("your query", k=5)

# 2. Multi-query retriever
multi_retriever = retriever_service.multi_query_retriever()
multi_results = retriever_service.search_with_retriever(multi_retriever, "your query")

# 3. Self-query retriever (for structured data)
metadata_info = [
    AttributeInfo(name="category", description="Document category", type="string"),
    AttributeInfo(name="date", description="Document date", type="date")
]
self_retriever = retriever_service.self_query_retriever(
    metadata_info, "Document content"
)
self_results = retriever_service.search_with_retriever(self_retriever, "Find documents in finance category")
```

## Troubleshooting

### Common Issues

1. **API Key Error**: Make sure `OPENAI_API_KEY` is set in your environment
2. **Model Not Found**: Verify the model name in `OPENAI_MODEL_NAME`
3. **Rate Limiting**: OpenAI has rate limits; consider implementing retry logic
4. **Token Limits**: Adjust `OPENAI_MAX_TOKENS` based on your needs

### Error Messages

- `"OPENAI_API_KEY is required but not set"`: Add your API key to environment variables
- `"Embedding service not available"`: Check your OpenAI configuration
- `"LLM service not available"`: Verify your OpenAI API key and model settings

## OpenAI-Only Configuration

The system now uses OpenAI exclusively for all AI services:

1. LLM functionality via OpenAI GPT models
2. Embeddings via OpenAI embedding models
3. No Watson dependencies or configuration needed

## Cost Considerations

OpenAI charges based on:
- **LLM Usage**: Per token for model inference
- **Embedding Usage**: Per token for embedding generation

Monitor your usage in the [OpenAI Dashboard](https://platform.openai.com/usage) to manage costs effectively.
