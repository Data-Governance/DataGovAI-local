"""
Base embeddings classes for the Generic AI Agent package.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class EmbeddingGenerator(ABC):
    """Base class for generating embeddings from text."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model = None
        self.dimension = self.config.get('dimension', 768)  # Default dimension
        self.batch_size = self.config.get('batch_size', 32)
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the embedding model."""
        pass
    
    @abstractmethod
    def generate(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        pass
    
    def generate_single(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.generate([text])[0]
    
    @abstractmethod
    def close(self) -> None:
        """Close the embedding model and free resources."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

__all__ = ["EmbeddingGenerator"] 