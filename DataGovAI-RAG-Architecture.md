# DataGovAI RAG System Architecture

This document explains the Retrieval-Augmented Generation (RAG) system architecture used in the DataGovAI application, designed for recreating with a Streamlit UI using LlamaIndex.

## Overview

DataGovAI uses a RAG approach to answer questions about Utah's General Retention Schedules (GRS). The system combines vector search with traditional information retrieval to provide accurate, contextually relevant responses.

## System Components

### 1. Document Processing Pipeline

The document pipeline handles ingestion, processing, and storage of documents:

- **Document Loading**: PDF documents are loaded using PyMuPDF (fitz)
- **Text Extraction**: Extracts text content from documents
- **Semantic Chunking**: Documents are split into semantically meaningful chunks using NLTK's sentence tokenizer
- **Embedding Generation**: Chunks are embedded using Sentence Transformers (default: all-mpnet-base-v2)
- **Database Storage**: Document content and vector embeddings are stored in PostgreSQL with pgvector extension

### 2. Vector Database Schema

The system uses PostgreSQL with pgvector for storing documents and their embeddings:

- **Documents Table**: Stores original documents and metadata
  - `document_id`: Unique document identifier
  - `title`: Document title
  - `source_url`: Source URL for attribution
  - `metadata`: JSON metadata (document type, version, etc.)

- **Chunks Table**: Stores document chunks and embeddings
  - `chunk_id`: Unique chunk identifier
  - `document_id`: Foreign key to documents table
  - `content`: Text content of the chunk
  - `embedding`: Vector representation (768 dimensions)

### 3. Query Processing

When a user submits a query:

1. **Query Embedding**: The query is embedded using the same model used for document embeddings
2. **Vector Search**: The system performs similarity search to find the most relevant chunks
3. **Filtering**: Results are filtered based on similarity threshold (configured by `SIMILARITY_CUTOFF`)
4. **Context Building**: Relevant chunks and their source documents are retrieved and assembled
5. **Response Generation**: The context and query are sent to an LLM (OpenAI GPT-4) to generate a response

### 4. Query Classification and Routing

The system distinguishes between different types of queries:

- **GRS-Related Queries**: Questions about retention schedules that should trigger vector search retrieval
- **Follow-up Questions**: Contextual questions that refer to previous conversation turns
- **General Questions**: Non-domain questions that don't require knowledge base access

Classification is performed using:
1. Keyword matching for domain-specific terms
2. Semantic similarity to known GRS question patterns
3. Contextual analysis for detecting follow-up questions (pronoun detection, etc.)

Based on classification, queries are routed to:
- RAG pipeline for GRS-related queries (retrieves from knowledge base)
- Conversation memory access for follow-up questions
- Direct LLM response for general questions (without retrieval)

### 5. Conversation Memory Management

The system maintains conversation history using:

- Session-based memory for short-term context
- Conversation summarization for long conversations
- Entity extraction and tracking across conversation turns
- Memory-augmented prompting to maintain context with GPT-4

### 6. User Interface Components

The UI is built with Streamlit and includes:

- Chat interface for user interaction
- Source attribution for transparency
- Conversation history management
- Handling of follow-up questions
- Query type indicators showing processing mode (RAG vs. direct)

## Key Implementation Features

1. **Multi-GPU Support**: For processing large document collections, the system supports multi-GPU processing
2. **Semantic Chunking**: Documents are chunked based on semantic boundaries rather than fixed lengths
3. **Similarity Thresholding**: Only results above a similarity threshold are included in context
4. **Source Attribution**: System tracks and includes source documents in responses
5. **Conversation Management**: Maintains conversation history for contextual follow-up questions
6. **Query Classification**: Intelligently routes queries to appropriate processing pipelines
7. **Testing Framework**: Supports evaluation against classified test questions

## Configuration Parameters

The system is highly configurable with environment variables:

- `EMBEDDING_MODEL`: Model used for generating document and query embeddings (default: all-mpnet-base-v2)
- `TOP_K`: Number of results to retrieve from vector search (default: 5)
- `SIMILARITY_CUTOFF`: Minimum similarity score for inclusion (default: 0.6)
- `LLM_MODEL`: OpenAI model to use for response generation (default: gpt-4o-mini)
- `MAX_CHUNK_SIZE`: Maximum size of document chunks (default: 2000 characters)
- `MIN_CHUNK_SIZE`: Minimum size of document chunks (default: 200 characters)
- `OVERLAP_SIZE`: Overlap between consecutive chunks (default: 100 characters)
- `CONVERSATION_MEMORY_LIMIT`: Maximum number of conversation turns to retain (default: 10)
- `GRS_CLASSIFICATION_THRESHOLD`: Threshold for classifying as GRS-related (default: 0.75)

## Implementation with LlamaIndex and Streamlit

To recreate this system with LlamaIndex and Streamlit:

1. **Database Setup**:
   - PostgreSQL database with pgvector extension
   - Tables for documents and chunks with vector embeddings

