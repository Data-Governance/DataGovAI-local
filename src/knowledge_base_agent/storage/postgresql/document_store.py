"""
PostgreSQL implementation of document store.
"""

import logging
from typing import Dict, List, Optional

from ...models import Document
from .base import get_engine, init_db
from .models import DocumentModel

logger = logging.getLogger(__name__)

class PostgresDocumentStore:
    """PostgreSQL implementation of a document store."""
    
    def __init__(self, storage_path=None, connection_string=None):
        """
        Initialize PostgreSQL document store.
        
        Args:
            storage_path (str, optional): Path to storage directory
            connection_string (str, optional): Direct connection string for PostgreSQL
        """
        self.engine = get_engine(storage_path, connection_string)
        self.Session = init_db(self.engine, storage_path, connection_string)
    
    def store_document(self, document: Document) -> bool:
        """
        Store a document.
        
        Args:
            document (Document): Document to store
            
        Returns:
            bool: True if successful
        """
        session = self.Session()
        try:
            # Convert Document pydantic model to dict
            doc_data = document.dict()
            
            # Check if document already exists
            existing = session.query(DocumentModel).filter_by(id=document.id).first()
            if existing:
                # Update existing document
                for key, value in doc_data.items():
                    if key != 'id':  # Don't update the primary key
                        setattr(existing, key, value)
                session.commit()
                logger.debug(f"Updated document {document.id} in database")
            else:
                # Create new document
                doc_model = DocumentModel(**doc_data)
                session.add(doc_model)
                session.commit()
                logger.debug(f"Added document {document.id} to database")
            
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing document {document.id}: {e}")
            return False
        finally:
            session.close()
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            doc_id (str): Document ID
            
        Returns:
            Optional[Document]: Document if found, None otherwise
        """
        session = self.Session()
        try:
            doc_model = session.query(DocumentModel).filter_by(id=doc_id).first()
            if doc_model:
                # Convert SQLAlchemy model to Pydantic model
                doc_dict = doc_model.to_dict()
                return Document(**doc_dict)
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None
        finally:
            session.close()
    
    def get_documents(self) -> List[Document]:
        """
        Get all documents.
        
        Returns:
            List[Document]: List of all documents
        """
        session = self.Session()
        try:
            doc_models = session.query(DocumentModel).all()
            return [Document(**model.to_dict()) for model in doc_models]
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
        finally:
            session.close()
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id (str): Document ID
            
        Returns:
            bool: True if document was deleted, False otherwise
        """
        session = self.Session()
        try:
            doc_model = session.query(DocumentModel).filter_by(id=doc_id).first()
            if doc_model:
                session.delete(doc_model)
                session.commit()
                logger.debug(f"Deleted document {doc_id} from database")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
        finally:
            session.close()
    
    def close(self):
        """Close the document store connection."""
        self.Session.remove()
        
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.close()
        except:
            pass 