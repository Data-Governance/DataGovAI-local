"""
Core document processing functionality for the Knowledge Base Agent.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from openai import OpenAI
import tiktoken
from datetime import datetime
import logging
from functools import lru_cache
import hashlib
import time
import uuid
import re

from .storage.document_store import DocumentStore
from .storage.vector_store import VectorStore
from .processors.text_processor import TextProcessor
from .models import (
    Document as PydanticDocument,
    ProcessingConfig,
    SearchResult,
    Entity,
    Relationship,
    SearchQuery,
    ProcessingStatus
)
from .storage.knowledge_store import KnowledgeStore
from .embeddings.base import BaseEmbeddingModel
from .extractors.local_llm_extractor import LocalLlmExtractor
from .utils.text import semantic_chunk_document
from .exceptions import (
    ProcessingError,
    EntityExtractionError,
    StorageError,
    EmbeddingError
)

# Configure logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

# Replacing the old chunking function with our new semantic approach
def chunk_document(text: str, config: ProcessingConfig, tokenizer=None) -> List[str]:
    """Splits text into semantic chunks based on sentence boundaries.
    
    This is a wrapper around the semantic_chunk_document function that returns
    just the content of each chunk rather than the full chunk objects.
    
    Args:
        text: Document text to chunk
        config: Processing configuration containing chunk size parameters
        tokenizer: Optional tokenizer (not used in semantic chunking)
        
    Returns:
        List of chunk text strings
    """
    # Use the semantic chunking function
    chunks = semantic_chunk_document(
        text=text,
        max_chunk_size=config.max_chunk_size,
        min_chunk_size=config.min_chunk_size,
        overlap_sentences=1  # Use a sensible default for sentence overlap
    )
    
    # Extract just the content field from each chunk
    return [chunk["content"] for chunk in chunks]

class DocumentProcessor:
    """Process and store documents with both vector embeddings and knowledge graph representation."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        document_store: DocumentStore,
        knowledge_store: KnowledgeStore,
        embedding_model: BaseEmbeddingModel,
        entity_extractor: Optional[LocalLlmExtractor] = None,
        config: Optional[ProcessingConfig] = None
    ):
        """Initialize the document processor.
        
        Args:
            vector_store: Vector store instance
            document_store: Document store instance
            knowledge_store: Knowledge store instance
            embedding_model: Embedding model instance
            entity_extractor: Optional LocalLlmExtractor instance
            config: Processing configuration
        """
        self.vector_store = vector_store
        self.document_store = document_store
        self.knowledge_store = knowledge_store
        self.embedding_model = embedding_model
        self.entity_extractor = entity_extractor or LocalLlmExtractor()
        self.config = config or ProcessingConfig()
        
        # Initialize components
        self.text_processor = TextProcessor(config)
        
        # Configure retries
        self.max_retries = self.config.max_retries or 3
        self.retry_delay = self.config.retry_delay or 1
        
        # Initialize cache
        self.cache_size = self.config.cache_size or 1000
        self.query_cache = lru_cache(maxsize=self.cache_size)(self._query_impl)
        
        # Initialize storage (using simple in-memory storage for now)
        self.documents = []
        self.embeddings = []
        
        # Initialize tokenizer for text splitting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
    
    def _extract_entities_rules(self, text: str, doc_id: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities using predefined rules (regex)."""
        entities = []
        relationships = [] # Rule-based relationships are complex, return empty for now
        
        # Regex patterns (adjust based on actual document structure)
        # Make patterns case-insensitive and multi-line
        patterns = {
            "RetentionPeriod": re.compile(r"Retention:\s*(.*?)(?=\n\s*(?:Disposition:|Legal Authority:|$))", re.IGNORECASE | re.DOTALL),
            "DispositionAction": re.compile(r"Disposition:\s*(.*?)(?=\n\s*(?:Legal Authority:|$))", re.IGNORECASE | re.DOTALL),
            "Description": re.compile(r"Description:\s*(.*?)(?=\n\s*(?:Retention:|Disposition:|Legal Authority:|$))", re.IGNORECASE | re.DOTALL),
            "LegalAuthority": re.compile(r"Legal Authority:\s*(.*?)(?=\n\s*\n|$)", re.IGNORECASE | re.DOTALL)
            # Add more patterns as needed (e.g., Title, RecordSeriesNumber if not reliably in metadata)
        }

        for entity_type, pattern in patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                value = match.group(1).strip()
                if value: # Only create entity if value is non-empty
                    entity = Entity(
                        id=str(uuid.uuid4()), # Simple unique ID for the entity instance
                        type=entity_type,
                        value=value,
                        metadata={"source": "regex"} 
                    )
                    entities.append(entity)
                    logger.debug(f"Regex extracted {entity_type}: '{value[:50]}...' for doc {doc_id}")

        # Simple check for UCA codes if LegalAuthority pattern didn't find much
        if not any(e.type == "LegalAuthority" for e in entities):
             uca_pattern = re.compile(r"UCA\s+\d+-\d+(?:-\d+)*", re.IGNORECASE)
             uca_matches = uca_pattern.findall(text)
             if uca_matches:
                 combined_uca = ", ".join(set(uca_matches)) # Combine unique findings
                 entity = Entity(
                        id=str(uuid.uuid4()),
                        type="LegalAuthority",
                        value=combined_uca,
                        metadata={"source": "regex_uca"} 
                    )
                 entities.append(entity)
                 logger.debug(f"Regex extracted LegalAuthority (UCA): '{combined_uca}' for doc {doc_id}")

        logger.info(f"Rule-based extraction found {len(entities)} entities for {doc_id}.")
        return entities, relationships

    def process_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Process a document: embed, store, extract entities/relations.
        
        Args:
            content: The document content as a string.
            metadata: Optional metadata dictionary.
            
        Returns:
            str: The document ID
        """
        # Construct the PydanticDocument object internally
        document = PydanticDocument(
            id=str(uuid.uuid4()), # Generate a new ID for each processing attempt initially
            content=content,
            metadata=metadata or {},
            chunks=[] # Chunks are typically not pre-defined here for GRS processing
        )
            
        # Ensure document has an ID (redundant check, but safe)
        if not document.id:
            document.id = str(uuid.uuid4())
            logger.warning(f"Document object lost ID somehow. Assigned new ID: {document.id}")
            
        doc_id = document.id
        logger.info(f"Starting processing for document_id: {doc_id}")

        try:
            # 1. Content Validation
            logger.debug(f"Checking content for document {doc_id}")
            if not isinstance(document.content, str) or not document.content.strip():
                raise ProcessingError(f"Document {doc_id} content is not a non-empty string (type: {type(document.content)}). Cannot process.")

            # 2. Store document structure
            try:
                self.document_store.store_document(document)
                logger.info(f"Stored document structure for {doc_id}")
            except StorageError as e:
                logger.error(f"Failed to store document {doc_id}: {e}")
                raise

            # 3. Extract entities using LLM
            try:
                extracted_data = self.entity_extractor.extract_entities(content)
                
                # Convert extracted data to entities
                entities = []
                for field, value in extracted_data.items():
                    if value:  # Only create entity if value is not None
                        entity = Entity(
                            id=str(uuid.uuid4()),
                            type=field,
                            value=value,
                            metadata={"source": "llm"}
                        )
                        entities.append(entity)
                
                # Store entities and relationships
                for entity in entities:
                    self.knowledge_store.store_entity(entity)
                    # Create relationship between document and entity
                    relationship = Relationship(
                        id=str(uuid.uuid4()),
                        source_id=doc_id,
                        target_id=entity.id,
                        type="CONTAINS",
                        metadata={"confidence": 1.0}
                    )
                    self.knowledge_store.store_relationship(relationship)
                    
                logger.info(f"Stored {len(entities)} entities for document {doc_id}")
                
            except Exception as e:
                logger.error(f"Entity extraction failed for document {doc_id}: {e}")
                # Fall back to rule-based extraction if LLM fails
                entities, relationships = self._extract_entities_rules(content, doc_id)
                for entity in entities:
                    self.knowledge_store.store_entity(entity)
                for relationship in relationships:
                    self.knowledge_store.store_relationship(relationship)
                logger.info(f"Fallback: Stored {len(entities)} rule-based entities for document {doc_id}")

            # 4. Generate and store embeddings
            try:
                # Split into chunks if needed
                chunks = chunk_document(content, self.config, self.tokenizer)
                document.chunks = chunks  # Update document with chunks
                
                # Generate embeddings for chunks
                chunk_embeddings = self._generate_embeddings(chunks)
                
                # Store embeddings
                for chunk, embedding in zip(chunks, chunk_embeddings):
                    self.vector_store.store_embedding(
                        doc_id=doc_id,
                        text=chunk,
                        embedding=embedding,
                        metadata={"chunk": True}
                    )
                logger.info(f"Stored {len(chunks)} chunk embeddings for document {doc_id}")
                
            except Exception as e:
                logger.error(f"Failed to process embeddings for document {doc_id}: {e}")
                raise ProcessingError(f"Embedding generation failed: {e}")

            return doc_id

        except Exception as e:
            logger.error(f"Processing failed for document {doc_id}: {e}")
            raise ProcessingError(f"Document processing failed: {e}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
        use_graph: bool = True
    ) -> List[SearchResult]:
        """Search for relevant document chunks and aggregate results."""
        logger.info(f"Starting search with query: '{query[:50]}...', top_k={top_k}, use_graph={use_graph}")
        try:
            # 1. Get query embedding
            try:
                # Assuming generate expects a single item list or handles str directly
                query_embedding = self._generate_embeddings_with_retry([query])[0]
                logger.debug("Generated query embedding.")
            except Exception as e:
                logger.error(f"Failed to generate query embedding: {e}", exc_info=True)
                raise EmbeddingError(f"Failed to generate query embedding: {str(e)}")

            # 2. Search vector store for relevant chunks
            try:
                # Assuming search returns [(doc_id, chunk_id, score), ...]
                logger.debug(f"Searching vector store for top {top_k} chunks.")
                chunk_results = self.vector_store.search(
                    query_embedding,
                    top_k=top_k,
                    # min_score=min_score # Pass min_score if supported by vector_store.search
                )
                logger.info(f"Vector store returned {len(chunk_results)} chunk results.")
                if not chunk_results:
                    return [] # No matches found

            except Exception as e:
                 logger.error(f"Vector store search failed: {e}", exc_info=True)
                 raise StorageError(f"Vector store search failed: {str(e)}")

            # 3. Aggregate results by document and retrieve documents
            doc_scores: Dict[str, List[Tuple[int, float]]] = {} # {doc_id: [(chunk_id, score), ...]}
            doc_ids_needed = set()
            for doc_id, chunk_id, score in chunk_results:
                 # Apply min_score filter here if not done by vector_store
                if score >= min_score:
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = []
                    doc_scores[doc_id].append((chunk_id, score))
                    doc_ids_needed.add(doc_id)
                else:
                    logger.debug(f"Chunk {chunk_id} of doc {doc_id} skipped due to low score ({score} < {min_score}).")


            if not doc_ids_needed:
                logger.info("No chunks met the minimum score requirement.")
                return []


            logger.debug(f"Retrieving {len(doc_ids_needed)} unique documents from document store.")
            documents: Dict[str, PydanticDocument] = {}
            try:
                # Assume document store can fetch multiple docs efficiently if possible
                # Otherwise, fetch one by one
                for doc_id in doc_ids_needed:
                    doc = self.document_store.get_document(doc_id)
                    if doc:
                        documents[doc_id] = doc
                    else:
                         logger.warning(f"Document {doc_id} referenced by vector store not found in document store.")

            except Exception as e:
                 logger.error(f"Failed to retrieve documents from document store: {e}", exc_info=True)
                 raise StorageError(f"Failed to retrieve documents: {str(e)}")


            # 4. Format results at the chunk level
            search_results: List[SearchResult] = []
            for doc_id, chunk_idx, score in chunk_results:
                # Check if the document was retrieved and the score is sufficient
                if doc_id in documents and score >= min_score:
                    retrieved_doc = documents[doc_id]
                    # Ensure the chunk index is valid for the retrieved document
                    if 0 <= chunk_idx < len(retrieved_doc.chunks):
                        chunk_content = retrieved_doc.chunks[chunk_idx]
                        result = SearchResult(
                            document_id=doc_id,
                            content=chunk_content,
                            score=score,
                            metadata=retrieved_doc.metadata or {},
                            # entities and relationships are not populated here by default
                            # Could be optionally added by fetching from KnowledgeStore if needed
                        )
                        search_results.append(result)
                    else:
                        logger.warning(
                            f"Chunk index {chunk_idx} out of bounds for document {doc_id} "
                            f"(found {len(retrieved_doc.chunks)} chunks). Skipping this result."
                        )
                # We already filtered by min_score earlier, but double-checking doesn't hurt
                # Or handle the case where the document wasn't found
                elif doc_id not in documents:
                    logger.warning(f"Document {doc_id} for chunk {chunk_idx} not found. Skipping result.")

            # 5. Sort final results by score
            search_results.sort(key=lambda x: x.score, reverse=True)

            # 6. Limit to top_k results (already implicitly handled by vector search limit, but good practice)
            # The number of results might be less than top_k if some docs/chunks weren't found
            # or filtered by min_score.
            final_results = search_results[:top_k] 
            logger.info(f"Returning {len(final_results)} search results.")
            return final_results

        except (StorageError, EmbeddingError, ProcessingError) as e:
             logger.error(f"Search failed due to {type(e).__name__}: {e}")
             raise # Re-raise the specific error
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}", exc_info=True)
            raise ProcessingError(f"Search failed: {str(e)}")
    
    def get_entity_context(
        self,
        entity_id: str,
        max_depth: int = 2
    ) -> Dict:
        """Get contextual information about an entity from the knowledge graph.
        
        Args:
            entity_id: Entity ID
            max_depth: Maximum depth of relationships to traverse
            
        Returns:
            Dictionary containing entity context
            
        Raises:
            StorageError: If knowledge store operations fail
        """
        try:
            return self.knowledge_store.query_related_entities(entity_id, max_depth)
        except Exception as e:
            raise StorageError(f"Failed to get entity context: {str(e)}")
    
    def query(self, query: str, limit: int = 3) -> Dict:
        """Query the knowledge base.
        
        Args:
            query: The query text
            limit: Maximum number of results to return
            
        Returns:
            Dict containing search results
            
        Raises:
            ProcessingError: If query fails
        """
        # Generate cache key
        cache_key = hashlib.md5(f"{query}:{limit}".encode()).hexdigest()
        
        try:
            # Try to get from cache
            return self.query_cache(cache_key, query, limit)
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}", exc_info=True)
            raise ProcessingError(f"Query failed: {str(e)}")
    
    def _query_impl(self, cache_key: str, query: str, limit: int) -> Dict:
        """Implementation of query logic (wrapped with caching)."""
        logger.debug(f"Executing query (cache miss or disabled): '{query[:50]}...', limit={limit}")
        try:
            # Generate query embedding
            query_embedding = self._generate_embeddings_with_retry([query])[0]

            # Search vector store for relevant chunks
            # Assuming search returns [(doc_id, chunk_id, score), ...]
            matches = self.vector_store.search(query_embedding, limit)
            logger.debug(f"Vector store returned {len(matches)} matches for query.")

            # Get document chunks associated with the matches
            results = []
            doc_cache = {} # Simple cache for documents within this query
            for doc_id, chunk_idx, similarity in matches:
                doc = doc_cache.get(doc_id)
                if not doc:
                    logger.debug(f"Cache miss for document {doc_id}, retrieving from document store.")
                    doc = self.document_store.get_document(doc_id)
                    if doc:
                        doc_cache[doc_id] = doc
                    else:
                        logger.warning(f"Document {doc_id} not found for chunk {chunk_idx} during query.")
                        continue # Skip this match if doc not found

                # Ensure the chunk index is valid
                if doc and 0 <= chunk_idx < len(doc.chunks):
                    chunk_content = doc.chunks[chunk_idx]
                    results.append({
                        'content': chunk_content,
                        'similarity': float(similarity),
                        'document_id': doc_id, # Include doc_id
                        'chunk_id': chunk_idx,   # Include chunk_id
                        'metadata': doc.metadata # Use document metadata
                    })
                else:
                     logger.warning(f"Invalid chunk index {chunk_idx} for document {doc_id} (has {len(doc.chunks)} chunks).")


            logger.debug(f"Query successful, returning {len(results)} results.")
            return {
                'success': True,
                'results': results
            }

        except Exception as e:
             logger.error(f"Error during query implementation: {e}", exc_info=True)
             # Return error structure consistent with original code, but log details
             return {
                 'success': False,
                 'error': f"Query execution failed: {str(e)}"
             }
    
    def _generate_embeddings_with_retry(self, texts: List[str], attempt: int = 1) -> List[np.ndarray]:
        """Generate embeddings with retry logic."""
        try:
            return self._generate_embeddings(texts)
        except Exception as e:
            if attempt < self.max_retries:
                time.sleep(self.retry_delay)
                return self._generate_embeddings_with_retry(texts, attempt + 1)
            raise EmbeddingError(f"Failed to generate embeddings after {self.max_retries} attempts: {str(e)}")
    
    def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a list of texts."""
        logger.debug(f"Generating embeddings for {len(texts)} text items.")
        try:
            # Assuming the base embedding model handles potential API errors internally
            # or we rely on the retry mechanism in _generate_embeddings_with_retry
            embeddings = self.embedding_model.generate(texts)
            logger.debug(f"Successfully generated {len(embeddings)} embeddings.")
            return embeddings
        except Exception as e:
             logger.error(f"Underlying embedding model failed: {e}", exc_info=True)
             # The exception will be caught by _generate_embeddings_with_retry
             raise EmbeddingError(f"Failed to generate embeddings: {str(e)}")
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    def close(self):
        """Close all resources."""
        try:
            self.vector_store.close()
            self.document_store.close()
            self.knowledge_store.close()
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}", exc_info=True) 