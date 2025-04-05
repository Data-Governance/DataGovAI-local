# Chapter 6: System Integration

## Introduction

System integration is crucial for building production-ready knowledge base agents. This chapter explores API design, caching strategies, load balancing, and monitoring systems.

## API Design

A well-designed API is essential for integrating knowledge base agents into larger systems.

### API Patterns

1. **REST API**
   - Resource-based endpoints
   - HTTP methods
   - Status codes
   - Query parameters

2. **GraphQL API**
   - Flexible queries
   - Type system
   - Resolvers
   - Subscriptions

### Implementation Examples

1. **FastAPI REST Implementation**
```python
class KnowledgeBaseAPI:
    def __init__(
        self,
        qa_system: AdvancedQASystem,
        doc_processor: AdvancedDocumentProcessor
    ):
        self.qa_system = qa_system
        self.doc_processor = doc_processor
        self.app = FastAPI()
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.post("/documents")
        async def add_document(
            document: DocumentInput
        ) -> DocumentResponse:
            # Process document
            processed = await self.doc_processor.process_document(
                document.content
            )
            
            # Store document
            doc_id = await self.qa_system.store_document(
                processed
            )
            
            return DocumentResponse(
                id=doc_id,
                status="success"
            )
            
        @self.app.get("/search")
        async def search(
            query: str,
            top_k: int = 5
        ) -> SearchResponse:
            results = await self.qa_system.search(
                query,
                top_k=top_k
            )
            
            return SearchResponse(
                results=results
            )
            
        @self.app.post("/ask")
        async def ask(
            question: QuestionInput
        ) -> AnswerResponse:
            answer = await self.qa_system.answer(
                question.text,
                strategy=question.strategy
            )
            
            return AnswerResponse(
                question=question.text,
                answer=answer["answer"],
                sources=answer["sources"]
            )
```

2. **GraphQL Implementation**
```python
class KnowledgeBaseGraphQL:
    def __init__(
        self,
        qa_system: AdvancedQASystem,
        doc_processor: AdvancedDocumentProcessor
    ):
        self.qa_system = qa_system
        self.doc_processor = doc_processor
        
    async def resolve_search(
        self,
        info,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        results = await self.qa_system.search(
            query,
            top_k=top_k
        )
        
        return results
        
    async def resolve_ask(
        self,
        info,
        question: str,
        strategy: str = "default"
    ) -> Dict[str, Any]:
        answer = await self.qa_system.answer(
            question,
            strategy=strategy
        )
        
        return answer
        
    async def resolve_add_document(
        self,
        info,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        # Process document
        processed = await self.doc_processor.process_document(
            content,
            metadata=metadata
        )
        
        # Store document
        doc_id = await self.qa_system.store_document(
            processed
        )
        
        return doc_id
```

## Caching

Effective caching strategies improve performance and reduce resource usage.

### Cache Levels

1. **Application Cache**
   - In-memory cache
   - Local file cache
   - Distributed cache

2. **Result Cache**
   - Query results
   - Embeddings
   - Document metadata

### Implementation Examples

1. **Multi-Level Cache**
```python
class CacheManager:
    def __init__(self):
        # In-memory cache
        self.memory_cache = LRUCache(maxsize=1000)
        
        # Redis cache
        self.redis_cache = Redis(
            host="localhost",
            port=6379
        )
        
        # File cache
        self.file_cache = FileCache(
            directory="cache",
            max_size_gb=10
        )
        
    async def get(
        self,
        key: str,
        level: str = "all"
    ) -> Optional[Any]:
        # Check memory cache
        if level in ["all", "memory"]:
            if key in self.memory_cache:
                return self.memory_cache[key]
                
        # Check Redis cache
        if level in ["all", "redis"]:
            value = await self.redis_cache.get(key)
            if value:
                return self.deserialize(value)
                
        # Check file cache
        if level in ["all", "file"]:
            value = await self.file_cache.get(key)
            if value:
                return self.deserialize(value)
                
        return None
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ):
        # Set in memory
        self.memory_cache[key] = value
        
        # Set in Redis
        serialized = self.serialize(value)
        await self.redis_cache.set(
            key,
            serialized,
            ex=ttl
        )
        
        # Set in file
        await self.file_cache.set(
            key,
            serialized
        )
```

2. **Smart Cache**
```python
class SmartCache:
    def __init__(
        self,
        cache_manager: CacheManager
    ):
        self.cache_manager = cache_manager
        self.stats = defaultdict(int)
        
    async def get_search_results(
        self,
        query: str,
        **params
    ) -> Optional[List[Dict[str, Any]]]:
        cache_key = self.make_key(
            "search",
            query,
            params
        )
        
        results = await self.cache_manager.get(
            cache_key,
            level="memory"
        )
        
        if results:
            self.stats["cache_hits"] += 1
            return results
            
        self.stats["cache_misses"] += 1
        return None
        
    async def cache_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        **params
    ):
        cache_key = self.make_key(
            "search",
            query,
            params
        )
        
        await self.cache_manager.set(
            cache_key,
            results,
            ttl=3600  # 1 hour
        )
        
    def should_cache(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        # Check query frequency
        query_count = self.stats[f"query:{query}"]
        
        # Check result quality
        result_quality = self.assess_quality(results)
        
        return (
            query_count > 5 or  # Popular query
            result_quality > 0.8  # High quality results
        )
```

