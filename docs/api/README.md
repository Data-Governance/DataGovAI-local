# 🔌 API Documentation

## Overview

The DataGovAI API provides programmatic access to the GRS Knowledge Base system. It includes REST endpoints, a Python client library, and a CLI tool for interacting with the system.

## API Versions

| Version | Status | Release Date | End of Life |
|---------|--------|--------------|-------------|
| v1.0.0  | Stable | 2024-04-01  | 2025-04-01 |
| v0.9.0  | Beta   | 2024-03-01  | 2024-06-01 |

## Authentication

### API Keys
```python
DATAGOVAI_API_KEY="your-api-key-here"
```

### Authentication Methods
1. **Bearer Token**
   ```http
   Authorization: Bearer <api-key>
   ```

2. **Query Parameter**
   ```
   GET /api/v1/documents?api_key=<api-key>
   ```

3. **Environment Variable**
   ```bash
   export DATAGOVAI_API_KEY="your-api-key-here"
   ```

## REST API

### Base URL
```
https://api.datagovai.utah.gov/v1
```

### Endpoints

#### Documents

1. **List Documents**
   ```http
   GET /documents
   ```
   Parameters:
   - `category` (string): Filter by category
   - `page` (int): Page number
   - `per_page` (int): Items per page
   - `sort` (string): Sort field
   - `order` (string): Sort order (asc/desc)

2. **Get Document**
   ```http
   GET /documents/{document_id}
   ```
   Parameters:
   - `include_chunks` (bool): Include document chunks
   - `include_entities` (bool): Include extracted entities

3. **Create Document**
   ```http
   POST /documents
   ```
   Request Body:
   ```json
   {
       "title": "Financial Records Retention",
       "content": "...",
       "metadata": {
           "category": "financial",
           "retention_period": "7 years"
       }
   }
   ```

4. **Update Document**
   ```http
   PUT /documents/{document_id}
   ```
   Request Body:
   ```json
   {
       "metadata": {
           "retention_period": "10 years"
       }
   }
   ```

5. **Delete Document**
   ```http
   DELETE /documents/{document_id}
   ```

#### Search

1. **Semantic Search**
   ```http
   POST /search/semantic
   ```
   Request Body:
   ```json
   {
       "query": "What is the retention period for financial records?",
       "filters": {
           "category": "financial"
       },
       "top_k": 5
   }
   ```

2. **Structured Search**
   ```http
   POST /search/structured
   ```
   Request Body:
   ```json
   {
       "conditions": {
           "metadata.retention.period": "7 years",
           "category": "financial"
       },
       "sort": [
           {"field": "created_at", "order": "desc"}
       ]
   }
   ```

3. **Graph Search**
   ```http
   POST /search/graph
   ```
   Request Body:
   ```json
   {
       "start_node": "GRS-2024-FIN-001",
       "pattern": {
           "relationship": "supersedes",
           "direction": "outgoing",
           "depth": 3
       }
   }
   ```

#### Knowledge Graph

1. **List Entities**
   ```http
   GET /entities
   ```
   Parameters:
   - `type` (string): Entity type
   - `document_id` (string): Filter by document
   - `page` (int): Page number
   - `per_page` (int): Items per page

2. **Get Entity**
   ```http
   GET /entities/{entity_id}
   ```
   Parameters:
   - `include_relationships` (bool): Include related entities

3. **Create Entity**
   ```http
   POST /entities
   ```
   Request Body:
   ```json
   {
       "type": "retention_period",
       "value": "7 years",
       "document_id": "GRS-2024-FIN-001",
       "metadata": {
           "confidence": 0.95
       }
   }
   ```

4. **List Relationships**
   ```http
   GET /relationships
   ```
   Parameters:
   - `type` (string): Relationship type
   - `source_id` (string): Source entity ID
   - `target_id` (string): Target entity ID

## Python Client

### Installation
```bash
pip install datagovai-client
```

### Usage

1. **Client Setup**
   ```python
   from datagovai import Client
   
   client = Client(api_key="your-api-key-here")
   ```

