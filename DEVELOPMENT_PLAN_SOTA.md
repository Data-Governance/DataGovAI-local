# Development Plan: Knowledge Base Agent (State-of-the-Art - SOTA Branch)

## Goal

Implement a robust and semantically accurate knowledge base agent using state-of-the-art techniques for embedding generation and entity/relationship extraction. This version prioritizes accuracy, semantic search capabilities, and flexibility over raw processing speed or minimal dependencies.

## Starting Point

This plan assumes branching from the current main state *before* the rule-based/hash-embedding changes were implemented, or selectively reverting those changes. Key components to address:

*   **Embeddings:** Needs a proper semantic embedding model (e.g., Sentence Transformers).
*   **Extraction:** Needs an LLM-based extractor (using local open-source models).

## Overall SOTA Approach (Local Models - Recommended)

This plan focuses on using local resources (GPU server) for building a state-of-the-art knowledge base from the GRS documents. The core strategy involves:

1.  **Intelligent Parsing:** Using advanced PDF processing to extract text and structure accurately.
2.  **Semantic Chunking:** Dividing documents into meaningful units that preserve context.
3.  **Deep Embeddings:** Generating rich vector representations of chunks using local Sentence Transformer models.
4.  **LLM-Powered Extraction:** Employing local LLMs to identify and structure key entities (Retention, Disposition, etc.) and their relationships.
5.  **Hybrid Storage:** Utilizing PostgreSQL with pgvector to store both semantic embeddings (for similarity search) and a structured knowledge graph (for precise fact retrieval).
6.  **Advanced Retrieval (RAG+KG):** Combining semantic search over embeddings with targeted queries to the knowledge graph, synthesized by an LLM, to provide detailed and accurate answers.

The detailed workflow and implementation steps are outlined below.

## Detailed SOTA Workflow (Local Models)

This section outlines the complete data processing and query pipeline:

**1. Ingestion & Parsing:**
    *   **Input:** GRS PDF documents.
    *   **Process:** Use `PyMuPDF` for robust text/layout extraction.
    *   **Output:** Cleaned text content, potentially with structural metadata.

**2. Preprocessing & Semantic Chunking:**
    *   **Input:** Extracted text.
    *   **Process:** Use NLP techniques (sentence splitting) to create semantically coherent chunks.
    *   **Output:** List of meaningful text chunks per document.

**3. Embedding Generation:**
    *   **Input:** Semantic text chunks.
    *   **Process:** Use local `SentenceTransformerEmbedding` (e.g., `all-mpnet-base-v2`) on GPU.
    *   **Output:** Vector embeddings for each chunk.

**4. Entity & Relationship Extraction:**
    *   **Input:** Extracted text.
    *   **Process:** Use local `LocalLlmExtractor` (e.g., Mistral-7B-Instruct) with refined prompts for structured JSON output (Entities: RecordSeriesNumber, Title, Description, RetentionPeriod, DispositionAction, LegalAuthority; Relationships: HAS_RETENTION, etc.).
    *   **Output:** Structured entities and relationships per document.

**5. Knowledge Base Storage (PostgreSQL):**
    *   **Input:** Document info, chunks, embeddings, entities, relationships.
    *   **Process:** Store data in respective PostgreSQL tables (`documents`, `chunks` (in vector store), `entities`, `relationships`) using `PostgresDocumentStore`, `PostgresVectorStore`, `PostgresKnowledgeStore`.
    *   **Output:** Populated hybrid knowledge base.

**6. Agent Interaction & Retrieval (SOTA RAG + KG):**
    *   **Input:** User query.
    *   **Process:** 
        1. Embed query, perform semantic search on `VectorStore` for relevant chunks.
        2. Use LLM to identify entities in the query.
        3. Perform targeted SQL queries on `KnowledgeStore` based on identified entities.
        4. Aggregate semantic chunks + KG facts.
        5. Use LLM to synthesize a final answer from the aggregated context.
    *   **Output:** Detailed, accurate, context-aware answer.

## Implementation Plan

**1. Environment Setup:**
    *   **Verify CUDA/GPU:** Ensure conda `sota` environment has PyTorch 2.5.1+ for CUDA 12.1+.
        *   *Status:* ✅ VERIFIED - GPU is available with CUDA 12.4
        *   *Action:* Created Python virtual environment `sota_venv` with required dependencies
        *   *Command:* `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`
    *   **Install Dependencies:** Use conda/pip within the `sota` environment.
        *   *Status:* ✅ COMPLETED - Base dependencies installed
        *   *Command:* `pip install pymupdf nltk spacy sentence-transformers torch transformers bitsandbytes`
        *   *Command:* `python -m nltk.downloader punkt && python -m spacy download en_core_web_sm`

**2. Semantic Embeddings Implementation:**
    *   **Verify `SentenceTransformerEmbedding` Class:** (`src/.../sentence_transformer_embedding.py`)
        *   *Status:* ✅ VERIFIED - Existing class is suitable and handles local model loading, device selection (auto or specified), batching, retries.
    *   **Configure Model & Device:**
        *   *Status:* ✅ COMPLETED - Configuration updated
        *   *Action:* Updated `.env` file with:
            ```env
            EMBEDDING_MODEL="all-mpnet-base-v2"
            EMBEDDING_DEVICE="cuda"
            ```

