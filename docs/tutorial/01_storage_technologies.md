# Chapter 2: Storage Technologies for Knowledge Base Agents

## Introduction

Storage is a fundamental component of any knowledge base agent. This chapter explores different storage technologies, their characteristics, and how to choose the right combination for your needs.

## Vector Stores

Vector stores are specialized databases designed to efficiently store and retrieve high-dimensional vectors, which are crucial for semantic search and similarity matching.

### Key Concepts

1. **Vector Similarity**
   - Cosine similarity
   - Euclidean distance
   - Dot product

2. **Indexing Methods**
   - Approximate Nearest Neighbors (ANN)
   - Locality-Sensitive Hashing (LSH)
   - Tree-based methods

3. **Performance Factors**
   - Vector dimension
   - Dataset size
   - Query latency
   - Memory usage

### Technology Comparison

| Feature | ChromaDB | Milvus | FAISS | Pinecone | Weaviate |
|---------|----------|--------|-------|-----------|-----------|
| Setup Complexity | Low | Medium | High | Low | Medium |
| Scalability | Medium | High | Low | High | High |
| Cloud Offering | No | Yes | No | Yes | Yes |
| Performance | Good | Excellent | Excellent | Good | Good |
| Persistence | Yes | Yes | No | Yes | Yes |
| Additional Features | Basic | Advanced | Basic | Advanced | Advanced |
| Cost | Free | Mixed | Free | Paid | Mixed |

### Implementation Examples

1. **ChromaDB (Simple Setup)**
```python
class ChromaVectorStore:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    async def store(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict]] = None
    ):
        await self.collection.add(
            embeddings=embeddings,
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        results = await self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return self._format_results(results)
```

2. **Milvus (Production Scale)**
```python
class MilvusVectorStore:
    def __init__(
        self,
        collection_name: str = "documents",
        dim: int = 768
    ):
        self.client = Milvus(
            host="localhost",
            port=19530
        )
        self.collection = self.client.create_collection(
            name=collection_name,
            dimension=dim,
            index_params={
                "index_type": "IVF_SQ8",
                "metric_type": "L2",
                "params": {"nlist": 1024}
            }
        )
        
    async def store(
        self,
        ids: List[str],
        embeddings: List[List[float]]
    ):
        entities = [
            {"id": id, "embedding": emb}
            for id, emb in zip(ids, embeddings)
        ]
        await self.collection.insert(entities)
        await self.collection.flush()
        
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        results = await self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k
        )
        return self._format_results(results)
```

## Document Stores

Document stores manage the original content and metadata, providing flexible schema and rich querying capabilities.

### Technology Comparison

| Feature | MongoDB | Elasticsearch | PostgreSQL | DynamoDB |
|---------|---------|--------------|------------|-----------|
| Query Flexibility | High | Very High | Medium | Low |
| Scalability | Good | Excellent | Medium | Excellent |
| Schema Flexibility | High | High | Low | High |
| Full-text Search | Basic | Excellent | Basic | No |
| Analytics | Limited | Good | Excellent | Limited |
| Cost | Mixed | High | Low | Usage-based |

### Implementation Examples

1. **MongoDB (Flexible Schema)**
```python
class MongoDocStore:
    def __init__(self, database: str = "knowledge_base"):
        self.client = MongoClient()
        self.db = self.client[database]
        self.collection = self.db.documents
        
    async def store(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        document = {
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
        
    async def get(self, id: str) -> Optional[Dict]:
        return await self.collection.find_one(
            {"_id": ObjectId(id)}
        )
        
    async def search(
        self,
        query: Dict,
        limit: int = 10
    ) -> List[Dict]:
        return await self.collection.find(
            query
        ).limit(limit).to_list(length=limit)
```

2. **Elasticsearch (Full-text Search)**
```python
class ElasticsearchDocStore:
    def __init__(self, index: str = "documents"):
        self.client = Elasticsearch()
        self.index = index
        
    async def store(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        document = {
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "vector_id": None  # Link to vector store
        }
        response = await self.client.index(
            index=self.index,
            document=document
        )
        return response["_id"]
        
    async def search(
        self,
        query: str,
        fields: List[str] = ["content"],
        limit: int = 10
    ) -> List[Dict]:
        response = await self.client.search(
            index=self.index,
            query={
                "multi_match": {
                    "query": query,
                    "fields": fields
                }
            },
            size=limit
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]
```

