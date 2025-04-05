"""
Analyzes the content of the data directory, focusing on GRS PDF documents.

Identifies file types, counts documents, checks PDF structure and text 
extractability for a sample, and looks for common GRS patterns.
"""

import argparse
import logging
import re
from pathlib import Path
from collections import Counter
from typing import Dict

# Import PyPDF2 if available
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common GRS Patterns to look for
GRS_PATTERNS = {
    "schedule_ref": re.compile(r'GRS \d+(\.\d+)?', re.IGNORECASE),
    "item_ref": re.compile(r'Item \d+[a-zA-Z]?', re.IGNORECASE),
    "disposition": re.compile(r'Disposition:', re.IGNORECASE),
    "retention": re.compile(r'Retention Period:', re.IGNORECASE),
    "authority": re.compile(r'Authority:', re.IGNORECASE)
}

def analyze_pdf_sample(pdf_path: Path, num_pages_to_check: int = 2) -> Dict:
    """Analyzes a single PDF file sample."""
    analysis = {
        "path": str(pdf_path),
        "page_count": 0,
        "text_extractable": False,
        "first_500_chars": "",
        "patterns_found": {k: False for k in GRS_PATTERNS}
    }
    if not PDF_AVAILABLE:
        logger.warning("PyPDF2 not installed. Cannot perform PDF analysis.")
        return analysis

    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            analysis["page_count"] = len(reader.pages)
            
            extracted_text = ""
            for i in range(min(num_pages_to_check, analysis["page_count"])):
                page = reader.pages[i]
                try:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                except Exception as page_err:
                    logger.warning(f"Could not extract text from page {i+1} of {pdf_path}: {page_err}")
            
            if extracted_text.strip():
                analysis["text_extractable"] = True
                analysis["first_500_chars"] = extracted_text[:500].strip()
                
                # Check for GRS patterns
                for name, pattern in GRS_PATTERNS.items():
                    if pattern.search(extracted_text):
                        analysis["patterns_found"][name] = True
            else:
                analysis["first_500_chars"] = "(No text extracted or empty)"

    except Exception as e:
        logger.error(f"Failed to analyze PDF {pdf_path}: {e}")
        analysis["first_500_chars"] = f"(Error during analysis: {e})"
        
    return analysis

def main(data_dir: str, pdf_sample_size: int = 5):
    """Main analysis function."""
    data_path = Path(data_dir)
    if not data_path.is_dir():
        logger.error(f"Data directory not found: {data_dir}")
        return

    logger.info(f"Starting analysis of directory: {data_dir}")
    
    file_paths = list(data_path.rglob('*'))
    total_files = 0
    file_extensions = Counter()
    pdf_files = []

    for file_path in file_paths:
        if file_path.is_file():
            total_files += 1
            ext = file_path.suffix.lower()
            file_extensions[ext] += 1
            if ext == '.pdf':
                pdf_files.append(file_path)
    
    logger.info(f"Total files found: {total_files}")
    logger.info("File counts by extension:")
    for ext, count in file_extensions.items():
        logger.info(f"  {ext}: {count}")
        
    if not pdf_files:
        logger.warning("No PDF files found in the directory.")
        return

    logger.info(f"Analyzing a sample of {min(pdf_sample_size, len(pdf_files))} PDF files...")
    pdf_sample_results = []
    for i in range(min(pdf_sample_size, len(pdf_files))):
        result = analyze_pdf_sample(pdf_files[i])
        pdf_sample_results.append(result)
        logger.info(f"-- Sample {i+1}: {result['path']} --")
        logger.info(f"   Pages: {result['page_count']}")
        logger.info(f"   Text Extractable: {result['text_extractable']}")
        logger.info(f"   Patterns Found: {result['patterns_found']}")
        logger.info(f"   First ~500 Chars: \n{result['first_500_chars']}\n")

    # --- Add Summary Assessment Here --- 
    # Based on the sample, provide an overall assessment.
    num_extractable = sum(1 for r in pdf_sample_results if r["text_extractable"])
    if num_extractable == len(pdf_sample_results):
        logger.info("Assessment: All sampled PDFs appear to have extractable text.")
    elif num_extractable > 0:
        logger.warning("Assessment: Some sampled PDFs may not have extractable text (potential scans). OCR might be needed.")
    else:
         logger.error("Assessment: None of the sampled PDFs had extractable text. Processing will likely fail without OCR.")

    logger.info("Analysis complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze GRS documents in a directory.")
    parser.add_argument("data_dir", type=str, help="Path to the data directory containing GRS documents.")
    parser.add_argument("--sample-size", type=int, default=5, help="Number of PDF files to sample for detailed analysis.")
    
    args = parser.parse_args()
    main(args.data_dir, args.sample_size) 