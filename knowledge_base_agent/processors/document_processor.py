"""
Advanced document processor with intelligent chunking and processing capabilities.
"""

from typing import List, Dict, Optional, Union
import logging
from pathlib import Path
import hashlib
import json
from datetime import datetime

from ..storage import VectorStore, DocumentStore, KnowledgeGraph
from ..embeddings import EmbeddingGenerator
from .text_processor import AdaptiveTextProcessor, TextChunk

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Advanced document processor with intelligent processing capabilities."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        document_store: DocumentStore,
        knowledge_graph: KnowledgeGraph,
        embedding_generator: EmbeddingGenerator,
        config: Optional[Dict] = None
    ):
        """Initialize the document processor.
        
        Args:
            vector_store: Vector store instance
            document_store: Document store instance
            knowledge_graph: Knowledge graph instance
            embedding_generator: Embedding generator instance
            config: Optional configuration dictionary
        """
        self.vector_store = vector_store
        self.document_store = document_store
        self.knowledge_graph = knowledge_graph
        self.embedding_generator = embedding_generator
        
        # Load configuration
        self.config = config or {}
        
        # Initialize text processor
        self.text_processor = AdaptiveTextProcessor(
            max_chunk_size=self.config.get('max_chunk_size', 512),
            min_chunk_size=self.config.get('min_chunk_size', 100),
            overlap_size=self.config.get('overlap_size', 0.1),
            embedding_model=self.config.get('embedding_model', 'all-MiniLM-L6-v2'),
            enable_semantic_chunking=self.config.get('enable_semantic_chunking', True)
        )
    
    def process_document(
        self,
        content: str,
        metadata: Optional[Dict] = None,
        chunking_strategy: str = 'adaptive',
        generate_embeddings: bool = True,
        extract_entities: bool = True,
        doc_id: Optional[str] = None
    ) -> Dict:
        """Process a document with advanced chunking and analysis.
        
        Args:
            content: Document content
            metadata: Optional document metadata
            chunking_strategy: Chunking strategy to use
            generate_embeddings: Whether to generate embeddings
            extract_entities: Whether to extract entities
            doc_id: Optional document ID
            
        Returns:
            Processing results including chunks, embeddings, and analysis
        """
        try:
            # Generate document ID if not provided
            if not doc_id:
                doc_id = self._generate_doc_id(content)
            
            # Analyze text structure
            analysis = self.text_processor.analyze_text_structure(content)
            
            # Process text into chunks
            chunks = self.text_processor.process_text(
                text=content,
                chunking_strategy=chunking_strategy
            )
            
            # Generate embeddings if requested
            if generate_embeddings:
                chunk_embeddings = self.embedding_generator.generate_batch([
                    chunk.content for chunk in chunks
                ])
                for chunk, embedding in zip(chunks, chunk_embeddings):
                    chunk.embedding = embedding
            
            # Store document and chunks
            doc_metadata = {
                **(metadata or {}),
                'processing_date': datetime.now().isoformat(),
                'chunking_strategy': chunking_strategy,
                'num_chunks': len(chunks),
                'analysis': analysis
            }
            
            # Store in document store
            self.document_store.store_document(
                doc_id=doc_id,
                content=content,
                metadata=doc_metadata,
                chunks=[{
                    'content': chunk.content,
                    'start_idx': chunk.start_idx,
                    'end_idx': chunk.end_idx,
                    'chunk_type': chunk.chunk_type,
                    'metadata': chunk.metadata
                } for chunk in chunks]
            )
            
            # Store in vector store if embeddings were generated
            if generate_embeddings:
                self.vector_store.store_vectors(
                    vectors=[chunk.embedding for chunk in chunks],
                    metadata=[{
                        'doc_id': doc_id,
                        'chunk_idx': i,
                        'chunk_type': chunk.chunk_type,
                        **chunk.metadata
                    } for i, chunk in enumerate(chunks)]
                )
            
            # Extract and store entities if requested
            entities = []
            relations = []
            if extract_entities:
                # Entity extraction would go here
                # This is a placeholder for the actual implementation
                pass
            
            return {
                'success': True,
                'doc_id': doc_id,
                'num_chunks': len(chunks),
                'analysis': analysis,
                'chunks': [{
                    'content': chunk.content[:100] + '...',
                    'type': chunk.chunk_type,
                    'metadata': chunk.metadata
                } for chunk in chunks],
                'entities': entities,
                'relations': relations
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def query(
        self,
        query: str,
        limit: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Query the knowledge base with advanced retrieval.
        
        Args:
            query: Query string
            limit: Maximum number of results
            min_similarity: Minimum similarity score
            filters: Optional filters to apply
            
        Returns:
            Query results with chunks and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate(query)
            
            # Search vector store
            vector_results = self.vector_store.search(
                query_vector=query_embedding,
                limit=limit * 2,  # Get more results for reranking
                filters=filters
            )
            
            # Get full chunks from document store
            chunks = []
            for result in vector_results:
                doc = self.document_store.get_document(result['doc_id'])
                if doc:
                    chunk = next(
                        (c for c in doc['chunks'] 
                         if c['chunk_idx'] == result['chunk_idx']),
                        None
                    )
                    if chunk:
                        chunks.append({
                            **chunk,
                            'similarity': result['similarity'],
                            'doc_metadata': doc['metadata']
                        })
            
            # Rerank results considering:
            # 1. Vector similarity
            # 2. Chunk quality (based on metadata)
            # 3. Document relevance
            reranked_chunks = self._rerank_results(chunks, query)
            
            # Filter by minimum similarity
            filtered_chunks = [
                chunk for chunk in reranked_chunks
                if chunk['similarity'] >= min_similarity
            ]
            
            return {
                'success': True,
                'results': filtered_chunks[:limit],
                'total_chunks': len(filtered_chunks),
                'query_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge base: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_doc_id(self, content: str) -> str:
        """Generate a unique document ID."""
        return hashlib.sha256(
            content.encode('utf-8')
        ).hexdigest()[:16]
    
    def _rerank_results(
        self,
        chunks: List[Dict],
        query: str
    ) -> List[Dict]:
        """Rerank results using multiple factors."""
        for chunk in chunks:
            # Calculate chunk quality score
            quality_score = self._calculate_chunk_quality(chunk)
            
            # Adjust similarity score
            chunk['similarity'] = 0.7 * chunk['similarity'] + 0.3 * quality_score
        
        # Sort by adjusted similarity
        return sorted(
            chunks,
            key=lambda x: x['similarity'],
            reverse=True
        )
    
    def _calculate_chunk_quality(self, chunk: Dict) -> float:
        """Calculate a quality score for a chunk."""
        score = 1.0
        
        # Prefer semantic chunks
        if chunk['chunk_type'] == 'semantic':
            score *= 1.2
        
        # Prefer chunks with higher similarity between sentences
        if 'similarity_score' in chunk.get('metadata', {}):
            score *= (0.5 + 0.5 * chunk['metadata']['similarity_score'])
        
        # Penalize very short chunks
        if len(chunk['content']) < 100:
            score *= 0.8
        
        return min(score, 1.0)  # Cap at 1.0 