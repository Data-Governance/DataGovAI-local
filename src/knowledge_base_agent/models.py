"""
Data models for the Knowledge Base Agent.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    max_chunk_size: int = 1000
    min_chunk_size: int = 100
    overlap_size: int = 50
    extract_entities: bool = True
    extract_relationships: bool = True
    max_retries: int = 3
    retry_delay: int = 1
    cache_size: int = 1000

@dataclass
class Document:
    """Document model."""
    id: str
    content: str
    chunks: List[str]
    title: str = ""
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Entity:
    """Entity model."""
    id: str
    name: str
    type: str
    metadata: Dict = field(default_factory=dict)

@dataclass
class Relationship:
    """Relationship between entities."""
    source_id: str
    target_id: str
    type: str
    metadata: Dict = field(default_factory=dict)

@dataclass
class SearchResult:
    """Search result model."""
    content: str
    score: float
    metadata: Dict = field(default_factory=dict)
    source_id: Optional[str] = None
    chunk_index: Optional[int] = None

@dataclass
class SearchQuery:
    """Search query model."""
    text: str
    filters: Dict = field(default_factory=dict)
    limit: int = 5
    min_score: float = 0.0

@dataclass
class ProcessingStatus:
    """Document processing status."""
    doc_id: str
    status: str
    progress: float = 0.0
    error: Optional[str] = None
    completed_at: Optional[datetime] = None 