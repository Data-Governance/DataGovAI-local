# 📊 Data Model Documentation

## Overview

The DataGovAI system uses a hybrid data model combining document storage, vector embeddings, and graph relationships. This design enables both semantic search capabilities and structured querying of retention schedules.

## Document Model

### Core Document Structure

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| document_id | string | Unique GRS identifier | "GRS-2024-FIN-001" |
| title | string | Document title | "Financial Audit Records" |
| category | string | Primary classification | "Financial Records" |
| subcategory | string | Specific type | "Audit Documentation" |
| content | text | Full document text | Full content of the document |
| metadata | jsonb | Additional metadata | See Metadata Structure |

### Metadata Structure

```json
{
    "retention": {
        "period": "7 years",
        "basis": "fiscal_year_end",
        "exceptions": [
            {
                "condition": "litigation_hold",
                "period": "indefinite",
                "authority": "Legal Counsel"
            }
        ],
        "authority": "Utah Code § 63G-2-604"
    },
    "disposition": {
        "action": "destroy",
        "method": "secure_shredding",
        "requirements": [
            "records_officer_approval",
            "audit_completion"
        ]
    },
    "classification": {
        "primary": "public",
        "restrictions": [
            {
                "type": "private",
                "fields": ["personnel_data", "financial_details"],
                "authority": "GRAMA § 63G-2-302"
            }
        ]
    },
    "administrative": {
        "created_date": "2024-01-15",
        "last_modified": "2024-04-06",
        "review_date": "2025-01-15",
        "version": "2.0",
        "supersedes": "GRS-2023-FIN-001"
    }
}
```

## Database Schema

### 1. Documents Table

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_document_id CHECK (document_id ~ '^GRS-\d{4}-[A-Z]{3}-\d{3}$')
);

CREATE INDEX idx_documents_category ON documents(category);
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
```

### 2. Chunks Table

```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB,
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_chunk_index CHECK (chunk_index >= 0)
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_embedding USING ivfflat (embedding vector_cosine_ops);
```

### 3. Entities Table

```sql
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    context TEXT,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_document_id ON entities(document_id);
```

### 4. Relationships Table

```sql
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES entities(id),
    target_id INTEGER REFERENCES entities(id),
    type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_relationship CHECK (source_id != target_id)
);

CREATE INDEX idx_relationships_source ON relationships(source_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
CREATE INDEX idx_relationships_type ON relationships(type);
```

### 5. Audit Log Table

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_document ON audit_log(document_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
```

## Entity Types

| Type | Description | Examples |
|------|-------------|----------|
| retention_period | Time period for retention | "7 years", "permanent" |
| disposition_action | Final disposition method | "destroy", "transfer" |
| legal_authority | Legal basis for retention | "UCA § 63G-2-604" |
| organization | Organizational entity | "Finance Department" |
| record_series | Record series reference | "GRS-2024-FIN-001" |
| date | Important dates | "fiscal_year_end" |
| requirement | Processing requirements | "secure_shredding" |

## Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| supersedes | Newer version replaces older | A → B (A supersedes B) |
| references | Document references another | A → B (A references B) |
| requires | Dependency relationship | A → B (A requires B) |
| related_to | General relationship | A ↔ B (bidirectional) |

## Data Validation

### Document ID Format
- Pattern: `GRS-YYYY-CAT-NNN`
- Example: `GRS-2024-FIN-001`
- Validation regex: `^GRS-\d{4}-[A-Z]{3}-\d{3}$`

### Category Validation

```sql
CREATE TYPE document_category AS ENUM (
    'financial',
    'administrative',
    'public_services',
    'personnel',
    'education',
    'legal',
    'records_management',
    'property',
    'health'
);
```

### Retention Period Format

```sql
CREATE DOMAIN retention_period AS VARCHAR(50)
CHECK (
    VALUE ~ '^(\d+\s+(years?|months?|days?)|permanent)$'
    OR VALUE ~ '^until\s+[a-z_]+(\s+plus\s+\d+\s+(years?|months?|days?))?$'
);
```

## Query Examples

### 1. Find Documents by Category with Recent Changes

```sql
SELECT 
    document_id,
    title,
    metadata->>'retention_period' as retention,
    updated_at
FROM documents
WHERE 
    category = 'financial'
    AND updated_at > NOW() - INTERVAL '30 days'
ORDER BY updated_at DESC;
```

### 2. Get Related Documents with Relationship Context

```sql
SELECT 
    d2.document_id,
    d2.title,
    r.type as relationship_type,
    r.metadata->>'context' as context
FROM documents d1
JOIN relationships r ON d1.id = r.source_id
JOIN documents d2 ON r.target_id = d2.id
WHERE d1.document_id = 'GRS-2024-FIN-001';
```

### 3. Find Documents by Retention Period

```sql
SELECT 
    document_id,
    title,
    metadata->'retention'->>'period' as retention_period
FROM documents
WHERE 
    metadata->'retention'->>'period' ~ '7 years'
    AND category = 'financial';
```

## Best Practices

1. **Data Integrity**
   - Always use transactions for related operations
   - Maintain referential integrity
   - Validate data before insertion

2. **Performance**
   - Use appropriate indexes
   - Partition large tables by category
   - Regular VACUUM and maintenance

3. **Security**
   - Implement row-level security
   - Audit sensitive operations
   - Regular permission reviews

4. **Maintenance**
   - Regular backup schedule
   - Periodic data validation
   - Index optimization

For implementation details, see:
- [Processing Pipeline](./processing.md)
- [Query System](./querying.md) 