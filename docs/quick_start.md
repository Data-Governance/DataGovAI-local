# Quick Start Guide

This guide will help you get started with the Knowledge Base Agent quickly.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ with pgvector extension
- CUDA-capable GPU (recommended for SOTA features)
- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/knowledge-base-agent.git
   cd knowledge-base-agent
   ```

2. **Set up the conda environment:**
   ```bash
   conda env create -f chatbot_environment.yml
   conda activate chatbot
   ```

3. **Configure the environment:**
   Create a `.env` file in the project root:
   ```env
   POSTGRES_CONNECTION="postgresql://postgres@localhost:5432/knowledge_base"
   EMBEDDING_MODEL=all-mpnet-base-v2
   EMBEDDING_DEVICE=cuda
   EMBEDDING_BATCH_SIZE=32
   ```

## Basic Usage

1. **Process documents:**
   ```bash
   kb-agent process --file path/to/document.pdf
   ```

2. **Query the knowledge base:**
   ```bash
   kb-agent query "What is the retention period for financial records?"
   ```

3. **Use advanced RAG+KG queries:**
   ```bash
   kb-agent query "Show me all documents about personnel files" --advanced-query
   ```

## Next Steps

- Read the [Architecture Guide](architecture/README.md) to understand the system
- Check [Basic Usage Examples](examples/basic_usage.md) for more examples
- Review [Configuration Reference](api/configuration.md) for customization
- Join our [Community](../CONTRIBUTING.md) to contribute

## Troubleshooting

Common issues and solutions:

1. **GPU Not Detected**
   - Verify CUDA installation: `python -c "import torch; print(torch.cuda.is_available())"`
   - Check GPU drivers
   - See [GPU Configuration Guide](guides/gpu_setup.md)

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string in `.env`
   - See [Database Setup Guide](guides/database_setup.md)

3. **Memory Issues**
   - Adjust batch sizes in `.env`
   - Use 4-bit quantization for LLMs
   - See [Performance Optimization](guides/optimization.md)

For more help, check our [Troubleshooting Guide](maintenance/troubleshooting.md). 