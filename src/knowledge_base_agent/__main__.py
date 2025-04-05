"""
Main entry point for the Knowledge Base Agent.
"""

import os
import logging
from typing import Optional
import click
from dotenv import load_dotenv
import uvicorn

from knowledge_base_agent.processor import DocumentProcessor
from knowledge_base_agent.storage.document_store import DocumentStore
from knowledge_base_agent.storage.vector_store import VectorStore
from knowledge_base_agent.storage.knowledge_store import KnowledgeStore

# Import PostgreSQL storage implementations
try:
    from knowledge_base_agent.storage.postgresql import (
        PostgresDocumentStore,
        PostgresVectorStore,
        PostgresKnowledgeStore
    )
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from knowledge_base_agent.embeddings.openai_embedding import OpenAIEmbedding
from knowledge_base_agent.config import get_config
from knowledge_base_agent.api import create_app

def setup_logging(config):
    """Set up logging configuration."""
    logging.basicConfig(
        level=config.logging.level,
        format=config.logging.format,
        filename=config.logging.file
    )
    return logging.getLogger(__name__)

def create_processor(config=None):
    """Create and configure a document processor instance."""
    if config is None:
        config = get_config()
    
    logger = logging.getLogger(__name__)
    
    # Initialize stores based on configuration
    if config.storage.document_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL document store")
        document_store = PostgresDocumentStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory document store")
        document_store = DocumentStore()
    
    if config.storage.vector_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL vector store")
        vector_store = PostgresVectorStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory vector store")
        vector_store = VectorStore()
    
    if config.storage.knowledge_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL knowledge store")
        knowledge_store = PostgresKnowledgeStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory knowledge store")
        knowledge_store = KnowledgeStore()
    
    # Initialize embedding model
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
    
    return processor

@click.group()
@click.option('--config', type=click.Path(exists=True), help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """Knowledge Base Agent CLI."""
    ctx.obj = {'config': get_config(config)}
    logger = setup_logging(ctx.obj['config'])

@cli.command()
@click.option('--host', help='Host to bind to')
@click.option('--port', type=int, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def serve(ctx, host, port, debug):
    """Start the API server."""
    config = ctx.obj['config']
    
    # Override config with CLI options
    if host:
        config.api.host = host
    if port:
        config.api.port = port
    if debug:
        config.api.debug = debug
    
    app = create_app(create_processor(config))
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level="debug" if config.api.debug else "info"
    )

@cli.command()
@click.argument('file_path')
@click.option('--title', help='Document title')
@click.option('--source', help='Document source')
@click.pass_context
def process(ctx, file_path, title, source):
    """Process a document."""
    processor = create_processor(ctx.obj['config'])
    logger = setup_logging(ctx.obj['config'])
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        metadata = {
            'title': title or os.path.basename(file_path),
            'source': source or file_path
        }
        
        doc_id = processor.process_document(content, metadata)
        click.echo(f"Successfully processed document. ID: {doc_id}")
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('query')
@click.option('--limit', default=5, help='Maximum number of results')
@click.pass_context
def search(ctx, query, limit):
    """Search the knowledge base."""
    processor = create_processor(ctx.obj['config'])
    logger = setup_logging(ctx.obj['config'])
    
    try:
        results = processor.search(query, top_k=limit)
        
        for i, result in enumerate(results, 1):
            click.echo(f"\nResult {i} (Score: {result.score:.2f}):")
            click.echo(f"Content: {result.content[:200]}...")
            if hasattr(result, 'entities') and result.entities:
                click.echo("Entities:")
                for entity in result.entities:
                    click.echo(f"  - {entity.name} ({entity.type})")
        
    except Exception as e:
        logger.error(f"Error searching: {str(e)}", exc_info=True)
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == '__main__':
    cli() 