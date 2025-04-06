"""
Custom exceptions for the Knowledge Base Agent.
"""

class KnowledgeBaseError(Exception):
    """Base exception for all knowledge base errors."""
    pass

class ConfigurationError(KnowledgeBaseError):
    """Error in configuration."""
    pass

class StorageError(KnowledgeBaseError):
    """Error in storage operations."""
    pass

class DocumentStoreError(StorageError):
    """Error in document store operations."""
    pass

class VectorStoreError(StorageError):
    """Error in vector store operations."""
    pass

class KnowledgeStoreError(StorageError):
    """Error in knowledge store operations."""
    pass

class EmbeddingError(KnowledgeBaseError):
    """Error in embedding operations."""
    pass

class ProcessingError(KnowledgeBaseError):
    """Error in document processing."""
    pass

class EntityExtractionError(ProcessingError):
    """Error in entity extraction."""
    pass

class APIError(KnowledgeBaseError):
    """Error in API operations."""
    pass

class ValidationError(KnowledgeBaseError):
    """Error in data validation."""
    pass 