# 🛠️ Development Documentation

This document contains detailed information for developers working on the DataGovAI project.

## 🏗️ Architecture Overview

The Knowledge Base Agent is built around a central `DocumentProcessor` which orchestrates the interaction between various components:

### Components

| Component | Description |
|-----------|-------------|
| Input Processing | • CLI (`kb-agent process`)<br>• REST API (`POST /api/documents`)<br>• Search queries via CLI/API |
| Document Processing | • PyMuPDF for PDF extraction<br>• NLTK/spaCy for semantic chunking |
| RAG Component | • SentenceTransformer embeddings<br>• GPU-accelerated processing |
| KG Component | • Local LLM-based entity extraction<br>• Relationship mapping |
| Storage | • PostgreSQL with pgvector<br>• Hybrid document/vector storage |

### Processing Pipeline

| Stage | Description |
|-------|-------------|
| 1. Input | Document ingestion through CLI or API |
| 2. Extraction | PDF processing and text extraction |
| 3. Chunking | Semantic document segmentation |
| 4. Embedding | Vector representation generation |
| 5. Entity Analysis | LLM-based entity and relationship extraction |
| 6. Storage | Hybrid storage in PostgreSQL |

## 🤔 Design Rationale

### Data Characteristics

| Aspect | Details |
|--------|----------|
| Volume | ~20,000 documents |
| Types | Forms, guidelines, policies |
| Structure | Mixed structured/unstructured |
| Content | Retention periods, dispositions, requirements |

### Architecture Choice

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| Vector Store Only | • Good semantic search<br>• Flexible queries | • Poor fact retrieval<br>• Limited structure |
| Knowledge Graph Only | • Precise fact retrieval<br>• Clear relationships | • Limited semantic understanding<br>• Complex maintenance |
| Hybrid RAG+KG | • Best of both approaches<br>• Flexible and precise | • More complex implementation<br>• Higher resource usage |

## 🧪 Testing Strategy

### Document Processing Tests

| Test Type | Description | Examples |
|-----------|-------------|----------|
| Sample Selection | Test across categories | 1 from each category |
| Batch Processing | Various batch sizes | 10, 100, 1000 docs |
| Format Handling | PDF extraction tests | Layout, text, metadata |
| Metadata Extraction | Entity extraction tests | GRS numbers, dates |

### Knowledge Extraction

```python
test_documents = {
    'administrative': ['policies-and-procedures-(GRS-1234).pdf'],
    'financial': ['annual-budget-(GRS-5678).pdf'],
    'legal': ['civil-case-files-(GRS-9012).pdf']
}

expected_entities = {
    'retention_period': r'Retain for \d+ years',
    'document_type': r'^[a-zA-Z\s-]+(?=-\(GRS)',
    'grs_number': r'GRS-\d+'
}
```

### Query Testing

| Type | Example | Purpose |
|------|---------|---------|
| Retention Period | `SELECT * FROM grs_documents WHERE category = 'financial'` | Basic fact retrieval |
| Cross-Category | `knowledge_base.find_related(document_id="GRS-1234")` | Relationship testing |
| Semantic Search | `knowledge_base.semantic_search("financial audit records")` | Concept matching |

## 📊 Development Phases

| Phase | Status | Components |
|-------|--------|------------|
| 1. Basic Processing | ✅ | • Document ingestion<br>• Basic extraction |
| 2. Enhanced Analysis | ✅ | • Entity extraction<br>• Relationship mapping |
| 3. Query System | ✅ | • Semantic search<br>• Structured queries |
| 4. Advanced Features | 🔄 | • Multi-doc analysis<br>• Compliance checking |

## 🛠️ Development Setup

### Environment Setup

```bash
# Create and activate environment
conda env create -f environment.yml
conda activate chatbot

# Install dependencies
pip install -r requirements.txt
```

### Database Setup

```bash
# Create database
sudo -u postgres psql -c "CREATE DATABASE knowledge_base;"

# Verify connection
sudo -u postgres psql -d knowledge_base -c "\conninfo"

# Set connection string
echo 'export POSTGRES_CONNECTION="postgresql://postgres@localhost:5432/knowledge_base"' >> ~/.bashrc
source ~/.bashrc
```

