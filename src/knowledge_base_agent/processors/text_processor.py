"""
Text processor for handling document text.
"""

from typing import List
from ..models import ProcessingConfig

class TextProcessor:
    """Process text documents."""
    
    def __init__(self, config: ProcessingConfig):
        """Initialize text processor."""
        self.config = config
        
    def process_text(self, text: str) -> str:
        """Process text by cleaning and normalizing."""
        # For now, just return the text as is
        return text
        
    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks."""
        # For now, just split by newlines
        chunks = text.split('\n')
        return [chunk for chunk in chunks if chunk.strip()] 