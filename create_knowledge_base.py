#!/usr/bin/env python
"""
Create Knowledge Base - Script to initialize and build the knowledge base from GRS documents.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import List, Optional
import time

from src.knowledge_base_agent.config import get_config
from src.knowledge_base_agent.processor import DocumentProcessor
from src.knowledge_base_agent.cli import create_processor, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def initialize_database(config) -> bool:
    """Initialize database tables for the knowledge base."""
    try:
        from src.knowledge_base_agent.storage.postgresql import (
            PostgresDocumentStore,
            PostgresVectorStore,
            PostgresKnowledgeStore
        )
        
        logger.info("Initializing PostgreSQL database...")
        
        # Create document store tables
        doc_store = PostgresDocumentStore(
            connection_string=config.storage.postgres_connection
        )
        doc_store.initialize()
        logger.info(f"Document store initialized")
        
        # Create vector store tables with pgvector support
        vector_store = PostgresVectorStore(
            connection_string=config.storage.postgres_connection
        )
        vector_store.initialize()
        logger.info(f"Vector store initialized")
        
        # Create knowledge store tables
        kg_store = PostgresKnowledgeStore(
            connection_string=config.storage.postgres_connection
        )
        kg_store.initialize()
        logger.info(f"Knowledge store initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        return False

def process_documents(processor: DocumentProcessor, data_dir: Path, limit: Optional[int] = None) -> int:
    """Process documents from the data directory.
    
    Args:
        processor: The document processor instance
        data_dir: Path to the directory containing GRS documents
        limit: Optional maximum number of documents to process
        
    Returns:
        The number of successfully processed documents
    """
    logger.info(f"Processing documents from {data_dir}")
    
    # Find all PDF files in the data directory
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_dir}")
        return 0
        
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Apply limit if specified
    if limit and limit > 0:
        pdf_files = pdf_files[:limit]
        logger.info(f"Processing limited to {limit} documents")
    
    # Process each file
    successful = 0
    failed = 0
    
    for idx, file_path in enumerate(pdf_files):
        logger.info(f"Processing file {idx+1}/{len(pdf_files)}: {file_path.name}")
        try:
            # Extract text from PDF
            import fitz  # PyMuPDF
            pdf_document = fitz.open(file_path)
            text_content = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text_content.append(page.get_text())
            content = "\n".join(text_content)
            pdf_document.close()
            
            if not content.strip():
                logger.warning(f"Empty content extracted from {file_path.name}, skipping")
                failed += 1
                continue
                
            # Extract GRS number from filename
            import re
            grs_match = re.search(r'GRS-(\d+)', file_path.name)
            grs_number = f"GRS-{grs_match.group(1)}" if grs_match else None
            
            # Create metadata
            metadata = {
                'title': file_path.stem.replace('-', ' ').title(),
                'source': str(file_path),
                'record_series_number': grs_number
            }
            
            # Process the document
            doc_id = processor.process_document(content, metadata)
            logger.info(f"Successfully processed {file_path.name}. Doc ID: {doc_id}")
            successful += 1
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            failed += 1
            
        # Add a small delay to avoid overloading the database or GPU
        time.sleep(0.5)
    
    logger.info(f"Document processing complete. Successful: {successful}, Failed: {failed}")
    return successful

def main():
    """Main function to build the knowledge base."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Create and build the knowledge base")
    parser.add_argument("--config", default=".env", help="Path to configuration file")
    parser.add_argument("--data-dir", default="data", help="Directory containing GRS documents")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--process", action="store_true", help="Process documents")
    parser.add_argument("--limit", type=int, help="Limit the number of documents to process")
    args = parser.parse_args()
    
    # Load configuration
    config = get_config(args.config)
    setup_logging(config.logging.level)
    
    # Initialize database if requested
    if args.init_db:
        success = initialize_database(config)
        if not success:
            logger.error("Database initialization failed. Exiting.")
            return
    
    # Process documents if requested
    if args.process:
        # Create processor
        processor = create_processor(config)
        
        # Process documents
        data_dir = Path(args.data_dir)
        if not data_dir.is_dir():
            logger.error(f"Data directory does not exist: {data_dir}")
            return
            
        processed = process_documents(processor, data_dir, args.limit)
        logger.info(f"Successfully processed {processed} documents")
    
    # Done
    logger.info("Knowledge base creation complete")

if __name__ == "__main__":
    main() 