#!/bin/bash
# Example script for processing documents with PostgreSQL storage

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export POSTGRES_CONNECTION="postgres:postgres@localhost:5432/knowledge_base"

# Variables
DATA_DIR="./data"
OUTPUT_DIR="./exports"

# Create PostgreSQL database if it doesn't exist
echo "Creating PostgreSQL database 'knowledge_base' if it doesn't exist..."
psql -h localhost -U postgres -c "CREATE DATABASE knowledge_base;" 2>/dev/null || echo "Database already exists."

# Install pgvector extension if needed
echo "Installing pgvector extension in the database..."
psql -h localhost -U postgres -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null

# Process documents using PostgreSQL storage
echo "Processing documents in $DATA_DIR using PostgreSQL storage..."
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "$POSTGRES_CONNECTION" \
    process "$DATA_DIR"

# Query the knowledge base
echo "Querying the knowledge base..."
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "$POSTGRES_CONNECTION" \
    query "What is the main topic of the documents?"

# Export the knowledge base
echo "Exporting the knowledge base..."
PYTHONPATH=src python -m knowledge_base_agent.cli \
    --document-store-type postgres \
    --vector-store-type postgres \
    --knowledge-store-type postgres \
    --postgres-connection "$POSTGRES_CONNECTION" \
    export "$OUTPUT_DIR" --format json 