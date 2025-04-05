# PostgreSQL Knowledge Base Storage

This guide explains how to set up and use PostgreSQL as a storage backend for the Knowledge Base Agent.

## Prerequisites

1. PostgreSQL server installed and running
2. pgvector extension installed in PostgreSQL
3. Python dependencies installed:
   - psycopg2
   - sqlalchemy
   - pgvector
   - alembic

## Installation

### 1. Install PostgreSQL

#### Ubuntu
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

### 2. Install pgvector extension

#### Ubuntu
```bash
sudo apt install postgresql-server-dev-14  # Use your PostgreSQL version
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

#### macOS
```bash
brew install pgvector
```

### 3. Install Python dependencies

```bash
conda activate chatbot
conda install -c conda-forge psycopg2 sqlalchemy pgvector alembic
```

## Database Setup

1. Create a PostgreSQL database:
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE knowledge_base;
postgres=# \q
```

2. Enable the pgvector extension in the database:
```bash
sudo -u postgres psql -d knowledge_base -c "CREATE EXTENSION vector;"
```

## Configuration

You can configure the storage backend using either:

### Environment Variables
```bash
export STORAGE_PATH="/path/to/your/storage"
export POSTGRES_CONNECTION="user:password@localhost:5432/knowledge_base"
```

### Command-Line Arguments
```bash
python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "user:password@localhost:5432/knowledge_base" \
    process ./data
```

## Usage

### Processing Documents

```bash
# Using PostgreSQL for all stores
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "postgres:postgres@localhost:5432/knowledge_base" \
    process ./data
```

### Querying the Knowledge Base

```bash
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "postgres:postgres@localhost:5432/knowledge_base" \
    query "What are the main topics in these documents?"
```

### Exporting the Knowledge Base

```bash
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "postgres:postgres@localhost:5432/knowledge_base" \
    export ./exports --format json
```

## Database Structure

The PostgreSQL storage implementation uses the following tables:

1. **documents**: Stores the original documents and their metadata
2. **chunk_embeddings**: Stores vector embeddings for document chunks
3. **entities**: Stores entities extracted from documents
4. **relationships**: Stores relationships between entities

## Monitoring the Database

You can monitor and query the database directly using PostgreSQL tools:

```bash
psql -h localhost -U postgres -d knowledge_base

# Count documents
knowledge_base=# SELECT COUNT(*) FROM documents;

# Count embeddings
knowledge_base=# SELECT COUNT(*) FROM chunk_embeddings;

# Count entities
knowledge_base=# SELECT COUNT(*) FROM entities;

# Count relationships
knowledge_base=# SELECT COUNT(*) FROM relationships;

# List entities by type
knowledge_base=# SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;
```

## Example Script

For a complete example, see the `postgres-example.sh` script in the repository. 