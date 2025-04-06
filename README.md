# 🧠 Knowledge Base Agent for Utah GRS

A powerful RAG (Retrieval-Augmented Generation) based knowledge base agent specifically designed for Utah's General Retention Schedules (GRS). This system helps government entities efficiently access and understand record retention requirements and related policies.

## 🎯 Project Context

This Knowledge Base Agent is part of the **DataGovAI** platform, a collaboration between Utah Valley University's Smith College of Engineering and Technology and the Utah Office of Data Privacy (ODP). The system processes and provides intelligent access to Utah's General Retention Schedules, helping government entities maintain compliance with state records management requirements.

## ✨ Features

- 🤖 Intelligent chat interface for querying GRS documents
- 🔍 Advanced RAG-based retrieval system
- 📚 Comprehensive document processing pipeline
- 🎯 High-accuracy responses with source citations
- 💡 Helpful example questions and guidance
- 🔐 Environment-based configuration
- 📊 Clean and intuitive web interface

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- CUDA-capable GPU (recommended for optimal performance)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DataGovAI.git
cd DataGovAI
```

2. Create and activate a virtual environment:
```bash
python -m venv rag_env
source rag_env/bin/activate  # On Windows: rag_env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python scripts/init_db.py
```

### Running the Application

1. Start the Flask application:
```bash
python app/app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## 💬 Usage

The knowledge base agent provides an intuitive chat interface where you can:

1. Ask questions about record retention requirements
2. Get specific GRS document references
3. Understand retention periods and disposition requirements
4. Explore related documents and requirements

Example questions:
- "What is the retention period for financial records?"
- "How long should we keep employee personnel files?"
- "What are the disposition requirements for audit records?"

## 📁 Project Structure

```
DataGovAI/
├── app/                    # Main application directory
│   ├── static/            # CSS, JavaScript, and other static files
│   ├── templates/         # HTML templates
│   └── app.py            # Flask application
├── data/                  # Data storage directory
│   └── processed/        # Processed document embeddings
├── docs/                  # Documentation
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── .env.example          # Example environment configuration
├── environment.yml       # Conda environment specification
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

Key configuration options in `.env`:

```ini
# Database Configuration
POSTGRES_CONNECTION=postgresql://user:password@localhost:5432/knowledge_base

# Embedding Configuration
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=32

# Application Configuration
FLASK_ENV=development
DEBUG=True
```

## 📊 GRS Documents Analysis

### Document Categories Overview
The Utah General Retention Schedules (GRS) documents are organized into the following major categories:

1. **Administrative & Governance (791 documents, 4.1%)**
   - Executive correspondence
   - Policies and procedures
   - Council minutes
   - Organizational records
   - Administrative files

2. **Financial Records (1,518 documents, 7.8%)**
   - Budget documents
   - Payroll records
   - Audit reports
   - Tax records
   - Financial statements

3. **Public Services (763 documents, 3.9%)**
   - City council records
   - Utility management
   - Cemetery records
   - Public works documentation
   - Community services

4. **Legal & Compliance (426 documents, 2.2%)**
   - Civil cases
   - Criminal records
   - Warrants
   - Legal documentation
   - Enforcement records

5. **Education & Training (557 documents, 2.9%)**
   - Student records
   - School documentation
   - Training materials
   - Educational programs
   - Academic records

6. **Personnel Management (558 documents, 2.9%)**
   - Employee files
   - HR documentation
   - Staff records
   - Employment applications
   - Personnel policies

7. **Health & Medical (348 documents, 1.8%)**
   - Medical records
   - Patient files
   - Healthcare administration
   - Pharmacy records
   - Health services

8. **Property & Planning (365 documents, 1.9%)**
   - Building permits
   - Zoning records
   - Land management
   - Construction files
   - Planning documentation

9. **Records Management (399 documents, 2.1%)**
   - Document tracking
   - Archive management
   - Records transfer
   - File systems
   - Documentation standards

### Testing Strategy

#### 1. Document Processing Testing
- **Sample Selection**: Test with representative documents from each category
- **Batch Processing**: Test with varying batch sizes (10, 100, 1000 documents)
- **Format Handling**: Verify PDF extraction and text processing
- **Metadata Extraction**: Test GRS number, retention period, and document type extraction

#### 2. Knowledge Extraction Testing
```python
# Example knowledge extraction test
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

