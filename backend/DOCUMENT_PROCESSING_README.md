# Document Processing & Chunking Comparison System

A comprehensive system for testing and comparing different document chunking strategies for RAG (Retrieval-Augmented Generation) systems, with a focus on financial documents.

## 🏗️ Architecture Overview

The system consists of two main components:

### Backend (Django REST Framework)
- **Document Processing API**: Upload, parse, and chunk documents
- **Multiple Chunking Methods**: Unstructured.io, LlamaParse, Hierarchical, Semantic, Financial-specific
- **Evaluation Engine**: Comprehensive metrics for chunking quality assessment
- **Comparison System**: Side-by-side analysis of different chunking strategies

### Frontend (React)
- **Document Upload Interface**: Drag-and-drop file upload with progress tracking
- **Method Configuration**: Interactive forms for tuning chunking parameters
- **Results Visualization**: Charts, tables, and detailed analysis dashboards
- **Export Tools**: Download results in various formats

## 🚀 Features

### Document Processing
- **Multi-format Support**: PDF, DOCX, TXT, MD files
- **Structure-aware Parsing**: Preserves tables, headers, and hierarchical content
- **API Integration**: Unstructured.io and LlamaParse for advanced parsing
- **File Size Limits**: Up to 50MB per document

### Chunking Methods

#### 1. Unstructured.io Parser
- Structure-aware parsing for complex layouts
- Table and header detection
- Configurable parsing strategies

#### 2. LlamaParse Parser
- GPT-4V powered document parsing
- Advanced structure recognition
- Markdown output format

#### 3. Hierarchical Chunking
- Maintains document structure and relationships
- Parent-child chunk relationships
- Configurable hierarchical depth

#### 4. Semantic Chunking
- Uses embeddings for semantic boundaries
- Sentence-transformers integration
- Configurable similarity thresholds

#### 5. Financial Document Chunking
- Specialized for financial documents
- Table-aware processing
- Financial entity detection

#### 6. Traditional Methods
- Recursive character splitting
- Sentence-based splitting
- Token-based splitting

### Evaluation Metrics

#### Quantitative Metrics
- **Chunk Size Distribution**: Consistency and optimal sizing
- **Overlap Analysis**: Optimal overlap ratios
- **Processing Efficiency**: Speed and resource usage
- **Structure Retention**: Preservation of document structure
- **Semantic Coherence**: Content similarity between chunks

#### Qualitative Analysis
- **Context Preservation**: Parent-child relationships
- **Table Detection**: Financial table recognition
- **Hierarchical Preservation**: Document structure maintenance

## 📊 API Endpoints

### Document Management
```
POST /api/document-processing/documents/upload/     # Upload document
GET  /api/document-processing/documents/            # List documents
GET  /api/document-processing/documents/{id}/       # Get document details
DELETE /api/document-processing/documents/{id}/     # Delete document
```

### Chunking Methods
```
GET /api/document-processing/chunking-methods/      # List available methods
GET /api/document-processing/chunking-methods/{id}/ # Get method details
GET /api/document-processing/chunking-methods/{id}/config/ # Get configuration options
```

### Processing
```
POST /api/document-processing/documents/{id}/process/ # Process document
GET  /api/document-processing/processing-jobs/        # List processing jobs
GET  /api/document-processing/processing-jobs/{id}/   # Get job details
```

### Results & Comparison
```
GET  /api/document-processing/chunking-results/      # List chunking results
GET  /api/document-processing/chunking-results/{id}/ # Get result details
POST /api/document-processing/documents/{id}/compare/ # Compare methods
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Docker & Docker Compose (recommended)

### Backend Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py populate_chunking_methods
   ```

4. **Run Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run Development Server**
   ```bash
   npm run dev
   ```

### Docker Setup

1. **Build and Run**
   ```bash
   docker-compose up --build
   ```

2. **Access Services**
   - Frontend: http://localhost:8080
   - Backend: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 🔧 Configuration

### API Keys Required
- **OpenAI API Key**: For embeddings and semantic analysis
- **Unstructured.io API Key**: For structure-aware parsing
- **LlamaParse API Key**: For GPT-4V powered parsing

### Chunking Parameters

