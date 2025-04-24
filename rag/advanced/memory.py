"""Conversation memory management for the RAG system."""

import logging
from typing import Optional, List, Dict, Any
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core import ServiceContext, VectorStoreIndex, Settings, get_response_synthesizer
from llama_index.core.llms import LLM
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SimilarityPostprocessor

from .. import config

logger = logging.getLogger(__name__)

def create_chat_engine_with_memory(
    index: VectorStoreIndex,
    llm: Optional[LLM] = None,
    memory_limit: int = config.CONVERSATION_HISTORY_LIMIT,
    chat_mode: str = "condense_question",
    verbose: bool = config.VERBOSE,
    system_prompt: Optional[str] = None
) -> CondenseQuestionChatEngine:
    """Creates a LlamaIndex ChatEngine with conversation memory.

    Args:
        index: The LlamaIndex vector store index.
        llm: The language model to use (defaults to settings).
        memory_limit: The maximum number of conversation turns to retain in memory.
        chat_mode: The chat engine mode to use (e.g., condense_question).
        verbose: Whether to enable verbose logging.
        system_prompt: Optional system prompt for the chat engine.

    Returns:
        An initialized CondenseQuestionChatEngine (or other ChatEngine type based on mode).
    """
    logger.info(f"Creating chat engine with memory (limit: {memory_limit} turns, mode: {chat_mode})")
    
    # Use global LLM settings if none provided
    llm_instance = llm or Settings.llm
    if not llm_instance:
        raise ValueError("LLM must be initialized in Settings or passed explicitly.")

    # Initialize memory buffer
    memory = ChatMemoryBuffer.from_defaults(
        token_limit=4096  # Using token limit for more precise control
    )
    
    try:
        # Using direct index.as_query_engine is more robust to embedding issues
        # as it will use the existing index without requiring new embeddings
        query_engine = index.as_query_engine(
            similarity_top_k=config.TOP_K,
            response_mode=config.RESPONSE_MODE,
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=config.SIMILARITY_CUTOFF)
            ] if config.SIMILARITY_CUTOFF > 0 else None
        )
        
        # Create the chat engine with the query engine
        chat_engine = CondenseQuestionChatEngine.from_defaults(
            query_engine=query_engine,
            llm=llm_instance,
            memory=memory,
            verbose=verbose
        )
        
        logger.info("Chat engine created successfully.")
        return chat_engine
        
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        # If we can't create the chat engine, raise the error
        raise 