2. **Document Operations**
   ```python
   # List documents
   documents = await client.documents.list(
       category="financial",
       page=1,
       per_page=10
   )
   
   # Get document
   document = await client.documents.get(
       "GRS-2024-FIN-001",
       include_chunks=True
   )
   
   # Create document
   new_doc = await client.documents.create(
       title="New Financial Policy",
       content="...",
       metadata={"category": "financial"}
   )
   ```

3. **Search Operations**
   ```python
   # Semantic search
   results = await client.search.semantic(
       query="retention period for audits",
       filters={"category": "financial"},
       top_k=5
   )
   
   # Graph search
   related = await client.search.graph(
       start_node="GRS-2024-FIN-001",
       pattern={
           "relationship": "supersedes",
           "depth": 2
       }
   )
   ```

4. **Knowledge Graph Operations**
   ```python
   # List entities
   entities = await client.entities.list(
       type="retention_period",
       document_id="GRS-2024-FIN-001"
   )
   
   # Create relationship
   relationship = await client.relationships.create(
       source_id="entity1",
       target_id="entity2",
       type="supersedes"
   )
   ```

## CLI Tool

### Installation
```bash
pip install datagovai-cli
```

### Configuration
```bash
datagovai config set api_key "your-api-key-here"
```

### Commands

1. **Document Management**
   ```bash
   # List documents
   datagovai docs list --category financial
   
   # Get document details
   datagovai docs get GRS-2024-FIN-001
   
   # Upload document
   datagovai docs upload path/to/document.pdf
   
   # Delete document
   datagovai docs delete GRS-2024-FIN-001
   ```

2. **Search**
   ```bash
   # Semantic search
   datagovai search "retention period for financial records"
   
   # Structured search
   datagovai search --filter "category=financial" \
                    --filter "retention_period=7 years"
   
   # Graph search
   datagovai graph search GRS-2024-FIN-001 \
                         --relationship supersedes \
                         --depth 3
   ```

3. **Knowledge Graph**
   ```bash
   # List entities
   datagovai entities list --type retention_period
   
   # Get entity details
   datagovai entities get entity-id
   
   # List relationships
   datagovai relationships list --type supersedes
   ```

## Response Formats

### Success Response
```json
{
    "status": "success",
    "data": {
        "id": "GRS-2024-FIN-001",
        "title": "Financial Records Retention",
        "metadata": {
            "category": "financial",
            "retention_period": "7 years"
        }
    }
}
```

### Error Response
```json
{
    "status": "error",
    "error": {
        "code": "invalid_request",
        "message": "Invalid document ID format",
        "details": {
            "field": "document_id",
            "pattern": "^GRS-\\d{4}-[A-Z]{3}-\\d{3}$"
        }
    }
}
```

## Rate Limiting

| Plan      | Requests/Min | Burst | Monthly Limit |
|-----------|-------------|-------|---------------|
| Basic     | 60          | 100   | 100,000      |
| Premium   | 300         | 500   | 1,000,000    |
| Enterprise| Unlimited   | -     | Unlimited    |

Headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1682512345
```

## Webhooks

### Configuration
```http
POST /webhooks
```
Request Body:
```json
{
    "url": "https://your-server.com/webhook",
    "events": ["document.created", "document.updated"],
    "secret": "your-webhook-secret"
}
```

### Event Types
1. Document Events
   - `document.created`
   - `document.updated`
   - `document.deleted`

2. Entity Events
   - `entity.created`
   - `entity.updated`
   - `entity.deleted`

3. Processing Events
   - `processing.started`
   - `processing.completed`
   - `processing.failed`

### Event Payload
```json
{
    "event": "document.created",
    "timestamp": "2024-04-06T12:34:56Z",
    "data": {
        "document_id": "GRS-2024-FIN-001",
        "title": "Financial Records",
        "category": "financial"
    }
}
```

## See Also
- [Getting Started](../guides/getting_started.md)
- [Data Model](../knowledge_base/data_model.md)
- [Query System](../knowledge_base/querying.md)