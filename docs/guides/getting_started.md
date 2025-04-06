# Getting Started with Knowledge Base Agent

This guide walks you through setting up and using the Knowledge Base Agent for processing and querying Utah General Retention Schedules (GRS).

## Prerequisites

Before you begin, make sure you have:

- Python 3.10 or higher installed
- CUDA-compatible GPU (recommended for optimal performance)
- PostgreSQL 13+ with pgvector extension installed
- Git for cloning the repository

## Environment Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/knowledge-base-agent.git
cd knowledge-base-agent
```

### Step 2: Create and Activate Virtual Environment

Using venv:
```bash
python -m venv sota_venv
source sota_venv/bin/activate  # On Windows: sota_venv\Scripts\activate
```

Using conda:
```bash
conda env create -f environment.yml
conda activate chatbot
```

### Step 3: Install Dependencies

```bash
pip install -e .

# Install additional dependencies for SOTA features
pip install pymupdf nltk spacy sentence-transformers torch transformers bitsandbytes

# Download required NLP models
python -m nltk.downloader punkt
python -m spacy download en_core_web_sm
```

### Step 4: Configure the Environment

Create a `.env` file in the project root:

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

Adjust these settings based on your system capabilities, especially if you're not using a GPU.

## Database Setup

### Step 1: Create the PostgreSQL Database

```bash
sudo -u postgres psql -c "CREATE DATABASE knowledge_base;"
sudo -u postgres psql -c "CREATE USER kb_agent_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE knowledge_base TO kb_agent_user;"
```

### Step 2: Install pgvector Extension

```bash
sudo -u postgres psql -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 3: Initialize the Database Schema

```bash
python create_knowledge_base.py --init-db
```

## Processing Documents

### Step 1: Prepare Document Directory

Create a directory to store your GRS documents:

```bash
mkdir -p data
```

Place your PDF documents in the data directory.

### Step 2: Process Documents

Process all documents in the data directory:

```bash
python create_knowledge_base.py --process
```

For a test run with a limited number of documents:

```bash
python create_knowledge_base.py --process --limit 5
```

The system will:
1. Extract text from PDFs using PyMuPDF
2. Split text into semantic chunks using NLTK
3. Generate embeddings using SentenceTransformers
4. Extract entities and relationships using the local LLM
5. Store everything in the PostgreSQL database

## Querying the Knowledge Base

### Basic Querying

```bash
python query_knowledge_base.py "What is the retention period for zoning maps?"
```

### Advanced Querying (RAG+KG)

This is the default mode that combines vector search with knowledge graph querying:

```bash
python query_knowledge_base.py "What is the retention period for financial records?"
```

### Verbose Mode

For more detailed output that shows vector results and extracted entities:

```bash
python query_knowledge_base.py "What happens to yearbooks after their retention period?" --verbose
```

### Standard Vector Search

To use only vector search without the knowledge graph component:

```bash
python query_knowledge_base.py "What legal authorities are cited for record series GRS-664?" --standard
```

## Troubleshooting

### Common Issues

#### Database Connection Issues

If you encounter database connection errors:

1. Check your PostgreSQL service is running:
   ```bash
   sudo service postgresql status
   ```

2. Verify connection parameters in `.env`:
   ```bash
   POSTGRES_CONNECTION=postgresql://kb_agent_user:password@localhost:5432/knowledge_base
   ```

3. Test the connection directly:
   ```bash
   psql -U kb_agent_user -d knowledge_base -h localhost
   ```

#### GPU Memory Issues

If you encounter CUDA out of memory errors:

1. Reduce batch sizes:
   ```env
   EMBEDDING_BATCH_SIZE=16
   ```

2. Use 4-bit quantization (already enabled by default):
   ```env
   EXTRACTOR_4BIT=True
   ```

3. Use a smaller LLM model:
   ```env
   EXTRACTOR_MODEL=mistralai/Mistral-7B-Instruct-v0.1
   ```

4. Fall back to CPU if necessary:
   ```env
   EMBEDDING_DEVICE=cpu
   EXTRACTOR_DEVICE=cpu
   ```

#### Empty Results

If queries return no results:

1. Check if documents were processed successfully:
   ```bash
   psql -U kb_agent_user -d knowledge_base -c "SELECT COUNT(*) FROM documents;"
   ```

2. Reduce the minimum similarity score:
   ```bash
   python query_knowledge_base.py "your query" --min-score 0.5
   ```

3. Use more generic query terms that are likely to appear in the documents

## Next Steps

After setting up the basic system, you might want to:

1. **Customize Entity Extraction**: Modify the entity extraction prompts in `src/knowledge_base_agent/extractors/local_llm_extractor.py`

2. **Optimize Performance**: Adjust chunking parameters and batch sizes in `.env`

3. **Add API Access**: Use the FastAPI interface by running `python -m src.knowledge_base_agent serve`

4. **Extend the Knowledge Graph**: Add additional relationship types by modifying the extraction logic

For more details, see the [Architecture Overview](../architecture/overview.md) and [Query Agent](../components/query_agent.md) documentation. 