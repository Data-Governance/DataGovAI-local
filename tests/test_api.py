"""
Tests for the API endpoints.
"""

import pytest
from unittest.mock import Mock, patch, ANY
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException # Import for checking error details

# Assuming models are correctly defined
from knowledge_base_agent.models import Document, SearchResult, Entity # Import models used in responses/mocks
from knowledge_base_agent.processor import DocumentProcessor # Import Processor for type hinting
from knowledge_base_agent.exceptions import ProcessingError, StorageError

# Need to create the app for TestClient
# We assume __main__.create_app exists or create a minimal one here for testing
# Let's try importing create_app from the actual location if possible
try:
    from knowledge_base_agent.api import create_app # Assuming api.py or api/__init__.py has create_app
except ImportError:
    # Fallback or raise error if create_app isn't found
    pytest.skip("Could not import create_app, skipping API tests.", allow_module_level=True)


@pytest.fixture
def mock_processor() -> DocumentProcessor: # Add type hint
    """Create a mock processor."""
    processor = Mock(spec=DocumentProcessor) # Use spec for better mocking
    # Add mock document_store if it's accessed directly in routes (e.g., GET /documents/{id})
    processor.document_store = Mock() 
    return processor

@pytest.fixture
def client(mock_processor):
    """Create a test client for the FastAPI application."""
    # Pass the mock processor to the app factory
    app = create_app(mock_processor) 
    return TestClient(app)

def test_process_document_success(client: TestClient, mock_processor: Mock): # Add type hints
    """Test successful document processing."""
    # Mock processor response
    expected_doc_id = "test-doc-id-123"
    mock_processor.process_document.return_value = expected_doc_id
    
    request_data = {
        "content": "Test content for processing.",
        "metadata": {
            "title": "API Test Doc",
            "source": "pytest-api"
        }
    }
    
    # Send request
    response = client.post("/documents", json=request_data) # Use /documents route
    
    # Verify response
    assert response.status_code == 200
    # The endpoint returns the doc_id directly as a string
    assert response.json() == expected_doc_id 
    
    # Verify processor call
    mock_processor.process_document.assert_called_once_with(
        content=request_data["content"],
        metadata=request_data["metadata"]
    )

def test_process_document_error(client: TestClient, mock_processor: Mock):
    """Test document processing with error."""
    # Mock processor error
    error_message = "Processing failed spectacularly"
    mock_processor.process_document.side_effect = ProcessingError(error_message)
    
    request_data = {"content": "Content that causes error", "metadata": {}}
    
    # Send request
    response = client.post("/documents", json=request_data)
    
    # Verify response (FastAPI routes raise HTTPException)
    assert response.status_code == 500
    assert response.json() == {"detail": error_message} # Check detail field

def test_search_success(client: TestClient, mock_processor: Mock):
    """Test successful search returns list of SearchResult."""
    # Mock search results (chunk-level)
    mock_results = [
        SearchResult(
            document_id="doc1", 
            content="Relevant text chunk one.", 
            score=0.95, 
            metadata={"source": "doc1_meta"}
        ),
        SearchResult(
            document_id="doc2", 
            content="Relevant text chunk two.", 
            score=0.88, 
            metadata={"source": "doc2_meta"}
        )
    ]
    mock_processor.search.return_value = mock_results
    
    # Send request
    query = "test search query"
    top_k = 5
    min_score = 0.1
    use_graph = False
    response = client.get(f"/search?query={query}&top_k={top_k}&min_score={min_score}&use_graph={use_graph}")
    
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) == len(mock_results)
    # Check structure of the first result against the SearchResult model
    assert response_data[0]["document_id"] == mock_results[0].document_id
    assert response_data[0]["content"] == mock_results[0].content
    assert response_data[0]["score"] == mock_results[0].score
    assert response_data[0]["metadata"] == mock_results[0].metadata
    
    # Verify processor call
    mock_processor.search.assert_called_once_with(
        query=query,
        top_k=top_k,
        min_score=min_score,
        use_graph=use_graph
    )

def test_search_error(client: TestClient, mock_processor: Mock):
    """Test search with error."""
    # Mock processor error
    error_message = "Search index corrupted"
    mock_processor.search.side_effect = StorageError(error_message)
    
    # Send request
    response = client.get("/search?query=error_query")
    
    # Verify response
    assert response.status_code == 500
    assert response.json() == {"detail": error_message}

def test_get_document_success(client: TestClient, mock_processor: Mock):
    """Test successful document retrieval."""
    # Mock document (should match the Document Pydantic model)
    doc_id = "test-doc-retrieval-id"
    mock_doc = Document(
        id=doc_id,
        title="Retrieved Doc",
        content="Retrieved content.",
        chunks=["Retrieved content."], # Example chunks
        source="retrieval_test",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={"key": "value"}
    )
    # Mock the document_store's get_document method on the processor mock
    mock_processor.document_store.get_document.return_value = mock_doc
    
    # Send request
    response = client.get(f"/documents/{doc_id}")
    
    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    # Assert against the structure of the Document model
    assert response_data["id"] == mock_doc.id
    assert response_data["title"] == mock_doc.title
    assert response_data["content"] == mock_doc.content
    assert response_data["chunks"] == mock_doc.chunks
    assert response_data["source"] == mock_doc.source
    assert response_data["metadata"] == mock_doc.metadata
    # Check datetime serialization (FastAPI handles this)
    assert "created_at" in response_data
    
    # Verify processor.document_store call
    mock_processor.document_store.get_document.assert_called_once_with(doc_id)

def test_get_document_not_found(client: TestClient, mock_processor: Mock):
    """Test retrieving a document that is not found."""
    doc_id = "non-existent-doc-id"
    # Mock document_store to return None
    mock_processor.document_store.get_document.return_value = None
    
    # Send request
    response = client.get(f"/documents/{doc_id}")
    
    # Verify response (expect 404 based on route logic)
    assert response.status_code == 404
    assert response.json() == {"detail": f"Document with ID {doc_id} not found"}
    
    # Verify processor.document_store call
    mock_processor.document_store.get_document.assert_called_once_with(doc_id)

def test_get_entity_context_success(client: TestClient, mock_processor: Mock):
    """Test successful entity context retrieval."""
    entity_id = "test-entity-id-ctx"
    # Mock context data (simple dict, as route doesn't specify response_model)
    mock_context_data = {
        "entities": [("e1", "Alice", "PERSON"), ("e2", "Acme", "ORG")], 
        "relationships": [{"from": "e1", "to": "e2", "type": "WORKS_AT"}]
    }
    mock_processor.get_entity_context.return_value = mock_context_data
    max_depth=3
    
    # Send request
    response = client.get(f"/entities/{entity_id}/context?max_depth={max_depth}")
    
    # Verify response
    assert response.status_code == 200
    # Endpoint returns the context dict directly
    assert response.json() == mock_context_data 
    
    # Verify processor call
    mock_processor.get_entity_context.assert_called_once_with(
        entity_id,
        max_depth=max_depth
    )

def test_get_entity_context_error(client: TestClient, mock_processor: Mock):
    """Test entity context retrieval with error."""
    entity_id = "error-entity-id"
    # Mock processor error
    error_message = "Knowledge graph query failed"
    mock_processor.get_entity_context.side_effect = StorageError(error_message)
    
    # Send request
    response = client.get(f"/entities/{entity_id}/context")
    
    # Verify response
    assert response.status_code == 500 # Assuming route raises 500 for StorageError
    assert response.json() == {"detail": error_message}

def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 