## 📚 API Examples

### REST API

```python
import requests

# Process document
response = requests.post(
    "http://localhost:8000/api/documents",
    json={
        "content": "Document content",
        "metadata": {"title": "Test Document"}
    }
)

# Search
results = requests.get(
    "http://localhost:8000/api/search",
    params={"query": "test query", "limit": 5}
).json()["results"]
```

### Python API

```python
from knowledge_base_agent import DocumentProcessor
from knowledge_base_agent.config import get_config

processor = DocumentProcessor.from_config(get_config())

# Process document
doc_id = processor.process_document(
    content="Document content",
    metadata={"title": "Test"}
)

# Search
results = processor.search("test query", top_k=5)
```

For more detailed documentation, refer to the specific guides in the `docs/` directory.

# 👩‍�� Development Guide

## Overview

This guide covers development practices, setup, and workflows for the DataGovAI project. It includes environment setup, coding standards, testing procedures, and contribution guidelines.

## Development Environment

### 1. Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Core development |
| Poetry | 1.6+ | Dependency management |
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Local development |
| Git | 2.40+ | Version control |
| Make | 4.0+ | Build automation |

### 2. Initial Setup

```bash
# Clone repository
git clone https://github.com/utah-data-privacy/datagovai.git
cd datagovai

# Install dependencies
poetry install

# Set up pre-commit hooks
poetry run pre-commit install

# Create .env file
cp .env.example .env

# Start development services
docker-compose up -d
```

### 3. Environment Configuration

```ini
# .env
# Database
DATABASE_URL=postgresql://datagovai:datagovai@localhost:5432/datagovai
DATABASE_TEST_URL=postgresql://datagovai:datagovai@localhost:5432/datagovai_test

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Processing
BATCH_SIZE=10
MAX_CONCURRENT_TASKS=4
VECTOR_DIMENSION=768

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000

# Storage
DOCUMENT_STORAGE_PATH=./data/documents
VECTOR_CACHE_PATH=./data/cache
```

## Project Structure

```
datagovai/
├── app/
│   ├── api/              # REST API endpoints
│   ├── core/             # Core business logic
│   ├── db/               # Database models and migrations
│   ├── processing/       # Document processing pipeline
│   ├── search/          # Search and query functionality
│   └── utils/           # Utility functions
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
├── docs/                # Documentation
├── scripts/             # Development scripts
├── docker/             # Docker configurations
├── pyproject.toml      # Project metadata
└── README.md           # Project overview
```

## Code Style

### 1. Python Style Guide

```python
# app/core/document.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class Document(BaseModel):
    """
    Represents a GRS document in the system.
    
    Attributes:
        id: Unique identifier for the document
        title: Document title
        content: Full document text
        metadata: Additional document metadata
        created_at: Document creation timestamp
        updated_at: Last update timestamp
    """
    id: str = Field(..., pattern=r'^GRS-\d{4}-[A-Z]{3}-\d{3}$')
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def update(self, **kwargs) -> None:
        """
        Update document attributes.
        
        Args:
            **kwargs: Attributes to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
```

### 2. Code Formatting

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py310']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = "E203"
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist"
]
```

## Testing

### 1. Unit Tests

```python
# tests/unit/test_document.py
import pytest
from datetime import datetime
from app.core.document import Document

def test_document_creation():
    """Test document creation with valid data."""
    doc = Document(
        id="GRS-2024-FIN-001",
        title="Financial Records",
        content="Test content"
    )
    assert doc.id == "GRS-2024-FIN-001"
    assert doc.title == "Financial Records"
    assert isinstance(doc.created_at, datetime)
    assert doc.updated_at is None

def test_document_update():
    """Test document update functionality."""
    doc = Document(
        id="GRS-2024-FIN-001",
        title="Financial Records",
        content="Test content"
    )
    original_created_at = doc.created_at
    
    doc.update(title="Updated Title")
    
    assert doc.title == "Updated Title"
    assert doc.created_at == original_created_at
    assert doc.updated_at is not None

def test_invalid_document_id():
    """Test document creation with invalid ID format."""
    with pytest.raises(ValueError):
        Document(
            id="invalid-id",
            title="Financial Records",
            content="Test content"
        )
