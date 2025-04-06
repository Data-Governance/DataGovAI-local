"""
Command-line interface for the Generic AI Agent
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import torch

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
from .query_agent import RAGKGQueryAgent

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

def create_processor(config) -> DocumentProcessor:
    """Create and configure a DocumentProcessor instance."""
    
    # Configure environment and logger
    logger = logging.getLogger(__name__)
    
    # Determine what storage implementations to use
    if POSTGRES_AVAILABLE and config.document_store.type == "postgresql":
        logger.info("Using PostgreSQL storage implementations")
        document_store = PostgresDocumentStore(
            connection_string=config.postgres.connection,
            table_name=config.document_store.table_name
        )
        vector_store = PostgresVectorStore(
            connection_string=config.postgres.connection,
            table_name=config.vector_store.table_name
        )
        knowledge_store = PostgresKnowledgeStore(
            connection_string=config.postgres.connection,
            table_name=config.knowledge_store.table_name
        )
    else:
        # For now, fall back to memory-based implementations
        logger.warning("PostgreSQL not available or not configured. Using memory-based stores.")
        # These would be simple in-memory implementations
        
    # Initialize embedding model
    if config.embedding.model.startswith("text-embedding-") or config.embedding.provider == "openai":
        # Use OpenAI if configured
        logger.info(f"Using OpenAI embedding model: {config.embedding.model}")
        embedding_model = OpenAIEmbedding(
            model=config.embedding.model,
            api_key=config.openai.api_key,
            batch_size=config.embedding.batch_size
        )
    else:
        # Use Sentence Transformer model (local)
        logger.info(f"Using Sentence Transformer embedding model: {config.embedding.model}")
        device = getattr(config.embedding, 'device', None) or ("cuda" if torch.cuda.is_available() else "cpu")
        embedding_model = SentenceTransformerEmbedding(
            model=config.embedding.model,
            batch_size=config.embedding.batch_size,
            device=device
        )
        
    # Initialize entity extractor
    if hasattr(config, 'extractor') and hasattr(config.extractor, 'model'):
        logger.info(f"Using Local LLM extractor with model: {config.extractor.model}")
        # Use local LLM extractor
        device = getattr(config.extractor, 'device', None) or ("cuda" if torch.cuda.is_available() else "cpu")
        use_4bit = getattr(config.extractor, '4bit', True)
        entity_extractor = LocalLlmExtractor(
            model_name=config.extractor.model,
            device=device,
            load_in_4bit=use_4bit
        )
    else:
        # Fall back to OpenAI-based extraction if no local LLM configured
        logger.info("Using OpenAI-based entity extraction")
        from .extractors.entity_extractor import EntityExtractor
        entity_extractor = EntityExtractor(api_key=config.openai.api_key)
        
    # Create and return processor
    processor = DocumentProcessor(
        document_store=document_store,
        vector_store=vector_store,
        knowledge_store=knowledge_store,
        embedding_model=embedding_model,
        entity_extractor=entity_extractor,
        config=config
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
    
    logger.info(f"Executing query: {args.query}")
    try:
        # Use RAG+KG query agent if advanced_query is specified
        if args.advanced_query:
            logger.info("Using RAG+KG query agent for advanced retrieval")
            # Create the query agent
            query_agent = RAGKGQueryAgent(
                processor=processor,
                llm_model_name=config.extractor.model if hasattr(config, 'extractor') else "mistralai/Mistral-7B-Instruct-v0.2",
                device=config.extractor.device if hasattr(config, 'extractor') else ("cuda" if torch.cuda.is_available() else "cpu"),
                use_4bit=config.extractor.get('4bit', True) if hasattr(config, 'extractor') else True
            )
            
            # Execute the query
            results = query_agent.query(
                query=args.query,
                top_k=args.limit,
                min_score=args.min_score if hasattr(args, 'min_score') else 0.6
            )
            
            # Display answer
            if results["success"]:
                print("\n" + "=" * 80)
                print("ANSWER:")
                print(results["answer"])
                print("=" * 80 + "\n")
                
                if args.verbose:
                    print("\nVector Search Results:")
                    for i, r in enumerate(results["vector_results"]):
                        print(f"  Result {i+1} (Score: {r['score']:.2f}):")
                        print(f"  {r['content'][:200]}...")
                        print()
                        
                    print("\nExtracted Entities:")
                    for entity_type, value in results["extracted_entities"].items():
                        print(f"  {entity_type}: {value}")
                        
                    print("\nKnowledge Graph Results:")
                    if results["knowledge_graph_results"]:
                        for i, kg_result in enumerate(results["knowledge_graph_results"]):
                            print(f"  Entity {i+1}: {kg_result.get('type', 'Unknown')} - {kg_result.get('value', 'Unknown')}")
                    else:
                        print("  No specific entities found in knowledge graph.")
            else:
                print(f"Query failed: {results['error']}")
        else:
            # Use standard processor query
            results = processor.query(
                query=args.query,
                limit=args.limit
            )
            
            # Process and print results
            if results.get('success', False):
                print(f"Query returned {len(results.get('results', []))} results:") 
                for i, result in enumerate(results.get('results', [])):
                    print(f"\nResult {i+1} (Score: {result.get('similarity', 0):.2f}):")
                    print(f"Document: {result.get('document_id', 'Unknown')}")
                    content = result.get('content', '')
                    print(f"Content: {content[:500]}..." if len(content) > 500 else f"Content: {content}")
            else:
                print(f"Query failed: {results.get('error', 'Unknown error')}")
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

def main() -> None:
    """Main function to parse arguments and execute commands."""
    
    # Create the top-level parser
    parser = argparse.ArgumentParser(description="Generic AI Agent")
    
    # Add common arguments
    parser.add_argument("--config", default=".env", help="Configuration file path")
    
    # Create sub-parsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: process
    process_parser = subparsers.add_parser("process", help="Process a document")
    process_parser.add_argument("--file", help="Path to the document file")
    process_parser.add_argument("--dir", help="Directory containing documents to process")
    process_parser.add_argument("--pattern", help="File pattern to match (with --dir)")
    
    # Command: query
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("query", help="Query string")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    query_parser.add_argument("--min-score", type=float, default=0.6, help="Minimum similarity score")
    query_parser.add_argument("--advanced-query", action="store_true", help="Use RAG+KG for advanced querying")
    query_parser.add_argument("--verbose", action="store_true", help="Show detailed results")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the appropriate command
    if args.command == "process":
        if args.file:
            # Process a single file
            process_file(args)
        elif args.dir:
            # Process all files in a directory
            process_directory(args)
        else:
            print("Error: Either --file or --dir must be specified")
            sys.exit(1)
    elif args.command == "query":
        # Query the knowledge base
        query_knowledge_base(args)
    else:
        # No command or unknown command
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 