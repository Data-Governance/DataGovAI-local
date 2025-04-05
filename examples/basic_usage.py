"""
Basic example of using the Knowledge Base Agent
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from knowledge_base_agent.processors import DocumentProcessor
from knowledge_base_agent.models import ProcessingConfig, Document
from knowledge_base_agent.storage import KnowledgeStore

# Load environment variables
load_dotenv()

def main():
    # Initialize the knowledge store
    knowledge_store = KnowledgeStore(
        mongodb_host=os.getenv("MONGODB_HOST", "localhost"),
        mongodb_port=int(os.getenv("MONGODB_PORT", "27017")),
        mongodb_username=os.getenv("MONGODB_USERNAME", "root"),
        mongodb_password=os.getenv("MONGODB_PASSWORD", "example"),
        mongodb_database=os.getenv("MONGODB_DATABASE", "knowledge_base"),
        neo4j_host=os.getenv("NEO4J_HOST", "localhost"),
        neo4j_port=int(os.getenv("NEO4J_PORT", "7687")),
        neo4j_username=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "password"),
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        milvus_host=os.getenv("MILVUS_HOST", "localhost"),
        milvus_port=int(os.getenv("MILVUS_PORT", "19530")),
        milvus_collection=os.getenv("MILVUS_COLLECTION", "knowledge_base"),
    )

    # Create processing configuration
    config = ProcessingConfig(
        batch_size=int(os.getenv("BATCH_SIZE", "32")),
        max_tokens=int(os.getenv("MAX_TOKENS", "512")),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        spacy_model=os.getenv("SPACY_MODEL", "en_core_web_sm"),
    )

    # Initialize document processor
    processor = DocumentProcessor(knowledge_store, config)

    # Example documents
    documents = [
        Document(
            content="Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.",
            metadata={"source": "example", "type": "biography"}
        ),
        Document(
            content="The theory of relativity revolutionized our understanding of space, time, gravity, and the universe.",
            metadata={"source": "example", "type": "science"}
        ),
    ]

    # Process documents
    print("Processing documents...")
    processor.process_documents(documents)

    # Perform a hybrid search
    print("\nPerforming hybrid search...")
    query = "Who developed the theory of relativity?"
    results = processor.search(query, limit=5)

    print("\nSearch Results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Content: {result.content}")
        print(f"   Score: {result.score}")
        print(f"   Metadata: {result.metadata}")
        if result.entities:
            print(f"   Entities: {', '.join(e.text for e in result.entities)}")
        if result.relationships:
            print(f"   Relationships: {', '.join(str(r) for r in result.relationships)}")

    # Clean up
    knowledge_store.close()

if __name__ == "__main__":
    main() 