## Load Balancing

Load balancing ensures efficient resource utilization and high availability.

### Implementation Examples

1. **Service Load Balancer**
```python
class LoadBalancer:
    def __init__(self):
        self.services = {
            "qa": [],
            "embedding": [],
            "processing": []
        }
        self.stats = defaultdict(dict)
        
    async def register_service(
        self,
        service_type: str,
        endpoint: str,
        capacity: int = 100
    ):
        self.services[service_type].append({
            "endpoint": endpoint,
            "capacity": capacity,
            "current_load": 0
        })
        
    async def get_service(
        self,
        service_type: str
    ) -> str:
        services = self.services[service_type]
        
        # Find least loaded service
        service = min(
            services,
            key=lambda s: s["current_load"] / s["capacity"]
        )
        
        return service["endpoint"]
        
    async def update_load(
        self,
        service_type: str,
        endpoint: str,
        load: int
    ):
        for service in self.services[service_type]:
            if service["endpoint"] == endpoint:
                service["current_load"] = load
                break
```

2. **Smart Load Balancer**
```python
class SmartLoadBalancer:
    def __init__(self):
        self.load_balancer = LoadBalancer()
        self.circuit_breaker = CircuitBreaker()
        
    async def route_request(
        self,
        service_type: str,
        request: Dict[str, Any]
    ) -> Any:
        # Get available service
        endpoint = await self.load_balancer.get_service(
            service_type
        )
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute(endpoint):
            # Use fallback service
            endpoint = await self.get_fallback_service(
                service_type
            )
            
        try:
            # Execute request
            response = await self.execute_request(
                endpoint,
                request
            )
            
            # Update metrics
            await self.update_metrics(
                endpoint,
                "success"
            )
            
            return response
            
        except Exception as e:
            # Handle failure
            await self.handle_failure(
                endpoint,
                e
            )
            
            # Retry with different service
            return await self.retry_request(
                service_type,
                request
            )
```

## Monitoring

Comprehensive monitoring ensures system health and performance.

### Implementation Examples

1. **Basic Monitoring**
```python
class MonitoringSystem:
    def __init__(self):
        self.metrics = PrometheusMetrics()
        self.logger = Logger()
        
    async def log_request(
        self,
        endpoint: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        duration: float
    ):
        # Log request details
        self.logger.info(
            "Request processed",
            extra={
                "endpoint": endpoint,
                "duration": duration,
                "status": response.get("status")
            }
        )
        
        # Update metrics
        self.metrics.request_duration.observe(
            duration,
            {"endpoint": endpoint}
        )
        self.metrics.request_count.inc(
            {"endpoint": endpoint}
        )
        
    async def monitor_health(self):
        while True:
            # Check service health
            health = await self.check_services()
            
            # Update metrics
            self.metrics.service_health.set(
                health["score"],
                {"status": health["status"]}
            )
            
            # Log health status
            self.logger.info(
                "Health check",
                extra=health
            )
            
            await asyncio.sleep(60)
```

2. **Advanced Monitoring**
```python
class AdvancedMonitoring:
    def __init__(self):
        self.basic_monitoring = MonitoringSystem()
        self.alerting = AlertingSystem()
        self.tracing = TracingSystem()
        
    async def monitor_request(
        self,
        context: Dict[str, Any]
    ):
        # Start trace
        with self.tracing.start_span(
            "process_request",
            context
        ) as span:
            try:
                # Process request
                result = await self.process_with_monitoring(
                    context,
                    span
                )
                
                # Record success
                await self.record_success(
                    context,
                    result
                )
                
                return result
                
            except Exception as e:
                # Record failure
                await self.record_failure(
                    context,
                    e
                )
                
                # Alert if necessary
                await self.check_alert_conditions(
                    context,
                    e
                )
                
                raise
                
    async def process_with_monitoring(
        self,
        context: Dict[str, Any],
        span: Span
    ) -> Dict[str, Any]:
        # Add request details to span
        span.set_tag(
            "request.type",
            context["type"]
        )
        
        # Monitor sub-operations
        with span.new_child("prepare"):
            request = await self.prepare_request(context)
            
        with span.new_child("execute"):
            result = await self.execute_request(request)
            
        with span.new_child("process"):
            processed = await self.process_result(result)
            
        return processed
```

## Best Practices

1. **API Design**
   - Use consistent patterns
   - Implement proper validation
   - Handle errors gracefully
   - Document thoroughly

2. **Caching**
   - Choose appropriate levels
   - Set proper TTL values
   - Monitor hit rates
   - Handle invalidation

3. **Load Balancing**
   - Monitor service health
   - Implement failover
   - Balance load evenly
   - Handle failures

4. **Monitoring**
   - Track key metrics
   - Set up alerts
   - Maintain logs
   - Analyze trends

## Conclusion

Effective system integration is crucial for production knowledge base agents. Consider:

1. **Architecture Decisions**
   - API design choices
   - Caching strategy
   - Load balancing approach
   - Monitoring needs

2. **Implementation Approach**
   - Service organization
   - Error handling
   - Performance optimization
   - Maintenance requirements

3. **Operational Factors**
   - Deployment strategy
   - Scaling approach
   - Monitoring setup
   - Maintenance procedures

Choose appropriate integration patterns based on your specific requirements and implement proper monitoring and maintenance procedures to ensure reliable operation. 