#### 3. Query Testing Scenarios
1. **Retention Period Queries**
   ```sql
   -- Example retention period query
   SELECT document_type, retention_period 
   FROM grs_documents 
   WHERE category = 'financial'
   ```

2. **Cross-Category Relations**
   ```python
   # Example relationship test
   related_docs = knowledge_base.find_related(
       document_id="GRS-1234",
       relationship_type="references"
   )
   ```

3. **Semantic Search Tests**
   ```python
   # Example semantic search test
   results = knowledge_base.semantic_search(
       query="What is the retention period for financial audit records?",
       category="financial"
   )
   ```

### Document Metadata Structure
```json
{
    "document_id": "GRS-XXXXX",
    "metadata": {
        "title": "Document Title",
        "category": "Major Category",
        "subcategory": "Specific Type",
        "retention_period": "Retention Duration",
        "disposition": "Final Disposition",
        "created_date": "YYYY-MM-DD",
        "last_modified": "YYYY-MM-DD"
    },
    "relationships": {
        "references": ["GRS-YYYY", "GRS-ZZZZ"],
        "supersedes": ["GRS-AAAA"],
        "related_to": ["GRS-BBBB"]
    },
    "extracted_entities": {
        "organization": ["Department Name", "Division"],
        "dates": ["Retention Start", "Review Date"],
        "requirements": ["Legal Reference", "Compliance Note"]
    }
}
```

### Development Testing Phases

1. **Phase 1: Basic Document Processing**
   - Document ingestion and storage
   - Metadata extraction
   - Basic text extraction
   - Category classification

2. **Phase 2: Enhanced Analysis**
   - Entity extraction
   - Relationship mapping
   - Retention period parsing
   - Cross-reference detection

3. **Phase 3: Query Capabilities**
   - Basic keyword search
   - Category-based filtering
   - Semantic similarity search
   - Relationship-based queries

4. **Phase 4: Advanced Features**
   - Multi-document analysis
   - Temporal analysis
   - Compliance checking
   - Automated updates

## 🏗️ Architecture Overview

The Knowledge Base Agent is built around a central `DocumentProcessor` which orchestrates the interaction between various components:

1.  **Input**: Documents can be ingested via the CLI (`kb-agent process`) or the REST API (`POST /api/documents`). Search queries are handled via the CLI (`kb-agent query`) or the API (`GET /api/search`).
2.  **Processing (Ingestion & Knowledge Building)**: When a document is processed:
    *   The `DocumentProcessor` receives the content (using **PyMuPDF** for robust PDF extraction in the SOTA branch) and metadata.
    *   It chunks the document into smaller, semantically meaningful segments (using techniques like sentence splitting via **NLTK/spaCy** in the SOTA branch).
    *   **RAG Component:** An **Embedding Model** (e.g., `SentenceTransformerEmbedding` using models like `all-mpnet-base-v2` on GPU in SOTA) generates dense vector representations (embeddings) for each chunk. These capture the semantic meaning of the text.
    *   **KG Component:** An **Extractor Model** (e.g., `LocalLlmExtractor` using models like `Mistral-7B-Instruct` on GPU in SOTA) is prompted to analyze the document's text. It identifies key entities (like Record Series Number, Title, Retention Period, Disposition Action, Legal Authority) and their relationships (e.g., a Record Series `HAS_RETENTION` of 'X years', or `SUPERSEDES` another GRS). The goal is to output this structured information, often in JSON format.
    *   **Storage (Hybrid - PostgreSQL):**
        *   The original content and metadata are stored in a **Document Store** (e.g., a `documents` table in PostgreSQL).
        *   The extracted entities and relationships (**KG Component**) are stored in dedicated tables within the *same* PostgreSQL database (e.g., `entities`, `relationships` tables). This allows linking structured knowledge directly back to the source document.
        *   The vector embeddings (**RAG Component**) are stored in a **Vector Store** using PostgreSQL's `pgvector` extension (e.g., a `chunks` table with an embedding column). This enables efficient semantic similarity search.
