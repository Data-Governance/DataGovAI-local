"""
Base embedding model interface and mock implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union

import numpy as np

class BaseEmbeddingModel(ABC):
    """Base class for embedding models."""
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> dict:
        """Return metadata about the embedding model."""
        pass

    @abstractmethod
    def generate(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of texts."""
        pass

class MockEmbeddingModel(BaseEmbeddingModel):
    """Mock embedding model for testing."""
    
    def __init__(self, dim: int = 768):
        """Initialize mock model."""
        self.dim = dim
        
    def generate(self, texts: List[str]) -> List[np.ndarray]:
        """Generate random embeddings for testing."""
        return [np.random.randn(self.dim) for _ in texts] 