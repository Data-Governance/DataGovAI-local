"""
Preprocesses Utah General Retention Schedule PDFs and loads them into the PostgreSQL knowledge base.

Extracts metadata, retention/disposition info using Regex, and stores documents, 
embeddings, and extracted entities.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple

# Import PyPDF2 if available
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("Error: PyPDF2 library is required but not installed.", file=sys.stderr)
    print("Please install it: conda install pypdf2", file=sys.stderr)
    PDF_AVAILABLE = False
    sys.exit(1)

# Assuming these are adjusted or available
from knowledge_base_agent.config import get_config
from knowledge_base_agent.processor import DocumentProcessor
from knowledge_base_agent.models import Document as PydanticDocument, Entity, Relationship
from knowledge_base_agent.cli import create_processor # Reuse CLI function for setup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Regex Patterns for Utah GRS --- 
# Adjust these based on more samples if needed
TITLE_RS_PATTERN = re.compile(r'^(.*?)\s*\((RS-\d+)\)', re.IGNORECASE | re.MULTILINE)
DESCRIPTION_PATTERN = re.compile(r'Description\s*\n(.*?)\n\s*Retention and Disposition', re.IGNORECASE | re.DOTALL)
RETENTION_DISPOSITION_PATTERN = re.compile(r'Retention and Disposition\s*\n(.*?)(?:\n\s*Categories|\n\s*Previous Schedule Number|\Z)', re.IGNORECASE | re.DOTALL)
UCA_PATTERN = re.compile(r'(Utah Code|UCA) (\S+)', re.IGNORECASE)

# Simple patterns to split Retention/Disposition text
RETENTION_PATTERN = re.compile(r'Retain (?:for )?([^;]+)', re.IGNORECASE)
DISPOSITION_PATTERN = re.compile(r'then (\w+)(?: records)?\.', re.IGNORECASE)

def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extracts text from all pages of a PDF."""
    full_text = ""
    if not PDF_AVAILABLE:
        return None
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                except Exception as page_err:
                    logger.warning(f"Could not extract text from a page in {pdf_path.name}: {page_err}")
        return full_text.strip()
    except Exception as e:
        logger.error(f"Error opening or reading PDF {pdf_path.name}: {e}")
        return None

def parse_utah_rs_text(text: str) -> Optional[Dict]:
    """Parses the full text of a Utah RS PDF using Regex."""
    if not text:
        return None

    parsed_data = {
        "record_series_title": None,
        "record_series_number": None,
        "description": None,
        "retention_disposition_text": None,
        "retention_period": None,
        "disposition_action": None,
        "legal_authorities": []
    }

    # Extract Title and RS Number
    title_match = TITLE_RS_PATTERN.search(text)
    if title_match:
        parsed_data["record_series_title"] = title_match.group(1).strip()
        parsed_data["record_series_number"] = title_match.group(2).strip()
    else:
        logger.warning("Could not extract Title/RS Number.")
        # Potentially try extracting from filename later if needed
        return None # Require RS number as ID

    # Extract Description
    desc_match = DESCRIPTION_PATTERN.search(text)
    if desc_match:
        parsed_data["description"] = desc_match.group(1).strip().replace('\n', ' ')
        # Extract Legal Authorities from Description
        for match in UCA_PATTERN.finditer(parsed_data["description"]):
            parsed_data["legal_authorities"].append(match.group(0))
    else:
        logger.warning(f"Could not extract Description for {parsed_data['record_series_number']}.")

    # Extract Retention and Disposition section text
    rd_match = RETENTION_DISPOSITION_PATTERN.search(text)
    if rd_match:
        rd_text = rd_match.group(1).strip().replace('\n', ' ')
        parsed_data["retention_disposition_text"] = rd_text
        
        # Try to parse out retention period
        ret_match = RETENTION_PATTERN.search(rd_text)
        if ret_match:
            parsed_data["retention_period"] = ret_match.group(1).strip()
            
        # Try to parse out disposition action
        disp_match = DISPOSITION_PATTERN.search(rd_text)
        if disp_match:
            parsed_data["disposition_action"] = disp_match.group(1).strip()
    else:
         logger.warning(f"Could not extract Retention/Disposition section for {parsed_data['record_series_number']}.")
         # Consider LLM fallback here if Retention/Disposition are critical

    return parsed_data

