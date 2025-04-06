# 🧠 Knowledge Base Agent

> Building next-generation knowledge processing systems with modern technologies

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](CONTRIBUTING.md)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-2024-blue.svg)](https://github.com/yourusername/knowledge-base-agent/commits/main)

A powerful and flexible knowledge base agent that processes, stores, and retrieves information using advanced AI techniques. This repository provides comprehensive documentation and implementation for building modern knowledge base systems.

## ✨ Features

- Document processing with chunking and embedding generation
- Vector similarity search using PostgreSQL/pgvector (or other backends)
- Knowledge graph storage using PostgreSQL (or other backends like Neo4j)
- Entity and relationship extraction using LLMs
- Advanced RAG+KG query system with entity recognition and answer synthesis
- Semantic chunking for optimal document segmentation
- RESTful API with FastAPI
- CLI interface for easy interaction
- Comprehensive test suite
- Docker support for easy deployment

## 📈 SOTA Branch

The `sota` branch offers state-of-the-art features designed to maximize semantic accuracy and leverage local GPU resources:

- 🔍 **PyMuPDF** for superior PDF extraction with layout preservation
- 🧠 **Semantic Chunking** using NLTK/spaCy for context-aware document segmentation
- 🔮 **SentenceTransformers** for high-quality, GPU-accelerated embeddings
- 🤖 **Local LLMs** (Mistral, Llama, etc.) for entity extraction with relationship support
- 📊 **RAG+KG Query Engine** that combines vector search with knowledge graph queries
- 💬 **LLM-powered Answer Synthesis** for comprehensive, accurate responses

To use the SOTA features, use the `--advanced-query` flag when querying:

```bash
kb-agent query "What is the retention period for financial records?" --advanced-query
```

## 🎯 Project Context: DataGovAI

This Knowledge Base Agent is being developed as part of the **DataGovAI** platform, a collaboration between Utah Valley University's Smith College of Engineering and Technology and the Utah Office of Data Privacy (ODP).

**Goal:** DataGovAI aims to support Utah governmental entities in achieving modern, legally compliant, and efficient data governance. It aligns with key Utah statutes like GRAMA, DARSMGR, GDPA, and GIIPA, and implements the state's Privacy Program Framework.

**Functionality:** The system serves as an intelligent, centralized knowledge base consolidating Utah's legal requirements for data privacy, records management, and transparency. It helps automate compliance checks, streamline audits, and provides agencies quick access to relevant statutes and guidelines.

**Data Focus:** A primary data source for this knowledge base is the **Utah General Retention Schedules**. These schedules, maintained under DARSMGR, define how long different types of government records (Record Series) must be kept and their final disposition (e.g., destroy, transfer to archives). Processing these schedules allows DataGovAI to provide specific guidance on records management compliance.

## 🏗️ Architecture Overview

The Knowledge Base Agent is built around a central `DocumentProcessor` which orchestrates the interaction between various components:

1.  **Input**: Documents can be ingested via the CLI (`kb-agent process`) or the REST API (`POST /api/documents`). Search queries are handled via the CLI (`kb-agent search`) or the API (`GET /api/search`).
2.  **Processing**: When a document is processed:
    *   The `DocumentProcessor` receives the content and metadata.
    *   It chunks the document into smaller segments using semantic chunking.
    *   An **Embedding Model** (e.g., `SentenceTransformerEmbedding`) generates vector representations for the chunks.
    *   The original content, metadata, and extracted entities/relations are stored in the **Document Store** and **Knowledge Store**.
    *   The vector embeddings are stored in the **Vector Store** for efficient similarity search.
3.  **Search**: When a query is received:
    *   In standard mode: The processor performs semantic search to find relevant document chunks.
    *   In advanced RAG+KG mode:
        1. The `RAGKGQueryAgent` performs semantic search
        2. It extracts entities from the query using an LLM
        3. It executes targeted knowledge graph queries based on the entities
        4. It aggregates semantic chunks and KG results
        5. It uses an LLM to synthesize a comprehensive answer
4.  **Interfaces**:
    *   A **CLI** provides command-line tools for processing, searching, and managing the agent.
    *   A **REST API** (FastAPI-based) exposes the agent's functionality over HTTP.
5.  **Configuration**: System settings are managed via a configuration system using `.env` files.

This modular design allows for flexibility in choosing different storage backends, embedding models, and processing techniques.

## 🚀 Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Storage** | ChromaDB, Milvus, Neo4j, MongoDB, Elasticsearch |
| **Processing** | OpenAI GPT-4, Claude, spaCy, Hugging Face |
| **Integration** | FastAPI, GraphQL, Redis, Prometheus |

## 📚 Documentation

Start with our [Table of Contents](docs/00_table_of_contents.md) or dive into specific chapters:

- [**Introduction**](docs/00_introduction.md): Fundamentals and architecture patterns
- [**Storage Technologies**](docs/01_storage_technologies.md): Vector stores, document stores, graph databases
- [**Processing & Analysis**](docs/02_processing_and_analysis.md): Document processing, entity recognition
- [**Retrieval Systems**](docs/03_retrieval_systems.md): Vector search, hybrid approaches
- [**Language Models & AI**](docs/04_language_models.md): LLMs, embeddings, QA systems
- [**System Integration**](docs/05_system_integration.md): APIs, caching, monitoring
- [**Advanced Topics**](docs/06_advanced_topics.md): Scaling, security, optimization

## 📚 Documentation Structure

This project includes comprehensive documentation to guide development and usage:

- **[Development Plan](DEVELOPMENT_PLAN_SOTA.md)**: The central reference for all development activities
- **[Documentation Directory](docs/index.md)**: Structured documentation hub with architecture diagrams, component references, and guides
- **[KB README](KB_README.md)**: Guide to creating and querying the knowledge base

### Development Plan Tracking

To ensure all development stays aligned with the overall plan:

1. **Before coding**: Always check the development plan
   ```bash
   python -m src.knowledge_base_agent.scripts.check_plan
   ```

2. **Find relevant documentation**:
   ```bash
   python -m src.knowledge_base_agent.scripts.check_docs "RAG+KG Query"
   ```

3. **List available components**:
   ```bash
   python -m src.knowledge_base_agent.scripts.check_docs --list
   ```

4. **Install Git hooks** to automate development plan checking:
   ```bash
   python scripts/install_hooks.py
   ```

### Documentation Directories

- `docs/architecture/`: System design and data flow diagrams
- `docs/components/`: Detailed documentation for specific modules
- `docs/guides/`: How-to guides for setup and usage
- `docs/api-reference/`: Command and function references

## 🔧 Installation

### Using pip

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