"""
PostgreSQL implementation of knowledge store.
"""

import logging
from typing import Dict, List, Optional, Set

from sqlalchemy import or_

from ...models import Entity, Relationship
from .base import get_engine, init_db
from .models import EntityModel, RelationshipModel

logger = logging.getLogger(__name__)

class PostgresKnowledgeStore:
    """PostgreSQL implementation of a knowledge store."""
    
    def __init__(self, storage_path=None, connection_string=None):
        """
        Initialize PostgreSQL knowledge store.
        
        Args:
            storage_path (str, optional): Path to storage directory
            connection_string (str, optional): Direct connection string for PostgreSQL
        """
        self.engine = get_engine(storage_path, connection_string)
        self.Session = init_db(self.engine, storage_path, connection_string)
    
    def store_entity(self, entity: Entity) -> str:
        """
        Store an entity.
        
        Args:
            entity (Entity): Entity to store
            
        Returns:
            str: Entity ID
        """
        session = self.Session()
        try:
            # Convert Entity pydantic model to dict
            entity_data = entity.dict()
            
            # Check if entity already exists
            existing = session.query(EntityModel).filter_by(id=entity.id).first()
            if existing:
                # Update existing entity
                for key, value in entity_data.items():
                    if key != 'id':  # Don't update the primary key
                        setattr(existing, key, value)
                session.commit()
                logger.debug(f"Updated entity {entity.id} in database")
            else:
                # Create new entity
                entity_model = EntityModel(**entity_data)
                session.add(entity_model)
                session.commit()
                logger.debug(f"Added entity {entity.id} to database")
            
            return entity.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing entity {entity.id}: {e}")
            return entity.id  # Still return the ID even if storage fails
        finally:
            session.close()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get an entity by ID.
        
        Args:
            entity_id (str): Entity ID
            
        Returns:
            Optional[Entity]: Entity if found, None otherwise
        """
        session = self.Session()
        try:
            entity_model = session.query(EntityModel).filter_by(id=entity_id).first()
            if entity_model:
                # Convert SQLAlchemy model to Pydantic model
                entity_dict = entity_model.to_dict()
                return Entity(**entity_dict)
            return None
        except Exception as e:
            logger.error(f"Error retrieving entity {entity_id}: {e}")
            return None
        finally:
            session.close()
    
    def store_relationship(self, relationship: Relationship) -> bool:
        """
        Store a relationship.
        
        Args:
            relationship (Relationship): Relationship to store
            
        Returns:
            bool: True if successful
        """
        session = self.Session()
        try:
            # Convert Relationship pydantic model to dict
            rel_data = relationship.dict()
            
            # Check if relationship already exists
            existing = session.query(RelationshipModel).filter_by(id=relationship.id).first()
            if existing:
                # Update existing relationship
                for key, value in rel_data.items():
                    if key != 'id':  # Don't update the primary key
                        setattr(existing, key, value)
                session.commit()
                logger.debug(f"Updated relationship {relationship.id} in database")
            else:
                # Create new relationship
                rel_model = RelationshipModel(**rel_data)
                session.add(rel_model)
                session.commit()
                logger.debug(f"Added relationship {relationship.id} to database")
            
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing relationship {relationship.id}: {e}")
            return False
        finally:
            session.close()
    
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """
        Get relationships for an entity.
        
        Args:
            entity_id (str): Entity ID
            
        Returns:
            List[Relationship]: List of relationships involving the entity
        """
        session = self.Session()
        try:
            # Query relationships where entity is source or target
            rel_models = session.query(RelationshipModel).filter(
                or_(
                    RelationshipModel.source_id == entity_id,
                    RelationshipModel.target_id == entity_id
                )
            ).all()
            
            # Convert SQLAlchemy models to Pydantic models
            relationships = [Relationship(**model.to_dict()) for model in rel_models]
            return relationships
        except Exception as e:
            logger.error(f"Error retrieving relationships for entity {entity_id}: {e}")
            return []
        finally:
            session.close()
    
    def get_related_entities(self, entity_id: str, max_depth: int = 1) -> Set[str]:
        """
        Get related entity IDs up to max_depth.
        
        Args:
            entity_id (str): Entity ID
            max_depth (int, optional): Maximum depth of relationships to traverse
            
        Returns:
            Set[str]: Set of related entity IDs
        """
        related = set()
        current_depth = 0
        current_entities = {entity_id}
        
        session = self.Session()
        try:
            while current_depth < max_depth and current_entities:
                next_entities = set()
                for eid in current_entities:
                    # Query relationships where entity is source or target
                    rel_models = session.query(RelationshipModel).filter(
                        or_(
                            RelationshipModel.source_id == eid,
                            RelationshipModel.target_id == eid
                        )
                    ).all()
                    
                    # Extract related entities
                    for rel in rel_models:
                        if rel.source_id == eid:
                            next_entities.add(rel.target_id)
                        else:
                            next_entities.add(rel.source_id)
                
                # Remove already processed entities
                next_entities -= current_entities
                next_entities -= related
                
                # Add to result set
                related.update(next_entities)
                
                # Move to next level
                current_entities = next_entities
                current_depth += 1
            
            return related
        except Exception as e:
            logger.error(f"Error retrieving related entities for {entity_id}: {e}")
            return set()
        finally:
            session.close()
    
    def close(self):
        """Close the knowledge store connection."""
        self.Session.remove()
        
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            self.close()
        except:
            pass 