"""
Mock vector store for testing.
"""

from typing import Dict, List, Tuple
import numpy as np

class VectorStore:
    def __init__(self):
        """Initialize mock store."""
        self.store = []
        
    def store_embeddings(self, embeddings: List[Dict]) -> List[int]:
        """Store embeddings in mock store."""
        ids = []
        for e in embeddings:
            self.store.append({
                'id': len(self.store),
                'doc_id': str(e['doc_id']),
                'chunk_idx': int(e['chunk_idx']),
                'embedding': e['embedding']
            })
            ids.append(len(self.store) - 1)
        return ids
        
    def search(self, query_embedding: np.ndarray, limit: int = 3) -> List[Tuple[str, int, float]]:
        """Mock search that returns dummy results."""
        return [
            ('test_doc_1', 0, 0.95),
            ('test_doc_2', 1, 0.85),
            ('test_doc_3', 2, 0.75)
        ]
        
    def delete_embeddings(self, doc_id: str) -> bool:
        """Delete embeddings for a document."""
        self.store = [e for e in self.store if e['doc_id'] != doc_id]
        return True
        
    def close(self):
        """Close mock store."""
        self.store = [] 