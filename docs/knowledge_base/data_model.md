# Knowledge Base Data Model

## Overview

The Knowledge Base uses a hybrid data model combining document storage, vector embeddings, and a knowledge graph structure. This document details the complete data model and explains how different components interact.

## Document Model

### Core Document
```typescript
interface Document {
    id: string;
    content: string;
    metadata: {
        title: string;
        source: string;
        category: string;
        created_at: timestamp;
        modified_at: timestamp;
        file_path: string;
        file_type: string;
        processing_status: string;
    };
}
```

### Document Chunk
```typescript
interface DocumentChunk {
    id: string;
    document_id: string;
    content: string;
    embedding: Float32Array; // 768-dimensional vector
    chunk_index: number;
    metadata: {
        start_char: number;
        end_char: number;
        section: string;
    };
}
```

## Knowledge Graph Model

### Entity
```typescript
interface Entity {
    id: string;
    type: EntityType;
    value: string;
    document_id: string;
    metadata: {
        confidence: number;
        extracted_at: timestamp;
        context: string;
        normalized_value?: string;
    };
}

enum EntityType {
    RECORD_SERIES = 'record_series',
    TITLE = 'title',
    RETENTION_PERIOD = 'retention_period',
    DISPOSITION_ACTION = 'disposition_action',
    LEGAL_AUTHORITY = 'legal_authority',
    ORGANIZATION = 'organization',
    DATE = 'date',
    REQUIREMENT = 'requirement'
}
```

### Relationship
```typescript
interface Relationship {
    id: string;
    source_id: string;
    target_id: string;
    type: RelationType;
    metadata: {
        confidence: number;
        extracted_at: timestamp;
        context: string;
        attributes: Record<string, any>;
    };
}

enum RelationType {
    HAS_RETENTION = 'has_retention',
    HAS_DISPOSITION = 'has_disposition',
    SUPERSEDES = 'supersedes',
    REFERENCES = 'references',
    RELATED_TO = 'related_to',
    REQUIRES = 'requires',
    MANAGES = 'manages'
}
```

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending'
);

CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX idx_documents_status ON documents (processing_status);
```

### Chunks Table
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_document ON chunks (document_id);
```

### Entities Table
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_entities_type_value ON entities (type, value);
CREATE INDEX idx_entities_document ON entities (document_id);
CREATE INDEX idx_entities_metadata ON entities USING GIN (metadata);
```

### Relationships Table
```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    target_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_relationships_source ON relationships (source_id);
CREATE INDEX idx_relationships_target ON relationships (target_id);
CREATE INDEX idx_relationships_type ON relationships (type);
```

## Example Data

### Document Example
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "...",
    "metadata": {
        "title": "Personnel Records Retention Schedule",
        "source": "Utah State Archives",
        "category": "personnel",
        "file_path": "/data/grs/personnel/GRS-1234.pdf",
        "file_type": "pdf",
        "processing_status": "completed"
    }
}
```

### Entity Examples
```json
[
    {
        "id": "987fcdeb-51a2-3456-789a-bcdef0123456",
        "type": "record_series",
        "value": "GRS-1234",
        "document_id": "123e4567-e89b-12d3-a456-426614174000",
        "metadata": {
            "confidence": 0.98,
            "context": "Personnel Records (GRS-1234)"
        }
    },
    {
        "id": "456abcde-f123-4567-89ab-cdef01234567",
        "type": "retention_period",
        "value": "7 years",
        "document_id": "123e4567-e89b-12d3-a456-426614174000",
        "metadata": {
            "confidence": 0.95,
            "normalized_value": "P7Y"
        }
    }
]
```

### Relationship Example
```json
{
    "id": "789bcdef-0123-4567-89ab-cdef01234567",
    "source_id": "987fcdeb-51a2-3456-789a-bcdef0123456",
    "target_id": "456abcde-f123-4567-89ab-cdef01234567",
    "type": "has_retention",
    "metadata": {
        "confidence": 0.92,
        "context": "Personnel Records (GRS-1234) must be retained for 7 years"
    }
}
```

## Query Examples

### Find Documents by Entity
```sql
SELECT d.*
FROM documents d
JOIN entities e ON d.id = e.document_id
WHERE e.type = 'record_series'
AND e.value = 'GRS-1234';
```

### Get Entity Relationships
```sql
SELECT e2.*, r.type as relationship_type
FROM entities e1
JOIN relationships r ON e1.id = r.source_id
JOIN entities e2 ON r.target_id = e2.id
WHERE e1.type = 'record_series'
AND e1.value = 'GRS-1234';
```

### Semantic Search with Entity Filter
```sql
SELECT d.*, (c.embedding <=> :query_embedding) as distance
FROM documents d
JOIN chunks c ON d.id = c.document_id
JOIN entities e ON d.id = e.document_id
WHERE e.type = 'retention_period'
AND e.value LIKE '%7 years%'
ORDER BY distance
LIMIT 5;
```

## See Also

- [Architecture Overview](architecture.md)
- [Query Patterns](query_patterns.md)
- [Database Setup](../guides/database_setup.md) 