# Development Plan: Knowledge Base Agent (State-of-the-Art - SOTA Branch)

## Goal

Implement a robust and semantically accurate knowledge base agent using state-of-the-art techniques for embedding generation and entity/relationship extraction. This version prioritizes accuracy, semantic search capabilities, and flexibility over raw processing speed or minimal dependencies.

## Starting Point

This plan assumes branching from the current main state *before* the rule-based/hash-embedding changes were implemented, or selectively reverting those changes. Key components to address:

*   **Embeddings:** Needs a proper semantic embedding model (e.g., Sentence Transformers or OpenAI).
*   **Extraction:** Needs an LLM-based extractor (local open-source model or OpenAI API).

## Option 1: SOTA using Local Models (Recommended for Control & Cost)

This approach utilizes local resources (GPU server) for both embeddings and extraction.

1.  **Setup Environment for Local Models:**
    *   **Verify CUDA/GPU:** Ensure the conda `chatbot` environment has the correct PyTorch version compiled for the server's CUDA version and NVIDIA driver. Resolve any `libcudnn` errors.
        *   *Action:* Use PyTorch installation guide or `conda install pytorch torchvision torchaudio pytorch-cuda=XX.X -c pytorch -c nvidia` (replace XX.X with correct CUDA version).
    *   **Install Transformers:** `pip install transformers accelerate bitsandbytes sentence-transformers` (add other libraries as needed for specific models).

2.  **Implement Semantic Embeddings (Local Sentence Transformer):**
    *   **Revert/Update `SentenceTransformerEmbedding`:** Modify `src/knowledge_base_agent/embeddings/sentence_transformer_embedding.py` to correctly load and use a chosen Sentence Transformer model (e.g., `all-MiniLM-L6-v2`, `all-mpnet-base-v2`).
    *   **Fix Hugging Face Access (if needed):** Address potential 401 errors when downloading models. This might involve:
        *   Logging in via `huggingface-cli login` on the server.
        *   Pre-downloading the model manually to the cache.
        *   Using models that don't require authentication.
    *   **Ensure GPU Usage:** Confirm the model is loaded onto the GPU (`device='cuda'`).

3.  **Implement LLM Extraction (Local Open Source Model):**
    *   **Choose Model:** Select a suitable open-source LLM for extraction (e.g., Mistral-7B-Instruct, Llama-3-8B-Instruct, Phi-3-mini-instruct). Consider model size vs. server VRAM.
    *   **Create Local Extractor Class:** Develop a new extractor class (e.g., `LocalLlmExtractor`) in `src/knowledge_base_agent/extractors/`.
        *   Use the `transformers` library pipeline (`text-generation` or custom loading with `AutoModelForCausalLM`, `AutoTokenizer`).
        *   Implement prompt engineering to guide the model to extract desired entities (`RetentionPeriod`, `DispositionAction`, `Description`, etc.) and relationships in a structured format (e.g., JSON).
        *   Handle model loading (consider quantization like 4-bit using `bitsandbytes` if VRAM is limited).
        *   Ensure model runs on the GPU.
    *   **Update `DocumentProcessor`:**
        *   Modify `__init__` to accept and store an instance of the `LocalLlmExtractor`.
        *   Update `process_document` to call the local LLM extractor instead of rules or OpenAI.
    *   **Update `cli.py`:** Modify `create_processor` to instantiate and pass the `LocalLlmExtractor` to the `DocumentProcessor`.

4.  **Testing and Refinement:**
    *   Test processing with a small subset of documents.
    *   Debug environment issues (CUDA, model loading, memory).
    *   Refine extraction prompts for better accuracy.
    *   Evaluate semantic search quality using the `query` command.

## Option 2: SOTA using OpenAI API (Simpler Setup, Higher Cost/Latency)

This approach uses OpenAI for both embeddings and extraction.

1.  **Configure API Access:**
    *   Ensure `OPENAI_API_KEY` is correctly set in the environment.
    *   Choose appropriate models in the configuration (`.env` or `config.yaml`):
        *   `EMBEDDING_MODEL`: e.g., `text-embedding-3-small`
        *   `LLM_MODEL`: e.g., `gpt-4o-mini` or `gpt-4-turbo` (for extraction)

2.  **Implement Semantic Embeddings (OpenAI):**
    *   Ensure `src/knowledge_base_agent/embeddings/openai_embedding.py` is correctly implemented.
    *   Modify `cli.py` (`create_processor`) to reliably instantiate `OpenAIEmbedding` when configured.

3.  **Implement LLM Extraction (OpenAI):**
    *   Ensure `src/knowledge_base_agent/extractors/entity_extractor.py` (using OpenAI client) is correctly implemented.
    *   Update `DocumentProcessor`:
        *   Reinstate initialization of `OpenAI` client and `EntityExtractor` in `__init__`.
        *   Ensure `process_document` calls the `entity_extractor`.
    *   **Implement Rate Limiting:** Modify the `EntityExtractor` or the call site in `DocumentProcessor` to handle `429 Too Many Requests` errors gracefully. Use exponential backoff (already partially present via `openai` library defaults) and potentially add proactive delays or use libraries like `ratelimit`.

4.  **Testing and Refinement:**
    *   Test processing with a small subset.
    *   Monitor API costs and usage.
    *   Refine extraction prompts if using Chat Completions API within the extractor.
    *   Evaluate semantic search quality.

## General Steps (Applicable to Both Options)

*   **Branching:** Create a new git branch (e.g., `feature/sota-processing`) for these changes.
*   **Configuration:** Update configuration files (`.env`, `config.yaml`) as needed for model names, API keys, etc.
*   **Documentation:** Update README and other documentation to reflect the chosen SOTA approach.
*   **Testing:** Add unit and integration tests for the new embedding and extraction components. 