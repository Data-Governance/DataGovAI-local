# Knowledge Base Creation Guide

This guide explains how to create and query the knowledge base for Utah General Retention Schedules (GRS) using our state-of-the-art RAG+KG system.

## Prerequisites

1. **Environment Setup**:
   - Python virtual environment: `sota_venv`
   - Required packages installed: `pymupdf`, `nltk`, `spacy`, `sentence-transformers`, `torch`, `transformers`, `bitsandbytes`
   - GPU with CUDA support (recommended)

2. **PostgreSQL with pgvector**:
   - PostgreSQL 13+ with pgvector extension
   - Database `knowledge_base` created
   - User with permissions to create tables

3. **Configuration**:
   - `.env` file with appropriate settings (see below)

## Configuration

Create or update your `.env` file with these settings:

```env
# PostgreSQL Configuration
POSTGRES_CONNECTION=postgresql://kb_agent_user:password@localhost:5432/knowledge_base
DOCUMENT_STORE_TYPE=postgresql

# Embedding Configuration
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=32

# LLM Extractor Configuration
EXTRACTOR_MODEL=mistralai/Mistral-7B-Instruct-v0.2
EXTRACTOR_DEVICE=cuda
EXTRACTOR_4BIT=True

# Document Processing
MAX_CHUNK_SIZE=2000
MIN_CHUNK_SIZE=200
OVERLAP_SIZE=100
```

## Building the Knowledge Base

### Step 1: Activate the Environment

```bash
source sota_venv/bin/activate
```

### Step 2: Initialize the Database

This creates the required tables in PostgreSQL:

```bash
python create_knowledge_base.py --init-db
```

### Step 3: Process GRS Documents

Process all documents in the `data` directory:

```bash
python create_knowledge_base.py --process
```

For a smaller test run, use the `--limit` option:

```bash
python create_knowledge_base.py --process --limit 10
```

## Querying the Knowledge Base

Use the query script to interact with the knowledge base:

```bash
python query_knowledge_base.py "What is the retention period for zoning maps?"
```

For more detailed output:

```bash
python query_knowledge_base.py "What is the retention period for zoning maps?" --verbose
```

To use standard vector search instead of the RAG+KG agent:

```bash
python query_knowledge_base.py "What is the retention period for zoning maps?" --standard
```

## How It Works

The system works in the following way:

1. **Document Processing**:
   - PDFs are extracted using PyMuPDF for high-quality text extraction
   - Text is semantically chunked into meaningful segments using NLTK
   - Embeddings are generated using SentenceTransformers
   - Entities and relationships are extracted using a local LLM
   - All data is stored in PostgreSQL with pgvector for vector similarity search

2. **RAG+KG Querying**:
   - User query is processed to extract relevant entities
   - Vector search finds semantically similar text chunks
   - Knowledge graph queries find specific entities and relationships
   - Results are aggregated and passed to an LLM for answer synthesis
   - A comprehensive answer is generated based on all retrieved information

## Troubleshooting

- **Database Connection Issues**:
  - Check your PostgreSQL connection string in `.env`
  - Ensure the database and pgvector extension are set up correctly

- **GPU Memory Issues**:
  - Reduce batch sizes for embeddings and LLM processing
  - Set `EXTRACTOR_4BIT=True` to use 4-bit quantization for the LLM
  - Use a smaller LLM model if needed

- **Empty or Poor Results**:
  - Check if documents were processed successfully
  - Adjust the `min_score` parameter for queries
  - Try more specific queries that match content in the documents

## Example Queries

Here are some example queries to try:

- "What is the retention period for zoning maps?"
- "Tell me about the retention schedule for financial records"
- "What happens to yearbooks after their retention period?"
- "What is the disposition action for youth case files?"
- "What legal authorities are cited for record series GRS-664?" 