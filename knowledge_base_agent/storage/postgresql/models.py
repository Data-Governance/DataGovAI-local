"""
SQLAlchemy models for PostgreSQL storage.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

# Import pgvector's vector type for embeddings
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for development/testing without pgvector installed
    from sqlalchemy import LargeBinary as Vector 

from .base import Base

class DocumentModel(Base):
    """SQLAlchemy model for documents."""
    __tablename__ = 'documents'
    
    # Primary key and identifying fields
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=True)
    title = Column(String, nullable=True)
    source = Column(String, nullable=True)
    
    # Document content and metadata
    content = Column(Text, nullable=True)
    extra_data = Column(JSONB, nullable=True)
    
    # Document chunks as JSONB array
    chunks = Column(JSONB, nullable=True)
    
    # Status and tracking fields
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chunk_embeddings = relationship("ChunkEmbeddingModel", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("EntityModel", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'title': self.title,
            'source': self.source,
            'content': self.content,
            'metadata': self.extra_data,
            'chunks': self.chunks,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ChunkEmbeddingModel(Base):
    """SQLAlchemy model for chunk embeddings."""
    __tablename__ = 'chunk_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey('documents.id', ondelete='CASCADE'))
    chunk_idx = Column(Integer)
    # Use the Vector type from pgvector
    embedding = Column(Vector(1536))  # Dimension depends on the embedding model
    
    # Relationship back to parent document
    document = relationship("DocumentModel", back_populates="chunk_embeddings")
    
    # Add index for faster vector similarity search using pgvector
    __table_args__ = (
        Index('idx_chunk_embedding_vector', embedding, postgresql_using='ivfflat', postgresql_with={'lists': 100}),
    )


class EntityModel(Base):
    """SQLAlchemy model for entities."""
    __tablename__ = 'entities'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    document_id = Column(String, ForeignKey('documents.id', ondelete='CASCADE'))
    extra_data = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    document = relationship("DocumentModel", back_populates="entities")
    source_relationships = relationship("RelationshipModel", 
                                       foreign_keys="RelationshipModel.source_id",
                                       back_populates="source_entity",
                                       cascade="all, delete-orphan")
    target_relationships = relationship("RelationshipModel", 
                                       foreign_keys="RelationshipModel.target_id",
                                       back_populates="target_entity",
                                       cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'entity_type': self.entity_type,
            'document_id': self.document_id,
            'metadata': self.extra_data,
            'description': self.description,
        }


class RelationshipModel(Base):
    """SQLAlchemy model for relationships between entities."""
    __tablename__ = 'relationships'
    
    id = Column(String, primary_key=True)
    source_id = Column(String, ForeignKey('entities.id', ondelete='CASCADE'))
    target_id = Column(String, ForeignKey('entities.id', ondelete='CASCADE'))
    relation_type = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    extra_data = Column(JSONB, nullable=True)
    
    # Relationships
    source_entity = relationship("EntityModel", foreign_keys=[source_id], back_populates="source_relationships")
    target_entity = relationship("EntityModel", foreign_keys=[target_id], back_populates="target_relationships")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type,
            'confidence': self.confidence,
            'metadata': self.extra_data,
        } 