```

### 2. Integration Tests

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_document_creation():
    """Test document creation through API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/documents",
            json={
                "id": "GRS-2024-FIN-001",
                "title": "Financial Records",
                "content": "Test content"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "GRS-2024-FIN-001"
        assert data["title"] == "Financial Records"

@pytest.mark.asyncio
async def test_document_search():
    """Test document search functionality."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create test document
        await client.post(
            "/documents",
            json={
                "id": "GRS-2024-FIN-001",
                "title": "Financial Records",
                "content": "Test content about retention periods"
            }
        )
        
        # Search for document
        response = await client.post(
            "/search/semantic",
            json={
                "query": "retention periods",
                "filters": {"category": "financial"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) > 0
        assert data["results"][0]["id"] == "GRS-2024-FIN-001"
```

## Database Management

### 1. Migrations

```python
# app/db/migrations/versions/001_initial.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'documents',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.CheckConstraint(
            "id ~ '^GRS-\\d{4}-[A-Z]{3}-\\d{3}$'",
            name='valid_document_id'
        )
    )
    
    op.create_index(
        'ix_documents_title',
        'documents',
        ['title']
    )

def downgrade():
    op.drop_index('ix_documents_title')
    op.drop_table('documents')
```

### 2. Database Scripts

```python
# scripts/db.py
import asyncio
import typer
from app.db.session import engine
from app.db.base import Base

app = typer.Typer()

@app.command()
def create_tables():
    """Create all database tables."""
    async def run():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    asyncio.run(run())
    typer.echo("Tables created successfully!")

@app.command()
def drop_tables():
    """Drop all database tables."""
    async def run():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    asyncio.run(run())
    typer.echo("Tables dropped successfully!")

if __name__ == "__main__":
    app()
```

## API Development

### 1. Route Definition

```python
# app/api/routes/documents.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.core.document import Document
from app.core.schemas import DocumentCreate, DocumentUpdate
from app.core.services import DocumentService

router = APIRouter()

@router.post("/", response_model=Document)
async def create_document(
    document: DocumentCreate,
    service: DocumentService = Depends()
):
    """
    Create a new document.
    
    Args:
        document: Document creation data
        service: Document service instance
    
    Returns:
        Created document
    
    Raises:
        HTTPException: If document creation fails
    """
    try:
        return await service.create(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    service: DocumentService = Depends()
):
    """
    Get document by ID.
    
    Args:
        document_id: Document identifier
        service: Document service instance
    
    Returns:
        Retrieved document
    
    Raises:
        HTTPException: If document not found
    """
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
```

### 2. Middleware Configuration

```python
# app/api/middleware.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Authentication middleware
    app.add_middleware(AuthenticationMiddleware)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code}")
        
        return response
```

## Error Handling

### 1. Exception Definitions

```python
# app/core/exceptions.py
from typing import Optional, Any

class DataGovAIError(Exception):
    """Base exception for DataGovAI errors."""
    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = 500,
        details: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class DocumentNotFoundError(DataGovAIError):
    """Raised when a document is not found."""
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            code="document_not_found",
            status_code=404
        )

class ValidationError(DataGovAIError):
    """Raised when data validation fails."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=400,
            details=details
        )
```

### 2. Error Handlers

```python
# app/api/errors.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DataGovAIError

def setup_error_handlers(app: FastAPI) -> None:
    """Configure application error handlers."""
    
    @app.exception_handler(DataGovAIError)
    async def datagovai_error_handler(
        request: Request,
        exc: DataGovAIError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def general_error_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        # Log unexpected errors
        logger.exception("Unexpected error occurred")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "code": "internal_error",
                "message": "An unexpected error occurred"
            }
        )
```

## Contribution Guidelines

### 1. Pull Request Process

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. Push changes:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create pull request:
   - Use the PR template
   - Link related issues
   - Add appropriate labels
   - Request reviews

### 2. Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

Example:
```
feat(documents): add retention period validation

- Add validation for retention period format
- Update documentation
- Add unit tests

Closes #123
```

## See Also
- [Architecture Overview](../architecture/README.md)
- [API Documentation](../api/README.md)
- [Deployment Guide](../deployment/README.md) 