3.  **Search (Querying & Answer Synthesis)**: When a query is received:
    *   In standard mode: The processor typically performs semantic search on the Vector Store to find relevant document chunks based on the query's meaning.
    *   In **advanced Hybrid RAG+KG mode (SOTA branch)**:
        1. The `RAGKGQueryAgent` embeds the user query and performs semantic search (**RAG**) against the `pgvector` store to find chunks with similar meaning.
        2. It uses an LLM to extract key entities mentioned in the user's query (e.g., a specific GRS number, a concept like 'payroll').
        3. It executes targeted SQL queries against the structured `entities` and `relationships` tables (**KG**) based on the extracted entities (e.g., retrieving the exact Retention Period for a specific GRS number).
        4. It aggregates the context from both the semantically relevant chunks (RAG) and the precise facts retrieved from the knowledge graph (KG).
        5. It uses a powerful LLM to synthesize a comprehensive, accurate answer based on this combined RAG+KG context.
4.  **Interfaces**:
    *   A **CLI** provides command-line tools for processing, searching, and managing the agent.
    *   A **REST API** (FastAPI-based) exposes the agent's functionality over HTTP.
5.  **Configuration**: System settings are managed via a configuration system using `.env` files.

This modular design allows for flexibility in choosing different storage backends, embedding models, and processing techniques.

## 🤔 Knowledge Base Design Rationale (Hybrid RAG+KG)

The choice of a hybrid Retrieval-Augmented Generation (RAG) and Knowledge Graph (KG) approach for the knowledge base stems from the specific characteristics of the Utah General Retention Schedules (GRS) data:

**1. GRS Data Characteristics:**
   *   **High Volume & Variety:** The dataset comprises nearly 20,000 documents with diverse types, from specific forms to broad guidelines.
   *   **Structured Information:** GRS documents inherently contain structured data points (Record Series Numbers, Titles, Retention Periods, Dispositions, Legal Authorities) crucial for precise queries.
   *   **Descriptive Content:** Significant descriptive text explains context, purpose, and scope, requiring semantic understanding.
   *   **Categorization Challenge:** Even after classification efforts, a large portion (~50% in initial analyses) remains less defined ("other/general"), indicating that purely structured approaches might be insufficient.

**2. Evaluating Storage/Retrieval Approaches:**
   *   **Vector Store (RAG) Only:** Good for semantic similarity ("*Find documents about X*") but weak for precise fact retrieval ("*What is the retention period for Y?*"). It struggles to reliably extract specific details like dates or codes from unstructured text chunks alone.
   *   **Knowledge Graph (KG) Only:** Excellent for structured facts and relationships ("*Show records with 'Permanent' retention linked to 'State Archives'*"). However, it depends heavily on consistent LLM extraction across all documents, which can be challenging with diverse and less structured content. It also doesn't handle purely conceptual queries well.
   *   **Hybrid RAG + KG (Chosen Approach):** Leverages the strengths of both:
        *   The **KG** captures explicit, structured facts (Retention, Disposition, Series Number) for precise, targeted queries.
        *   The **RAG** component captures the semantic meaning of descriptive text, enabling broader conceptual searches and providing rich context for LLM answer synthesis. It serves as a vital fallback for documents where KG extraction might be incomplete or less reliable (e.g., the "other" category).

**Conclusion:** The Hybrid RAG + KG architecture provides the necessary balance of structured fact retrieval and semantic understanding required to effectively query the complex and varied GRS dataset.

## 🚀 Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Storage** | ChromaDB, Milvus, Neo4j, MongoDB, Elasticsearch |
| **Processing** | OpenAI GPT-4, Claude, spaCy, Hugging Face |
| **Integration** | FastAPI, GraphQL, Redis, Prometheus |

## 📚 Documentation Structure

### Core Documentation
- **[Quick Start Guide](docs/quick_start.md)**: Get up and running quickly
- **[Development Plan](docs/development/plan.md)**: Central reference for all development activities
- **[Architecture Guide](docs/architecture/README.md)**: Detailed system design and components
- **[API Reference](docs/api/README.md)**: Complete API documentation
- **[Knowledge Base Guide](docs/knowledge_base/README.md)**: Working with the knowledge base

