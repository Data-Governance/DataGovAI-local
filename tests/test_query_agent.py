"""
Tests for the RAG+KG Query Agent.
"""
import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, ANY

import torch
import numpy as np
from knowledge_base_agent.query_agent import RAGKGQueryAgent
from knowledge_base_agent.models import SearchResult
from knowledge_base_agent.exceptions import ProcessingError

# Skip tests if torch not available
torch_available = torch.cuda.is_available()

@pytest.fixture
def mock_processor():
    """Create a mock processor with the necessary methods."""
    processor = MagicMock()
    # Set up search to return some sample results
    processor.search.return_value = [
        SearchResult(
            document_id="doc1",
            content="This is a sample chunk about retention periods.",
            score=0.85,
            metadata={"title": "Test Document"}
        ),
        SearchResult(
            document_id="doc2",
            content="Another chunk about legal authorities.",
            score=0.75,
            metadata={"title": "Legal Document"}
        )
    ]
    
    # Set up knowledge_store with query_entities method
    processor.knowledge_store = MagicMock()
    processor.knowledge_store.query_entities.return_value = [
        {
            "id": "entity1",
            "type": "retention_period",
            "value": "3 years",
            "document_id": "doc1"
        }
    ]
    
    return processor

@pytest.fixture
def mock_model_and_tokenizer():
    """Create mock model and tokenizer for testing without loading actual models."""
    with patch('transformers.AutoModelForCausalLM.from_pretrained') as mock_model:
        with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
            # Configure the tokenizer mock
            tokenizer_instance = MagicMock()
            tokenizer_instance.decode.return_value = "Test response with some JSON content: {\"record_series_number\": null, \"retention_period\": \"3 years\", \"disposition_action\": null, \"legal_authority\": null}"
            tokenizer_instance.encode.return_value = [1, 2, 3]  # Dummy token IDs
            tokenizer_instance.eos_token_id = 50256
            mock_tokenizer.return_value = tokenizer_instance
            
            # Configure the model mock
            model_instance = MagicMock()
            # Return some output tensor when generate is called
            outputs = torch.tensor([[1, 2, 3]])
            model_instance.generate.return_value = outputs
            model_instance.to.return_value = model_instance  # For device placement
            mock_model.return_value = model_instance
            
            yield mock_model, mock_tokenizer

@pytest.mark.skipif(not torch_available, reason="Torch not available")
def test_query_agent_initialization(mock_processor, mock_model_and_tokenizer):
    """Test initialization of the RAGKGQueryAgent."""
    # Setup
    mock_model, mock_tokenizer = mock_model_and_tokenizer
    
    # Execute
    agent = RAGKGQueryAgent(processor=mock_processor)
    
    # Verify
    assert agent.processor == mock_processor
    assert agent.device in ["cuda", "cpu"]
    assert agent.model_name == "mistralai/Mistral-7B-Instruct-v0.2"
    assert agent.temperature == 0.1

@pytest.mark.skipif(not torch_available, reason="Torch not available")
def test_query_execution(mock_processor, mock_model_and_tokenizer):
    """Test the full query execution flow."""
    # Setup
    mock_model, mock_tokenizer = mock_model_and_tokenizer
    
    # Create a query agent with mocked components
    with patch.object(RAGKGQueryAgent, '_extract_entities_from_query') as mock_extract:
        with patch.object(RAGKGQueryAgent, '_synthesize_answer') as mock_synthesize:
            # Configure mocks
            mock_extract.return_value = {"retention_period": "3 years"}
            mock_synthesize.return_value = "The retention period is 3 years."
            
            # Create the agent and execute query
            agent = RAGKGQueryAgent(processor=mock_processor)
            result = agent.query("What is the retention period?")
            
            # Verify
            assert result["success"] is True
            assert result["answer"] == "The retention period is 3 years."
            assert "vector_results" in result
            assert "knowledge_graph_results" in result
            assert result["extracted_entities"] == {"retention_period": "3 years"}
            
            # Verify method calls
            mock_processor.search.assert_called_once()
            mock_extract.assert_called_once_with("What is the retention period?")
            mock_processor.knowledge_store.query_entities.assert_called()
            mock_synthesize.assert_called_once()

@pytest.mark.skipif(not torch_available, reason="Torch not available")
def test_entity_extraction_from_query(mock_processor, mock_model_and_tokenizer):
    """Test entity extraction from query."""
    # Setup
    mock_model, mock_tokenizer = mock_model_and_tokenizer
    
    # Create a query agent with mocked text generation
    with patch.object(RAGKGQueryAgent, '_generate_text') as mock_generate:
        # Configure the mock to return a JSON response
        mock_generate.return_value = '{"record_series_number": null, "retention_period": "3 years", "disposition_action": null, "legal_authority": null}'
        
        # Create the agent and extract entities
        agent = RAGKGQueryAgent(processor=mock_processor)
        entities = agent._extract_entities_from_query("What is the retention period for 3 years?")
        
        # Verify
        assert entities == {"retention_period": "3 years"}
        mock_generate.assert_called_once()

@pytest.mark.skipif(not torch_available, reason="Torch not available")
def test_error_handling(mock_processor):
    """Test handling of errors during query execution."""
    # Setup
    mock_processor.search.side_effect = ProcessingError("Search failed")
    
    # Create agent with mocks for components that shouldn't be called
    agent = RAGKGQueryAgent(processor=mock_processor)
    
    # Execute
    result = agent.query("Test query")
    
    # Verify
    assert result["success"] is False
    assert "error" in result
    assert "Search failed" in result["error"] 