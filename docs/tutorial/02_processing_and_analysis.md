# Chapter 3: Processing and Analysis

## Introduction

Processing and analysis form the backbone of knowledge extraction in a knowledge base agent. This chapter explores the techniques and tools used to transform raw content into structured knowledge.

## Document Processing

Document processing involves converting raw input into clean, structured text suitable for further analysis.

### Text Extraction Methods

1. **File Format Handling**
   - PDF extraction (PyPDF2, pdfminer)
   - Office documents (python-docx)
   - HTML parsing (BeautifulSoup)
   - Image text extraction (Tesseract OCR)

2. **Text Cleaning**
   - Unicode normalization
   - Special character handling
   - Whitespace normalization
   - Language detection

3. **Text Segmentation**
   - Sentence splitting
   - Paragraph detection
   - Section identification
   - Table extraction

### Technology Comparison

| Feature | Tika | Textract | PDFMiner | DocX |
|---------|------|----------|-----------|------|
| Format Support | Extensive | Limited | PDF Only | DOCX Only |
| Accuracy | High | High | Medium | High |
| Speed | Medium | Fast | Medium | Fast |
| Maintenance | Active | AWS Managed | Active | Active |
| Cost | Free | Pay per use | Free | Free |

### Implementation Examples

1. **Basic Document Processor**
```python
class DocumentProcessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
    def clean_text(self, text: str) -> str:
        # Normalize unicode
        text = unicodedata.normalize("NFKC", text)
        
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        
        # Remove special characters
        text = re.sub(r"[^\w\s.,!?-]", "", text)
        
        return text.strip()
        
    def split_into_sentences(
        self,
        text: str
    ) -> List[str]:
        doc = self.nlp(text)
        return [
            str(sent).strip()
            for sent in doc.sents
            if str(sent).strip()
        ]
        
    def process_document(
        self,
        content: str,
        clean: bool = True
    ) -> Dict[str, Any]:
        if clean:
            content = self.clean_text(content)
            
        sentences = self.split_into_sentences(content)
        
        return {
            "content": content,
            "sentences": sentences,
            "sentence_count": len(sentences),
            "processed_at": datetime.utcnow()
        }
```

2. **Advanced Document Processor**
```python
class AdvancedDocumentProcessor:
    def __init__(self):
        self.basic_processor = DocumentProcessor()
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn"
        )
        self.classifier = pipeline(
            "text-classification",
            model="facebook/bart-large-mnli"
        )
        
    async def process_document(
        self,
        content: str,
        extract_metadata: bool = True
    ) -> Dict[str, Any]:
        # Basic processing
        basic_result = self.basic_processor.process_document(
            content
        )
        
        # Generate summary
        summary = await self.summarize(content)
        
        # Classify content
        category = await self.classify(content)
        
        # Extract metadata
        metadata = (
            await self.extract_metadata(content)
            if extract_metadata
            else {}
        )
        
        return {
            **basic_result,
            "summary": summary,
            "category": category,
            "metadata": metadata
        }
        
    async def summarize(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30
    ) -> str:
        summary = await self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return summary[0]["summary_text"]
        
    async def classify(
        self,
        text: str
    ) -> str:
        result = await self.classifier(
            text,
            candidate_labels=[
                "technical",
                "business",
                "academic",
                "general"
            ]
        )
        return result[0]["label"]
```

## Entity Recognition

Entity recognition identifies and classifies named entities in text.

### Approaches

1. **Rule-Based NER**
   - Regular expressions
   - Gazetteer lists
   - Pattern matching
   - Custom rules

2. **Machine Learning NER**
   - Statistical models (CRF)
   - Deep learning (BERT, SpaCy)
   - Custom trained models
   - Ensemble approaches

### Technology Comparison

| Feature | SpaCy | NLTK | Stanford NER | Flair |
|---------|-------|------|--------------|-------|
| Accuracy | High | Medium | High | Very High |
| Speed | Fast | Medium | Slow | Slow |
| Ease of Use | High | Medium | Low | Medium |
| Customization | Good | Limited | Good | Excellent |
| Language Support | Many | Many | Limited | Many |

### Implementation Examples

1. **Rule-Based Entity Extractor**
```python
class RuleBasedEntityExtractor:
    def __init__(self):
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\+?1?\d{9,15}\b",
            "url": r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "date": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
        }
        
    def extract_entities(
        self,
        text: str
    ) -> Dict[str, List[str]]:
        entities = {}
        
        for entity_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            entities[entity_type] = [
                match.group()
                for match in matches
            ]
            
        return entities
        
    def deduplicate_entities(
        self,
        entities: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        return {
            k: list(set(v))
            for k, v in entities.items()
        }
```

2. **ML-Based Entity Extractor**
```python
class MLEntityExtractor:
    def __init__(
        self,
        model: str = "en_core_web_trf"
    ):
        self.nlp = spacy.load(model)
        
    async def extract_entities(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        doc = await self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
            
        return self.deduplicate_entities(entities)
        
    def deduplicate_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity["text"], entity["label"])
            if key not in seen:
                seen.add(key)
                unique.append(entity)
                
        return unique
```

## Relationship Extraction

Relationship extraction identifies connections between entities in text.

### Approaches

