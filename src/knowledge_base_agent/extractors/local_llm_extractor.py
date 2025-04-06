"""
Local LLM-based entity extractor implementation.
"""
from typing import Dict, Any, Optional, List
import json
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from pydantic import BaseModel

from .entity_extractor import BaseEntityExtractor
from ..exceptions import ExtractionError

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract the following information from the given text. Return the information in a structured JSON format.

ENTITIES:
- record_series_number: The record series number (if present)
- title: The title of the record series
- description: A description of what the record series contains
- retention_period: How long the records should be kept (e.g., "3 years", "permanent")
- disposition_action: What should be done with the records after the retention period (e.g., "destroy", "transfer to archives")
- legal_authorities: Any legal citations or authorities mentioned

RELATIONSHIPS:
For each entity, also identify relationships between entities. Common relationships include:
- HAS_RETENTION: Links a record series to its retention period
- HAS_DISPOSITION: Links a record series to its disposition action
- CITES_AUTHORITY: Links a record series to legal authorities
- RELATED_TO: Links related record series together (if mentioned)

Text to analyze:
{text}

Return ONLY the following JSON structure, no other text. Use null for missing fields:
{
    "entities": {
        "record_series_number": string or null,
        "title": string or null,
        "description": string or null,
        "retention_period": string or null,
        "disposition_action": string or null,
        "legal_authorities": string or null
    },
    "relationships": [
        {
            "source": "record_series_number",
            "relationship_type": "HAS_RETENTION",
            "target": "retention_period"
        },
        {
            "source": "record_series_number",
            "relationship_type": "HAS_DISPOSITION",
            "target": "disposition_action"
        },
        {
            "source": "record_series_number",
            "relationship_type": "CITES_AUTHORITY",
            "target": "legal_authorities"
        }
    ]
}"""

class LocalLlmExtractor(BaseEntityExtractor):
    """Entity extractor using local LLM models."""
    
    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        device: str = None,
        load_in_4bit: bool = True,
        max_length: int = 2048,
        temperature: float = 0.1
    ):
        """Initialize the local LLM extractor.
        
        Args:
            model_name: Name of the model to use (from HuggingFace)
            device: Device to run on ('cuda' or 'cpu'). If None, uses CUDA if available
            load_in_4bit: Whether to use 4-bit quantization (reduces VRAM usage)
            max_length: Maximum sequence length for generation
            temperature: Temperature for text generation (lower = more deterministic)
        """
        super().__init__()
        
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.model_name = model_name
        self.max_length = max_length
        self.temperature = temperature
        
        logger.info(f"Initializing {model_name} on {self.device} (4-bit: {load_in_4bit})")
        
        try:
            # Configure quantization if needed
            if load_in_4bit and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
            else:
                quantization_config = None
            
            # Load model and tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
                
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}", exc_info=True)
            raise ExtractionError(f"Failed to initialize model: {e}") from e
            
    def _generate_text(self, prompt: str) -> str:
        """Generate text from the model given a prompt."""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_length)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the response
            response = response[len(prompt):].strip()
            return response
            
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            raise ExtractionError(f"Failed to generate text: {e}") from e
            
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse the JSON response from the model."""
        try:
            # Find the first '{' and last '}' to extract just the JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")
                
            json_str = response[start:end]
            result = json.loads(json_str)
            
            # Ensure the right structure exists
            if "entities" not in result:
                # If the old format was returned, restructure it
                entities = {}
                for field in ["record_series_number", "title", "description", 
                             "retention_period", "disposition_action", "legal_authorities"]:
                    entities[field] = result.get(field, None)
                
                # Create default relationships if they don't exist
                relationships = []
                if "relationships" not in result and entities.get("record_series_number"):
                    if entities.get("retention_period"):
                        relationships.append({
                            "source": "record_series_number",
                            "relationship_type": "HAS_RETENTION",
                            "target": "retention_period"
                        })
                    if entities.get("disposition_action"):
                        relationships.append({
                            "source": "record_series_number",
                            "relationship_type": "HAS_DISPOSITION",
                            "target": "disposition_action"
                        })
                    if entities.get("legal_authorities"):
                        relationships.append({
                            "source": "record_series_number",
                            "relationship_type": "CITES_AUTHORITY",
                            "target": "legal_authorities"
                        })
                
                result = {
                    "entities": entities,
                    "relationships": relationships
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}", exc_info=True)
            raise ExtractionError(f"Failed to parse JSON response: {e}") from e
            
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from the given text using the local LLM."""
        try:
            # Prepare the prompt
            prompt = EXTRACTION_PROMPT.format(text=text)
            
            # Generate response
            response = self._generate_text(prompt)
            
            # Parse and validate response
            result = self._parse_json_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            raise ExtractionError(f"Failed to extract entities: {e}") from e
            
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the extractor."""
        return {
            "model": self.model_name,
            "device": self.device,
            "max_length": self.max_length,
            "temperature": self.temperature
        } 