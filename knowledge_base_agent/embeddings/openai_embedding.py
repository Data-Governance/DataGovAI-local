from typing import List
import numpy as np
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseEmbeddingModel

class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI embedding model implementation."""
    
    def __init__(
        self,
        model: str = "text-embedding-3-large",
        api_key: str = None,
        batch_size: int = 100,
        max_retries: int = 3
    ):
        """Initialize the OpenAI embedding model.
        
        Args:
            model: The OpenAI model to use
            api_key: OpenAI API key
            batch_size: Maximum number of texts to embed in one batch
            max_retries: Maximum number of retries for API calls
        """
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._dimension = self._get_model_dimension()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embeddings for a single text."""
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return np.array(response.data[0].embedding)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.model
            )
            batch_embeddings = [np.array(data.embedding) for data in response.data]
            embeddings.extend(batch_embeddings)
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        return self._dimension
    
    def get_metadata(self) -> dict:
        """Return metadata about the embedding model."""
        return {
            "model": self.model,
            "dimension": self._dimension,
            "provider": "OpenAI",
            "batch_size": self.batch_size
        }
    
    def generate(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of texts."""
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            # Use retry logic similar to embed_text if desired, or rely on embed_batch's implicit retry if it calls embed_text
            # For simplicity here, directly calling the client with batch
            @retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=4, max=10)
            )
            def get_embeddings_with_retry(batch_texts):
                return self.client.embeddings.create(
                    input=batch_texts,
                    model=self.model
                )

            try:
                response = get_embeddings_with_retry(batch)
                batch_embeddings = [np.array(data.embedding) for data in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                # Handle or log the error appropriately
                # Depending on requirements, you might raise an error, return partial results, or skip the batch
                print(f"Error generating embeddings for batch starting at index {i}: {e}") # Basic logging
                # Decide on error strategy: raise, continue, fill with zeros, etc.
                # For now, let's fill with zero vectors of the correct dimension if a batch fails
                # This might not be ideal for all use cases
                num_failed = len(batch)
                zero_embedding = np.zeros(self.get_dimension())
                all_embeddings.extend([zero_embedding] * num_failed)
                # Alternatively, re-raise the exception:
                # raise EmbeddingError(f"Failed to generate embeddings for batch: {e}") from e

        return all_embeddings
    
    def _get_model_dimension(self) -> int:
        """Get the embedding dimension for the model."""
        dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536
        }
        return dimensions.get(self.model, 1536) 