1. **Pattern-Based**
   - Regular expressions
   - Dependency parsing
   - Syntactic patterns
   - Rule-based systems

2. **Machine Learning**
   - Supervised learning
   - Distant supervision
   - Neural networks
   - Joint entity and relation extraction

### Implementation Examples

1. **Pattern-Based Relationship Extractor**
```python
class PatternRelationshipExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf")
        self.patterns = [
            {
                "pattern": [
                    {"POS": "PROPN"},
                    {"LEMMA": "be"},
                    {"POS": "DET", "OP": "?"},
                    {"POS": "NOUN"}
                ],
                "label": "is_a"
            },
            {
                "pattern": [
                    {"POS": "PROPN"},
                    {"LEMMA": "work"},
                    {"LEMMA": "for"},
                    {"POS": "PROPN"}
                ],
                "label": "works_for"
            }
        ]
        
    async def extract_relationships(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        doc = await self.nlp(text)
        relationships = []
        
        for sent in doc.sents:
            for pattern in self.patterns:
                matches = self.matcher(sent, pattern)
                relationships.extend(matches)
                
        return relationships
```

2. **ML-Based Relationship Extractor**
```python
class MLRelationshipExtractor:
    def __init__(
        self,
        model_name: str = "jean-baptiste/roberta-large-ner-english"
    ):
        self.entity_extractor = MLEntityExtractor()
        self.relation_model = pipeline(
            "text-classification",
            model=model_name
        )
        
    async def extract_relationships(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        # Extract entities
        entities = await self.entity_extractor.extract_entities(
            text
        )
        
        # Extract relationships between entities
        relationships = []
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                relation = await self.classify_relationship(
                    text,
                    e1,
                    e2
                )
                if relation:
                    relationships.append({
                        "from": e1,
                        "to": e2,
                        "relation": relation
                    })
                    
        return relationships
        
    async def classify_relationship(
        self,
        text: str,
        entity1: Dict[str, Any],
        entity2: Dict[str, Any]
    ) -> Optional[str]:
        # Extract text between entities
        start = min(entity1["end"], entity2["end"])
        end = max(entity1["start"], entity2["start"])
        between_text = text[start:end]
        
        # Classify relationship
        result = await self.relation_model(
            between_text,
            candidate_labels=[
                "works_for",
                "located_in",
                "part_of",
                "related_to"
            ]
        )
        
        return result[0]["label"]
```

## Embedding Generation

Embedding generation converts text into dense vector representations.

### Approaches

1. **Traditional Methods**
   - TF-IDF
   - Word2Vec
   - GloVe
   - FastText

2. **Modern Transformers**
   - BERT
   - RoBERTa
   - DPR
   - Sentence-BERT

### Technology Comparison

| Feature | Sentence-BERT | OpenAI | DPR | Word2Vec |
|---------|---------------|--------|-----|----------|
| Quality | High | Very High | High | Medium |
| Speed | Fast | API Latency | Medium | Very Fast |
| Cost | Free | Pay per token | Free | Free |
| Dimension | 768/384 | 1536 | 768 | Configurable |

### Implementation Examples

1. **Basic Embedding Generator**
```python
class EmbeddingGenerator:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.model = SentenceTransformer(model_name)
        
    async def generate_embedding(
        self,
        text: str
    ) -> List[float]:
        return await self.model.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        
    async def generate_batch_embeddings(
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

2. **Advanced Embedding Generator**
```python
class AdvancedEmbeddingGenerator:
    def __init__(self):
        self.models = {
            "default": SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            ),
            "multilingual": SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ),
            "semantic": SentenceTransformer(
                "sentence-transformers/msmarco-distilbert-base-v4"
            )
        }
        
    async def generate_embedding(
        self,
        text: str,
        model_type: str = "default"
    ) -> List[float]:
        model = self.models.get(
            model_type,
            self.models["default"]
        )
        
        return await model.encode(
            text,
            convert_to_tensor=False,
            normalize_embeddings=True
        )
        
    async def generate_multi_embeddings(
        self,
        text: str
    ) -> Dict[str, List[float]]:
        embeddings = {}
        
        for model_type, model in self.models.items():
            embeddings[model_type] = await model.encode(
                text,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            
        return embeddings
```

## Best Practices

1. **Document Processing**
   - Validate input formats
   - Handle encoding issues
   - Implement error recovery
   - Maintain processing logs

2. **Entity Recognition**
   - Use domain-specific models
   - Validate entity types
   - Handle overlapping entities
   - Consider context

3. **Relationship Extraction**
   - Validate relationship types
   - Handle bidirectional relations
   - Consider temporal aspects
   - Maintain confidence scores

4. **Embedding Generation**
   - Choose appropriate models
   - Implement caching
   - Handle long texts
   - Normalize embeddings

## Conclusion

Effective processing and analysis are crucial for building a robust knowledge base agent. Consider:

1. **Quality vs. Speed**
   - Processing accuracy
   - Response time requirements
   - Resource constraints

2. **Scalability**
   - Batch processing
   - Parallel execution
   - Resource management

3. **Maintenance**
   - Model updates
   - Error monitoring
   - Performance tracking

Choose appropriate tools and techniques based on your specific requirements, and implement proper error handling and monitoring to ensure reliable operation. 