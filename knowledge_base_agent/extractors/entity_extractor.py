"""
Entity and Relationship Extractor using OpenAI's LLM.
"""

import json
import logging
import uuid
from typing import List, Tuple, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Entity, Relationship
from ..exceptions import EntityExtractionError

# Configure logging
logger = logging.getLogger(__name__)

class EntityExtractor:
    """Extracts entities and relationships from text using an LLM."""

    DEFAULT_MODEL = "gpt-4o-mini" # Or another suitable model like gpt-3.5-turbo
    DEFAULT_ENTITY_TYPES = ["PERSON", "ORGANIZATION", "LOCATION", "DATE", "EVENT", "MISC"]

    def __init__(self, client: OpenAI, model: Optional[str] = None):
        """Initialize entity extractor.
        
        Args:
            client: An initialized OpenAI client instance.
            model: The OpenAI model to use for extraction (defaults to DEFAULT_MODEL).
        """
        if client is None:
            raise ValueError("OpenAI client must be provided.")
        self.client = client
        self.model = model or self.DEFAULT_MODEL
        logger.info(f"EntityExtractor initialized with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry_error_callback=lambda retry_state: logger.error(
            f"Retrying entity/relationship extraction failed after {retry_state.attempt_number} attempts: {retry_state.outcome.exception()}"
        )
    )
    def extract_entities_and_relationships(
        self, 
        text: str, 
        entity_types: Optional[List[str]] = None
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from text using the configured LLM.

        Args:
            text: The input text to process.
            entity_types: A list of specific entity types to focus on (optional).

        Returns:
            A tuple containing:
                - List[Entity]: The extracted entities.
                - List[Relationship]: The extracted relationships.
                
        Raises:
            EntityExtractionError: If extraction fails after retries or parsing fails.
        """
        if not text.strip():
            logger.warning("Received empty text for extraction, returning empty results.")
            return [], []
            
        entity_types_list = entity_types or self.DEFAULT_ENTITY_TYPES
        prompt = self._build_extraction_prompt(text, entity_types_list)

        logger.debug(f"Attempting extraction from text (length: {len(text)}) with model {self.model}. Prompt starts with: {prompt[:200]}...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert assistant skilled in extracting structured information like entities and relationships from text according to user instructions. Respond ONLY with the requested JSON object, without any introductory text, explanations, or apologies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # Lower temperature for more deterministic extraction
                response_format={"type": "json_object"} # Request JSON output if model supports it
            )
            
            content = response.choices[0].message.content
            logger.debug(f"LLM raw response content: {content}")

            if not content:
                 raise EntityExtractionError("LLM returned empty content.")

            # Parse the JSON response
            try:
                # Sometimes the model might still wrap the JSON in backticks
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                     content = content[3:-3].strip()
                     
                extracted_data = json.loads(content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse JSON response: {json_err}. Response content: {content}")
                raise EntityExtractionError(f"Failed to parse LLM JSON response: {json_err}") from json_err

            # Validate structure (basic check)
            if not isinstance(extracted_data, dict) or 'entities' not in extracted_data or 'relationships' not in extracted_data:
                 logger.error(f"Unexpected JSON structure received: {extracted_data}")
                 raise EntityExtractionError("LLM response has unexpected JSON structure.")

            entities_data = extracted_data.get('entities', [])
            relationships_data = extracted_data.get('relationships', [])

            entities = self._parse_entities(entities_data)
            relationships = self._parse_relationships(relationships_data, entities) # Pass entities for ID mapping

            logger.info(f"Successfully extracted {len(entities)} entities and {len(relationships)} relationships.")
            return entities, relationships

        except Exception as e:
            # Catch API errors or other unexpected issues
            logger.error(f"Error during entity/relationship extraction API call or processing: {e}", exc_info=True)
            # Let the retry handle API errors, otherwise raise a specific extraction error
            if not hasattr(e, 'should_retry') or not e.should_retry: # Check if it's a tenacity-related exception attribute
                 raise EntityExtractionError(f"Extraction failed: {e}") from e
            raise # Re-raise to allow tenacity to retry

    def _build_extraction_prompt(self, text: str, entity_types: List[str]) -> str:
        """Constructs the prompt for the LLM extraction task."""
        # Improved prompt structure
        prompt = f"""
Analyze the following text and extract entities and relationships based on the instructions below.

**Instructions:**

1.  **Identify Entities:** Extract named entities corresponding to the following types: {', '.join(entity_types)}. For each entity, provide its name and type. Assign a unique temporary ID (e.g., "ent-1", "ent-2") to each distinct entity found.
2.  **Identify Relationships:** Extract relationships between the identified entities. Each relationship should be represented as a triple: (subject_id, predicate, object_id), where 'subject_id' and 'object_id' are the temporary IDs of the related entities, and 'predicate' describes the relationship (e.g., "works_at", "located_in", "born_on"). Only extract relationships where both subject and object entities have been identified in step 1.
3.  **Output Format:** Provide the results strictly as a JSON object with two keys: "entities" and "relationships".
    *   The value for "entities" should be a list of objects, each with "id" (temporary ID), "name", and "type".
    *   The value for "relationships" should be a list of objects, each with "subject_id", "predicate", and "object_id".

**Example Output Format:**

```json
{{
  "entities": [
    {{"id": "ent-1", "name": "Alice", "type": "PERSON"}},
    {{"id": "ent-2", "name": "Acme Corp", "type": "ORGANIZATION"}}
  ],
  "relationships": [
    {{"subject_id": "ent-1", "predicate": "works_at", "object_id": "ent-2"}}
  ]
}}
```

**Text to Analyze:**

```text
{text}
```

**Output JSON:**
"""
        return prompt

    def _parse_entities(self, entities_data: List[dict]) -> List[Entity]:
        """Parses entity data from LLM response into Entity objects."""
        entities = []
        temp_id_map = {} # Map temporary LLM IDs to final Entity IDs
        for item in entities_data:
            if not all(k in item for k in ['id', 'name', 'type']):
                logger.warning(f"Skipping malformed entity data: {item}")
                continue
            
            entity_id = str(uuid.uuid4()) # Generate unique ID for storage
            temp_id = item['id']
            temp_id_map[temp_id] = entity_id # Store mapping

            entities.append(Entity(
                id=entity_id,
                name=item['name'],
                type=item['type'],
                metadata={'llm_temp_id': temp_id} # Store temp ID in metadata if needed
            ))
        
        # Store the mapping for relationship parsing
        self._temp_entity_id_map = temp_id_map 
        return entities

    def _parse_relationships(self, relationships_data: List[dict], entities: List[Entity]) -> List[Relationship]:
        """Parses relationship data from LLM response into Relationship objects."""
        relationships = []
        
        # Use the map created during entity parsing
        temp_id_map = getattr(self, '_temp_entity_id_map', {}) 
        if not temp_id_map and relationships_data:
             logger.warning("Entity ID map is missing, cannot resolve relationship IDs.")
             return []
             
        entity_id_set = {e.id for e in entities} # For quick validation

        for item in relationships_data:
            if not all(k in item for k in ['subject_id', 'predicate', 'object_id']):
                logger.warning(f"Skipping malformed relationship data: {item}")
                continue

            temp_subj_id = item['subject_id']
            temp_obj_id = item['object_id']
            
            # Map temporary IDs to final entity IDs
            final_subj_id = temp_id_map.get(temp_subj_id)
            final_obj_id = temp_id_map.get(temp_obj_id)

            if not final_subj_id or not final_obj_id:
                logger.warning(f"Could not map relationship IDs to final entity IDs: {item}. Subject exists: {bool(final_subj_id)}, Object exists: {bool(final_obj_id)}")
                continue
                
            # Optional: Validate that these IDs correspond to extracted entities
            if final_subj_id not in entity_id_set or final_obj_id not in entity_id_set:
                 logger.warning(f"Relationship refers to entity IDs not found in the extracted entities list: {item}")
                 continue

            relationships.append(Relationship(
                # Note: Relationship model in models.py needs `id` field or adjust here
                # id=str(uuid.uuid4()), # Add if Relationship needs an ID
                source_id=final_subj_id,
                target_id=final_obj_id,
                type=item['predicate'], # Use 'predicate' as the relationship 'type'
                metadata={} # Add any relevant metadata
            ))
            
        # Clean up the temporary map
        if hasattr(self, '_temp_entity_id_map'):
             del self._temp_entity_id_map
             
        return relationships 