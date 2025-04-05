#!/usr/bin/env python
"""
Simple example of using the Knowledge Base Agent.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_base_agent.processor import DocumentProcessor
from knowledge_base_agent.storage.document_store import DocumentStore
from knowledge_base_agent.storage.vector_store import VectorStore
from knowledge_base_agent.storage.knowledge_store import KnowledgeStore
from knowledge_base_agent.embeddings.openai_embedding import OpenAIEmbedding
from knowledge_base_agent.config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run a simple example of the Knowledge Base Agent."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    config = get_config()
    
    # Initialize components
    document_store = DocumentStore()
    vector_store = VectorStore()
    knowledge_store = KnowledgeStore()
    embedding_model = OpenAIEmbedding(
        api_key=config.embedding.api_key,
        model=config.embedding.model
    )
    
    # Create processor
    processor = DocumentProcessor(
        vector_store=vector_store,
        document_store=document_store,
        knowledge_store=knowledge_store,
        embedding_model=embedding_model,
        config=config.processing
    )
    
    # Example document
    document_content = """
    The Knowledge Base Agent is a powerful tool for processing and retrieving information.
    It uses advanced AI techniques to extract knowledge from documents and make it searchable.
    
    Key features include:
    - Document processing with chunking and embedding generation
    - Vector similarity search using FAISS
    - Knowledge graph storage with Neo4j
    - Entity and relationship extraction
    - RESTful API with FastAPI
    
    The agent can be used to build intelligent search systems, question answering systems,
    and knowledge management applications.
    """
    
    # Process document
    logger.info("Processing document...")
    doc_id = processor.process_document(
        content=document_content,
        metadata={
            "title": "Knowledge Base Agent Overview",
            "source": "example",
            "author": "Knowledge Base Team"
        }
    )
    logger.info(f"Document processed with ID: {doc_id}")
    
    # Search for information
    logger.info("Searching for information...")
    query = "What are the key features of the Knowledge Base Agent?"
    results = processor.search(query, top_k=3)
    
    # Display results
    logger.info(f"Search results for query: '{query}'")
    for i, result in enumerate(results, 1):
        logger.info(f"\nResult {i} (Score: {result.score:.2f}):")
        logger.info(f"Content: {result.content}")
        
        if hasattr(result, 'entities') and result.entities:
            logger.info("Entities:")
            for entity in result.entities:
                logger.info(f"  - {entity.name} ({entity.type})")
    
    # Get entity context
    if hasattr(results[0], 'entities') and results[0].entities:
        entity_id = results[0].entities[0].id
        logger.info(f"\nGetting context for entity: {results[0].entities[0].name}")
        context = processor.get_entity_context(entity_id)
        logger.info(f"Entity context: {context}")

if __name__ == "__main__":
    main() 