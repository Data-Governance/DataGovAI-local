# Knowledge Base Query Patterns

## Overview

The Knowledge Base supports various query patterns through its hybrid RAG+KG architecture. This document outlines common query patterns and provides examples of how to implement them.

## Query Types

### 1. Semantic Search (RAG)

Best for finding documents based on meaning rather than exact matches.

```python
from knowledge_base_agent.search import semantic_search

# Basic semantic search
results = semantic_search(
    query="What are the retention requirements for financial records?",
    top_k=5
)

# With category filter
results = semantic_search(
    query="audit documentation requirements",
    filters={"category": "financial"},
    top_k=5
)

# With date range
results = semantic_search(
    query="personnel policy updates",
    filters={
        "metadata.created_at": {
            "gte": "2023-01-01",
            "lte": "2023-12-31"
        }
    }
)
```

### 2. Structured Queries (KG)

Best for precise fact retrieval and relationship exploration.

```python
from knowledge_base_agent.query import kg_query

# Find specific GRS document
results = kg_query(
    """
    MATCH (d:Document)-[:HAS_SERIES]->(s:RecordSeries)
    WHERE s.value = 'GRS-1234'
    RETURN d
    """
)

# Get retention period for a record series
results = kg_query(
    """
    MATCH (s:RecordSeries {value: $series})-[:HAS_RETENTION]->(r:RetentionPeriod)
    RETURN r.value
    """,
    params={"series": "GRS-1234"}
)

# Find related documents
results = kg_query(
    """
    MATCH (d1:Document)-[:REFERENCES]->(d2:Document)
    WHERE d1.id = $doc_id
    RETURN d2
    """,
    params={"doc_id": "123e4567-e89b-12d3-a456-426614174000"}
)
```

### 3. Hybrid Queries (RAG+KG)

Combines semantic search with structured knowledge.

```python
from knowledge_base_agent.query import hybrid_query

# Query with both semantic and structured components
results = hybrid_query(
    query="What is the retention period for personnel evaluation records?",
    entity_types=["record_series", "retention_period"],
    relationships=["has_retention"]
)

# Complex query with multiple constraints
results = hybrid_query(
    query="Show me all financial records that require permanent retention",
    filters={
        "category": "financial",
        "entities": {
            "type": "retention_period",
            "value": "permanent"
        }
    }
)
```

## Common Query Patterns

### 1. Document Lookup

```python
# By GRS number
def find_by_grs(grs_number: str) -> Document:
    return kg_query(
        """
        MATCH (d:Document)-[:HAS_SERIES]->(s:RecordSeries {value: $grs})
        RETURN d
        """,
        params={"grs": grs_number}
    )

# By title (fuzzy match)
def find_by_title(title: str) -> List[Document]:
    return semantic_search(
        query=title,
        filters={"metadata.type": "title"},
        top_k=5
    )
```

### 2. Retention Requirements

```python
# Get retention period
def get_retention_period(grs_number: str) -> str:
    return kg_query(
        """
        MATCH (s:RecordSeries {value: $grs})-[:HAS_RETENTION]->(r:RetentionPeriod)
        RETURN r.value
        """,
        params={"grs": grs_number}
    )

# Find all documents with specific retention
def find_by_retention(period: str) -> List[Document]:
    return hybrid_query(
        query=f"documents with {period} retention period",
        filters={
            "entities": {
                "type": "retention_period",
                "value": period
            }
        }
    )
```

### 3. Related Documents

```python
# Find superseded documents
def find_superseded(grs_number: str) -> List[Document]:
    return kg_query(
        """
        MATCH (s1:RecordSeries {value: $grs})-[:SUPERSEDES]->(s2:RecordSeries)
        RETURN s2
        """,
        params={"grs": grs_number}
    )

# Find documents with similar content
def find_similar(doc_id: str, threshold: float = 0.8) -> List[Document]:
    return semantic_search(
        query_by_document_id=doc_id,
        similarity_threshold=threshold,
        exclude_self=True
    )
```

### 4. Complex Queries

```python
# Find all financial documents with specific requirements
def find_financial_requirements(requirement_type: str) -> List[Document]:
    return hybrid_query(
        query=f"financial documents with {requirement_type} requirements",
        filters={
            "category": "financial",
            "entities": {
                "type": "requirement",
                "value_contains": requirement_type
            }
        }
    )

# Find documents affected by legal changes
def find_affected_by_law(law_reference: str) -> List[Document]:
    return hybrid_query(
        query=f"documents affected by {law_reference}",
        entity_types=["legal_authority"],
        relationships=["requires", "references"]
    )
```

## Query Optimization

### 1. Caching

```python
from knowledge_base_agent.cache import QueryCache

# Initialize cache
cache = QueryCache()

# Cache common queries
@cache.memoize(ttl=3600)  # Cache for 1 hour
def get_document_retention(grs_number: str) -> str:
    return get_retention_period(grs_number)
```

### 2. Batch Processing

```python
# Batch entity queries
def batch_get_retention_periods(grs_numbers: List[str]) -> Dict[str, str]:
    return kg_query(
        """
        MATCH (s:RecordSeries)-[:HAS_RETENTION]->(r:RetentionPeriod)
        WHERE s.value IN $grs_list
        RETURN s.value, r.value
        """,
        params={"grs_list": grs_numbers}
    )
```

### 3. Query Planning

```python
# Use query planner for complex queries
def optimize_complex_query(query: str) -> Dict:
    plan = query_planner.analyze(query)
    if plan.should_use_kg():
        return kg_query(plan.kg_query)
    elif plan.should_use_hybrid():
        return hybrid_query(plan.hybrid_query)
    else:
        return semantic_search(query)
```

## Best Practices

1. **Use the Right Query Type**
   - Semantic search for concept-based queries
   - KG queries for precise fact retrieval
   - Hybrid queries for complex information needs

2. **Optimize Performance**
   - Cache frequently used queries
   - Use batch processing for multiple items
   - Consider query planning for complex queries

3. **Handle Errors**
   - Implement proper error handling
   - Provide meaningful error messages
   - Consider fallback options

## See Also

- [Data Model](data_model.md)
- [Architecture Overview](architecture.md)
- [Performance Optimization](optimization.md) 