from typing import List, Optional, Dict, Any
import re
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

# Download required NLTK data
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    try:
        # punkt_tab might be needed by some tokenizers implicitly
        nltk.data.find('tokenizers/punkt_tab/english') 
    except LookupError:
        nltk.download('punkt_tab', quiet=True) 

download_nltk_data()

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and unwanted special characters."""
    # Remove special characters but keep punctuation and basic symbols
    # Keep letters, numbers, whitespace, and .,!?\-()'" (hyphen is escaped)
    text = re.sub(r'[^\w\s.,!?\-()\'"]', '', text) # Escaped hyphen
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_chunks(
    text: str,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 100,
    overlap_size: int = 50
) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks while preserving sentence boundaries.
    
    Args:
        text: Text to split
        max_chunk_size: Maximum chunk size in characters
        min_chunk_size: Minimum chunk size in characters
        overlap_size: Number of characters to overlap between chunks
        
    Returns:
        List of chunks with their metadata
    """
    # Handle edge cases
    if not text or len(text) <= min_chunk_size:
        return [{"content": text, "start": 0, "end": len(text)}]
        
    chunks = []
    current_pos = 0
    
    while current_pos < len(text):
        # Find a good splitting point
        end_pos = min(current_pos + max_chunk_size, len(text))
        
        # Try to find sentence boundary
        if end_pos < len(text):
            # Look for sentence endings
            for marker in [". ", "! ", "? ", "\n\n"]:
                last_marker = text[current_pos:end_pos].rfind(marker)
                if last_marker != -1:
                    end_pos = current_pos + last_marker + len(marker)
                    break
                    
        # Create chunk with metadata
        chunk = {
            "content": text[current_pos:end_pos].strip(),
            "start": current_pos,
            "end": end_pos
        }
        chunks.append(chunk)
        
        # Move position for next chunk, accounting for overlap
        current_pos = max(current_pos + min_chunk_size, end_pos - overlap_size)
    
    return chunks

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract important keywords from text using frequency analysis."""
    # Tokenize and clean
    words = word_tokenize(text.lower())
    words = [w for w in words if w.isalnum() and len(w) > 2]
    
    # Count frequencies
    from collections import Counter
    word_freq = Counter(words)
    
    # Get top keywords
    keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    return keywords

def get_text_stats(text: str) -> dict:
    """Get basic statistics about the text."""
    words = word_tokenize(text)
    sentences = sent_tokenize(text)
    
    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
        "avg_sentence_length": len(words) / len(sentences) if sentences else 0
    } 