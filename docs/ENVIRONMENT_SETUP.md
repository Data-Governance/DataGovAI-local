# Environment Setup for Knowledge Base Agent

This document explains how to set up the environment required for running the Knowledge Base Agent.

## GPU-Enabled Environment Setup

For optimal performance, we use a conda environment with GPU support. The provided `chatbot_environment.yml` file contains all the necessary packages for GPU processing.

### Requirements

- Anaconda or Miniconda installed
- CUDA-capable GPU (CUDA 11.8 compatible)
- About 5GB of disk space for the environment

### Setting up the environment

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd DataGovAI
   ```

2. Create the conda environment from the provided YAML file:
   ```bash
   conda env create -f chatbot_environment.yml
   ```

3. Activate the environment:
   ```bash
   conda activate chatbot
   ```

### Key packages included

The environment includes:
- Python 3.10
- PyTorch with CUDA support
- sentence-transformers 3.4.1
- spaCy 3.7.5 with en_core_web_sm model
- scikit-learn 1.6.1
- NumPy, pandas, and other data science libraries

## Processing Documents

To process documents and build the knowledge base with GPU acceleration:

```bash
conda activate chatbot
python scripts/process_documents.py
```

Options:
- `--data-dir <directory>`: Specify a custom data directory (default: "data")
- `--limit <number>`: Limit the number of documents to process

## Querying the Knowledge Base

To query the knowledge base after processing documents:

```bash
conda activate chatbot
python scripts/query_knowledge_base.py "your query here"
```

## Troubleshooting

If you encounter CUDA/GPU issues:
1. Verify your CUDA installation with `nvidia-smi`
2. Check PyTorch can access the GPU: `python -c "import torch; print(torch.cuda.is_available())"`
3. If problems persist, you can force CPU usage by setting `EMBEDDING_DEVICE=cpu` in your `.env` file 