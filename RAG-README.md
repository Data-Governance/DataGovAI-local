# RAG Branch - Retrieval-Augmented Generation System

## Overview

This branch implements a full Retrieval-Augmented Generation (RAG) system for the GRS documents knowledge base. The RAG system enables semantic search and intelligent querying of documents through vector embeddings stored in a PostgreSQL database with pgvector.

## Features

- **Document Processing Pipeline**: Extracts text from PDFs, semantically chunks them, generates embeddings, and stores everything in a PostgreSQL database
- **Vector Search**: Fast retrieval of relevant document chunks via embedding similarity search
- **Streamlit UI**: User-friendly interface for searching and browsing the knowledge base
- **Optimized for Performance**: GPU-accelerated embedding generation and multi-processing capabilities
- **Properly Categorized Data**: All GRS documents are classified into meaningful categories

## How It Works

1. **Document Ingestion**:
   - PDF files are read and text is extracted
   - Text is semantically chunked to preserve context
   - Chunks are embedded using a state-of-the-art language model
   - Embeddings are stored in PostgreSQL (using pgvector)

2. **Query Processing**:
   - User inputs a natural language query
   - Query is embedded using the same model
   - Vector similarity search identifies relevant document chunks
   - Results are presented to the user via the Streamlit UI

## Directory Structure

- `scripts/core/`: Core processing scripts for document ingestion
- `knowledge_base_agent/`: Main package with RAG system components
- `app.py`: Streamlit UI application file
- `data/`: Storage for document data (classified and processed)
- `tests/`: Testing infrastructure

## Getting Started

Please see the [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation and configuration instructions.

## Environment Management

We use a single, consolidated `conda` environment named `rag_env` defined in `environment_rag.yml`. This environment contains all dependencies for both the core processing pipeline and the Streamlit UI.

Activate the environment using:
```bash
conda activate rag_env
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for details on setting up this environment.

## Next Steps and Future Work

- **Knowledge Graph Integration**: Will be added in a separate branch to complement the RAG capabilities
- **Performance Optimization**: Further tuning of embedding generation and retrieval
- **Enhanced UI**: Additional visualization and interaction capabilities 