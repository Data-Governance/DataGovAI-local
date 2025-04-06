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