### Technical Documentation
1. **Architecture & Design**
   - [System Overview](docs/architecture/overview.md)
   - [Data Flow](docs/architecture/data_flow.md)
   - [Component Interactions](docs/architecture/component_interactions.md)
   - [Database Schema](docs/architecture/database_schema.md)

2. **Components**
   - [Document Processor](docs/components/document_processor.md)
   - [RAG System](docs/components/rag_system.md)
   - [Knowledge Graph](docs/components/knowledge_graph.md)
   - [Query Engine](docs/components/query_engine.md)
   - [LLM Integration](docs/components/llm_integration.md)

3. **Implementation Guides**
   - [Environment Setup](docs/guides/environment_setup.md)
   - [Database Setup](docs/guides/database_setup.md)
   - [GPU Configuration](docs/guides/gpu_setup.md)
   - [Security Best Practices](docs/guides/security.md)
   - [Performance Optimization](docs/guides/optimization.md)

4. **API Documentation**
   - [REST API Reference](docs/api/rest_api.md)
   - [Python API Reference](docs/api/python_api.md)
   - [CLI Reference](docs/api/cli.md)
   - [Configuration Reference](docs/api/configuration.md)

5. **Knowledge Base**
   - [KB Architecture](docs/knowledge_base/architecture.md)
   - [Data Model](docs/knowledge_base/data_model.md)
   - [Query Patterns](docs/knowledge_base/query_patterns.md)
   - [Optimization Guide](docs/knowledge_base/optimization.md)

### Development Resources
1. **Contributing**
   - [Contributing Guide](CONTRIBUTING.md)
   - [Code Style Guide](docs/contributing/code_style.md)
   - [Testing Guide](docs/contributing/testing.md)
   - [Documentation Guide](docs/contributing/documentation.md)

2. **Examples & Tutorials**
   - [Basic Usage Examples](docs/examples/basic_usage.md)
   - [Advanced Queries](docs/examples/advanced_queries.md)
   - [Custom Extensions](docs/examples/custom_extensions.md)
   - [Integration Examples](docs/examples/integration.md)

3. **Maintenance**
   - [Deployment Guide](docs/maintenance/deployment.md)
   - [Monitoring Guide](docs/maintenance/monitoring.md)
   - [Backup & Recovery](docs/maintenance/backup_recovery.md)
   - [Troubleshooting](docs/maintenance/troubleshooting.md)

### Development Tools

1. **Plan Tracking**
   ```bash
   # Check development plan status
   python scripts/check_plan.py
   
   # Find relevant documentation
   python scripts/find_docs.py "knowledge graph"
   
   # List available components
   python scripts/list_components.py
   ```

2. **Documentation Helpers**
   ```bash
   # Generate API documentation
   python scripts/generate_api_docs.py
   
   # Check documentation coverage
   python scripts/check_docs_coverage.py
   
   # Validate documentation links
   python scripts/validate_docs.py
   ```

3. **Git Hooks**
   ```bash
   # Install documentation hooks
   python scripts/install_doc_hooks.py
   ```

### Directory Structure
```
docs/
├── api/              # API documentation
├── architecture/     # System design docs
├── components/       # Component details
├── contributing/     # Contribution guides
├── examples/         # Usage examples
├── guides/          # How-to guides
├── knowledge_base/   # KB specific docs
└── maintenance/     # Maintenance guides
```

## 🔍 Key Documentation Pages

1. **For New Users**
   - Start with [Quick Start Guide](docs/quick_start.md)
   - Review [Basic Usage Examples](docs/examples/basic_usage.md)
   - Check [Configuration Reference](docs/api/configuration.md)

2. **For Developers**
   - Read [Contributing Guide](CONTRIBUTING.md)
   - Study [Architecture Guide](docs/architecture/README.md)
   - Follow [Development Plan](docs/development/plan.md)

3. **For System Administrators**
   - Review [Deployment Guide](docs/maintenance/deployment.md)
   - Study [Security Best Practices](docs/guides/security.md)
   - Check [Monitoring Guide](docs/maintenance/monitoring.md)

4. **For Data Scientists**
   - Explore [Knowledge Base Guide](docs/knowledge_base/README.md)
   - Study [Query Patterns](docs/knowledge_base/query_patterns.md)
   - Review [Performance Optimization](docs/guides/optimization.md)

