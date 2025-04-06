"""
Mock document store for testing.
"""

from typing import Dict, List, Optional
from ..models import Document

class DocumentStore:
    def __init__(self):
        """Initialize mock store."""
        self.documents = {}
        
    def store_document(self, document: Document) -> bool:
        """Store a document."""
        self.documents[document.id] = document
        return True
        
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
        
    def get_documents(self) -> List[Document]:
        """Get all documents."""
        return list(self.documents.values())
        
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False 