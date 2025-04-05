"""
PostgreSQL implementation of vector store using pgvector.
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .base import get_engine, init_db
from .models import ChunkEmbeddingModel

logger = logging.getLogger(__name__)

class PostgresVectorStore:
    """PostgreSQL implementation of a vector store using pgvector."""
    
    def __init__(self, storage_path=None, connection_string=None):
        """
        Initialize PostgreSQL vector store.
        
        Args:
            storage_path (str, optional): Path to storage directory
            connection_string (str, optional): Direct connection string for PostgreSQL
        """
        self.engine = get_engine(storage_path, connection_string)
        self.Session = init_db(self.engine, storage_path, connection_string)
    
    def store_embeddings(self, embeddings: List[Dict]) -> List[int]:
        """
        Store embeddings in the vector store.
        
        Args:
            embeddings (List[Dict]): List of dictionaries with keys:
                - doc_id: Document ID
                - chunk_idx: Chunk index
                - embedding: Embedding vector
                
        Returns:
            List[int]: List of IDs for stored embeddings
        """
        session = self.Session()
        try:
            ids = []
            for embedding in embeddings:
                # Check if embedding already exists
                existing = session.query(ChunkEmbeddingModel).filter_by(
                    document_id=embedding['doc_id'],
                    chunk_idx=embedding['chunk_idx']
                ).first()
                
                if existing:
                    # Update existing embedding
                    existing.embedding = embedding['embedding']
                    ids.append(existing.id)
                else:
                    # Create new embedding
                    chunk_embedding = ChunkEmbeddingModel(
                        document_id=embedding['doc_id'],
                        chunk_idx=embedding['chunk_idx'],
                        embedding=embedding['embedding']
                    )
                    session.add(chunk_embedding)
                    session.flush()  # Flush to get the ID
                    ids.append(chunk_embedding.id)
            
            session.commit()
            logger.debug(f"Stored {len(embeddings)} embeddings in database")
            return ids
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing embeddings: {e}")
            return []
        finally:
            session.close()
    
    def search(self, query_embedding: np.ndarray, limit: int = 5) -> List[Tuple[str, int, float]]:
        """
        Search for similar vectors using pgvector.
        
        Args:
            query_embedding (np.ndarray): Query embedding vector
            limit (int, optional): Maximum number of results to return
            
        Returns:
            List[Tuple[str, int, float]]: List of (document_id, chunk_idx, similarity) tuples
        """
        session = self.Session()
        try:
            # Convert numpy array to list for SQL query
            query_list = query_embedding.tolist()
            
            # Perform vector similarity search using pgvector
            results = []
            if self.engine.name == 'postgresql':
                # PostgreSQL with pgvector
                # Use <=> for cosine distance (pgvector returns distance, so 1-distance = similarity)
                # or <-> for L2 distance, or <#> for inner product (returns negative, so *-1 for similarity)
                stmt = text("""
                    SELECT document_id, chunk_idx, 1 - (embedding <=> :query_vector) as similarity 
                    FROM chunk_embeddings
                    ORDER BY embedding <=> :query_vector
                    LIMIT :limit
                """)
                result_proxy = session.execute(
                    stmt, 
                    {"query_vector": str(query_list), "limit": limit} # Pass vector as string
                )
                
                for row in result_proxy:
                    results.append((row[0], row[1], float(row[2])))
            else:
                # Fallback for SQLite or other DBs (less efficient)
                logger.warning("pgvector not available or not using PostgreSQL. Falling back to sequential scan.")
                embeddings = session.query(
                    ChunkEmbeddingModel.document_id,
                    ChunkEmbeddingModel.chunk_idx,
                    ChunkEmbeddingModel.embedding
                ).all()
                
                similarities = []
                for doc_id, chunk_idx, embedding in embeddings:
                    emb_array = np.array(embedding)
                    similarity = np.dot(query_embedding, emb_array) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(emb_array)
                    )
                    similarities.append((doc_id, chunk_idx, float(similarity)))
                
                similarities.sort(key=lambda x: x[2], reverse=True)
                results = similarities[:limit]
            
            logger.debug(f"Vector search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []
        finally:
            session.close()
    
    def delete_embeddings(self, doc_id: str) -> bool:
        """
        Delete embeddings for a document.
        
        Args:
            doc_id (str): Document ID
            
        Returns:
            bool: True if successful
        """
        session = self.Session()
        try:
            count = session.query(ChunkEmbeddingModel).filter_by(document_id=doc_id).delete()
            session.commit()
            logger.debug(f"Deleted {count} embeddings for document {doc_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting embeddings for document {doc_id}: {e}")
            return False
        finally:
            session.close()
    
    def close(self):
        """Close the vector store connection."""
        self.Session.remove()
        
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.close()
        except:
            pass 