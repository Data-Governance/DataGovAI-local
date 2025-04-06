# RAG System Environment Setup Guide

This guide provides instructions for setting up the environment for the Knowledge Base RAG system.

## Prerequisites

- Anaconda or Miniconda
- CUDA-capable GPU
- CUDA Drivers 12.1+ installed
- PostgreSQL 15+ with pgvector extension

## Environment Setup

We use a single conda environment that includes all necessary dependencies for both ML processing and UI components.

### Create and Activate Environment

```bash
# Create environment from the configuration file
conda env create -f environment.yml

# Activate the environment
conda activate rag_env
```

### Verify Installation

```bash
# Check PyTorch and CUDA
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA available: {torch.cuda.is_available()}, CUDA version: {torch.version.cuda}')"

# Check Sentence Transformers
python -c "import sentence_transformers; print(f'Sentence-Transformers: {sentence_transformers.__version__}')"
```

### Environment Configuration

Before running the application, make sure to configure your environment variables:

1. Copy the `.env.example` file to `.env`
2. Set the following variables:
   - `POSTGRES_CONNECTION`: PostgreSQL connection string
   - `EMBEDDING_DEVICE`: Set to "cuda" to use GPU
   - `EMBEDDING_BATCH_SIZE`: Adjust based on your GPU memory
   - `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI services)

## Database Setup

```bash
# Create the database (if not already created)
PGPASSWORD=your_password psql -U your_username -h 127.0.0.1 -p 5432 -c "CREATE DATABASE knowledge_base;"

# Enable the pgvector extension
PGPASSWORD=your_password psql -U your_username -h 127.0.0.1 -p 5432 -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Running the Application

### Process Documents

```bash
conda activate rag_env
python scripts/core/process_documents.py
```

### Start the Streamlit UI

```bash
conda activate rag_env
streamlit run app.py
```

## Troubleshooting

### CUDA Issues
- Ensure CUDA drivers are properly installed
- Try reinstalling PyTorch with the appropriate CUDA version
- Verify compatibility between PyTorch and CUDA versions

### Package Conflicts
- If you encounter dependency conflicts, consider updating the environment.yml file and recreating the environment

### Database Connection
- Verify PostgreSQL is running
- Check PostgreSQL connection string in .env file
- Ensure pgvector extension is enabled

## Maintenance

To update dependencies:

```bash
# Update the environment.yml file
# Then update the environment
conda env update -f environment.yml
``` 