#### Hierarchical Chunking
- `chunk_size`: Target chunk size in tokens (100-4000)
- `chunk_overlap`: Overlap between chunks (0-500)
- `preserve_structure`: Maintain hierarchical relationships
- `hierarchical_depth`: Maximum nesting depth (1-10)

#### Semantic Chunking
- `chunk_size`: Target chunk size in tokens (100-4000)
- `semantic_threshold`: Similarity threshold (0.0-1.0)
- `min_chunk_size`: Minimum chunk size (50-1000)
- `max_chunk_size`: Maximum chunk size (500-4000)

#### Financial Chunking
- `chunk_size`: Target chunk size in tokens (100-4000)
- `chunk_overlap`: Overlap between chunks (0-500)
- `table_aware`: Preserve table structures
- `preserve_financial_structure`: Maintain financial document structure

## 📈 Usage Examples

### 1. Upload and Process Document
```javascript
// Upload document
const formData = new FormData();
formData.append('file', file);
formData.append('name', 'Financial Report');

const document = await fetch('/api/document-processing/documents/upload/', {
  method: 'POST',
  body: formData
}).then(res => res.json());

// Process with multiple methods
const job = await fetch(`/api/document-processing/documents/${document.id}/process/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chunking_method_ids: [1, 2, 3], // Hierarchical, Semantic, Financial
    configuration: {
      hierarchical: { chunk_size: 1000, preserve_structure: true },
      semantic: { semantic_threshold: 0.7 },
      financial: { table_aware: true }
    }
  })
}).then(res => res.json());
```

### 2. Compare Results
```javascript
// Compare chunking methods
const comparison = await fetch(`/api/document-processing/documents/${document.id}/compare/`, {
  method: 'POST'
}).then(res => res.json());

console.log('Winner:', comparison.winner_method);
console.log('Metrics:', comparison.comparison_metrics);
```

## 📊 Evaluation Metrics Explained

### Chunk Size Distribution
- **Score**: 0-1 (higher is better)
- **Measures**: Consistency of chunk sizes
- **Details**: Min/max/mean/median/std deviation

### Overlap Analysis
- **Score**: 0-1 (higher is better)
- **Measures**: Optimal overlap between chunks
- **Details**: Mean overlap ratio, overlap count

### Context Preservation
- **Score**: 0-1 (higher is better)
- **Measures**: Hierarchical relationships maintained
- **Details**: Parent-child ratios, hierarchical levels

### Structure Retention
- **Score**: 0-1 (higher is better)
- **Measures**: Document structure preservation
- **Details**: Element type diversity, structure awareness

### Semantic Coherence
- **Score**: 0-1 (higher is better)
- **Measures**: Content similarity between chunks
- **Details**: Word overlap similarity scores

### Processing Efficiency
- **Score**: 0-1 (higher is better)
- **Measures**: Speed and resource usage
- **Details**: Chunks/second, tokens/second

## 🎯 Best Practices

### For Financial Documents
1. **Use Financial Chunking**: Specialized for tables and financial structures
2. **Enable Table Awareness**: Preserves financial tables as complete units
3. **Configure Structure Preservation**: Maintains document hierarchy
4. **Set Appropriate Chunk Sizes**: 1000-1500 tokens for financial content

### For General Documents
1. **Start with Hierarchical**: Good balance of structure and performance
2. **Try Semantic Chunking**: For content-heavy documents
3. **Compare Multiple Methods**: Always run comparisons for optimal results
4. **Monitor Evaluation Metrics**: Use metrics to guide parameter tuning

### Performance Optimization
1. **Batch Processing**: Process multiple documents together
2. **Async Processing**: Use background jobs for large documents
3. **Caching**: Cache parsed documents and embeddings
4. **Resource Monitoring**: Monitor memory and CPU usage

## 🔍 Troubleshooting

### Common Issues

#### Upload Failures
- Check file size (max 50MB)
- Verify file format (PDF, DOCX, TXT, MD)
- Ensure proper API keys are configured

#### Processing Errors
- Verify document parsing worked correctly
- Check chunking method configuration
- Review error logs for specific issues

#### Performance Issues
- Reduce chunk size for faster processing
- Use fewer chunking methods simultaneously
- Monitor system resources

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
export LOG_LEVEL=DEBUG

# Run with verbose output
python manage.py runserver --verbosity=2
```

## 📚 API Documentation

Full API documentation is available at:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the API documentation
- Contact the development team
