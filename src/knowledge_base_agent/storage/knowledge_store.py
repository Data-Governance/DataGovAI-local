"""
Mock knowledge store for testing.
"""

from typing import Dict, List, Optional, Set
from ..models import Entity, Relationship

class KnowledgeStore:
    def __init__(self):
        """Initialize mock store."""
        self.entities = {}
        self.relationships = []
        
    def store_entity(self, entity: Entity) -> str:
        """Store an entity."""
        self.entities[entity.id] = entity
        return entity.id
        
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)
        
    def store_relationship(self, relationship: Relationship) -> bool:
        """Store a relationship."""
        self.relationships.append(relationship)
        return True
        
    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Get relationships for an entity."""
        return [r for r in self.relationships if r.source_id == entity_id or r.target_id == entity_id]
        
    def get_related_entities(self, entity_id: str, max_depth: int = 1) -> Set[str]:
        """Get related entity IDs up to max_depth."""
        related = set()
        current_depth = 0
        current_entities = {entity_id}
        
        while current_depth < max_depth and current_entities:
            next_entities = set()
            for eid in current_entities:
                for rel in self.get_relationships(eid):
                    if rel.source_id == eid:
                        next_entities.add(rel.target_id)
                    else:
                        next_entities.add(rel.source_id)
            related.update(next_entities)
            current_entities = next_entities
            current_depth += 1
            
        return related 