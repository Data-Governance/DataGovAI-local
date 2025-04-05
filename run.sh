#!/bin/bash

# Exit on error
set -e

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update the .env file with your configuration."
fi

# Create necessary directories
mkdir -p data/raw data/processed logs
mkdir -p volumes/{etcd,minio,milvus,mongodb,neo4j/{data,logs,conf,plugins}}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Start Docker containers
echo "Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run the knowledge base agent
echo "Starting the Knowledge Base Agent..."
python -m knowledge_base_agent serve --host 0.0.0.0 --port 8000

# Print setup completion message
echo "
Knowledge Base Agent is running!

API available at:
- http://localhost:8000/api

Services available at:
- Neo4j Browser: http://localhost:7474
- MongoDB: localhost:27017
- Milvus: localhost:19530

To stop the services:
$ docker-compose down

To view logs:
$ docker-compose logs -f
" 