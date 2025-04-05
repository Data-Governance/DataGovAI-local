# Chapter 5: Language Models and AI

## Introduction

Language models are fundamental to modern knowledge base agents, enabling sophisticated text understanding and generation. This chapter explores different types of language models and their integration into knowledge base systems.

## Embedding Models

Embedding models convert text into dense vector representations for semantic search and similarity comparison.

### Model Types

1. **General Purpose**
   - BERT
   - RoBERTa
   - DeBERTa
   - T5

2. **Domain Specific**
   - BioBERT (medical)
   - SciBERT (scientific)
   - FinBERT (financial)
   - LegalBERT (legal)

3. **Multilingual**
   - mBERT
   - XLM-RoBERTa
   - LaBSE
   - MUSE

### Technology Comparison

| Feature | Sentence-BERT | OpenAI Ada | BGE | MPNet |
|---------|---------------|------------|-----|--------|
| Quality | High | Very High | High | High |
| Speed | Fast | API Latency | Fast | Medium |
| Cost | Free | Pay per token | Free | Free |
| Dimension | 384/768 | 1536 | 768 | 768 |
| Languages | Many | English | Many | Many |

### Implementation Examples

1. **Basic Embedding Service**
```python
class EmbeddingService:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.model = SentenceTransformer(
            model_name,
            device=device
        )
        self.cache = {}
        
    async def get_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> List[float]:
        if use_cache and text in self.cache:
            return self.cache[text]
            
        embedding = await self.model.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        
        if use_cache:
            self.cache[text] = embedding
            
        return embedding
        
    async def get_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        return await self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
```

2. **Advanced Embedding Service**
```python
class AdvancedEmbeddingService:
    def __init__(self):
        self.models = {
            "default": SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            ),
            "multilingual": SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
            "scientific": SentenceTransformer(
                "allenai/scibert_scivocab_uncased"
            )
        }
        self.cache = LRUCache(maxsize=10000)
        
    async def get_embedding(
        self,
        text: str,
        model_type: str = "default",
        use_cache: bool = True
    ) -> List[float]:
        cache_key = f"{model_type}:{text}"
        
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
            
        model = self.models.get(
            model_type,
            self.models["default"]
        )
        
        embedding = await model.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        
        if use_cache:
            self.cache[cache_key] = embedding
            
        return embedding
        
    async def get_cross_embeddings(
        self,
        text: str
    ) -> Dict[str, List[float]]:
        tasks = [
            self.get_embedding(text, model_type)
            for model_type in self.models.keys()
        ]
        
        embeddings = await asyncio.gather(*tasks)
        
        return dict(zip(
            self.models.keys(),
            embeddings
        ))
```

## Large Language Models

Large Language Models (LLMs) provide sophisticated text understanding and generation capabilities.

### Model Types

1. **Cloud APIs**
   - OpenAI GPT
   - Anthropic Claude
   - Google PaLM
   - Cohere

2. **Open Source**
   - Llama 2
   - Mistral
   - Falcon
   - MPT

### Implementation Examples

1. **Basic LLM Service**
```python
class LLMService:
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=kwargs.get(
                "temperature",
                self.temperature
            ),
            max_tokens=kwargs.get(
                "max_tokens",
                self.max_tokens
            )
        )
        
        return response.choices[0].message.content
        
    async def generate_with_context(
        self,
        prompt: str,
        context: str,
        **kwargs
    ) -> str:
        formatted_prompt = f"""Context:
{context}

Question:
{prompt}

Answer:"""
        
        return await self.generate(
            formatted_prompt,
            **kwargs
        )
```

2. **Advanced LLM Service**
```python
class AdvancedLLMService:
    def __init__(self):
        self.models = {
            "chat": OpenAI(model="gpt-3.5-turbo"),
            "completion": OpenAI(model="gpt-3.5-turbo-instruct"),
            "local": LocalLLM(model="mistral-7b-instruct")
        }
        self.cache = LRUCache(maxsize=1000)
        
    async def generate(
        self,
        prompt: str,
        model_type: str = "chat",
        use_cache: bool = True,
        **kwargs
    ) -> str:
        if use_cache:
            cache_key = f"{model_type}:{prompt}:{kwargs}"
            if cache_key in self.cache:
                return self.cache[cache_key]
                
        model = self.models.get(
            model_type,
            self.models["chat"]
        )
        
        response = await model.generate(
            prompt,
            **kwargs
        )
        
        if use_cache:
            self.cache[cache_key] = response
            
        return response
        
    async def generate_structured(
        self,
        prompt: str,
        output_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        formatted_prompt = f"""Generate a response in the following JSON format:
{json.dumps(output_format, indent=2)}

Prompt:
{prompt}"""
        
        response = await self.generate(
            formatted_prompt,
            temperature=0.1,
            **kwargs
        )
        
        return json.loads(response)
```

