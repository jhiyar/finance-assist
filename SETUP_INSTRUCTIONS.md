# Document Processing System Setup Instructions

## Quick Setup

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys (OpenAI, Unstructured.io, LlamaParse)

# Run the setup script
python setup_document_processing.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Admin Interface**: http://localhost:8080/admin
- **Document Processing**: http://localhost:8080/document-processing

## Manual Setup (if automated setup fails)

### Backend Manual Setup

```bash
cd backend

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Populate chunking methods
python manage.py populate_chunking_methods

# Create superuser (optional)
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### Docker Setup (Alternative)

```bash
# Build and run with Docker
docker-compose up --build
```

## Troubleshooting

### Issue: "No chunking methods available"

**Solution**: Run the populate command
```bash
cd backend
python manage.py populate_chunking_methods
```

### Issue: "Error loading chunking methods"

**Check**:
1. Backend server is running on http://localhost:8000
2. Database migrations have been run
3. Check browser console for API errors
4. Verify CORS settings in Django

### Issue: "Module not found" errors

**Solution**: Install missing dependencies
```bash
# Backend
pip install -r requirements.txt

# Frontend
npm install
```

### Issue: Database connection errors

**Solution**: 
1. Ensure MySQL is running
2. Check database credentials in settings.py
3. Run migrations: `python manage.py migrate`

## API Keys Required

Add these to your `.env` file:

```env
# OpenAI (required for semantic chunking)
OPENAI_API_KEY=your_openai_api_key_here

# Unstructured.io (optional, for advanced parsing)
UNSTRUCTURED_API_KEY=your_unstructured_api_key_here

# LlamaParse (optional, for GPT-4V parsing)
LLAMAPARSE_API_KEY=your_llamaparse_api_key_here
```

## Testing the System

1. **Upload a document**: Go to Document Processing page and upload a PDF or DOCX file
2. **Select methods**: Choose one or more chunking methods
3. **Process**: Click "Start Processing" and wait for completion
4. **View results**: Analyze the comparison results and metrics

## Development

### Backend Development
```bash
cd backend
python manage.py runserver --settings=finance_assist.settings
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell
```
