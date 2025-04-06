"""
Generic AI Agent - A versatile document processing and analysis system
"""

__version__ = "0.1.0"

from .processor import DocumentProcessor
from .models import Document, Entity, Relationship
from .extractors import BaseExtractor, ContentExtractor, MetadataExtractor, KnowledgeExtractor
from .storage import VectorStore, DocumentStore, KnowledgeStore
from .embeddings import EmbeddingGenerator

__all__ = [
    "DocumentProcessor",
    "Document",
    "Entity",
    "Relationship",
    "BaseExtractor",
    "ContentExtractor",
    "MetadataExtractor",
    "KnowledgeExtractor",
    "VectorStore",
    "DocumentStore",
    "KnowledgeStore",
    "EmbeddingGenerator",
]
