"""
Tests for the Pydantic data models.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
import uuid

from knowledge_base_agent.models import (
    Document,
    Entity,
    Relationship,
    SearchQuery,
    SearchResult,
    ProcessingStatus
)

def test_entity_creation():
    """Test creating an Entity instance."""
    now = datetime.utcnow()
    entity = Entity(
        type="PERSON",
        name="John Doe",
        document_id="doc123",
        metadata={"source": "test"},
        start_pos=0,
        end_pos=8,
        confidence=0.95,
        created_at=now
    )
    assert isinstance(entity.id, str)
    assert entity.type == "PERSON"
    assert entity.name == "John Doe"
    assert entity.document_id == "doc123"
    assert entity.metadata == {"source": "test"}
    assert entity.start_pos == 0
    assert entity.end_pos == 8
    assert entity.confidence == 0.95
    assert entity.created_at == now
    # Check default ID generation
    entity_default_id = Entity(type="ORG", name="ACME", document_id="doc456")
    assert isinstance(uuid.UUID(entity_default_id.id), uuid.UUID)

def test_relationship_creation():
    """Test creating a Relationship instance."""
    now = datetime.utcnow()
    rel = Relationship(
        from_entity_id="e1",
        to_entity_id="e2",
        type="WORKS_FOR",
        document_id="doc123",
        metadata={"verified": True},
        confidence=0.8,
        created_at=now
    )
    assert isinstance(rel.id, str)
    assert rel.from_entity_id == "e1"
    assert rel.to_entity_id == "e2"
    assert rel.type == "WORKS_FOR"
    assert rel.document_id == "doc123"
    assert rel.metadata == {"verified": True}
    assert rel.confidence == 0.8
    assert rel.created_at == now

def test_document_creation():
    """Test creating a Document instance."""
    now = datetime.utcnow()
    doc = Document(
        title="Test Doc",
        content="Some text content.",
        chunks=["Some text", " content."],
        source="test_source",
        created_at=now,
        updated_at=now,
        metadata={"language": "en"}
    )
    assert isinstance(doc.id, str)
    assert doc.title == "Test Doc"
    assert doc.content == "Some text content."
    assert doc.chunks == ["Some text", " content."]
    assert doc.source == "test_source"
    assert doc.created_at == now
    assert doc.updated_at == now
    assert doc.metadata == {"language": "en"}
    assert doc.entities == [] # Default empty list
    assert doc.relationships == [] # Default empty list

def test_search_query_creation():
    """Test creating a SearchQuery instance."""
    sq = SearchQuery(
        query="test query",
        search_type="vector",
        top_k=10,
        min_score=0.5,
        use_graph=False,
        filter={"metadata_field": "value"}
    )
    assert sq.query == "test query"
    assert sq.search_type == "vector"
    assert sq.top_k == 10
    assert sq.min_score == 0.5
    assert sq.use_graph is False
    assert sq.filter == {"metadata_field": "value"}

def test_search_result_creation():
    """Test creating a SearchResult instance."""
    sr = SearchResult(
        document_id="doc789",
        content="Relevant text chunk.",
        score=0.99,
        metadata={"chunk_source": "p1"}
    )
    assert sr.document_id == "doc789"
    assert sr.content == "Relevant text chunk."
    assert sr.score == 0.99
    assert sr.metadata == {"chunk_source": "p1"}
    assert sr.entities == []
    assert sr.relationships == []

def test_processing_status_creation():
    """Test creating a ProcessingStatus instance."""
    now = datetime.utcnow()
    ps = ProcessingStatus(
        document_id="doc_proc_1",
        status="COMPLETED",
        processed_at=now,
        metadata={"steps": 5}
    )
    assert ps.document_id == "doc_proc_1"
    assert ps.status == "COMPLETED"
    assert ps.processed_at == now
    assert ps.error is None
    assert ps.metadata == {"steps": 5}

    ps_failed = ProcessingStatus(
        document_id="doc_proc_2",
        status="FAILED",
        error="Something went wrong"
    )
    assert ps_failed.status == "FAILED"
    assert ps_failed.error == "Something went wrong"
    assert ps_failed.processed_at is None

# Example validation test (optional)
def test_entity_missing_required_field():
    """Test that creating an Entity fails if required fields are missing."""
    with pytest.raises(ValidationError):
        Entity(name="Just a name") # Missing type and document_id 