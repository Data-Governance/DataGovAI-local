# 📝 Examples

This directory contains examples demonstrating various features and use cases of the DataGovAI system.

## Document Processing Examples

### 1. Basic Document Processing

```python
# examples/processing/basic_processing.py
from datagovai import Client

async def process_document():
    # Initialize client
    client = Client()
    
    # Upload and process document
    document = await client.documents.create(
        title="Financial Records Retention",
        file_path="examples/data/financial_records.pdf",
        metadata={
            "category": "financial",
            "department": "accounting"
        }
    )
    
    print(f"Document created: {document.id}")
    
    # Wait for processing to complete
    status = await client.documents.wait_for_processing(document.id)
    print(f"Processing status: {status}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(process_document())
```

### 2. Batch Processing

```python
# examples/processing/batch_processing.py
import asyncio
from datagovai import Client
from pathlib import Path

async def process_directory(directory: str):
    client = Client()
    
    # Get all PDF files
    pdf_files = Path(directory).glob("*.pdf")
    
    # Process files concurrently
    tasks = []
    for pdf_file in pdf_files:
        task = client.documents.create(
            title=pdf_file.stem,
            file_path=str(pdf_file)
        )
        tasks.append(task)
    
    # Wait for all documents to be created
    documents = await asyncio.gather(*tasks)
    
    # Wait for processing to complete
    status_tasks = []
    for doc in documents:
        task = client.documents.wait_for_processing(doc.id)
        status_tasks.append(task)
    
    statuses = await asyncio.gather(*status_tasks)
    
    # Print results
    for doc, status in zip(documents, statuses):
        print(f"Document {doc.id}: {status}")

if __name__ == "__main__":
    asyncio.run(process_directory("examples/data/batch"))
```

## Search Examples

### 1. Semantic Search

```python
# examples/search/semantic_search.py
from datagovai import Client

async def search_documents():
    client = Client()
    
    # Simple semantic search
    results = await client.search.semantic(
        query="What is the retention period for financial audit records?",
        filters={
            "category": "financial"
        },
        top_k=5
    )
    
    print("\nSearch Results:")
    for result in results:
        print(f"\nDocument: {result.id}")
        print(f"Title: {result.title}")
        print(f"Score: {result.score}")
        print(f"Excerpt: {result.excerpt}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(search_documents())
```

### 2. Advanced Search

```python
# examples/search/advanced_search.py
from datagovai import Client

async def advanced_search():
    client = Client()
    
    # Hybrid search with multiple criteria
    results = await client.search.hybrid(
        semantic_query="audit requirements",
        filters={
            "category": "financial",
            "metadata.retention.period": "7 years"
        },
        graph_patterns=[
            {
                "relationship": "requires",
                "target_type": "requirement"
            }
        ],
        sort=[
            {"field": "created_at", "order": "desc"}
        ],
        top_k=10
    )
    
    print("\nAdvanced Search Results:")
    for result in results:
        print(f"\nDocument: {result.id}")
        print(f"Title: {result.title}")
        print(f"Score: {result.score}")
        print("Requirements:")
        for req in result.related_entities:
            print(f"- {req.value}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(advanced_search())
```

## Knowledge Graph Examples

### 1. Entity Extraction

```python
# examples/knowledge_graph/entity_extraction.py
from datagovai import Client

async def extract_entities():
    client = Client()
    
    # Create document with entity extraction
    document = await client.documents.create(
        title="Personnel Records Policy",
        content="""
        Personnel records must be retained for 7 years from the date of termination.
        This requirement is based on Utah Code § 63G-2-604.
        Records must be securely destroyed after the retention period.
        """,
        extract_entities=True
    )
    
    # Get extracted entities
    entities = await client.entities.list(document_id=document.id)
    
    print("\nExtracted Entities:")
    for entity in entities:
        print(f"\nType: {entity.type}")
        print(f"Value: {entity.value}")
        print(f"Confidence: {entity.metadata.get('confidence')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(extract_entities())
```

### 2. Relationship Analysis

```python
# examples/knowledge_graph/relationship_analysis.py
from datagovai import Client

async def analyze_relationships():
    client = Client()
    
    # Get document relationships
    document_id = "GRS-2024-FIN-001"
    relationships = await client.relationships.list(
        source_id=document_id,
        types=["supersedes", "requires", "references"]
    )
    
    print(f"\nRelationships for document {document_id}:")
    for rel in relationships:
        print(f"\nType: {rel.type}")
        print(f"Source: {rel.source_id}")
        print(f"Target: {rel.target_id}")
        print(f"Context: {rel.metadata.get('context')}")
        
        # Get related document details
        target_doc = await client.documents.get(rel.target_id)
        print(f"Related Document: {target_doc.title}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(analyze_relationships())
```