## Graph Databases

Graph databases excel at storing and querying relationships between entities, making them ideal for knowledge graphs.

### Technology Comparison

| Feature | Neo4j | DGraph | JanusGraph | Amazon Neptune |
|---------|-------|--------|------------|----------------|
| Query Language | Cypher | GraphQL+ | Gremlin | Multiple |
| Scalability | Medium | High | High | High |
| Learning Curve | Medium | Low | High | Medium |
| Community | Large | Growing | Medium | Small |
| Cost | Mixed | Mixed | Free | Usage-based |

### Implementation Examples

1. **Neo4j (Rich Relationships)**
```python
class Neo4jGraphStore:
    def __init__(self, uri: str = "bolt://localhost:7687"):
        self.driver = GraphDatabase.driver(uri)
        
    async def add_entity(
        self,
        properties: Dict,
        labels: List[str]
    ) -> str:
        async with self.driver.session() as session:
            result = await session.run("""
                CREATE (e:Entity)
                SET e += $properties
                SET e:$labels
                RETURN e
            """, {
                "properties": properties,
                "labels": labels
            })
            return result.single()["e"].id
            
    async def add_relationship(
        self,
        from_id: str,
        to_id: str,
        type: str,
        properties: Optional[Dict] = None
    ):
        async with self.driver.session() as session:
            await session.run("""
                MATCH (from) WHERE ID(from) = $from_id
                MATCH (to) WHERE ID(to) = $to_id
                CREATE (from)-[r:$type]->(to)
                SET r += $properties
            """, {
                "from_id": from_id,
                "to_id": to_id,
                "type": type,
                "properties": properties or {}
            })
```

## Hybrid Storage Solutions

Modern knowledge base agents often combine multiple storage types for optimal performance.

### Implementation Example

```python
class HybridStorage:
    def __init__(self):
        self.vector_store = MilvusVectorStore()
        self.doc_store = ElasticsearchDocStore()
        self.graph_store = Neo4jGraphStore()
        
    async def store_document(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> Dict[str, str]:
        # Store document
        doc_id = await self.doc_store.store(
            content,
            metadata
        )
        
        # Store vector
        vec_id = await self.vector_store.store(
            [doc_id],
            [embedding]
        )
        
        # Update document with vector ID
        await self.doc_store.update(
            doc_id,
            {"vector_id": vec_id}
        )
        
        return {
            "doc_id": doc_id,
            "vector_id": vec_id
        }
        
    async def search(
        self,
        query: str,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict]:
        # Search in parallel
        vector_results, text_results = await asyncio.gather(
            self.vector_store.search(
                query_embedding,
                top_k
            ),
            self.doc_store.search(
                query,
                limit=top_k
            )
        )
        
        # Merge and rank results
        return self.rank_results(
            vector_results,
            text_results
        )
```

## Best Practices

1. **Storage Selection**
   - Choose based on scale requirements
   - Consider operational complexity
   - Factor in cost constraints
   - Plan for future growth

2. **Data Management**
   - Implement proper backup strategies
   - Monitor performance metrics
   - Handle data consistency
   - Plan for data migration

3. **Performance Optimization**
   - Use appropriate indexing
   - Implement caching
   - Optimize query patterns
   - Monitor resource usage

4. **Error Handling**
```python
class ResilientStorage:
    def __init__(self):
        self.store = HybridStorage()
        self.retries = 3
        
    async def store_with_retry(
        self,
        content: str,
        embedding: List[float]
    ) -> Dict[str, str]:
        for attempt in range(self.retries):
            try:
                return await self.store.store_document(
                    content,
                    embedding
                )
            except Exception as e:
                if attempt == self.retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
```

## Conclusion

Choosing the right storage technologies is crucial for building an effective knowledge base agent. Consider:

1. **Scale Requirements**
   - Document volume
   - Query patterns
   - Growth projections

2. **Functional Needs**
   - Search capabilities
   - Relationship modeling
   - Analytics requirements

3. **Operational Factors**
   - Maintenance overhead
   - Cost considerations
   - Team expertise

Start with simpler solutions and evolve as needs grow. Monitor performance and be prepared to adapt your storage strategy based on real-world usage patterns. 