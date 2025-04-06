# RAG+KG Query Agent

The RAG+KG Query Agent combines Retrieval-Augmented Generation (RAG) with Knowledge Graph (KG) querying for advanced, accurate information retrieval and answer synthesis.

## Overview

The `RAGKGQueryAgent` implements a hybrid query approach that leverages both:

1. **Vector Similarity Search**: Finding semantically similar text chunks using embeddings
2. **Knowledge Graph Queries**: Precise retrieval of structured entities and relationships

This combined approach provides more accurate and comprehensive answers than either method alone.

## How It Works

### Query Processing Pipeline

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │     │                │
│  Embed Query   │────▶│ Vector Search  │────▶│ Entity         │────▶│ Knowledge Graph│
│                │     │                │     │ Extraction     │     │ Queries        │
│                │     │                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
                                                                            │
                                                                            │
                                                                            ▼
┌────────────────┐     ┌────────────────┐
│                │     │                │
│  Answer        │◀────│  Result        │
│  Synthesis     │     │  Aggregation   │
│                │     │                │
└────────────────┘     └────────────────┘
```

### Key Methods

1. `query(query, top_k, min_score)`: Main method to process a user query
   - Performs semantic search
   - Extracts entities from the query
   - Executes knowledge graph queries
   - Synthesizes the final answer

2. `_extract_entities_from_query(query)`: Uses an LLM to identify entities in the query
   - Identifies record series numbers, retention periods, disposition actions, etc.
   - Returns a structured dictionary of entities

3. `_execute_kg_query(query_info)`: Performs targeted lookups in the knowledge graph
   - Supports exact matches and similarity-based searches
   - Returns entities matching the query criteria

4. `_synthesize_answer(query, vector_results, kg_results)`: Generates the final answer
   - Formats retrieved information into a coherent prompt
   - Uses an LLM to synthesize a comprehensive answer

## LLM Integration

The agent uses a local LLM (default: Mistral-7B-Instruct) for:

1. **Entity Extraction**: Identifying key entities in the user query
2. **Answer Synthesis**: Generating the final answer from retrieved context

Advanced features include:
- 4-bit quantization for reduced VRAM usage
- Support for both CUDA and CPU execution
- Configurable temperature for generation

## Prompt Templates

### Entity Extraction Prompt

```
Extract entities from the following query that could be used to search a knowledge base about Utah General Retention Schedules (GRS).

Entities to extract:
- record_series_number: Any record series identifiers (e.g., "RS-1234")
- retention_period: References to retention periods (e.g., "3 years", "permanent")
- disposition_action: References to disposition actions (e.g., "destroy", "transfer to archives")
- legal_authority: References to legal authorities (e.g., "UCA 63G-2")

Query:
{query}

Respond with a JSON object containing the extracted entities. Use null for missing entities:
{
    "record_series_number": string or null,
    "retention_period": string or null,
    "disposition_action": string or null,
    "legal_authority": string or null
}
```

### Answer Synthesis Prompt

```
You are a knowledgeable assistant answering questions about Utah General Retention Schedules (GRS).

Use the following information to answer the user's question. 
If the information doesn't contain the answer, say so honestly - DO NOT make up information.

User Query: {query}

Vector Search Results (semantic search):
{vector_results}

Knowledge Graph Results (entity-based search):
{kg_results}

Provide a detailed, accurate answer based ONLY on the information provided above.
```

## Usage Example

```python
from src.knowledge_base_agent.query_agent import RAGKGQueryAgent
from src.knowledge_base_agent.processor import DocumentProcessor
from src.knowledge_base_agent.config import get_config

# Create processor and query agent
config = get_config()
processor = DocumentProcessor.from_config(config)
query_agent = RAGKGQueryAgent(
    processor=processor,
    llm_model_name="mistralai/Mistral-7B-Instruct-v0.2",
    device="cuda",
    use_4bit=True
)

# Execute query
results = query_agent.query(
    query="What is the retention period for financial records?",
    top_k=5,
    min_score=0.6
)

# Output the answer
print(results["answer"])
```

## Configuration Parameters

| Parameter        | Description                          | Default Value                      |
|------------------|--------------------------------------|-----------------------------------|
| `llm_model_name` | HuggingFace model to use            | "mistralai/Mistral-7B-Instruct-v0.2" |
| `device`         | Device to run on (cuda/cpu)         | Auto-detected                      |
| `use_4bit`       | Use 4-bit quantization              | True                               |
| `temperature`    | Generation temperature               | 0.1                                |
| `top_k`          | Number of vector results            | 5                                  |
| `min_score`      | Minimum similarity score (0-1)      | 0.6                                |

## Implementation Details

The `RAGKGQueryAgent` is implemented in `src/knowledge_base_agent/query_agent.py` and interfaces with:

- `DocumentProcessor` for access to the storage layers
- Local LLMs via Hugging Face Transformers
- BitsAndBytes for quantization support 