2. **Document Processing Pipeline**:
   - Use LlamaIndex's document loaders for PDF ingestion
   - Configure LlamaIndex to use Sentence Transformers for embeddings
   - Implement semantic chunking with customizable parameters

3. **Vector Store Integration**:
   - Use LlamaIndex's PostgresVectorStore for vector storage and retrieval
   - Configure similarity search with appropriate thresholds

4. **Query Engine**:
   - Create a RetrieverQueryEngine with response synthesizer
   - Configure the query engine to return sources for attribution

5. **Query Classification**:
   - Implement a query classifier using GPT-4 or a fine-tuned model
   - Set up routing logic to appropriate processing pipelines

6. **Conversation Memory**:
   - Use LlamaIndex's ChatEngine with memory
   - Implement entity extraction for context tracking

7. **Streamlit UI**:
   - Chat interface for query input
   - Display area for responses with source attribution
   - Session state management for conversation history
   - Query type indicators for transparency

## Query Classification Implementation

The query classification system can be implemented using:

```python
from llama_index.core.llms import OpenAI
from llama_index.core import Settings
import re

# Define common GRS-related terms for keyword matching
GRS_KEYWORDS = [
    "retention", "schedule", "records", "document", "archive", 
    "compliance", "regulatory", "disposition", "storage"
]

def is_grs_related(query: str, llm: OpenAI = None, threshold: float = 0.75) -> bool:
    """
    Determine if a query is related to GRS using a combination of:
    1. Keyword matching
    2. LLM-based classification (if available)
    """
    # Simple keyword matching
    query_lower = query.lower()
    keyword_match = any(keyword in query_lower for keyword in GRS_KEYWORDS)
    
    # If we have a strong keyword match, return immediately
    if keyword_match:
        return True
    
    # Use LLM for more nuanced classification if available
    if llm:
        prompt = f"""
        Determine if the following query is related to General Retention Schedules (GRS) 
        or document/records management policies. 
        
        Query: "{query}"
        
        Answer with only 'yes' or 'no'.
        """
        
        response = llm.complete(prompt).text.strip().lower()
        return response == "yes"
    
    return False

def is_followup_question(query: str, conversation_history: list) -> bool:
    """
    Determine if a query is a follow-up to previous conversation.
    """
    if not conversation_history:
        return False
    
    # Check for pronouns and other follow-up indicators
    followup_indicators = ["it", "they", "them", "those", "that", "these", "this", "the"]
    query_tokens = query.lower().split()
    
    # Simple pronoun detection
    if any(token in followup_indicators for token in query_tokens):
        return True
    
    # Check if query is very short (likely a follow-up)
    if len(query_tokens) <= 3:
        return True
    
    return False

def route_query(query: str, conversation_history: list, llm: OpenAI):
    """
    Route query to appropriate processing pipeline.
    """
    if is_followup_question(query, conversation_history):
        return "followup"
    elif is_grs_related(query, llm):
        return "grs"
    else:
        return "general"
```

## Conversation Memory Implementation

```python
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import ChatEngine, ServiceContext

def create_chat_engine_with_memory(index, llm, memory_limit=10):
    """Create a chat engine with conversation memory."""
    memory = ChatMemoryBuffer.from_defaults(token_limit=4096)
    
    service_context = ServiceContext.from_defaults(llm=llm)
    
    chat_engine = ChatEngine.from_defaults(
        retriever=index.as_retriever(similarity_top_k=5),
        service_context=service_context,
        memory=memory,
        system_prompt="""
        You are an assistant for the Utah General Retention Schedules (GRS).
        Answer questions based on the retrieved information.
        For questions not about retention schedules, respond based on your general knowledge.
        Always provide source citations when referencing retention schedule information.
        """
    )
    
    return chat_engine
```

## Testing with Classified Sample Questions

Create a testing framework with classified sample questions:

```python
import json
import pandas as pd
from typing import List, Dict

class RAGTester:
    def __init__(self, query_engine, query_classifier):
        self.query_engine = query_engine
        self.query_classifier = query_classifier
        self.test_results = []
    
    def load_test_questions(self, file_path: str) -> List[Dict]:
        """Load test questions from JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def run_tests(self, test_questions: List[Dict]):
        """Run tests on all classified questions."""
        for question in test_questions:
            query = question["query"]
            expected_type = question["type"] # grs, followup, general
            expected_answer = question.get("expected_answer", None)
            conversation = question.get("conversation_history", [])
            
            # Classify the query
            predicted_type = self.query_classifier(query, conversation)
            
            # Process query based on classification
            if predicted_type == "grs":
                response = self.query_engine.query(query)
                answer = response.response
                sources = [node.metadata.get("source", "Unknown") for node in response.source_nodes]
            else:
                # Handle direct or followup queries
                # ...
                answer = "Direct response"
                sources = []
            
            # Record results
            self.test_results.append({
                "query": query,
                "expected_type": expected_type,
                "predicted_type": predicted_type,
                "type_match": expected_type == predicted_type,
                "answer": answer,
                "sources": sources,
                "expected_answer": expected_answer
            })
    
    def get_results_dataframe(self):
        """Return results as a pandas DataFrame."""
        return pd.DataFrame(self.test_results)
    
    def get_summary(self):
        """Return summary statistics."""
        df = self.get_results_dataframe()
        return {
            "total_questions": len(df),
            "type_accuracy": df["type_match"].mean(),
            "grs_questions": len(df[df["expected_type"] == "grs"]),
            "followup_questions": len(df[df["expected_type"] == "followup"]),
            "general_questions": len(df[df["expected_type"] == "general"])
        }
```

