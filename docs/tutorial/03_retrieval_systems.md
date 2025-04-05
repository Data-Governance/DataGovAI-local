# Chapter 4: Retrieval Systems

## Introduction

Retrieval systems are responsible for finding and ranking relevant information from the knowledge base. This chapter explores different retrieval approaches and their implementations.

## Vector Search

Vector search uses similarity between embeddings to find relevant content.

### Key Concepts

1. **Similarity Metrics**
   - Cosine similarity
   - Euclidean distance
   - Inner product
   - Angular distance

2. **Indexing Structures**
   - HNSW (Hierarchical Navigable Small World)
   - IVF (Inverted File Index)
   - PQ (Product Quantization)
   - LSH (Locality-Sensitive Hashing)

3. **Performance Factors**
   - Index size
   - Query latency
   - Recall accuracy
   - Memory usage

### Implementation Examples

1. **Basic Vector Search**
```python
class VectorSearch:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator
    ):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        
    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(
            query
        )
        
        # Search vector store
        results = await self.vector_store.search(
            query_embedding,
            top_k=top_k
        )
        
        return results
```

2. **Advanced Vector Search**
```python
class AdvancedVectorSearch:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: AdvancedEmbeddingGenerator
    ):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        
    async def search(
        self,
        query: str,
        model_type: str = "default",
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(
            query,
            model_type=model_type
        )
        
        # Search vector store
        results = await self.vector_store.search(
            query_embedding,
            top_k=top_k
        )
        
        # Filter by similarity threshold
        filtered_results = [
            result for result in results
            if result["score"] >= threshold
        ]
        
        return filtered_results
```

## Hybrid Search

Hybrid search combines multiple search approaches for better results.

### Approaches

1. **Vector + Keyword**
   - Combines semantic and lexical search
   - Weights results from both approaches
   - Uses re-ranking strategies

2. **Vector + Graph**
   - Combines semantic and relationship-based search
   - Uses graph traversal for context
   - Weights by path relevance

### Implementation Examples

1. **Vector + Keyword Search**
```python
class HybridSearch:
    def __init__(
        self,
        vector_store: VectorStore,
        doc_store: DocumentStore,
        embedding_generator: EmbeddingGenerator
    ):
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.embedding_generator = embedding_generator
        
    async def search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        # Perform searches in parallel
        vector_results, keyword_results = await asyncio.gather(
            self.vector_search(query, top_k),
            self.keyword_search(query, top_k)
        )
        
        # Merge and rank results
        merged_results = self.merge_results(
            vector_results,
            keyword_results,
            vector_weight
        )
        
        return merged_results[:top_k]
        
    def merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float
    ) -> List[Dict[str, Any]]:
        # Create score map
        scores = defaultdict(float)
        
        # Add vector scores
        for result in vector_results:
            scores[result["id"]] += result["score"] * vector_weight
            
        # Add keyword scores
        for result in keyword_results:
            scores[result["id"]] += result["score"] * (1 - vector_weight)
            
        # Sort by combined score
        return sorted(
            [
                {"id": id, "score": score}
                for id, score in scores.items()
            ],
            key=lambda x: x["score"],
            reverse=True
        )
```

2. **Vector + Graph Search**
```python
class HybridGraphSearch:
    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        embedding_generator: EmbeddingGenerator
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedding_generator = embedding_generator
        
    async def search(
        self,
        query: str,
        top_k: int = 5,
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        # Get initial vector results
        vector_results = await self.vector_search(
            query,
            top_k
        )
        
        # Expand through graph
        expanded_results = await self.expand_through_graph(
            vector_results,
            max_hops
        )
        
        # Re-rank with graph context
        final_results = self.rerank_with_context(
            expanded_results,
            query
        )
        
        return final_results[:top_k]
        
    async def expand_through_graph(
        self,
        initial_results: List[Dict[str, Any]],
        max_hops: int
    ) -> List[Dict[str, Any]]:
        expanded = set()
        
        for result in initial_results:
            # Get connected nodes
            connected = await self.graph_store.get_connected_nodes(
                result["id"],
                max_hops=max_hops
            )
            expanded.update(connected)
            
        return list(expanded)
```

## Multi-Stage Retrieval

Multi-stage retrieval uses a pipeline of increasingly sophisticated retrieval and filtering steps.

### Stages

1. **Initial Retrieval**
   - Fast, approximate search
   - High recall, lower precision
   - Candidate generation

2. **Filtering**
   - Rule-based filtering
   - Metadata matching
   - Context validation

3. **Re-ranking**
   - Cross-encoder scoring
   - Context-aware ranking
   - Relevance scoring

### Implementation Example

