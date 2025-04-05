"""Tests for entity extraction functionality."""

import pytest
from knowledge_base_agent.processor import DocumentProcessor
from knowledge_base_agent.models import Entity

@pytest.fixture
def sample_grs_text():
    """Sample Utah GRS text for testing."""
    return """
    Title: Sample Record Series (RS-123)
    
    Description: This record series contains important documents related to state operations.
    
    Retention: Retain for 7 years after case closure.
    
    Disposition: Then destroy records.
    
    Legal Authority: UCA 63G-2-305, Utah Code 63G-2-302
    """

def test_extract_entities_rules():
    """Test rule-based entity extraction."""
    processor = DocumentProcessor()
    doc_id = "test-doc-1"
    
    entities, relationships = processor._extract_entities_rules(sample_grs_text(), doc_id)
    
    # Verify we got the expected number of entities
    assert len(entities) == 4, "Should extract 4 entities (Description, Retention, Disposition, Legal Authority)"
    assert len(relationships) == 0, "No relationships should be extracted in rule-based mode"
    
    # Verify each entity type was extracted
    entity_types = {e.type for e in entities}
    assert entity_types == {"Description", "RetentionPeriod", "DispositionAction", "LegalAuthority"}
    
    # Verify entity contents
    for entity in entities:
        assert isinstance(entity, Entity)
        assert entity.id is not None
        assert entity.metadata["source"] in ["regex", "regex_uca"]
        assert entity.metadata["confidence"] == "high"
        assert entity.metadata["document_id"] == doc_id

def test_validate_entity_value():
    """Test entity value validation."""
    processor = DocumentProcessor()
    
    # Test RetentionPeriod validation
    assert processor._validate_entity_value("Retain for 5 years", "RetentionPeriod")
    assert processor._validate_entity_value("Until superseded", "RetentionPeriod")
    assert not processor._validate_entity_value("Invalid retention", "RetentionPeriod")
    
    # Test DispositionAction validation
    assert processor._validate_entity_value("Then destroy", "DispositionAction")
    assert processor._validate_entity_value("Transfer to archives", "DispositionAction")
    assert not processor._validate_entity_value("Invalid action", "DispositionAction")
    
    # Test Description validation
    assert processor._validate_entity_value("This is a valid description", "Description")
    assert not processor._validate_entity_value("Too short", "Description")
    
    # Test LegalAuthority validation
    assert processor._validate_entity_value("UCA 63G-2-305", "LegalAuthority")
    assert processor._validate_entity_value("Utah Code 63G-2-302", "LegalAuthority")
    assert not processor._validate_entity_value("Invalid authority", "LegalAuthority")

def test_empty_and_invalid_input():
    """Test handling of empty and invalid input."""
    processor = DocumentProcessor()
    doc_id = "test-doc-2"
    
    # Test with empty input
    entities, relationships = processor._extract_entities_rules("", doc_id)
    assert len(entities) == 0
    assert len(relationships) == 0
    
    # Test with invalid input
    entities, relationships = processor._extract_entities_rules("Invalid text without any entities", doc_id)
    assert len(entities) == 0
    assert len(relationships) == 0 