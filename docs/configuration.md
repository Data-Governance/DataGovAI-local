# 🔧 DataGovAI Configuration Guide

This document provides a comprehensive overview of all configuration settings used by the DataGovAI application. It is important to ensure consistent configuration across all components for proper operation.

## 📋 Configuration Sources

Configuration settings are loaded from the following sources, in order of precedence:

1. **Environment Variables**: Set directly in the environment
2. **.env File**: Located in the project root directory
3. **Default Values**: Hardcoded in the application

## 🚀 Application Startup Configuration

The application uses `app_launcher.py` to start the Streamlit application. This launcher script:

1. Applies PyTorch-Streamlit compatibility fixes
2. Sets specific Streamlit environment variables
3. Launches the main application (`app.py`)

### Streamlit Server Configuration

| Setting | Source | Current Value | Description |
|---------|--------|---------------|-------------|
| `STREAMLIT_SERVER_PORT` | app_launcher.py | `8505` | Port where Streamlit server runs |
| `STREAMLIT_SERVER_HEADLESS` | app_launcher.py | `true` | Run without opening browser |
| `STREAMLIT_BROWSER_GATHER_USAGE_STATS` | app_launcher.py | `false` | Disable usage statistics |
| `STREAMLIT_FILE_WATCHER_TYPE` | app_launcher.py | `none` | Disable file watcher for compatibility |

⚠️ **Important Note**: There is a discrepancy between the `.env` file (which sets port `8501`) and `app_launcher.py` (which sets port `8505`). The `app_launcher.py` setting takes precedence, so the application runs on port `8505`.

## 🗃️ Database Configuration

### PostgreSQL Connection

| Setting | Source | Current Value | Comment |
|---------|--------|---------------|---------|
| `POSTGRES_CONNECTION` | app.py (line 44) | `postgresql://postgres:password@127.0.0.1:5432/knowledge_base` | Hardcoded in app.py |

⚠️ **Important**: The connection string in `app.py` overrides any setting in the `.env` file. This ensures consistent database access regardless of environment settings.

### Vector Store Configuration

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `VECTOR_DIMENSION` | .env | `768` | Dimension for the all-mpnet-base-v2 model |
| `DOCUMENT_STORE_TYPE` | .env | `postgresql` | Document storage backend |
| `VECTOR_STORE_TYPE` | .env | `postgresql` | Vector storage backend |
| `KNOWLEDGE_STORE_TYPE` | .env | `postgresql` | Knowledge graph storage backend |

## 🤖 AI Model Configuration

### OpenAI Integration

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `OPENAI_API_KEY` | .env | `sk-proj-***` | OpenAI API key |
| `OPENAI_LLM_MODEL` | app.py | `gpt-4o-mini` | Default LLM model |

### Embedding Model

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `EMBEDDING_MODEL` | .env | `all-mpnet-base-v2` | SentenceTransformer model |
| `EMBEDDING_DEVICE` | .env | `cuda` | Device for embedding generation (cuda/cpu) |
| `EMBEDDING_BATCH_SIZE` | .env | `1024` | Batch size for embedding generation |
| `EMBEDDING_MAX_LENGTH` | .env | `2048` | Maximum token length for embeddings |

### LLM Extraction

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `USE_LOCAL_LLM` | .env | `False` | Whether to use local LLMs for extraction |
| `EXTRACTOR_MODEL` | .env | `mistralai/Mistral-7B-Instruct-v0.2` | Model for entity extraction |
| `EXTRACTOR_DEVICE` | .env | `cuda` | Device for LLM extraction |
| `EXTRACTOR_4BIT` | .env | `True` | Use 4-bit quantization |

## 🧠 NLP Configuration

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `SPACY_MODEL` | .env | `en_core_web_sm` | spaCy model for text processing |
| `ENABLE_GPU` | .env | `true` | Use GPU for NLP processing |

## 📄 Document Processing

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `MAX_CHUNK_SIZE` | .env | `2000` | Maximum chunk size in characters |
| `MIN_CHUNK_SIZE` | .env | `200` | Minimum chunk size in characters |
| `OVERLAP_SIZE` | .env | `100` | Overlap between chunks in characters |
| `SUPPORTED_FILE_TYPES` | .env | `.txt,.pdf,.md,.doc,.docx,.html` | Supported file extensions |
| `BATCH_SIZE` | .env | `100` | Batch size for document processing |

## 🔌 API Configuration

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `API_HOST` | .env | `0.0.0.0` | API host address |
| `API_PORT` | .env | `8000` | API server port |
| `API_KEY` | .env | `generate-a-secure-random-key` | API authentication key |
| `ENABLE_CORS` | .env | `true` | Enable CORS for API |
| `ALLOWED_ORIGINS` | .env | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins |

## 📝 Logging Configuration

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `LOG_LEVEL` | .env | `INFO` | Logging level |
| `ENABLE_REQUEST_LOGGING` | .env | `true` | Log API requests |
| `LOG_FILE` | .env | `knowledge_base.log` | Log file name |

## 🔐 Authentication

| Setting | Source | Default | Description |
|---------|--------|---------|-------------|
| `HUGGING_FACE_HUB_TOKEN` | .env | `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` | Hugging Face API token |

## ⚠️ Configuration Issues and Recommendations

1. **Port Configuration Discrepancy**:
   - **Issue**: `.env` sets `STREAMLIT_SERVER_PORT=8501` but `app_launcher.py` overrides with `8505`
   - **Recommendation**: Update `.env` to match `app_launcher.py` for consistency: `STREAMLIT_SERVER_PORT=8505`

2. **Hardcoded Database Connection**:
   - **Issue**: `app.py` hardcodes the PostgreSQL connection string, ignoring `.env`
   - **Recommendation**: Remove the hardcoded override in `app.py` and rely on `.env` configuration

3. **OpenAI API Key Exposure**:
   - **Issue**: API key is directly stored in `.env` file which may be committed to version control
   - **Recommendation**: Use a key vault solution or environment variables set outside of `.env`

4. **Default API Key**:
   - **Issue**: `.env` contains a placeholder for `API_KEY`
   - **Recommendation**: Generate a proper random key for production using `openssl rand -hex 32`

## 🚀 Recommended Configuration Setup

For consistent configuration and security:

1. Create a proper `.env` file with all required settings
2. Ensure `app_launcher.py` and `.env` use consistent port settings
3. Remove hardcoded configuration overrides in `app.py`
4. Generate secure random keys for API authentication
5. Store sensitive credentials in environment variables outside of `.env`

Example `.env` configuration:

```env
# Database Configuration
POSTGRES_CONNECTION=postgresql://postgres:password@127.0.0.1:5432/knowledge_base

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8505
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key
OPENAI_LLM_MODEL=gpt-4o-mini

# Embedding Configuration
EMBEDDING_MODEL=all-mpnet-base-v2
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=1024
EMBEDDING_MAX_LENGTH=2048

# Document Processing
MAX_CHUNK_SIZE=2000
MIN_CHUNK_SIZE=200
OVERLAP_SIZE=100
BATCH_SIZE=100

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-generated-secure-key
```

## 🔄 Applying Configuration Changes

To apply configuration changes:

1. Edit `.env` file with the desired settings
2. Restart the application using `python app_launcher.py`
3. Verify the settings are correctly applied by checking the application logs 