## API Integration Examples

### 1. Webhook Handler

```python
# examples/api/webhook_handler.py
from fastapi import FastAPI, Request
from hmac import compare_digest
from datagovai.webhooks import verify_signature

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request):
    # Verify webhook signature
    signature = request.headers.get("X-DataGovAI-Signature")
    payload = await request.body()
    
    if not verify_signature(payload, signature, "your-webhook-secret"):
        return {"status": "error", "message": "Invalid signature"}
    
    # Parse event data
    event_data = await request.json()
    event_type = event_data["event"]
    
    # Handle different event types
    if event_type == "document.created":
        await handle_document_created(event_data["data"])
    elif event_type == "document.updated":
        await handle_document_updated(event_data["data"])
    elif event_type == "processing.completed":
        await handle_processing_completed(event_data["data"])
    
    return {"status": "success"}

async def handle_document_created(data):
    print(f"New document created: {data['document_id']}")
    # Add your document creation handling logic here

async def handle_document_updated(data):
    print(f"Document updated: {data['document_id']}")
    # Add your document update handling logic here

async def handle_processing_completed(data):
    print(f"Processing completed for: {data['document_id']}")
    # Add your processing completion handling logic here
```

### 2. Custom Client Integration

```python
# examples/api/custom_integration.py
from datagovai import Client
from typing import List, Optional
import asyncio

class RetentionManager:
    def __init__(self, api_key: str):
        self.client = Client(api_key=api_key)
    
    async def get_retention_requirements(
        self,
        category: str,
        subcategory: Optional[str] = None
    ) -> List[dict]:
        """Get retention requirements for a category."""
        # Search for relevant documents
        results = await self.client.search.semantic(
            query=f"retention requirements for {category}",
            filters={
                "category": category,
                "subcategory": subcategory
            } if subcategory else {"category": category}
        )
        
        # Extract retention information
        requirements = []
        for result in results:
            doc = await self.client.documents.get(
                result.id,
                include_entities=True
            )
            
            # Find retention period entities
            retention_entities = [
                e for e in doc.entities
                if e.type == "retention_period"
            ]
            
            # Get related requirements
            for entity in retention_entities:
                related = await self.client.relationships.list(
                    source_id=entity.id,
                    types=["requires"]
                )
                
                requirements.append({
                    "document_id": doc.id,
                    "title": doc.title,
                    "retention_period": entity.value,
                    "requirements": [
                        r.target.value for r in related
                    ]
                })
        
        return requirements

async def main():
    # Initialize manager
    manager = RetentionManager("your-api-key")
    
    # Get retention requirements
    requirements = await manager.get_retention_requirements(
        category="financial",
        subcategory="audit"
    )
    
    # Print results
    print("\nRetention Requirements:")
    for req in requirements:
        print(f"\nDocument: {req['document_id']}")
        print(f"Title: {req['title']}")
        print(f"Retention Period: {req['retention_period']}")
        print("Requirements:")
        for r in req['requirements']:
            print(f"- {r}")

if __name__ == "__main__":
    asyncio.run(main())
```

## CLI Examples

### 1. Document Management

```bash
# examples/cli/document_management.sh
#!/bin/bash

# Set API key
export DATAGOVAI_API_KEY="your-api-key"

# Upload document
echo "Uploading document..."
datagovai docs upload \
    --title "Financial Records Policy" \
    --category financial \
    path/to/document.pdf

# List documents
echo -e "\nListing documents..."
datagovai docs list \
    --category financial \
    --sort created_at \
    --order desc \
    --limit 5

# Get document details
echo -e "\nGetting document details..."
datagovai docs get GRS-2024-FIN-001 \
    --include-entities \
    --format json

# Delete document
echo -e "\nDeleting document..."
datagovai docs delete GRS-2024-FIN-001 \
    --force
```

### 2. Search Operations

```bash
# examples/cli/search_operations.sh
#!/bin/bash

# Set API key
export DATAGOVAI_API_KEY="your-api-key"

# Semantic search
echo "Performing semantic search..."
datagovai search \
    "retention period for financial audits" \
    --category financial \
    --limit 5

# Structured search
echo -e "\nPerforming structured search..."
datagovai search \
    --filter "category=financial" \
    --filter "metadata.retention.period=7 years" \
    --sort created_at:desc \
    --limit 5

# Graph search
echo -e "\nPerforming graph search..."
datagovai graph search GRS-2024-FIN-001 \
    --relationship supersedes \
    --depth 3 \
    --format json
```

## See Also
- [API Documentation](../api/README.md)
- [Knowledge Base Documentation](../knowledge_base/README.md)
- [Development Guide](../development/README.md) 