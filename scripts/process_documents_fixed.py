import sys
from pathlib import Path

# Add project root to sys.path to allow imports from knowledge_base_agent
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

#!/usr/bin/env python3
"""
Process documents and insert them into the PostgreSQL database.
"""

import os
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

def process_documents(file_paths: List[Path], config: Dict[str, Any]) -> None:
    """Process a batch of documents and store them in the database."""
    try:
        # Initialize sentence transformer model
        model = SentenceTransformer(config['embedding_model'])
        model.to(config['embedding_device'])
        
        # Connect to database
        conn = psycopg2.connect(config['postgres_connection'])
        
        for file_path in file_paths:
            try:
                # Extract text from PDF
                logger.info(f"Processing {file_path}")
                content = extract_text_from_pdf(file_path)
                if not content:
                    logger.warning(f"No content extracted from {file_path}")
                    continue
                
                # Create chunks
                chunks = semantic_chunk_document(
                    content,
                    config['max_chunk_size'],
                    config['min_chunk_size'],
                    config['overlap_size']
                )
                
                # Generate embeddings
                embeddings = model.encode(
                    chunks,
                    batch_size=config['embedding_batch_size'],
                    device=config['embedding_device']
                )
                
                # Store in database
                with conn.cursor() as cur:
                    # Insert document
                    document_id = f"doc_{uuid.uuid4().hex}"
                    metadata = {
                        'filename': file_path.name,
                        'path': str(file_path)
                    }
                    cur.execute(
                        "INSERT INTO documents (id, content, metadata) VALUES (%s, %s, %s)",
                        (document_id, content, json.dumps(metadata))
                    )
                    
                    # Insert chunks with embeddings
                    for chunk, embedding in zip(chunks, embeddings):
                        chunk_id = f"chunk_{uuid.uuid4().hex}"
                        cur.execute(
                            "INSERT INTO chunks (id, document_id, content, embedding) VALUES (%s, %s, %s, %s)",
                            (chunk_id, document_id, chunk, embedding.tolist())
                        )
                
                conn.commit()
                logger.info(f"Successfully processed {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                conn.rollback()
                continue
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

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
    """Chunk document into semantically meaningful sections."""
    sentences = nltk.sent_tokenize(content)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence)
        
        if current_size + sentence_size > max_chunk_size and current_chunk:
            # Store current chunk
            chunks.append(" ".join(current_chunk))
            # Start new chunk with overlap
            overlap_text = " ".join(current_chunk[-2:])  # Keep last 2 sentences
            current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
            current_size = len(overlap_text) + sentence_size if overlap_text else sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def main():
    """Main function to process documents."""
    parser = argparse.ArgumentParser(description="Process documents and store in database")
    parser.add_argument("files", nargs="+", type=Path, help="PDF files to process")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load configuration
    config = {
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-mpnet-base-v2'),
        'embedding_device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'embedding_batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '32')),
        'max_chunk_size': int(os.getenv('MAX_CHUNK_SIZE', '2000')),
        'min_chunk_size': int(os.getenv('MIN_CHUNK_SIZE', '200')),
        'overlap_size': int(os.getenv('OVERLAP_SIZE', '100')),
        'postgres_connection': os.getenv('POSTGRES_CONNECTION', 'postgresql://localhost/knowledge_base')
    }
    
    # Process documents
    process_documents(args.files, config)

if __name__ == "__main__":
    main() 