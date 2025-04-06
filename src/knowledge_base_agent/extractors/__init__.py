"""
Base extractor classes for the Generic AI Agent package.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from ..models import Document, Entity, Relationship
from .entity_extractor import EntityExtractor
from .local_llm_extractor import LocalLlmExtractor

class BaseExtractor(ABC):
    """Base class for all extractors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def extract(self, document: Document) -> Document:
        """Extract information from a document."""
        pass

class ContentExtractor(BaseExtractor):
    """Extracts and processes raw content from documents."""
    
    def extract(self, document: Document) -> Document:
        """Extract and process content from the document."""
        # Basic implementation - override for specific content processing
        if not document.content:
            raise ValueError("Document has no content")
        return document

class MetadataExtractor(BaseExtractor):
    """Extracts metadata from documents."""
    
    def extract(self, document: Document) -> Document:
        """Extract metadata from the document."""
        # Basic implementation - override for specific metadata extraction
        if not document.metadata:
            document.metadata = {}
        return document

class KnowledgeExtractor(BaseExtractor):
    """Extracts entities and relationships from documents."""
    
    def extract(self, document: Document) -> Document:
        """Extract entities and relationships from the document."""
        # Basic implementation - override for specific knowledge extraction
        document.entities = self._extract_entities(document)
        document.relationships = self._extract_relationships(document)
        return document
    
    def _extract_entities(self, document: Document) -> List[Entity]:
        """Extract entities from the document."""
        # Override this method in subclasses
        return []
    
    def _extract_relationships(self, document: Document) -> List[Relationship]:
        """Extract relationships from the document."""
        # Override this method in subclasses
        return []

__all__ = [
    "BaseExtractor",
    "ContentExtractor",
    "MetadataExtractor",
    "KnowledgeExtractor",
    'EntityExtractor',
    'LocalLlmExtractor'
] 