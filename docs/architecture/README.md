# 🏗️ DataGovAI Architecture

## System Overview

DataGovAI is built on a hybrid RAG (Retrieval-Augmented Generation) + KG (Knowledge Graph) architecture, specifically designed for processing and querying Utah's General Retention Schedules (GRS).

### High-Level Architecture

| Layer | Components | Purpose |
|-------|------------|---------|
| Interface | • Web UI<br>• REST API<br>• CLI | User interaction and data input |
| Processing | • Document Processor<br>• Semantic Chunker<br>• Entity Extractor | Document analysis and knowledge extraction |
| Storage | • PostgreSQL + pgvector<br>• Vector Store<br>• Knowledge Graph | Hybrid data storage |
| Query | • RAG Engine<br>• KG Query Engine<br>• Response Synthesizer | Intelligent query processing |

### Core Components

#### 1. Document Processing Pipeline

```mermaid
graph TD
    A[Input Document] --> B[PyMuPDF Extractor]
    B --> C[Text Preprocessing]
    C --> D[Semantic Chunking]
    D --> E[Embedding Generation]
    D --> F[Entity Extraction]
    E --> G[Vector Storage]
    F --> H[Knowledge Graph]
```

| Component | Technology | Purpose |
|-----------|------------|---------|
| PDF Extraction | PyMuPDF | High-quality PDF text extraction |
| Text Processing | NLTK/spaCy | Semantic text analysis |
| Chunking | Custom Algorithm | Context-aware document segmentation |
| Embedding | SentenceTransformers | Vector representation generation |
| Entity Extraction | Local LLM | Structured information extraction |

#### 2. Storage System

| Component | Implementation | Purpose |
|-----------|---------------|----------|
| Document Store | PostgreSQL | Original document storage |
| Vector Store | pgvector | Semantic search capabilities |
| Knowledge Graph | PostgreSQL | Structured relationship storage |

#### 3. Query System

| Component | Features | Implementation |
|-----------|----------|----------------|
| RAG Engine | • Semantic search<br>• Context retrieval | SentenceTransformers + pgvector |
| KG Engine | • Fact retrieval<br>• Relationship queries | SQL + Graph Queries |
| Synthesizer | • Answer generation<br>• Source citation | Local LLM |

## Data Flow

### 1. Document Ingestion

```mermaid
sequenceDiagram
    participant U as User
    participant P as Processor
    participant D as Database
    
    U->>P: Submit Document
    P->>P: Extract Text
    P->>P: Generate Chunks
    P->>P: Create Embeddings
    P->>P: Extract Entities
    P->>D: Store Document
    P->>D: Store Vectors
    P->>D: Store Relations
```

### 2. Query Processing

```mermaid
sequenceDiagram
    participant U as User
    participant Q as Query Engine
    participant R as RAG
    participant K as KG
    participant S as Synthesizer
    
    U->>Q: Submit Query
    Q->>R: Semantic Search
    Q->>K: Fact Retrieval
    R-->>Q: Relevant Contexts
    K-->>Q: Structured Facts
    Q->>S: Generate Response
    S->>U: Return Answer
```

## System Requirements

| Component | Requirement | Purpose |
|-----------|------------|----------|
| CPU | 4+ cores | Document processing |
| RAM | 16+ GB | Model operations |
| GPU | CUDA-capable | Embedding generation |
| Storage | 100+ GB SSD | Document storage |
| Database | PostgreSQL 14+ | Data management |

## Security Architecture

| Layer | Measures | Implementation |
|-------|----------|----------------|
| Authentication | • API keys<br>• JWT tokens | Custom middleware |
| Authorization | • Role-based access<br>• Document-level permissions | Database-level |
| Data Protection | • Encryption at rest<br>• Secure connections | PostgreSQL features |

## Performance Optimization

| Area | Technique | Implementation |
|------|-----------|----------------|
| Embedding | Batch processing | GPU acceleration |
| Search | Vector indexing | pgvector indexes |
| Caching | Query results | Redis (optional) |

## Integration Points

| System | Integration Type | Purpose |
|--------|-----------------|----------|
| Document Management | REST API | Document ingestion |
| User Systems | OAuth2 | Authentication |
| Monitoring | Prometheus/Grafana | System metrics |

For detailed component documentation, see:
- [Component Details](./components.md)
- [Data Flow](./data_flow.md)
- [Security Implementation](./security.md) 