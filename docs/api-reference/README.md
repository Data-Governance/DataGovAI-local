# 🌐 API Reference

This section provides comprehensive documentation for all DataGovAI APIs, including REST API endpoints, Python SDK, and CLI tools.

## 📑 API Overview

| API Type | Description | Documentation |
|----------|-------------|---------------|
| REST API | HTTP endpoints for web integration | [REST API Documentation](rest_api.md) |
| Python SDK | Native Python interface | [Python SDK Documentation](python_api.md) |
| CLI | Command-line tools | [CLI Documentation](cli.md) |

## 🔑 Authentication

All APIs require authentication using one of the following methods:
- API Key (REST API)
- Session Token (Web Interface)
- Environment Variables (CLI)

See [Authentication Guide](authentication.md) for details.

## 🚀 Quick Start

### REST API Example
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.datagovai.utah.gov/v1"

# Query the knowledge base
response = requests.post(
    f"{BASE_URL}/query",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "query": "What is the retention period for financial records?",
        "max_results": 5
    }
)

results = response.json()
```

### Python SDK Example
```python
from datagovai import KnowledgeBase

# Initialize the client
kb = KnowledgeBase(api_key="your_api_key")

# Query the knowledge base
results = kb.query(
    query="What is the retention period for financial records?",
    max_results=5
)
```

### CLI Example
```bash
# Set up authentication
export DATAGOVAI_API_KEY="your_api_key"

# Query the knowledge base
datagovai query "What is the retention period for financial records?" --max-results 5
```

## 📋 Available APIs

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Query the knowledge base |
| `/documents` | POST | Upload new documents |
| `/documents/{id}` | GET | Retrieve document details |
| `/entities` | GET | List extracted entities |
| `/relationships` | GET | List entity relationships |

### Python SDK Classes

| Class | Description |
|-------|-------------|
| `KnowledgeBase` | Main interface for KB operations |
| `Document` | Document management operations |
| `Entity` | Entity operations |
| `Relationship` | Relationship operations |

### CLI Commands

| Command | Description |
|---------|-------------|
| `query` | Query the knowledge base |
| `upload` | Upload new documents |
| `list` | List documents or entities |
| `export` | Export data or results |

## 🔧 Configuration

### REST API Configuration
```python
{
    "base_url": "https://api.datagovai.utah.gov/v1",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1
}
```

### Python SDK Configuration
```python
{
    "api_key": "your_api_key",
    "base_url": "https://api.datagovai.utah.gov/v1",
    "timeout": 30,
    "cache_enabled": true,
    "cache_ttl": 3600
}
```

### CLI Configuration
```bash
# ~/.datagovai/config.yaml
api_key: your_api_key
base_url: https://api.datagovai.utah.gov/v1
output_format: json
verbose: true
```

## 📊 Response Formats

### Query Response
```json
{
    "query": "What is the retention period for financial records?",
    "results": [
        {
            "document_id": "doc123",
            "content": "Financial records must be retained for 7 years...",
            "confidence": 0.95,
            "metadata": {
                "section": "Financial Records",
                "page": 1
            }
        }
    ],
    "entities": [
        {
            "type": "RETENTION_PERIOD",
            "value": "7 years",
            "confidence": 0.98
        }
    ]
}
```

## 🔍 Error Handling

All APIs use standard HTTP status codes and return detailed error messages:

```json
{
    "error": {
        "code": "INVALID_REQUEST",
        "message": "Invalid query parameter",
        "details": {
            "field": "max_results",
            "reason": "Must be between 1 and 100"
        }
    }
}
```

## 📈 Rate Limits

- REST API: 100 requests per minute
- Batch operations: 1000 documents per hour
- File size: 50MB per document

## 🔒 Security

- All APIs use TLS 1.3
- API keys must be kept secure
- Regular key rotation recommended
- IP whitelisting available

## 📚 Additional Resources

- [API Changelog](changelog.md)
- [Best Practices](best_practices.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Example Applications](examples.md)

---

For detailed documentation of each API type, please refer to the specific documentation files linked in the API Overview section. 