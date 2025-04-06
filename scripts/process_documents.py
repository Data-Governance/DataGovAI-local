#!/usr/bin/env python3
"""
Process documents and insert them into the PostgreSQL database.
"""

import os
import sys
import uuid
import json
import logging
import argparse
import psycopg2
import fitz  # PyMuPDF
import nltk
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from urllib.parse import urlparse
import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Download NLTK punkt if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def load_config() -> Dict[str, Any]:
    """Load configuration from .env file."""
    dotenv_path = Path('.env')
    if dotenv_path.exists():
        logger.info(f"Loading environment variables from {dotenv_path.resolve()}")
        # Clear existing environment variables that might conflict before loading
        # Relevant keys:
        relevant_keys = ["POSTGRES_CONNECTION", "EMBEDDING_MODEL", "EMBEDDING_DEVICE", 
                         "EMBEDDING_BATCH_SIZE", "MAX_CHUNK_SIZE", "MIN_CHUNK_SIZE", "OVERLAP_SIZE"]
        for key in relevant_keys:
            if key in os.environ:
                del os.environ[key]
                logger.debug(f"Cleared existing environment variable: {key}")
        
        load_dotenv(dotenv_path=dotenv_path, override=True) # Force override
    else:
        logger.warning(".env file not found. Using defaults and environment variables.")
    
    # Get value directly after loading
    postgres_conn_env = os.getenv("POSTGRES_CONNECTION")
    
    # Log the value *immediately* after getenv
    logger.info(f"Value of POSTGRES_CONNECTION from environment: {postgres_conn_env}")

    config = {
        # Use the fetched value or raise an error if not found (as it's critical)
        "postgres_connection": postgres_conn_env,
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2"),
        # Force CPU usage due to compatibility issues with Python 3.12 + PyTorch + GPU
        "embedding_device": "cpu",
        "embedding_batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
        "max_chunk_size": int(os.getenv("MAX_CHUNK_SIZE", "2000")),
        "min_chunk_size": int(os.getenv("MIN_CHUNK_SIZE", "200")),
        "overlap_size": int(os.getenv("OVERLAP_SIZE", "100")),
    }
    
    # Check if critical connection string is missing
    if not config["postgres_connection"]:
        logger.error("CRITICAL: POSTGRES_CONNECTION not found in .env or environment variables!")
        raise ValueError("POSTGRES_CONNECTION is required but not set.")

    logger.info(f"Final PostgreSQL Connection String Used: {config['postgres_connection']}")
    
    return config

