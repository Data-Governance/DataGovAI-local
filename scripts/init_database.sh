#!/bin/bash

# Exit on error
set -e

echo "Initializing PostgreSQL database for Knowledge Base Agent..."

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "Error: PostgreSQL server is not running."
    exit 1
fi

# Create database if it doesn't exist
echo "Creating database 'knowledge_base' if it doesn't exist..."
sudo -u postgres psql -c "CREATE DATABASE knowledge_base;" 2>/dev/null || echo "Database already exists."

# Install pgvector extension
echo "Installing pgvector extension in the database..."
sudo -u postgres psql -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null && echo "pgvector extension installed" || echo "Failed to install pgvector extension"

# Drop existing tables to avoid foreign key issues
echo "Dropping existing tables if they exist..."
sudo -u postgres psql -d knowledge_base -c "
DROP TABLE IF EXISTS relationships CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
" && echo "Existing tables dropped" || echo "Failed to drop tables"

# Create tables
echo "Creating tables..."
sudo -u postgres psql -d knowledge_base -c "
-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunks table with vector support
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

-- Entities table
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    entity_id VARCHAR(255) UNIQUE NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

-- Relationships table
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    source_entity_id VARCHAR(255) NOT NULL,
    target_entity_id VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_entity_id, target_entity_id, type),
    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_documents_document_id ON documents(document_id);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_entities_document_id ON entities(document_id);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX idx_relationships_type ON relationships(type);
" && echo "Database tables created successfully" || echo "Failed to create tables"

# Create vector index
echo "Creating vector index on chunks table..."
sudo -u postgres psql -d knowledge_base -c "
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
" && echo "Vector index created successfully" || echo "Failed to create vector index"

echo "Database initialization complete!" 