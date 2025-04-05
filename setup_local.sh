#!/bin/bash

# Exit on error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for conda
if ! command_exists conda; then
    echo "Conda is not installed. Please install Miniconda or Anaconda first."
    exit 1
fi

# Create and activate conda environment
echo "Creating conda environment 'chatbot'..."
conda create -y -n chatbot python=3.12
echo "Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate chatbot

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update the .env file with your configuration."
fi

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Run linting
echo "Running linting..."
flake8 src/ tests/
mypy src/ tests/

# Format code
echo "Formatting code..."
black src/ tests/
isort src/ tests/

echo "Setup completed successfully!"
echo "To activate the environment, run: conda activate chatbot"

# Create necessary directories for Docker volumes
mkdir -p volumes/{etcd,minio,milvus,mongodb,neo4j/{data,logs,conf,plugins}}

# Install Python dependencies
pip install -r requirements.txt

# Install SpaCy model
python -m spacy download en_core_web_sm

# Start Docker containers
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Initialize Milvus collection
python - << EOF
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import time

def wait_for_connection(host, port, max_retries=5):
    for i in range(max_retries):
        try:
            connections.connect(host=host, port=port)
            print("Successfully connected to Milvus")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: Failed to connect to Milvus. Retrying...")
            time.sleep(5)
    return False

if wait_for_connection("localhost", 19530):
    # Create collection if it doesn't exist
    if not utility.has_collection("knowledge_base"):
        dim = 768  # dimension for all-MiniLM-L6-v2
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        ]
        schema = CollectionSchema(fields=fields, description="Knowledge base collection")
        collection = Collection(name="knowledge_base", schema=schema)
        
        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print("Successfully initialized Milvus collection")
    else:
        print("Milvus collection already exists")
else:
    print("Failed to connect to Milvus")
EOF

# Print setup completion message
echo "
Local environment setup completed!

Services available at:
- Milvus: localhost:19530
- MongoDB: localhost:27017
- Neo4j: 
  - Bolt: localhost:7687
  - Browser: http://localhost:7474

Please update the .env file with the following credentials:
- MongoDB: admin/admin_password
- Neo4j: neo4j/your_password

To start using the knowledge base:
1. Update credentials in .env file
2. Run your application
3. Monitor the services using:
   - Neo4j Browser: http://localhost:7474
   - MongoDB Compass (optional): mongodb://admin:admin_password@localhost:27017

To stop the services:
$ docker-compose down

To view logs:
$ docker-compose logs -f
" 