def connect_to_db(connection_string: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database, handling peer authentication."""
    try:
        # Parse the connection string
        result = urlparse(connection_string)
        logger.info(f"Parsed connection string: scheme={result.scheme}, username={result.username}, password={'***' if result.password else None}, hostname={result.hostname}, port={result.port}, path={result.path}")
        
        # Check if it looks like a peer authentication URI (only dbname specified)
        is_peer_auth_format = result.scheme == 'postgresql' and result.path and not result.username and not result.password and result.hostname in (None, '', 'localhost')
        
        if is_peer_auth_format:
            # Assume peer authentication
            dbname = result.path[1:]
            current_user = getpass.getuser() # Get current OS username
            logger.info(f"Attempting peer authentication for database '{dbname}' as OS user '{current_user}'")
            # psycopg2 uses peer auth by default if user/password/host are omitted
            conn = psycopg2.connect(dbname=dbname)
        else:
            # Use provided connection details
            conn_params = {
                "dbname": result.path[1:] if result.path else None,
                "user": result.username,
                "password": result.password,
                "host": result.hostname,
                "port": result.port or 5432
            }
            conn_params = {k: v for k, v in conn_params.items() if v is not None}
            logger.info(f"Attempting password authentication with parameters: { {k: v if k != 'password' else '***' for k, v in conn_params.items()} }")
            conn = psycopg2.connect(**conn_params)
            
        logger.info(f"Connected to PostgreSQL database '{result.path[1:]}'")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    try:
        pdf_document = fitz.open(file_path)
        text_content = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text_content.append(page.get_text())
            
        content = "\n".join(text_content)
        pdf_document.close()
        
        return content
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def semantic_chunk_document(content: str, max_chunk_size: int = 2000, 
                           min_chunk_size: int = 200, overlap_size: int = 100) -> List[str]:
    """
    Chunk document into semantically meaningful sections based on sentence boundaries.
    
    Args:
        content: Document text content
        max_chunk_size: Maximum size of a chunk in characters
        min_chunk_size: Minimum size of a chunk in characters
        overlap_size: Size of overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Use NLTK to split into sentences
    sentences = nltk.sent_tokenize(content)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        # If adding this sentence would exceed max_chunk_size and we have enough text,
        # finalize the current chunk and start a new one
        if current_size + sentence_size > max_chunk_size and current_size >= min_chunk_size:
            # Join sentences in current chunk with spaces
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            # Start new chunk with overlap
            overlap_sentences = []
            overlap_size_count = 0
            
            # Add sentences from the end of current chunk until we reach overlap_size
            for s in reversed(current_chunk):
                if overlap_size_count + len(s) <= overlap_size:
                    overlap_sentences.insert(0, s)
                    overlap_size_count += len(s) + 1  # +1 for space
                else:
                    break
            
            current_chunk = overlap_sentences
            current_size = sum(len(s) for s in current_chunk) + len(current_chunk) - 1  # Account for spaces
        
        # Add current sentence to chunk
        current_chunk.append(sentence)
        current_size += sentence_size + 1  # +1 for space
    
    # Add the last chunk if it's not empty and meets minimum size
    if current_chunk and current_size >= min_chunk_size:
        chunk_text = " ".join(current_chunk)
        chunks.append(chunk_text)
    
    return chunks

def generate_embeddings(chunks: List[str], model_name: str, 
                       device: str = "cuda", batch_size: int = 32) -> List[List[float]]:
    """Generate embeddings for text chunks using SentenceTransformers."""
    try:
        # Get Hugging Face token from environment
        hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
        if hf_token:
            logger.info("Using Hugging Face token from HUGGING_FACE_HUB_TOKEN environment variable.")
        else:
            # Log a warning but proceed; maybe the model doesn't require auth or it's cached
            logger.warning("Hugging Face token not found in HUGGING_FACE_HUB_TOKEN environment variable. Proceeding without explicit token.")
        
        # Set environment variables to help with GPU compatibility issues
        os.environ["TORCH_INIT_MODEL_EMPTY_WEIGHTS"] = "0"
        
        # Configure PyTorch for better GPU compatibility
        import torch
        torch.set_grad_enabled(False)  # We're only doing inference
        
        if device == "cuda" and torch.cuda.is_available():
            logger.info(f"Using GPU for embeddings: {torch.cuda.get_device_name(0)}")
            # Set torch to use deterministic algorithms for better compatibility
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
            
            # Try to avoid the 'init_empty_weights' error
            import torch._dynamo
            torch._dynamo.config.suppress_errors = True
        else:
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                device = "cpu"
            logger.info("Using CPU for embeddings")
            
        # Load the model, passing the token explicitly if found
        model = SentenceTransformer(model_name, device=device, token=hf_token)
        
        # Generate embeddings
        embeddings = model.encode(chunks, batch_size=batch_size, show_progress_bar=True)
        
        # Convert numpy arrays to lists for JSON serialization
        embeddings_list = [embed.tolist() for embed in embeddings]
        
        return embeddings_list
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise

def insert_document(conn: psycopg2.extensions.connection, content: str, 
                   metadata: Dict[str, Any]) -> str:
    """Insert document into the database."""
    document_id = f"doc_{uuid.uuid4().hex}"
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (document_id, content, metadata) VALUES (%s, %s, %s)",
                (document_id, content, json.dumps(metadata))
            )
        conn.commit()
        logger.info(f"Document inserted with ID: {document_id}")
        return document_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting document: {e}")
        raise