def main(data_dir: str, batch_size: int, config_path: Optional[str]):
    """Main preprocessing and loading function."""
    data_path = Path(data_dir)
    if not data_path.is_dir():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    # --- Configuration and Processor Setup ---
    try:
        config = get_config(config_path)
        # Ensure PostgreSQL is selected (can be overridden by env vars/defaults in get_config)
        config.storage.document_store_type = "postgres"
        config.storage.vector_store_type = "postgres"
        config.storage.knowledge_store_type = "postgres"
        
        if not config.storage.postgres_connection:
            logger.error("POSTGRES_CONNECTION environment variable or config setting is required.")
            sys.exit(1)
            
        logger.info(f"Using PostgreSQL connection: {config.storage.postgres_connection}")
        processor = create_processor(config) # Uses config to setup stores
        # TODO: Implement efficient batch commits - this requires modifying stores/processor
        # For now, it will commit per document which is slow.
        
    except Exception as e:
        logger.exception(f"Failed to initialize processor or configuration: {e}")
        sys.exit(1)

    # --- File Discovery ---    
    logger.info(f"Scanning for PDF files in {data_dir}...")
    pdf_files = list(data_path.rglob('*.pdf'))
    total_files = len(pdf_files)
    logger.info(f"Found {total_files} PDF files.")

    if total_files == 0:
        logger.warning("No PDF files found. Exiting.")
        return

    # --- Processing Loop --- 
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for i in range(0, total_files, batch_size):
        batch_files = pdf_files[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}/{(total_files + batch_size - 1) // batch_size} ({len(batch_files)} files)...")
        
        # TODO: Implement batch DB Session handling here for efficiency
        # session = processor.document_store.Session() # Assuming stores expose Session
        # try:

        for pdf_path in batch_files:
            try:
                logger.debug(f"Processing: {pdf_path.name}")
                
                # 1. Extract Text
                full_text = extract_text_from_pdf(pdf_path)
                if not full_text:
                    logger.warning(f"Skipping {pdf_path.name} due to text extraction failure.")
                    skipped_count += 1
                    continue

                # 2. Parse Text with Regex
                parsed_data = parse_utah_rs_text(full_text)
                if not parsed_data or not parsed_data.get("record_series_number"):
                    logger.warning(f"Skipping {pdf_path.name} due to parsing failure (missing RS Number?).")
                    skipped_count += 1
                    continue
                
                record_series_id = parsed_data["record_series_number"]
                
                # 3. Check for Resumability (Requires store modification or direct query)
                # if processor.document_store.get_document(record_series_id, session=session): # Example modification
                #     logger.debug(f"Skipping {record_series_id} - already processed.")
                #     skipped_count += 1
                #     continue
                    
                # 4. Prepare Document Object
                doc_metadata = {
                    "record_series_title": parsed_data["record_series_title"],
                    "source": "Utah General Retention Schedule",
                    "retention_period_extracted": parsed_data["retention_period"],
                    "disposition_action_extracted": parsed_data["disposition_action"],
                    "legal_authorities_extracted": parsed_data["legal_authorities"],
                    "retention_disposition_full_text": parsed_data["retention_disposition_text"]
                }
                
                # Use Pydantic model defined in knowledge_base_agent.models
                doc = PydanticDocument(
                    id=record_series_id,
                    content=full_text, # Store full text for context/embedding
                    metadata=doc_metadata,
                    title=parsed_data["record_series_title"] or pdf_path.stem,
                    chunks=[] # Chunking might not be needed if embedding full doc
                )
                
                # 5. Process Document (stores doc, generates/stores embedding, extracts/stores entities)
                #    This currently commits per document - needs optimization for batching. 
                processor.process_document(doc) 
                # TODO: Pass session=session when batching is implemented
                
                processed_count += 1
                
            except Exception as file_err:
                logger.error(f"Error processing file {pdf_path.name}: {file_err}", exc_info=False)
                error_count += 1
        
        # TODO: Commit the batch session here when implemented
        # session.commit()
        # logger.info("Batch committed.")
        # except Exception as batch_err:
        #     logger.exception(f"Error during batch processing: {batch_err}")
        #     session.rollback()
        # finally:
        #     session.close()

    logger.info("--- Processing Summary ---")
    logger.info(f"Total Files: {total_files}")
    logger.info(f"Successfully Processed: {processed_count}")
    logger.info(f"Skipped: {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("Processing complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess Utah GRS PDFs and load into PostgreSQL KB.")
    parser.add_argument("data_dir", type=str, help="Path to the data directory containing GRS PDF documents.")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of files to process in each batch.")
    parser.add_argument("--config", type=str, default=None, help="Path to optional configuration file.")
    # Add other relevant args if needed (e.g., specific PG connection override)
    
    args = parser.parse_args()
    
    # Basic check for PyPDF2
    if not PDF_AVAILABLE:
        sys.exit(1)
        
    main(args.data_dir, args.batch_size, args.config) 