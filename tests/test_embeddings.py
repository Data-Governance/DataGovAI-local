import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from knowledge_base_agent.embeddings.base import BaseEmbeddingModel
from knowledge_base_agent.embeddings.openai_embedding import OpenAIEmbedding

def test_base_embedding_model_is_abstract():
    """Test that BaseEmbeddingModel cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseEmbeddingModel()

@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked OpenAI client."""
    mock_client = MagicMock()
    # Mock the response structure for embeddings.create
    mock_embedding_data = MagicMock()
    mock_embedding_data.embedding = list(np.random.rand(1536))
    mock_response = MagicMock()
    mock_response.data = [mock_embedding_data]
    mock_client.embeddings.create.return_value = mock_response
    return mock_client

@patch('knowledge_base_agent.embeddings.openai_embedding.OpenAI')
def test_openai_embedding_single_text(MockOpenAI, mock_openai_client):
    """Test OpenAI embedding for single text with patched client."""
    # Ensure the constructor uses the mocked client
    MockOpenAI.return_value = mock_openai_client 

    # Create embedding model (constructor will now use the mock)
    model = OpenAIEmbedding(api_key="test_key")
    
    # Test embedding
    text = "Test text"
    embedding = model.embed_text(text)
    
    # Verify results
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1536,)
    # Verify the mocked client's method was called
    mock_openai_client.embeddings.create.assert_called_once_with(
        input=text,
        model="text-embedding-3-large"
    )

@patch('knowledge_base_agent.embeddings.openai_embedding.OpenAI')
def test_openai_embedding_batch(MockOpenAI, mock_openai_client):
    """Test OpenAI embedding for batch of texts with patched client."""
    # Configure the mock for batch response
    mock_embedding_data_1 = MagicMock()
    mock_embedding_data_1.embedding = list(np.random.rand(1536))
    mock_embedding_data_2 = MagicMock()
    mock_embedding_data_2.embedding = list(np.random.rand(1536))
    mock_response = MagicMock()
    mock_response.data = [mock_embedding_data_1, mock_embedding_data_2]
    mock_openai_client.embeddings.create.return_value = mock_response
    
    # Ensure the constructor uses the mocked client
    MockOpenAI.return_value = mock_openai_client

    # Create embedding model
    model = OpenAIEmbedding(api_key="test_key", batch_size=2)
    
    # Test batch embedding
    texts = ["Text 1", "Text 2"]
    embeddings = model.embed_batch(texts)
    
    # Verify results
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (2, 1536)
    # Verify the mocked client's method was called
    mock_openai_client.embeddings.create.assert_called_once_with(
        input=texts,
        model="text-embedding-3-large"
    )

def test_openai_embedding_metadata():
    """Test OpenAI embedding metadata."""
    model = OpenAIEmbedding(api_key="test_key")
    metadata = model.get_metadata()
    
    assert metadata["model"] == "text-embedding-3-large"
    assert metadata["dimension"] == 3072
    assert metadata["provider"] == "OpenAI"
    assert metadata["batch_size"] == 100

def test_openai_embedding_dimension():
    """Test OpenAI embedding dimensions for different models."""
    models = {
        "text-embedding-3-large": 3072,
        "text-embedding-3-small": 1536,
        "text-embedding-ada-002": 1536
    }
    
    for model_name, expected_dim in models.items():
        model = OpenAIEmbedding(model=model_name, api_key="test_key")
        assert model.get_dimension() == expected_dim 