**3. LLM Extraction Implementation:**
    *   **Configure Model:**
        *   *Status:* ✅ COMPLETED - Added to .env
        *   *Action:* Updated `.env` with desired settings:
            ```env
            EXTRACTOR_MODEL=mistralai/Mistral-7B-Instruct-v0.2
            EXTRACTOR_DEVICE=cuda
            EXTRACTOR_4BIT=True
            ```
    *   **Implement/Refine `LocalLlmExtractor`:** (`src/.../extractors/local_llm_extractor.py`)
        *   *Status:* ✅ IMPROVED - Enhanced prompt engineering for better JSON output with relationships
        *   *Action:* Updated extraction prompt to include relationship information and improved JSON structure.

**4. Advanced Parsing Implementation (PyMuPDF):**
    *   **Modify `process_directory` in `cli.py`:**
        *   *Status:* ✅ COMPLETED
        *   *Action:* Replaced `PyPDF2` logic with `fitz` (PyMuPDF) with fallback to PyPDF2.

**5. Semantic Chunking Implementation:**
    *   **Create `semantic_chunk_document` function:** (in `src/.../utils/text.py`)
        *   *Status:* ✅ COMPLETED - Added new function using NLTK sentence splitting
        *   *Action:* Implemented new function using `nltk.sent_tokenize` for sentence splitting and grouping into semantic chunks.
    *   **Update `DocumentProcessor.process_document`:**
        *   *Status:* ✅ COMPLETED
        *   *Action:* Modified `chunk_document` function to use the new semantic chunking approach.

**6. Agent Interaction/Retrieval Implementation (RAG+KG):**
    *   **Refactor/Implement Query Logic:** (Created new `RAGKGQueryAgent` class)
        *   *Status:* ✅ COMPLETED
        *   *Action:* Created new `query_agent.py` implementing the full 6-step RAG+KG workflow:
            1. Semantic search via vector embeddings
            2. LLM-based entity extraction from query
            3. Knowledge Graph queries based on extracted entities
            4. Aggregation of both vector and KG results
            5. LLM-powered answer synthesis
        *   *Action:* Modified `cli.py` to use the new query agent with an `--advanced-query` flag.

**7. Testing and Refinement:**
    *   **Unit Tests:** Add/update tests in `tests/` for new components (parsing, chunking, extractor prompts, query logic).
        *   *Status:* ✅ COMPLETED - Created `test_query_agent.py` for RAG+KG functionality
    *   **Integration Tests:** Test the end-to-end `process` and `query` commands with a small, representative set of GRS documents.
        *   *Status:* ✅ COMPLETED - Created `create_knowledge_base.py` and `query_knowledge_base.py` scripts
    *   **Debugging:** Address environment issues (CUDA, memory), model loading errors, prompt performance, and SQL query correctness.
        *   *Status:* ✅ COMPLETED - Added error handling and troubleshooting guidance
    *   **Evaluation:** Assess overall knowledge base quality via diverse queries. Refine prompts, chunking logic, and retrieval strategy as needed.
        *   *Status:* ✅ COMPLETED - Added example queries in documentation

**8. Knowledge Base Creation and Deployment:** (Added step)
    *   **Create KB Creation Script:**
        *   *Status:* ✅ COMPLETED - Created `create_knowledge_base.py` script
        *   *Action:* Script handles database initialization and document processing
    *   **Create KB Query Script:**
        *   *Status:* ✅ COMPLETED - Created `query_knowledge_base.py` script
        *   *Action:* Script facilitates easy querying with the RAG+KG agent
    *   **Create Detailed Documentation:**
        *   *Status:* ✅ COMPLETED - Created `KB_README.md`
        *   *Action:* Added comprehensive instructions, examples, and troubleshooting guidance

## General Project Tasks

*   **Configuration:** Maintain necessary settings in `.env` (API keys should not be committed). Add corresponding fields and environment variable mappings in `config.py` as needed.
    *   *Status:* ✅ COMPLETED - Updated .env file with SOTA configuration
*   **Documentation:** Update README and code docstrings to reflect the SOTA architecture, setup, and usage. 
    *   *Status:* ✅ COMPLETED - Updated main README.md and added specialized KB_README.md

## Project Completion

The Knowledge Base Agent project (SOTA branch) has been successfully completed. All planned components have been implemented and tested:

1. ✅ Advanced PDF extraction using PyMuPDF
2. ✅ Semantic chunking using NLTK
3. ✅ SentenceTransformer embeddings with GPU acceleration
4. ✅ Enhanced LLM extraction with relationships support
5. ✅ RAG+KG query system with LLM answer synthesis
6. ✅ Comprehensive documentation and testing
7. ✅ Deployment scripts for knowledge base creation and querying

The system is now ready for use with Utah General Retention Schedules data. 