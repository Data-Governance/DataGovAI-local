import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import os
import torch
import logging
import psycopg2
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file."""
    load_dotenv()
    return {
        'postgres_connection': os.getenv('POSTGRES_CONNECTION'),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'all-mpnet-base-v2'),
        'embedding_device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
    }

def get_chunks(conn):
    """Get all chunks from the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, content FROM chunks")
        return cur.fetchall()

def insert_embeddings(conn, chunk_id, embedding):
    """Insert embedding for a chunk."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chunk_embeddings (chunk_idx, embedding) VALUES (%s, %s)",
            (chunk_id, embedding.tolist())
        )
    conn.commit()

def main():
    """Main function to generate embeddings for all chunks."""
    config = load_config()
    logger.info(f"Using device: {config['embedding_device']}")
    
    # Initialize the model
    model = SentenceTransformer(config['embedding_model'])
    model.to(config['embedding_device'])
    
    # Connect to database
    conn = psycopg2.connect(config['postgres_connection'])
    
    try:
        # Get all chunks
        chunks = get_chunks(conn)
        logger.info(f"Found {len(chunks)} chunks to process")
        
        # Process in batches
        batch_size = config['batch_size']
        for i in tqdm(range(0, len(chunks), batch_size)):
            batch = chunks[i:i + batch_size]
            chunk_ids, texts = zip(*batch)
            
            # Generate embeddings
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                device=config['embedding_device']
            )
            
            # Insert embeddings
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                insert_embeddings(conn, chunk_id, embedding)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{len(chunks)//batch_size + 1}")
        
        logger.info("Finished generating embeddings")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main() 