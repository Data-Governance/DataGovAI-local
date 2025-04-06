# Knowledge Base Agent - Architecture Overview

## System Architecture

The Knowledge Base Agent employs a modular architecture with several key components organized in a pipeline:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│  Document      │────▶│  Text          │────▶│  Embedding     │────▶│  Storage       │
│  Ingestion     │     │  Processing    │     │  Generation    │     │  Layer         │
│                │     │                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
                                                                            │
                                                                            │
                                                                            ▼
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│  Answer        │◀────│  Query         │◀────│  Search        │◀────│  Entity        │
│  Synthesis     │     │  Planning      │     │  Systems       │     │  Extraction    │
│                │     │                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

### Core Components

1. **Document Processing Pipeline**
   - **Ingestor**: Handles PDF extraction using PyMuPDF (via `fitz`)
   - **Processor**: Manages document processing workflow (`DocumentProcessor` class)
   - **Chunker**: Divides documents into semantic chunks using NLTK
   - **Embedder**: Generates vector embeddings using SentenceTransformers

2. **Storage Layer**
   - **Document Store**: Primary storage for document content and metadata
   - **Vector Store**: Stores and indexes embeddings for similarity search
   - **Knowledge Store**: Graph database for entities and relationships

3. **Retrieval System**
   - **Query Agent**: The `RAGKGQueryAgent` that orchestrates the query process
   - **Vector Search**: Semantic similarity search over document chunks
   - **Knowledge Graph Queries**: Direct lookups for specific entities

4. **LLM Integration**
   - **Entity Extraction**: Uses LLMs to extract entities from documents
   - **Answer Synthesis**: Combines retrieval results to generate answers

## Data Flow

### Document Processing Flow

1. Documents are ingested through the CLI (`create_knowledge_base.py`) or API
2. Text is extracted using PyMuPDF and cleaned
3. Text is divided into semantic chunks using `semantic_chunk_document`
4. Embeddings are generated for each chunk using `SentenceTransformerEmbedding`
5. Entity extraction is performed using `LocalLlmExtractor`
6. All data is stored in PostgreSQL with pgvector extension

### Query Flow

1. User query is received through CLI (`query_knowledge_base.py`) or API
2. Query is embedded using the same embedding model
3. Vector similarity search is performed to retrieve relevant chunks
4. Entities are extracted from the query using an LLM
5. Knowledge graph queries are constructed based on extracted entities
6. Results from both vector search and knowledge graph are aggregated
7. Answer is synthesized using an LLM

## Files Structure

- `src/knowledge_base_agent/` - Main package
  - `processor.py` - Core document processing logic
  - `query_agent.py` - RAG+KG query system
  - `cli.py` - Command-line interface
  - `config.py` - Configuration management
  - `extractors/` - Entity extraction modules
    - `local_llm_extractor.py` - LLM-based entity extraction
  - `embeddings/` - Embedding modules
    - `sentence_transformer_embedding.py` - Vector embedding generation
  - `storage/` - Storage backends
    - `postgresql/` - PostgreSQL storage implementation
  - `utils/` - Utility functions
    - `text.py` - Text processing utilities

## Scripts

- `create_knowledge_base.py` - Database initialization and document processing
- `query_knowledge_base.py` - Interface for querying the knowledge base

## Technology Stack

- **PDF Processing**: PyMuPDF
- **Text Processing**: NLTK, spaCy
- **Embeddings**: SentenceTransformers, PyTorch
- **Entity Extraction**: Hugging Face Transformers
- **Database**: PostgreSQL with pgvector
- **Quantization**: bitsandbytes for 4-bit quantization 