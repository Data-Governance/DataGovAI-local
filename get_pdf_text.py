"""Extracts and prints the full text content of a specified PDF file."""

import argparse
import sys
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("Error: PyPDF2 library is required but not installed.", file=sys.stderr)
    print("Please install it: conda install pypdf2", file=sys.stderr)
    PDF_AVAILABLE = False
    sys.exit(1)

def extract_text(pdf_path: Path) -> str:
    """Extracts text from all pages of a PDF."""
    full_text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            print(f"Reading {num_pages} pages from {pdf_path.name}...", file=sys.stderr)
            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n\n---\n\n" # Add page separator
                except Exception as page_err:
                    print(f"Warning: Could not extract text from page {i+1}: {page_err}", file=sys.stderr)
    except Exception as e:
        print(f"Error opening or reading PDF {pdf_path}: {e}", file=sys.stderr)
        return ""
    return full_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from a PDF file.")
    parser.add_argument("pdf_file", type=str, help="Path to the PDF file.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_file)
    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        print(f"Error: Invalid PDF file path: {args.pdf_file}", file=sys.stderr)
        sys.exit(1)

    if PDF_AVAILABLE:
        extracted_text = extract_text(pdf_path)
        if extracted_text:
            print(extracted_text)
        else:
            print(f"Could not extract text from {pdf_path.name}.", file=sys.stderr)
            sys.exit(1) 