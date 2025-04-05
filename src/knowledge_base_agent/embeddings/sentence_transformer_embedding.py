"""
Sentence Transformer embedding model implementation with GPU support.
"""
from typing import List
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import os

from .base import BaseEmbeddingModel
from ..exceptions import EmbeddingError

logger = logging.getLogger(__name__)

class SentenceTransformerEmbedding(BaseEmbeddingModel):
    """GPU-enabled Sentence Transformer embedding model implementation."""

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        device: str = None,
        max_retries: int = 3
    ):
        """Initialize the Sentence Transformer model.

        Args:
            model: Model name from sentence-transformers (e.g., 'all-MiniLM-L6-v2', 'all-mpnet-base-v2')
            batch_size: Maximum number of texts to embed in one batch
            device: Device to run the model on ('cuda' or 'cpu'). If None, will use CUDA if available
            max_retries: Maximum number of retries for potential issues
        """
        self.model_name = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        
        # Set device (use CUDA if available and not explicitly set to CPU)
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing Sentence Transformer model '{model}' on device '{self.device}'")
        
        try:
            self.model = SentenceTransformer(model, device=self.device)
            self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model initialized successfully with dimension: {self._dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}", exc_info=True)
            raise EmbeddingError(f"Failed to initialize model: {e}") from e

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text."""
        try:
            if not isinstance(text, str):
                logger.warning(f"Input to embed_text was not a string (type: {type(text)}). Converting...")
                text = str(text)
                
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding text: {e}", exc_info=True)
            raise EmbeddingError(f"Failed to encode text: {e}") from e

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=self.batch_size)
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding batch: {e}", exc_info=True)
            raise EmbeddingError(f"Failed to encode batch: {e}") from e

    def get_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        return self._dimension

    def get_metadata(self) -> dict:
        """Return metadata about the embedding model."""
        return {
            "model": self.model_name,
            "dimension": self._dimension,
            "provider": "sentence-transformers",
            "batch_size": self.batch_size,
            "device": self.device
        }

    def generate(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of texts."""
        all_embeddings = []
        num_texts = len(texts)
        
        for i in range(0, num_texts, self.batch_size):
            batch = texts[i:min(i + self.batch_size, num_texts)]
            
            @retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=2, max=6)
            )
            def get_embeddings_with_retry(batch_texts):
                batch_embeddings = self.embed_batch(batch_texts)
                return batch_embeddings

            try:
                batch_embeddings = get_embeddings_with_retry(batch)
                # Split the numpy array into a list of arrays
                all_embeddings.extend([batch_embeddings[j] for j in range(len(batch))])
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch after {self.max_retries} attempts: {e}", exc_info=True)
                # Fill with zeros as fallback
                num_failed = len(batch)
                zero_embedding = np.zeros(self.get_dimension())
                all_embeddings.extend([zero_embedding] * num_failed)

        return all_embeddings 