## Question Answering

Question answering systems combine retrieval and language models to provide accurate responses.

### Implementation Examples

1. **Basic QA System**
```python
class QASystem:
    def __init__(
        self,
        retriever: MultiStageRetrieval,
        llm: LLMService
    ):
        self.retriever = retriever
        self.llm = llm
        
    async def answer(
        self,
        question: str,
        max_context_tokens: int = 2000
    ) -> Dict[str, Any]:
        # Retrieve relevant context
        context_docs = await self.retriever.search(
            question,
            top_k=5
        )
        
        # Merge context
        context = self.merge_context(
            context_docs,
            max_context_tokens
        )
        
        # Generate answer
        answer = await self.llm.generate_with_context(
            question,
            context
        )
        
        return {
            "question": question,
            "answer": answer,
            "context": context,
            "sources": [doc["id"] for doc in context_docs]
        }
```

2. **Advanced QA System**
```python
class AdvancedQASystem:
    def __init__(
        self,
        retriever: MultiStageRetrieval,
        llm: AdvancedLLMService,
        embedding_service: AdvancedEmbeddingService
    ):
        self.retriever = retriever
        self.llm = llm
        self.embedding_service = embedding_service
        
    async def answer(
        self,
        question: str,
        strategy: str = "default"
    ) -> Dict[str, Any]:
        if strategy == "direct":
            return await self.direct_answer(question)
        elif strategy == "rag":
            return await self.rag_answer(question)
        else:
            return await self.hybrid_answer(question)
            
    async def direct_answer(
        self,
        question: str
    ) -> Dict[str, Any]:
        answer = await self.llm.generate(
            question,
            model_type="chat"
        )
        
        return {
            "question": question,
            "answer": answer,
            "method": "direct"
        }
        
    async def rag_answer(
        self,
        question: str
    ) -> Dict[str, Any]:
        # Get relevant documents
        context_docs = await self.retriever.search(
            question,
            top_k=5
        )
        
        # Format context
        context = self.format_context(context_docs)
        
        # Generate answer
        answer = await self.llm.generate_with_context(
            question,
            context,
            model_type="chat"
        )
        
        return {
            "question": question,
            "answer": answer,
            "context": context,
            "sources": [doc["id"] for doc in context_docs],
            "method": "rag"
        }
        
    async def hybrid_answer(
        self,
        question: str
    ) -> Dict[str, Any]:
        # Get both direct and RAG answers
        direct_result = await self.direct_answer(question)
        rag_result = await self.rag_answer(question)
        
        # Compare answers
        combined = await self.combine_answers(
            question,
            direct_result["answer"],
            rag_result["answer"],
            rag_result["context"]
        )
        
        return {
            "question": question,
            "answer": combined,
            "sources": rag_result.get("sources", []),
            "method": "hybrid"
        }
```

## Best Practices

1. **Model Selection**
   - Choose appropriate model sizes
   - Consider cost vs. quality
   - Evaluate multilingual needs
   - Test domain specificity

2. **Integration**
   - Implement proper caching
   - Handle API rate limits
   - Monitor token usage
   - Implement fallbacks

3. **Quality Control**
   - Validate model outputs
   - Monitor answer quality
   - Implement safety filters
   - Track user feedback

4. **Performance**
   - Optimize batch processing
   - Cache common queries
   - Monitor latency
   - Handle failures gracefully

## Conclusion

Language models are essential for modern knowledge base agents. Consider:

1. **Model Requirements**
   - Accuracy needs
   - Speed requirements
   - Cost constraints
   - Language support

2. **Integration Strategy**
   - API vs. local models
   - Caching strategy
   - Error handling
   - Monitoring needs

3. **Quality Assurance**
   - Output validation
   - Performance tracking
   - User feedback
   - Safety measures

Choose appropriate models and integration strategies based on your specific requirements, and implement proper monitoring and quality control measures. 