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
        *   *Status:* Already verified.
        *   *Command:* `conda activate sota`
        *   *Command:* `python -c \"import torch; print(torch.cuda.is_available(), torch.version.cuda)\"`
    *   **Install Dependencies:** Use conda/pip within the `sota` environment.
        *   *Status:* Base dependencies (`transformers`, `torch`, `sentence-transformers`, `bitsandbytes`, etc.) installed. Need to add SOTA requirements.
        *   *Command (Add these):* `pip install pymupdf nltk spacy`
        *   *Command (Download models):* `python -m spacy download en_core_web_sm` (or other spaCy models)
        *   *Command (Download NLTK data):* `python -m nltk.downloader punkt` (run Python interpreter and execute `import nltk; nltk.download('punkt')`)

**2. Semantic Embeddings Implementation:**
    *   **Verify `SentenceTransformerEmbedding` Class:** (`src/.../sentence_transformer_embedding.py`)
        *   *Status:* Existing class is suitable and handles local model loading, device selection (auto or specified), batching, retries. No changes needed.
    *   **Configure Model & Device:**
        *   *Status:* Configuration needs update.
        *   *Action:* Edit/Create `.env` file:
            ```env
            EMBEDDING_MODEL="all-mpnet-base-v2"
            EMBEDDING_DEVICE="cuda"
            ```
        *   *Action:* Update `EmbeddingConfig` in `src/.../config.py`:
            *   Add `device: Optional[str] = Field(default=None, ...)`
            *   Add `'EMBEDDING_DEVICE': ('embedding', 'device')` to `Config.from_env` mapping.
    *   **Verify CLI Integration:** (`src/.../cli.py`)
        *   *Status:* `create_processor` correctly passes device setting from config. No changes needed after config update.
    *   **Test Embedding Loading:**
        *   *Action:* Run a simple process command (`python -m knowledge_base_agent process ...`) and check logs for successful model loading on CUDA.

**3. LLM Extraction Implementation:**
    *   **Configure Model:**
        *   *Status:* Configurable via `.env` (`EXTRACTOR_MODEL`, `EXTRACTOR_DEVICE`, `EXTRACTOR_4BIT`).
        *   *Action:* Ensure `.env` has desired settings (e.g., `mistralai/Mistral-7B-Instruct-v0.2`, `cuda`, `True`).
    *   **Implement/Refine `LocalLlmExtractor`:** (`src/.../extractors/local_llm_extractor.py`)
        *   *Status:* Basic implementation exists, loads model, uses `BitsAndBytesConfig`, has basic prompt.
        *   *Action (Refinement):* Improve prompt engineering for more robust JSON output, including specified GRS entities and relationships (e.g., `HAS_RETENTION`). Ensure strict JSON parsing.
    *   **Update `DocumentProcessor`:** (`src/.../processor.py`)
        *   *Status:* Initializes extractor and calls `extract_entities` with regex fallback.
        *   *Action (Refinement):* Modify `process_document` to parse JSON output from extractor reliably. Store extracted entities *and* relationships in `KnowledgeStore`. Minimize reliance on regex fallback.
    *   **Verify `cli.py` Integration:** (`src/.../cli.py`)
        *   *Status:* `create_processor` correctly instantiates extractor from config. No changes needed.
    *   **Test Extraction:** Process a sample document and verify structured entities/relationships are created in the knowledge store.

**4. Advanced Parsing Implementation (PyMuPDF):**
    *   **Modify `process_directory` in `cli.py`:**
        *   *Status:* Currently uses `PyPDF2`.
        *   *Action:* Replace `PyPDF2` logic with `fitz` (PyMuPDF). Add import `import fitz`. Handle errors.
    *   **Test Parsing:** Process various GRS PDFs and compare extracted text quality.

**5. Semantic Chunking Implementation:**
    *   **Create `semantic_chunk_document` function:** (e.g., in `src/.../utils/text.py`)
        *   *Status:* Does not exist. Current chunking (`chunk_document` in `processor.py`) uses `tiktoken`.
        *   *Action:* Implement new function using `nltk.sent_tokenize` or `spacy` sentence splitting and logic for grouping sentences into semantic chunks.
    *   **Update `DocumentProcessor.process_document`:**
        *   *Action:* Replace call to `chunk_document` with the new `semantic_chunk_document`.
    *   **Test Chunking:** Process a document and examine the generated chunks for coherence.

**6. Agent Interaction/Retrieval Implementation (RAG+KG):**
    *   **Refactor/Implement Query Logic:** (Likely refactor `DocumentProcessor.search` or create new `QueryAgent` class)
        *   *Status:* Existing `search` and `query` methods primarily perform vector search. `get_entity_context` is separate.
        *   *Action:* Implement the full 6-step RAG+KG workflow: Semantic search -> LLM query analysis -> KG query -> Context aggregation -> LLM synthesis. This requires significant new logic, including LLM calls for analysis/synthesis and SQL query construction/execution.
    *   **Update `query_knowledge_base` in `cli.py`:**
        *   *Action:* Ensure it calls the new/refactored query method and handles the synthesized response.
    *   **Test Querying:** Run diverse queries and evaluate the quality, accuracy, and grounding of the synthesized answers.

**7. Testing and Refinement:**
    *   **Unit Tests:** Add/update tests in `tests/` for new components (parsing, chunking, extractor prompts, query logic).
    *   **Integration Tests:** Test the end-to-end `process` and `query` commands with a small, representative set of GRS documents.
    *   **Debugging:** Address environment issues (CUDA, memory), model loading errors, prompt performance, and SQL query correctness.
    *   **Evaluation:** Assess overall knowledge base quality via diverse queries. Refine prompts, chunking logic, and retrieval strategy as needed.

## General Project Tasks

*   **Branching:** Work on the `sota` branch (or a dedicated feature branch off `sota`).
*   **Configuration:** Maintain necessary settings in `.env` (API keys should not be committed). Add corresponding fields and environment variable mappings in `config.py` as needed.
*   **Documentation:** Update README and code docstrings to reflect the SOTA architecture, setup, and usage. 