## 🔧 Installation

### Environment Setup

For optimal performance with GPU acceleration, we recommend using the provided conda environment:

```bash
# Create the conda environment
conda env create -f chatbot_environment.yml

# Activate the environment
conda activate chatbot
```

For detailed environment setup instructions, see [Environment Setup Documentation](docs/ENVIRONMENT_SETUP.md).

### Traditional Installation

Alternatively, you can install the package using pip:

```bash
pip install knowledge-base-agent
```

### From source

```bash
git clone https://github.com/yourusername/knowledge-base-agent.git
cd knowledge-base-agent
pip install -e .
```

## ⚙️ Configuration

Create a `.env` file in your project root:

```env
# PostgreSQL (Development)
POSTGRES_CONNECTION="postgresql://postgres@localhost:5432/knowledge_base"

# Embedding Configuration (SOTA)
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=32

# LLM Extractor Configuration (SOTA)
EXTRACTOR_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EXTRACTOR_DEVICE=cuda
EXTRACTOR_4BIT=True

# Processing
BATCH_SIZE=100
MAX_CHUNK_SIZE=2000
MIN_CHUNK_SIZE=200
OVERLAP_SIZE=100
```

## 💡 Usage

### CLI Interface

Process a document:
```bash
kb-agent process --file path/to/document.txt --title "Document Title" --source "Source"
```

Process a directory:
```bash
kb-agent process --dir path/to/documents/ --pattern "*.pdf"
```

Search the knowledge base (standard):
```bash
kb-agent query "your query" --limit 5
```

Search with advanced RAG+KG (SOTA):
```bash
kb-agent query "your query" --advanced-query --verbose
```

Start the API server:
```bash
kb-agent serve --host 0.0.0.0 --port 8000
```

### REST API

Available endpoints:

- `POST /api/documents` - Process a new document
- `GET /api/search` - Search the knowledge base
- `GET /api/documents/{doc_id}` - Get a document
- `GET /api/entities/{entity_id}/context` - Get entity context
- `GET /api/health` - Health check

Example API usage:

```python
import requests

# Process a document
response = requests.post(
    "http://localhost:8000/api/documents",
    json={
        "content": "Document content",
        "metadata": {
            "title": "Test Document",
            "source": "test"
        }
    }
)
doc_id = response.json()["document_id"]

# Search
response = requests.get(
    "http://localhost:8000/api/search",
    params={"query": "test query", "limit": 5}
)
results = response.json()["results"]
```

### Python API

```python
from knowledge_base_agent import DocumentProcessor
from knowledge_base_agent.config import get_config

# Get configuration
config = get_config()

# Create processor
processor = DocumentProcessor.from_config(config)

# Process a document
doc_id = processor.process_document(
    content="Document content",
    metadata={"title": "Test", "source": "test"}
)

# Search
results = processor.search("test query", top_k=5)
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content[:200]}...")
```

## 🛠️ Development Setup

### Environment Setup
1. Clone the repository
2. Create and activate the conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate chatbot
   ```
   *(Note: The environment uses Python 3.10.16 and is named `chatbot`. All dependencies are managed through the `environment.yml` file.)*

### PostgreSQL Setup
1. Create the database:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE knowledge_base;"
   ```

2. Verify connection:
   ```bash
   sudo -u postgres psql -d knowledge_base -c "\conninfo"
   ```

3. Add connection string to your environment:
   ```bash
   echo 'export POSTGRES_CONNECTION="postgresql://postgres@localhost:5432/knowledge_base"' >> ~/.bashrc
   source ~/.bashrc
   ```

### Current Development Status
- ✅ Environment and configuration setup
- ✅ PostgreSQL database initialization
- ✅ Basic document processing pipeline
- ✅ Advanced PDF extraction (PyMuPDF)
- ✅ Semantic chunking (NLTK)
- ✅ SentenceTransformer embeddings with GPU acceleration
- ✅ Enhanced LLM extraction with relationships
- ✅ RAG+KG query system with LLM answer synthesis
- 🔄 Testing and refinement
- 📝 Documentation updates

## 🐳 Docker

Build the image:
```