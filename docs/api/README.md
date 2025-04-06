# 🔌 API Documentation

<p align="center">
  <img src="../../logo.png" alt="DataGovAI Logo" width="150"/>
</p>

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
   - `