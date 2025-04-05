"""
Utility functions for the Generic AI Agent package.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import yaml

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """Set up logging configuration."""
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),
            *([] if log_file is None else [logging.FileHandler(log_file)])
        ]
    )

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    separator: str = " "
) -> List[str]:
    """Split text into overlapping chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")
    
    words = text.split(separator)
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + chunk_size
        chunk = separator.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    
    return chunks

def get_file_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get metadata for a file."""
    file_path = Path(file_path)
    stats = file_path.stat()
    
    return {
        "filename": file_path.name,
        "extension": file_path.suffix.lower(),
        "size_bytes": stats.st_size,
        "created_at": stats.st_ctime,
        "modified_at": stats.st_mtime,
        "is_binary": not is_text_file(file_path),
    }

def is_text_file(file_path: Union[str, Path], sample_size: int = 8192) -> bool:
    """Check if a file is a text file by sampling its content."""
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            return not bool(sample.translate(None, bytes(range(32, 127)) + b'\n\r\t\f\b'))
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ensure the filename is not too long
    max_length = 255
    name, ext = os.path.splitext(filename)
    if len(filename) > max_length:
        return name[:max_length-len(ext)] + ext
    
    return filename

__all__ = [
    "setup_logging",
    "load_config",
    "chunk_text",
    "get_file_metadata",
    "is_text_file",
    "sanitize_filename",
] 