def insert_chunks(conn: psycopg2.extensions.connection, document_id: str, 
                 chunks: List[str], embeddings: List[List[float]]) -> List[str]:
    """Insert chunks and their embeddings into the database."""
    chunk_ids = []
    
    try:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"chunk_{uuid.uuid4().hex}"
            chunk_ids.append(chunk_id)
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO chunks (chunk_id, document_id, content, embedding) VALUES (%s, %s, %s, %s)",
                    (chunk_id, document_id, chunk, embedding)
                )
            
        conn.commit()
        logger.info(f"Inserted {len(chunks)} chunks for document {document_id}")
        return chunk_ids
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting chunks: {e}")
        raise

def process_document(conn: psycopg2.extensions.connection, file_path: Path, config: Dict[str, Any]) -> Optional[str]:
    """Process a single document and store it in the database."""
    try:
        logger.info(f"Processing document: {file_path}")
        
        # Extract text from PDF
        content = extract_text_from_pdf(file_path)
        if not content:
            logger.warning(f"No content extracted from {file_path}")
            return None
            
        # Create metadata
        metadata = {
            'title': file_path.stem,
            'source': str(file_path),
            'file_type': file_path.suffix.lower()
        }
        
        # Insert document
        document_id = insert_document(conn, content, metadata)
        
        # Chunk document
        chunks = semantic_chunk_document(
            content, 
            max_chunk_size=config["max_chunk_size"],
            min_chunk_size=config["min_chunk_size"],
            overlap_size=config["overlap_size"]
        )
        logger.info(f"Document split into {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = generate_embeddings(
            chunks,
            model_name=config["embedding_model"],
            device=config["embedding_device"],
            batch_size=config["embedding_batch_size"]
        )
        
        # Insert chunks and embeddings
        chunk_ids = insert_chunks(conn, document_id, chunks, embeddings)
        
        logger.info(f"Successfully processed document {file_path}")
        return document_id
        
    except Exception as e:
        logger.error(f"Error processing document {file_path}: {e}")
        return None

def process_directory(directory_path: Path, limit: Optional[int] = None, config: Dict[str, Any] = None) -> int:
    """Process all PDF documents in a directory."""
    if not directory_path.is_dir():
        logger.error(f"Not a valid directory: {directory_path}")
        return 0
        
    if config is None:
        config = load_config()
    
    # Find all PDF files
    pdf_files = list(directory_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {directory_path}")
        return 0
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    # Apply limit if specified
    if limit and limit > 0:
        pdf_files = pdf_files[:limit]
        logger.info(f"Processing limited to {limit} documents")
    
    # Process each file
    successful = 0
    
    # --- DEBUG: Log the connection string right before connecting ---
    db_connection_string = config.get("postgres_connection", "NOT_FOUND_IN_CONFIG")
    logger.info(f"DEBUG: Attempting to connect using connection string: {db_connection_string}")
    # --- END DEBUG ---
    
    conn = connect_to_db(db_connection_string)
    
    try:
        for file_path in pdf_files:
            document_id = process_document(conn, file_path, config)
            if document_id:
                successful += 1
    finally:
        if conn:
            conn.close()
    
    logger.info(f"Processing complete. Successfully processed {successful} documents")
    return successful

def main():
    """Main function to process documents."""
    parser = argparse.ArgumentParser(description="Process documents and store them in PostgreSQL")
    parser.add_argument("--data-dir", default="data", help="Directory containing documents to process")
    parser.add_argument("--limit", type=int, help="Limit the number of documents to process")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Process documents
    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        logger.error(f"Data directory does not exist: {data_dir}")
        sys.exit(1)
        
    process_directory(data_dir, args.limit, config)

if __name__ == "__main__":
    main() 