```python
class MultiStageRetrieval:
    def __init__(
        self,
        vector_store: VectorStore,
        doc_store: DocumentStore,
        cross_encoder: CrossEncoder,
        embedding_generator: EmbeddingGenerator
    ):
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.cross_encoder = cross_encoder
        self.embedding_generator = embedding_generator
        
    async def search(
        self,
        query: str,
        initial_k: int = 100,
        filter_k: int = 20,
        final_k: int = 5
    ) -> List[Dict[str, Any]]:
        # Stage 1: Initial retrieval
        initial_results = await self.initial_retrieval(
            query,
            initial_k
        )
        
        # Stage 2: Filtering
        filtered_results = await self.filter_results(
            query,
            initial_results,
            filter_k
        )
        
        # Stage 3: Re-ranking
        final_results = await self.rerank_results(
            query,
            filtered_results,
            final_k
        )
        
        return final_results
        
    async def initial_retrieval(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(
            query
        )
        
        # Get vector search results
        return await self.vector_store.search(
            query_embedding,
            top_k=top_k
        )
        
    async def filter_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        filtered = []
        
        for result in results:
            # Get full document
            doc = await self.doc_store.get(result["id"])
            
            # Apply filters
            if self.passes_filters(doc, query):
                filtered.append(result)
                
            if len(filtered) >= top_k:
                break
                
        return filtered
        
    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        # Get full documents
        docs = await asyncio.gather(*[
            self.doc_store.get(result["id"])
            for result in results
        ])
        
        # Generate cross-encoder scores
        scores = await self.cross_encoder.score(
            query,
            [doc["content"] for doc in docs]
        )
        
        # Sort by cross-encoder score
        scored_results = [
            {
                **result,
                "score": score
            }
            for result, score in zip(results, scores)
        ]
        
        return sorted(
            scored_results,
            key=lambda x: x["score"],
            reverse=True
        )[:top_k]
```

## Context Management

Context management ensures retrieved information is relevant and coherent.

### Approaches

1. **Context Window**
   - Fixed-size context
   - Sliding window
   - Dynamic sizing

2. **Context Relevance**
   - Semantic similarity
   - Temporal relevance
   - Source authority

### Implementation Example

```python
class ContextManager:
    def __init__(
        self,
        embedding_generator: EmbeddingGenerator
    ):
        self.embedding_generator = embedding_generator
        self.context_cache = {}
        
    async def get_context(
        self,
        query: str,
        results: List[Dict[str, Any]],
        max_tokens: int = 1000
    ) -> str:
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embedding(
            query
        )
        
        # Score context relevance
        scored_contexts = await self.score_contexts(
            query_embedding,
            results
        )
        
        # Select and merge contexts
        return self.merge_contexts(
            scored_contexts,
            max_tokens
        )
        
    async def score_contexts(
        self,
        query_embedding: List[float],
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        scored = []
        
        for result in results:
            # Get or compute context embedding
            context_embedding = await self.get_context_embedding(
                result["content"]
            )
            
            # Compute similarity
            similarity = cosine_similarity(
                query_embedding,
                context_embedding
            )
            
            scored.append({
                **result,
                "relevance": similarity
            })
            
        return sorted(
            scored,
            key=lambda x: x["relevance"],
            reverse=True
        )
        
    def merge_contexts(
        self,
        contexts: List[Dict[str, Any]],
        max_tokens: int
    ) -> str:
        merged = []
        token_count = 0
        
        for context in contexts:
            # Count tokens
            tokens = len(context["content"].split())
            
            if token_count + tokens > max_tokens:
                break
                
            merged.append(context["content"])
            token_count += tokens
            
        return "\n\n".join(merged)
```

## Best Practices

1. **Search Quality**
   - Use appropriate similarity metrics
   - Implement proper filtering
   - Consider context relevance
   - Monitor search quality

2. **Performance**
   - Optimize index structures
   - Implement caching
   - Use batch processing
   - Monitor latency

3. **Scalability**
   - Design for horizontal scaling
   - Implement sharding
   - Use connection pooling
   - Handle failures gracefully

4. **Maintenance**
   - Regular index updates
   - Performance monitoring
   - Error tracking
   - Quality metrics

## Conclusion

Effective retrieval is crucial for knowledge base agents. Consider:

1. **Search Requirements**
   - Accuracy needs
   - Latency requirements
   - Scale considerations

2. **Implementation Approach**
   - Single vs. multi-stage
   - Context handling
   - Result ranking

3. **Operational Factors**
   - Resource usage
   - Maintenance needs
   - Monitoring requirements

Choose appropriate retrieval approaches based on your specific needs and implement proper monitoring and maintenance procedures to ensure reliable operation. 