"""
Command-line interface for the Generic AI Agent
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import PyMuPDF for enhanced PDF processing
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    try:
        import PyPDF2
        PYPDF_FALLBACK = True
    except ImportError:
        PYPDF_FALLBACK = False

from .processor import DocumentProcessor
from .config import get_config
from .storage.document_store import DocumentStore
from .storage.vector_store import VectorStore
from .storage.knowledge_store import KnowledgeStore
from .embeddings.openai_embedding import OpenAIEmbedding
# Import the new Sentence Transformer embedding class
from .embeddings.sentence_transformer_embedding import SentenceTransformerEmbedding
from .extractors.local_llm_extractor import LocalLlmExtractor

# Import PostgreSQL storage implementations
try:
    from .storage.postgresql import (
        PostgresDocumentStore,
        PostgresVectorStore,
        PostgresKnowledgeStore
    )
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("generic_ai_agent.log")
        ]
    )

def create_processor(config):
    """Create a processor with the appropriate stores based on configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        DocumentProcessor: Configured processor instance
    """
    logger = logging.getLogger(__name__)
    
    # Initialize document store
    if config.storage.document_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL document store")
        document_store = PostgresDocumentStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory document store")
        document_store = DocumentStore()
    
    # Initialize vector store
    if config.storage.vector_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL vector store")
        vector_store = PostgresVectorStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory vector store")
        vector_store = VectorStore()
    
    # Initialize knowledge store
    if config.storage.knowledge_store_type == "postgres" and POSTGRES_AVAILABLE:
        logger.info("Using PostgreSQL knowledge store")
        knowledge_store = PostgresKnowledgeStore(
            storage_path=config.storage.storage_path,
            connection_string=config.storage.postgres_connection
        )
    else:
        logger.info("Using in-memory knowledge store")
        knowledge_store = KnowledgeStore()
    
    # Initialize embedding model based on configuration
    model_name = config.embedding.model
    logger.info(f"Initializing embedding model: {model_name}")
    
    # Check if the model name looks like a Sentence Transformer model
    if '/' in model_name or model_name.startswith("all-") or model_name.startswith("msmarco-") or model_name.startswith("paraphrase-"):
        logger.info("Detected Sentence Transformer model type.")
        try:
            embedding_model = SentenceTransformerEmbedding(
                model=model_name,
                batch_size=config.embedding.batch_size,
                device=getattr(config.embedding, 'device', None)
            )
        except Exception as e:
             logger.error(f"Failed to initialize SentenceTransformerEmbedding for {model_name}: {e}", exc_info=True)
             raise RuntimeError(f"Could not initialize embedding model {model_name}") from e
    else:
        # Assume OpenAI model otherwise
        logger.info("Detected OpenAI model type.")
        if not config.embedding.api_key:
            logger.error("OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI API key is required for OpenAI embedding models.")
            
        embedding_model = OpenAIEmbedding(
            api_key=config.embedding.api_key,
            model=model_name,
            batch_size=config.embedding.batch_size
        )
    
    logger.info(f"Embedding model '{model_name}' initialized successfully.")
    
    # Initialize entity extractor based on configuration
    extractor_config = getattr(config, 'extractor', None)
    if extractor_config and getattr(extractor_config, 'use_local_llm', True):
        logger.info("Initializing Local LLM Extractor")
        try:
            entity_extractor = LocalLlmExtractor(
                model_name=getattr(extractor_config, 'model_name', "mistralai/Mistral-7B-Instruct-v0.2"),
                device=getattr(extractor_config, 'device', None),
                load_in_4bit=getattr(extractor_config, 'load_in_4bit', True),
                max_length=getattr(extractor_config, 'max_length', 2048),
                temperature=getattr(extractor_config, 'temperature', 0.1)
            )
            logger.info("Local LLM Extractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Local LLM Extractor: {e}", exc_info=True)
            logger.warning("Proceeding without entity extractor")
            entity_extractor = None
    else:
        logger.info("Local LLM Extractor not configured, proceeding without it")
        entity_extractor = None
    
    # Create processor
    processor = DocumentProcessor(
        vector_store=vector_store,
        document_store=document_store,
        knowledge_store=knowledge_store,
        embedding_model=embedding_model,
        entity_extractor=entity_extractor,
        config=config.processing
    )
    
    return processor

def process_directory(args: argparse.Namespace) -> None:
    """Process a directory of documents."""
    # Load main configuration
    config = get_config(args.config)
    setup_logging(config.logging.level) # Call setup_logging for side effects
    logger = logging.getLogger(__name__) # Get the logger instance
    logger.info("Configuration loaded.")

    # Use the new create_processor function
    processor = create_processor(config)
    
    # --- Start Directory Processing Logic ---
    directory_path = Path(args.directory)
    if not directory_path.is_dir():
        logger.error(f"Provided path is not a valid directory: {args.directory}")
        sys.exit(1)

    logger.info(f"Processing directory: {args.directory}")
    processed_count = 0
    failed_count = 0
    file_types = args.file_types or ["*"] # Default to all files if none specified
    
    # Determine glob pattern based on recursive flag
    glob_pattern = "**/*" if not args.no_recursive else "*"

    files_to_process = []
    for pattern in file_types:
        files_to_process.extend(list(directory_path.glob(f"{glob_pattern}.{pattern.lstrip('.')}")))
        
    # Deduplicate in case patterns overlap
    files_to_process = sorted(list(set(files_to_process)))

    if not files_to_process:
        logger.warning(f"No files matching patterns {file_types} found in {directory_path}")
        return
        
    logger.info(f"Found {len(files_to_process)} files to process.")

    for file_path in files_to_process:
        if not file_path.is_file():
            continue # Skip directories that might match glob
            
        logger.info(f"Processing file: {file_path}")
        try:
            # Read content - handle different file types appropriately
            # TODO: Add robust file reading (encoding, binary files, etc.)
            content = ""
            if file_path.suffix.lower() == '.pdf':
                if PDF_AVAILABLE:
                    try:
                        # Use PyMuPDF (fitz) for better PDF text extraction
                        pdf_document = fitz.open(file_path)
                        text_content = []
                        for page_num in range(len(pdf_document)):
                            page = pdf_document[page_num]
                            text_content.append(page.get_text())
                        content = "\n".join(text_content)
                        pdf_document.close()
                        
                        if not content.strip():
                            logger.warning(f"Extracted empty content from PDF: {file_path}")
                            # Optionally skip or handle empty PDFs differently
                            # continue 
                    except Exception as pdf_err:
                        logger.error(f"Error reading PDF file {file_path} with PyMuPDF: {pdf_err}")
                        
                        # Fall back to PyPDF2 if available
                        if PYPDF_FALLBACK:
                            logger.info(f"Attempting fallback to PyPDF2 for {file_path}")
                            try:
                                with open(file_path, 'rb') as pdf_file:
                                    reader = PyPDF2.PdfReader(pdf_file)
                                    text_content = []
                                    for page in reader.pages:
                                        text_content.append(page.extract_text() or "")
                                    content = "\n".join(text_content)
                            except Exception as pypdf_err:
                                logger.error(f"Fallback to PyPDF2 also failed: {pypdf_err}")
                                failed_count += 1
                                continue
                        else:
                            failed_count += 1
                            continue # Skip to next file on PDF read error
                else:
                    logger.warning(f"Skipping PDF file {file_path}, PDF libraries not found. Please install pymupdf or pypdf2.")
                    continue # Skip if PDF library is not available
            else:
                # Assume text file for other types
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                except Exception as txt_err:
                    logger.error(f"Error reading text file {file_path}: {txt_err}")
                    failed_count += 1
                    continue # Skip to next file on text read error
            
            if not content.strip(): # Check if content is empty after extraction/reading
                logger.warning(f"Skipping file {file_path} due to empty content.")
                failed_count += 1
                continue
                
            metadata = {
                'title': file_path.name,
                'source': str(file_path.resolve())
            }
            
            doc_id = processor.process_document(content, metadata)
            logger.info(f"Successfully processed {file_path}. Doc ID: {doc_id}")
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}", exc_info=False) # Set exc_info=True for full traceback
            failed_count += 1
    
    logger.info(f"Directory processing complete. Processed: {processed_count}, Failed: {failed_count}")
    # --- End Directory Processing Logic ---

def query_knowledge_base(args: argparse.Namespace) -> None:
    """Query the knowledge base."""
    config = get_config(args.config)
    setup_logging(config.logging.level)
    logger = logging.getLogger(__name__)
    
    # Use the new create_processor function
    processor = create_processor(config)
    
    # Check if query method exists
    if not hasattr(processor, 'query'):
        logger.error("DocumentProcessor does not have a 'query' method.")
        sys.exit(1)
        
    logger.info(f"Executing query: {args.query}")
    try:
        results = processor.query(
            query=args.query,
            limit=args.limit
        )
        
        # Process and print results (adjust based on actual return type of processor.query)
        logger.info(f"Query returned results: {results}") 
        print(results)
    except Exception as e:
        logger.error(f"Error during query: {e}", exc_info=True)
        sys.exit(1)

def export_knowledge_base(args: argparse.Namespace) -> None:
    """Export the knowledge base."""
    config = get_config(args.config)
    setup_logging(config.logging.level)
    logger = logging.getLogger(__name__)
    
    # Use the new create_processor function
    processor = create_processor(config)
    
    # Check if export method exists
    if not hasattr(processor, 'export_knowledge_base'):
        logger.error("DocumentProcessor does not have an 'export_knowledge_base' method.")
        sys.exit(1)

    logger.info(f"Exporting knowledge base to {args.output_dir} in format {args.format}")
    try:
        exports = processor.export_knowledge_base(
            output_dir=args.output_dir,
            format=args.format
        )
        logger.info(f"Exports saved to: {exports}")
    except Exception as e:
        logger.error(f"Error during export: {e}", exc_info=True)
        sys.exit(1)

def main(args: Optional[list] = None) -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generic AI Agent for document processing and analysis"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    # Add storage configuration arguments
    storage_group = parser.add_argument_group('Storage Configuration')
    storage_group.add_argument(
        "--storage-path",
        type=str,
        help="Path for persistent storage"
    )
    storage_group.add_argument(
        "--postgres-connection",
        type=str,
        help="PostgreSQL connection string (e.g., user:password@localhost:5432/dbname)"
    )
    storage_group.add_argument(
        "--document-store-type",
        choices=["memory", "postgres"],
        default="memory",
        help="Type of document store to use"
    )
    storage_group.add_argument(
        "--vector-store-type",
        choices=["memory", "postgres"],
        default="memory",
        help="Type of vector store to use"
    )
    storage_group.add_argument(
        "--knowledge-store-type",
        choices=["memory", "postgres"],
        default="memory",
        help="Type of knowledge store to use"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process directory command
    process_parser = subparsers.add_parser(
        "process",
        help="Process a directory of documents"
    )
    process_parser.add_argument(
        "directory",
        type=str,
        help="Directory to process"
    )
    process_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't process subdirectories"
    )
    process_parser.add_argument(
        "--file-types",
        nargs="+",
        help="File types to process"
    )
    process_parser.add_argument(
        "--embedding-model",
        default="text-embedding-ada-002",
        help="Embedding model name"
    )
    process_parser.add_argument(
        "--llm-model",
        default="gpt-4-turbo-preview",
        help="LLM model name"
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the knowledge base"
    )
    query_parser.add_argument(
        "query",
        type=str,
        help="Query string"
    )
    query_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results"
    )
    query_parser.add_argument(
        "--no-context",
        action="store_true",
        help="Don't include document context"
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        "export",
        help="Export the knowledge base"
    )
    export_parser.add_argument(
        "output_dir",
        type=str,
        help="Output directory"
    )
    export_parser.add_argument(
        "--format",
        default="turtle",
        help="Export format"
    )
    
    args = parser.parse_args(args)
    
    # Set up logging
    setup_logging()
    
    # Override config from command line args if provided
    config = get_config(args.config)
    if hasattr(args, 'storage_path') and args.storage_path:
        config.storage.storage_path = args.storage_path
    if hasattr(args, 'postgres_connection') and args.postgres_connection:
        config.storage.postgres_connection = args.postgres_connection
    if hasattr(args, 'document_store_type') and args.document_store_type:
        config.storage.document_store_type = args.document_store_type
    if hasattr(args, 'vector_store_type') and args.vector_store_type:
        config.storage.vector_store_type = args.vector_store_type
    if hasattr(args, 'knowledge_store_type') and args.knowledge_store_type:
        config.storage.knowledge_store_type = args.knowledge_store_type
    
    try:
        if args.command == "process":
            process_directory(args)
        elif args.command == "query":
            query_knowledge_base(args)
        elif args.command == "export":
            export_knowledge_base(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 