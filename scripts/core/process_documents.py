import sys
from pathlib import Path

# Add project root to sys.path to allow imports from knowledge_base_agent
project_root = Path(__file__).resolve().parent.parent.parent # Adjusted path depth
sys.path.insert(0, str(project_root))

#!/usr/bin/env python3
"""
Process documents from the classified directory and insert them into the PostgreSQL database, avoiding duplicates.
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

# Removed multi-process pool imports
# Added torch multiprocessing
import torch.multiprocessing as mp

# Import custom exceptions if they exist, otherwise define simple ones
try:
    from knowledge_base_agent.exceptions import EmbeddingError, StorageError, ProcessingError
except ImportError:
    logger.warning("Could not import custom exceptions from knowledge_base_agent.exceptions. Defining defaults.")
    class EmbeddingError(Exception): pass
    class StorageError(Exception): pass
    class ProcessingError(Exception): pass

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
    dotenv_path = project_root / '.env' # Use project_root to find .env
    if dotenv_path.exists():
        logger.info(f"Loading environment variables from {dotenv_path.resolve()}")
        # Clear existing environment variables that might conflict before loading
        relevant_keys = ["POSTGRES_CONNECTION", "EMBEDDING_MODEL", "EMBEDDING_DEVICE",
                         "EMBEDDING_BATCH_SIZE", "MAX_CHUNK_SIZE", "MIN_CHUNK_SIZE", "OVERLAP_SIZE"]
        for key in relevant_keys:
            if key in os.environ:
                del os.environ[key]
                logger.debug(f"Cleared existing environment variable: {key}")

        load_dotenv(dotenv_path=dotenv_path, override=True)
    else:
        logger.warning(".env file not found at {dotenv_path.resolve()}. Using defaults and environment variables.")

    postgres_conn_env = os.getenv("POSTGRES_CONNECTION")
    logger.info(f"Value of POSTGRES_CONNECTION from environment: {postgres_conn_env}")

    # Check GPU availability and count
    gpu_devices = []
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        logger.info(f"Found {gpu_count} CUDA devices:")
        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            logger.info(f"  GPU {i}: {gpu_name}")
            gpu_devices.append(f"cuda:{i}")
            try:
                free_mem, total_mem = torch.cuda.mem_get_info(i)
                free_mem_gb = free_mem / (1024**3)
                total_mem_gb = total_mem / (1024**3)
                logger.info(f"    Memory: {free_mem_gb:.2f}GB free of {total_mem_gb:.2f}GB total")
            except:
                logger.info("    Memory info not available")
        device_setting = "cuda" # Indicate GPU preference
        # *** INCREASED DEFAULT BATCH SIZE FOR GPU ***
        default_embedding_batch_size = 256
    else:
        logger.warning("CUDA is not available. Using CPU for embeddings.")
        device_setting = "cpu"
        gpu_count = 0
        # Keep CPU batch size smaller
        default_embedding_batch_size = 64

    config = {
        "postgres_connection": postgres_conn_env,
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2"),
        "embedding_device": os.getenv("EMBEDDING_DEVICE", device_setting),
        # Batch size for model.encode within each GPU process
        "embedding_batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", str(default_embedding_batch_size))),
        "max_chunk_size": int(os.getenv("MAX_CHUNK_SIZE", "2000")),
        "min_chunk_size": int(os.getenv("MIN_CHUNK_SIZE", "200")),
        "overlap_size": int(os.getenv("OVERLAP_SIZE", "100")),
        "gpu_devices": gpu_devices # List of cuda device IDs like ["cuda:0", "cuda:1"]
    }

    logger.info(f"Using embedding batch size: {config['embedding_batch_size']}") # Log the actual size being used
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

# Helper function to encode on a specific GPU
def _encode_on_gpu(rank: int, world_size: int, chunks: List[str], model_name: str,
                   batch_size: int, hf_token: Optional[str], return_dict: Dict):
    """Function executed by each GPU process."""
    try:
        device = f'cuda:{rank}'
        torch.cuda.set_device(device)
        logger.info(f"Process {rank}/{world_size} starting on {device}")

        # Load model on the assigned device
        model = SentenceTransformer(model_name, device=device, token=hf_token)
        logger.info(f"Process {rank}: Model loaded on {device}")

        # Determine chunks for this process
        num_chunks = len(chunks)
        chunks_per_process = num_chunks // world_size
        remainder = num_chunks % world_size

        start_idx = rank * chunks_per_process + min(rank, remainder)
        end_idx = start_idx + chunks_per_process + (1 if rank < remainder else 0)

        process_chunks = chunks[start_idx:end_idx]
        if not process_chunks:
            logger.info(f"Process {rank}: No chunks assigned. Exiting.")
            return_dict[rank] = []
            return

        logger.info(f"Process {rank}: Encoding {len(process_chunks)} chunks (indices {start_idx}-{end_idx}) with batch size {batch_size}")

        # Encode the assigned chunks
        embeddings = model.encode(process_chunks, batch_size=batch_size, show_progress_bar=(rank == 0)) # Show progress only for rank 0

        # Store results (convert to list for pickling)
        return_dict[rank] = embeddings.tolist()
        logger.info(f"Process {rank}: Encoding finished.")

        # Clean up GPU memory if possible
        del model
        torch.cuda.empty_cache()

    except Exception as e:
        logger.error(f"Error in GPU process {rank}: {e}", exc_info=True)
        return_dict[rank] = e # Store exception to signal failure

def generate_embeddings(chunks: List[str], model_name: str,
                       gpu_devices: List[str], batch_size: int = 64) -> List[List[float]]:
    """Generate embeddings using manual multi-GPU processing via torch.multiprocessing."""
    try:
        hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
        num_gpus = len(gpu_devices)

        if num_gpus > 0:
            logger.info(f"Starting manual multi-GPU encoding using {num_gpus} devices: {gpu_devices}")

            # Use a manager dictionary to collect results from processes
            manager = mp.Manager()
            return_dict = manager.dict()

            # Spawn processes, one for each GPU
            # Using spawn context is generally safer with CUDA
            mp.spawn(_encode_on_gpu,
                     args=(num_gpus, chunks, model_name, batch_size, hf_token, return_dict),
                     nprocs=num_gpus,
                     join=True)

            logger.info("All GPU processes finished. Aggregating results.")

            # Aggregate results in the correct order and check for errors
            all_embeddings = []
            errors = []
            for i in range(num_gpus):
                result = return_dict.get(i)
                if isinstance(result, Exception):
                    errors.append(f"GPU {i} failed: {result}")
                elif result is not None:
                    all_embeddings.extend(result)
                else:
                    errors.append(f"GPU {i} did not return a result.")

            if errors:
                raise EmbeddingError("Errors occurred during multi-GPU encoding: " + "; ".join(errors))

            # Sanity check length
            if len(all_embeddings) != len(chunks):
                 logger.warning(f"Mismatch in embedding count: Expected {len(chunks)}, Got {len(all_embeddings)}. Check process logs.")
                 # Decide how to handle - maybe raise error or return partial?
                 # For now, raise an error if counts don't match
                 raise EmbeddingError(f"Embedding count mismatch: Expected {len(chunks)}, Got {len(all_embeddings)}")

            logger.info("Successfully aggregated embeddings from all GPUs.")
            return all_embeddings

        else: # Fallback to CPU
            logger.info(f"Encoding {len(chunks)} chunks on CPU with batch size {batch_size}")
            model = SentenceTransformer(model_name, token=hf_token, device='cpu')
            embeddings = model.encode(
                sentences=chunks,
                batch_size=batch_size,
                show_progress_bar=True
            )
            return [embed.tolist() for embed in embeddings]

    except Exception as e:
        # Catch potential spawn errors or aggregation errors
        logger.error(f"Error generating embeddings: {e}", exc_info=True)
        raise EmbeddingError(f"Failed during embedding generation: {e}")

def insert_documents_batch(conn: psycopg2.extensions.connection,
                           doc_batch_data: List[Dict[str, Any]]) -> Dict[str, str]:
    """Insert a batch of document records and return a mapping from original file path to document_id."""
    doc_id_map = {}
    insert_data = [] # Collect data for insertion
    for doc_data in doc_batch_data:
        document_id = f"doc_{uuid.uuid4().hex}"
        doc_id_map[doc_data['file_path']] = document_id # Map file path to generated ID
        insert_data.append((
            document_id,
            doc_data['content'],
            json.dumps(doc_data['metadata']) # Metadata now includes 'source' and 'relative_path'
        ))

    if not insert_data:
        logger.warning("No documents provided for batch insertion.")
        return doc_id_map

    try:
        with conn.cursor() as cursor:
            # Use execute_values for efficient batch insertion if psycopg2 version supports it
            # Fallback to executemany otherwise
            try:
                from psycopg2.extras import execute_values
                execute_values(
                    cursor,
                    "INSERT INTO documents (document_id, content, metadata) VALUES %s",
                    insert_data,
                    template='(%s, %s, %s)',
                    page_size=100 # Adjust page size as needed
                )
                logger.info(f"Inserted {len(insert_data)} document records using execute_values.")
            except ImportError:
                logger.warning("psycopg2.extras.execute_values not available, using slower executemany.")
                cursor.executemany(
                "INSERT INTO documents (document_id, content, metadata) VALUES (%s, %s, %s)",
                    insert_data
            )
                logger.info(f"Inserted {len(insert_data)} document records using executemany.")
        conn.commit()
        return doc_id_map
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting document batch: {e}", exc_info=True)
        raise StorageError(f"Failed to insert document batch: {e}")

def insert_chunks_batch(conn: psycopg2.extensions.connection,
                        chunk_batch_data: List[Tuple[str, str, str, List[float]]]):
    """Insert a batch of chunks and their embeddings.
       chunk_batch_data format: [(chunk_id, document_id, content, embedding), ...]
    """
    if not chunk_batch_data:
        logger.warning("No chunks provided for batch insertion.")
        return

    try:
        with conn.cursor() as cursor:
            try:
                from psycopg2.extras import execute_values
                execute_values(
                    cursor,
                    "INSERT INTO chunks (chunk_id, document_id, content, embedding) VALUES %s",
                    chunk_batch_data,
                    template='(%s, %s, %s, %s)',
                    page_size=500 # Adjust page size based on chunk size/memory
                )
                logger.info(f"Inserted {len(chunk_batch_data)} chunks using execute_values.")
            except ImportError:
                logger.warning("psycopg2.extras.execute_values not available, using slower executemany.")
                cursor.executemany(
                    "INSERT INTO chunks (chunk_id, document_id, content, embedding) VALUES (%s, %s, %s, %s)",
                    chunk_batch_data
                )
                logger.info(f"Inserted {len(chunk_batch_data)} chunks using executemany.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting chunk batch: {e}", exc_info=True)
        raise StorageError(f"Failed to insert chunk batch: {e}")


def check_if_processed(conn: psycopg2.extensions.connection, file_path: str) -> bool:
    """Check if a document with this file path has already been processed."""
    try:
        with conn.cursor() as cursor:
            # Query the metadata JSONB field for the 'source' key matching the file path
            # Note: Performance depends on indexing strategy for the metadata column (GIN index recommended)
            cursor.execute(
                "SELECT 1 FROM documents WHERE metadata->>'source' = %s LIMIT 1",
                (file_path,)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking processing status for {file_path}: {e}")
        # To be safe, assume it might have been processed if check fails
        return True


def main():
    """Main function to process documents in batches from the classified directory."""
    parser = argparse.ArgumentParser(description="Process classified GRS documents and store them in PostgreSQL")
    # Remove --data-dir argument
    # parser.add_argument("--data-dir", default="data", help="Directory containing documents to process")
    parser.add_argument("--limit", type=int, default=None, help="Limit the total number of documents to process")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of documents to process per batch")
    args = parser.parse_args()

    config = load_config()
    conn = None
    total_processed_count = 0
    total_skipped_count = 0
    total_error_count = 0
    initial_skip_check_count = 0 # Track skips found during the initial check
    doc_batch_size = args.batch_size

    try:
        conn = connect_to_db(config["postgres_connection"])
        # --- CHANGE: Set data_path specifically ---
        data_path = project_root / "data/classified_grs" # Use project_root
        if not data_path.is_dir():
            logger.error(f"CRITICAL: Classified data directory not found: {data_path.resolve()}")
            return # Exit if the classified directory doesn't exist

        logger.info(f"Searching for PDF files recursively in: {data_path.resolve()}")
        # --- CHANGE: Use rglob for recursion ---
        all_pdf_files = list(data_path.rglob("*.pdf"))
        total_files_found = len(all_pdf_files)
        logger.info(f"Found {total_files_found} PDF files in {data_path} and its subdirectories.")

        if not all_pdf_files:
            logger.warning("No PDF files found in the classified directory. Exiting.")
            return

        # --- ADD: Filter out already processed files ---
        logger.info("Checking database for already processed documents...")
        unprocessed_files = []
        for file_path in all_pdf_files:
            if not check_if_processed(conn, str(file_path)):
                unprocessed_files.append(file_path)
            else:
                initial_skip_check_count += 1
        logger.info(f"Found {initial_skip_check_count} documents already processed during initial check. Skipping them.")
        logger.info(f"Total unprocessed documents to process: {len(unprocessed_files)}")

        files_to_process = unprocessed_files
        if args.limit:
            limit = min(args.limit, len(files_to_process)) # Ensure limit doesn't exceed available files
            files_to_process = files_to_process[:limit]
            logger.info(f"Processing limited to {limit} previously unprocessed documents")
        else:
             logger.info(f"Attempting to process all {len(files_to_process)} previously unprocessed documents.")

        num_files_to_process = len(files_to_process)
        if num_files_to_process == 0:
            logger.info("No new documents to process. Exiting.")
            return

        for i in range(0, num_files_to_process, doc_batch_size):
            batch_files = files_to_process[i : i + doc_batch_size]
            batch_start_num = i + 1
            batch_end_num = min(i + doc_batch_size, num_files_to_process)
            logger.info(f"--- Processing document batch {batch_start_num}-{batch_end_num} of {num_files_to_process} (unprocessed files) ---")

            doc_data_for_batch = []       # Holds dicts for docs successfully extracted/chunked
            all_chunks_in_batch = []      # All chunks from all docs in this batch
            # chunk_to_doc_map removed as we map later using file_path_to_doc_id_map
            batch_error_count = 0
            batch_skipped_intra_loop_count = 0 # Count skips found *during* this batch loop

            # 1. Extract text and chunk documents in the batch
            for file_path in batch_files:
                # Double-check before expensive processing (in case of script restart/long runs)
                if check_if_processed(conn, str(file_path)):
                    logger.debug(f"Skipping {file_path.name} as it was processed between initial check and batch start.")
                    batch_skipped_intra_loop_count += 1
                    continue

                try:
                    logger.debug(f"Extracting and chunking: {file_path.name}")
                    content = extract_text_from_pdf(file_path)
                    if not content:
                        logger.warning(f"No content extracted from {file_path.name}, skipping.")
                        batch_error_count += 1
                        continue

                    chunks = semantic_chunk_document(
                        content,
                        config["max_chunk_size"],
                        config["min_chunk_size"],
                        config["overlap_size"]
                    )
                    if not chunks:
                        logger.warning(f"No chunks generated for {file_path.name}, skipping.")
                        batch_error_count += 1
                        continue

                    metadata = {
                        'title': file_path.stem,
                        'source': str(file_path), # Store the full path as source
                        'file_type': file_path.suffix.lower(),
                        # Add relative path within classified_grs for context
                        'relative_path': str(file_path.relative_to(data_path))
                    }
                    doc_data_for_batch.append({
                        'file_path': str(file_path), # Keep original path for mapping
                        'content': content,
                        'metadata': metadata,
                        'num_chunks': len(chunks)
                    })

                    all_chunks_in_batch.extend(chunks)

                except Exception as e:
                    logger.error(f"Error during extraction/chunking for {file_path.name}: {e}", exc_info=False)
                    batch_error_count += 1
                    continue # Loop continues automatically to next file

            total_error_count += batch_error_count
            total_skipped_count += batch_skipped_intra_loop_count # Add skips found during batch processing
            if not doc_data_for_batch:
                logger.warning(f"No documents successfully processed for text/chunks in batch {batch_start_num}-{batch_end_num}. Skipping embedding/insertion.")
                continue # Skip to the next batch

            logger.info(f"Collected {len(all_chunks_in_batch)} chunks from {len(doc_data_for_batch)} documents in batch {batch_start_num}-{batch_end_num}.")

            # 2. Generate embeddings for all chunks in the batch
            batch_embeddings = None # Initialize
            try:
                if all_chunks_in_batch:
                    logger.info(f"Generating embeddings for {len(all_chunks_in_batch)} chunks...")
                    batch_embeddings = generate_embeddings(
                        all_chunks_in_batch,
                        config["embedding_model"],
                        config["gpu_devices"],
                        config["embedding_batch_size"]
                    )
                    logger.info(f"Embedding generation complete for batch.")
                else:
                    logger.warning("No chunks found in batch to generate embeddings for.")
                    # This shouldn't happen if doc_data_for_batch is not empty, but good to check
                    continue # Skip embedding if no chunks

            except (EmbeddingError, Exception) as e:
                logger.error(f"Failed to generate embeddings for batch {batch_start_num}-{batch_end_num}: {e}", exc_info=True)
                total_error_count += len(doc_data_for_batch) # Count all docs in batch as errors if embedding fails
                logger.warning("Skipping database insertion for this batch due to embedding failure.")
                continue # Skip to the next batch

            if batch_embeddings is None or len(batch_embeddings) != len(all_chunks_in_batch):
                logger.error(f"Embedding generation failed or returned incorrect number of embeddings for batch {batch_start_num}-{batch_end_num}.")
                total_error_count += len(doc_data_for_batch)
                logger.warning("Skipping database insertion for this batch.")
                continue

            # 3. Insert documents batch
            file_path_to_doc_id_map = None # Initialize
            try:
                # Insert doc records and get mapping from file_path -> document_id
                file_path_to_doc_id_map = insert_documents_batch(conn, doc_data_for_batch)
            except (StorageError, Exception) as e:
                logger.error(f"Failed to insert document batch {batch_start_num}-{batch_end_num}: {e}", exc_info=True)
                total_error_count += len(doc_data_for_batch) # Count all docs as errors
                logger.warning("Skipping chunk insertion for this batch due to document insertion failure.")
                continue # Skip to the next batch

            # 4. Prepare and Insert chunks batch
            chunk_batch_data_to_insert = []
            processed_docs_in_batch = 0
            try:
                chunk_embedding_index = 0
                # Iterate through the documents that were *successfully* processed for text/chunking
                for doc_data in doc_data_for_batch:
                    original_file_path = doc_data['file_path']
                    document_id = file_path_to_doc_id_map.get(original_file_path)
                    num_chunks_for_doc = doc_data['num_chunks']

                    if document_id:
                        # Get the corresponding chunks and embeddings for this document
                        start_chunk_idx = chunk_embedding_index
                        end_chunk_idx = chunk_embedding_index + num_chunks_for_doc
                        doc_chunks = all_chunks_in_batch[start_chunk_idx:end_chunk_idx]
                        doc_embeddings = batch_embeddings[start_chunk_idx:end_chunk_idx]

                        for chunk_content, embedding in zip(doc_chunks, doc_embeddings):
                            chunk_id = f"chunk_{uuid.uuid4().hex}"
                            chunk_batch_data_to_insert.append((
                                chunk_id,
                                document_id,
                                chunk_content,
                                embedding # Assumes embedding is list/tuple
                            ))
                        chunk_embedding_index = end_chunk_idx # Move index for next doc
                        processed_docs_in_batch += 1 # Count successful doc processing
                    else:
                        # This case should ideally not happen if doc insertion succeeded and mapping is correct
                        logger.warning(f"Could not find document_id for file {original_file_path} during chunk preparation. Skipping its chunks.")
                        # Need to advance the chunk_embedding_index anyway
                        chunk_embedding_index += num_chunks_for_doc

                if chunk_batch_data_to_insert:
                    insert_chunks_batch(conn, chunk_batch_data_to_insert)
                    total_processed_count += processed_docs_in_batch # Increment overall count
                else:
                     logger.warning(f"No chunks prepared for insertion for batch {batch_start_num}-{batch_end_num}.")

            except (StorageError, Exception) as e:
                 logger.error(f"Failed to insert chunk batch {batch_start_num}-{batch_end_num}: {e}", exc_info=True)
                 # Log error, but don't double-count total_error_count
                 logger.warning("Chunk insertion failed for potentially inserted documents.")
                 continue # Skip to next batch

            logger.info(f"--- Finished processing document batch {batch_start_num}-{batch_end_num} --- Successfully processed {processed_docs_in_batch} documents in this batch ---")

    except Exception as e:
        logger.critical(f"An unrecoverable error occurred during main processing loop: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")
        logger.info(f"Processing complete. Total documents successfully processed: {total_processed_count}. Total skipped (already processed): {total_skipped_count + initial_skip_check_count}. Total errors encountered: {total_error_count}.")


if __name__ == "__main__":
    # Set start method for multiprocessing if needed (forkserver or spawn recommended with CUDA)
    try:
        mp.set_start_method('spawn', force=True)
        logger.info("Set multiprocessing start method to 'spawn'")
    except RuntimeError as e:
        logger.warning(f"Could not set multiprocessing start method to 'spawn': {e}. Using default.")
    main() 