## Streamlit UI with Classification Indicators

```python
import streamlit as st
import json
from typing import List, Dict

def setup_streamlit_ui(chat_engine, query_classifier):
    st.title("DataGovAI: Utah GRS Assistant")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Display query type for user messages
            if message.get("query_type") and message["role"] == "user":
                st.caption(f"Query classified as: {message['query_type']}")
            # Display sources for assistant responses if available
            if message.get("sources") and message["role"] == "assistant":
                with st.expander("View Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.write(f"{i}. {source}")
    
    # Sample questions sidebar
    with st.sidebar:
        st.header("Sample Questions")
        
        # Load sample questions from file or define them inline
        sample_questions = [
            {"query": "What is the retention period for financial records?", "type": "grs"},
            {"query": "How long should we keep employee files?", "type": "grs"},
            {"query": "Tell me more about these records", "type": "followup"},
            {"query": "What's the weather like today?", "type": "general"}
        ]
        
        # Display sample questions as buttons
        for q in sample_questions:
            query_type_indicator = {"grs": "📚", "followup": "🔄", "general": "❓"}
            if st.button(f"{query_type_indicator.get(q['type'], '❓')} {q['query']}"):
                st.session_state.input_key = q["query"]
                
    # User input
    user_query = st.chat_input("Ask about Utah's General Retention Schedules", key="input_key")
    
    if user_query:
        # Process user query
        process_query(user_query, chat_engine, query_classifier)
        
def process_query(query: str, chat_engine, query_classifier):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Classify query
    query_type = query_classifier(query, st.session_state.conversation_history)
    
    # Update message with classification
    st.session_state.messages[-1]["query_type"] = query_type
    
    # Add to conversation history
    st.session_state.conversation_history.append({"role": "user", "content": query})
    
    # Process based on query type
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if query_type == "grs":
                # Use RAG for GRS questions
                response = chat_engine.chat(query)
                answer = response.response
                sources = []
                if hasattr(response, "source_nodes"):
                    sources = [f"{node.metadata.get('source', 'Unknown')}" for node in response.source_nodes]
            elif query_type == "followup":
                # Use conversation history for context
                response = chat_engine.chat(query)
                answer = response.response
                sources = []
                if hasattr(response, "source_nodes"):
                    sources = [f"{node.metadata.get('source', 'Unknown')}" for node in response.source_nodes]
            else:
                # Direct to LLM for general questions
                answer = "This is not related to Utah's retention schedules. As a general response: " + chat_engine.chat(query).response
                sources = []
        
        # Display answer
        st.write(answer)
        
        # Store sources if any
        assistant_message = {
            "role": "assistant", 
            "content": answer,
            "sources": sources
        }
        
        # Add to conversation history and messages
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})
        st.session_state.messages.append(assistant_message)
```

## Sample Questions JSON Format

Here's an example format for classified test questions:

```json
{
  "test_questions": [
    {
      "query": "What is the retention period for financial records?",
      "type": "grs",
      "expected_answer_contains": ["7 years", "retention schedule"],
      "expected_sources": ["financial_records.pdf"]
    },
    {
      "query": "Tell me more about these records",
      "type": "followup",
      "conversation_history": [
        {"role": "user", "content": "What is the retention period for financial records?"},
        {"role": "assistant", "content": "Financial records generally have a retention period of 7 years according to Utah's GRS."}
      ]
    },
    {
      "query": "What's the weather like in Salt Lake City?",
      "type": "general"
    }
  ]
}
```

## Key Considerations

1. **Model Selection**: Choose appropriate embedding models based on accuracy and performance requirements
2. **Memory Management**: Implement batching for large document collections
3. **Error Handling**: Robust error handling for various failure scenarios
4. **Conversation Context**: Implement proper conversation history management for follow-up questions
5. **Attribution**: Always include source attribution for RAG responses
6. **Query Classification**: Balance precision and recall in query type identification
7. **Conversation Memory**: Manage token limits for long conversations
8. **Test Coverage**: Ensure test questions cover diverse scenarios and edge cases

By following this architecture, you can recreate the DataGovAI RAG system with Streamlit and LlamaIndex, customizing it for your specific use case and including advanced features like query classification, conversational memory, and a testing framework. 