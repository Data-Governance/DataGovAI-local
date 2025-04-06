"""
RAG+KG Query Agent for advanced retrieval combining semantic search and knowledge graph.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel
import os # Added for OpenAI API Key
import openai # Added for OpenAI API client

from .processor import DocumentProcessor
from .exceptions import ProcessingError, StorageError, EmbeddingError

logger = logging.getLogger(__name__)

# Prompt template for entity extraction from query
ENTITY_EXTRACTION_PROMPT = """Extract entities from the following query that could be used to search a knowledge base about Utah General Retention Schedules (GRS).

Entities to extract:
- record_series_number: Any record series identifiers (e.g., "RS-1234")
- retention_period: References to retention periods (e.g., "3 years", "permanent")
- disposition_action: References to disposition actions (e.g., "destroy", "transfer to archives")
- legal_authority: References to legal authorities (e.g., "UCA 63G-2")

Query:
{query}

Respond with a JSON object containing the extracted entities. Use null for missing entities:
{
    "record_series_number": string or null,
    "retention_period": string or null,
    "disposition_action": string or null,
    "legal_authority": string or null
}"""

# Prompt template for answer synthesis (Consider refining for GPT-4o)
ANSWER_SYNTHESIS_PROMPT = """You are a knowledgeable assistant answering questions about Utah General Retention Schedules (GRS).

Use ONLY the following retrieved information to answer the user's question. 
If the information doesn't contain the answer, state that clearly. DO NOT make up information or use external knowledge.

User Query: {query}

--- Start of Retrieved Information ---

**Vector Search Results (semantic search):**
{vector_results}

**Knowledge Graph Results (entity-based search):**
{kg_results}

--- End of Retrieved Information ---

Answer the user's query based *only* on the information provided above:
"""

class RAGKGQueryAgent:
    """Query agent combining RAG with Knowledge Graph for advanced retrieval."""
    
    def __init__(
        self,
        processor: DocumentProcessor,
        entity_extractor_model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        generator_model_name: str = "gpt-4o", # Default to GPT-4o
        device: str = None,
        use_4bit: bool = True,
        temperature: float = 0.1
    ):
        """Initialize the RAG+KG Query Agent.
        
        Args:
            processor: Document processor instance with access to stores
            entity_extractor_model_name: Name of the *local* model for entity extraction
            generator_model_name: Name of the OpenAI model for answer synthesis (e.g., "gpt-4o")
            device: Device for the *local* entity extractor model ('cuda' or 'cpu')
            use_4bit: Whether to use 4-bit quantization for the *local* entity extractor
            temperature: Temperature for OpenAI generation
        """
        self.processor = processor
        self.generator_model_name = generator_model_name
        self.entity_extractor_model_name = entity_extractor_model_name
        self.temperature = temperature
        
        # Set device for local entity extractor
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing RAG+KG Query Agent:")
        logger.info(f"  - Entity Extractor (Local): {entity_extractor_model_name} on {self.device}")
        logger.info(f"  - Answer Generator (API): {generator_model_name}")
        
        # Initialize OpenAI client
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise ProcessingError(f"Failed to initialize OpenAI client: {e}")

        # Load local tokenizer and model *only* for entity extraction
        try:
            from transformers import BitsAndBytesConfig
            
            # Configure quantization if needed
            if use_4bit and self.device == "cuda":
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16
                )
            else:
                quantization_config = None
            
            # Load tokenizer and model
            self.entity_tokenizer = AutoTokenizer.from_pretrained(entity_extractor_model_name)
            self.entity_model = AutoModelForCausalLM.from_pretrained(
                entity_extractor_model_name,
                quantization_config=quantization_config,
                device_map="auto" if self.device == "cuda" else None,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            if self.device == "cpu":
                self.entity_model = self.entity_model.to(self.device)
                
            logger.info("Local Entity Extractor LLM loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize local entity extractor LLM: {e}", exc_info=True)
            # We might decide to proceed without local extraction or raise an error
            logger.warning("Could not load local entity extractor model. KG queries might be limited.")
            self.entity_tokenizer = None
            self.entity_model = None
    
    def _generate_text_local(self, prompt: str, max_new_tokens: int = 100) -> str:
        """Generate text from the LOCAL LLM (for entity extraction)."""
        if not self.entity_model or not self.entity_tokenizer:
            logger.warning("Local entity extractor model not loaded. Cannot generate text locally.")
            return "{}" # Return empty JSON string
            
        try:
            inputs = self.entity_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.entity_model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens, # Shorter length for entity extraction
                    temperature=0.1, # Low temp for deterministic extraction
                    do_sample=False, # No sampling for extraction
                    pad_token_id=self.entity_tokenizer.eos_token_id
                )
                
            response = self.entity_tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the prompt from the response
            # Find the end of the prompt within the response to remove it accurately
            prompt_end_index = response.find(prompt) + len(prompt) if prompt in response else 0
            response = response[prompt_end_index:].strip()
            return response
            
        except Exception as e:
            logger.error(f"Error generating text with local model: {e}", exc_info=True)
            raise ProcessingError(f"Failed to generate text with local model: {e}")

    def _generate_text_openai(self, prompt: str, max_new_tokens: int = 1536) -> str:
        """Generate text using the OpenAI API (for answer synthesis)."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.generator_model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering questions based on provided context."}, 
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_new_tokens,
                temperature=self.temperature,
                n=1,
                stop=None,
            )
            generated_text = response.choices[0].message.content.strip()
            return generated_text
        except Exception as e:
            logger.error(f"Error generating text via OpenAI API: {e}", exc_info=True)
            raise ProcessingError(f"Failed to generate text via OpenAI API: {e}")
    
    def _extract_entities_from_query(self, query: str) -> Dict[str, Any]:
        """Extract entities from the query using the LOCAL LLM."""
        try:
            # Prepare the prompt
            prompt = ENTITY_EXTRACTION_PROMPT.format(query=query)
            
            # Generate response using the local model
            response = self._generate_text_local(prompt)
            
            # Parse JSON response (ensure robust parsing)
            import json
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    result = json.loads(json_str)
                    # Remove None/null values
                    return {k: v for k, v in result.items() if v is not None}
                else:
                    logger.warning(f"Could not find JSON in entity extraction response: {response}")
                    return {}
            except json.JSONDecodeError as json_err:
                logger.warning(f"Failed to decode JSON from entity extractor: {json_err}. Response was: {response}")
                return {}
            
        except Exception as e:
            logger.error(f"Error extracting entities from query: {e}", exc_info=True)
            return {}  # Return empty dict on error
    
    def _construct_kg_queries(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construct queries for the knowledge graph based on extracted entities."""
        kg_queries = []
        
        if "record_series_number" in entities:
            # Direct lookup by record series number
            kg_queries.append({
                "type": "exact_match",
                "entity_type": "record_series_number",
                "value": entities["record_series_number"]
            })
            
        if "retention_period" in entities:
            # Find records with similar retention period
            kg_queries.append({
                "type": "similar",
                "entity_type": "retention_period",
                "value": entities["retention_period"]
            })
            
        if "disposition_action" in entities:
            # Find records with the specified disposition action
            kg_queries.append({
                "type": "similar",
                "entity_type": "disposition_action",
                "value": entities["disposition_action"]
            })
            
        if "legal_authority" in entities:
            # Find records citing this legal authority
            kg_queries.append({
                "type": "similar",
                "entity_type": "legal_authority",
                "value": entities["legal_authority"]
            })
            
        return kg_queries
    
    def _execute_kg_query(self, query_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a query against the knowledge graph."""
        try:
            if query_info["type"] == "exact_match":
                # Execute an exact match query
                # This would be a SQL query like:
                # SELECT * FROM entities WHERE type = ? AND value = ?
                entities = self.processor.knowledge_store.query_entities(
                    entity_type=query_info["entity_type"],
                    value=query_info["value"],
                    exact_match=True
                )
                return entities
                
            elif query_info["type"] == "similar":
                # Execute a similarity-based query
                # This would be a SQL query with LIKE operators or text search
                entities = self.processor.knowledge_store.query_entities(
                    entity_type=query_info["entity_type"],
                    value=query_info["value"],
                    exact_match=False
                )
                return entities
                
            else:
                logger.warning(f"Unknown query type: {query_info['type']}")
                return []
                
        except Exception as e:
            logger.error(f"Error executing KG query: {e}", exc_info=True)
            return []
    
    def _synthesize_answer(
        self, 
        query: str, 
        vector_results: List[Dict[str, Any]], 
        kg_results: List[Dict[str, Any]]
    ) -> str:
        """Synthesize an answer from the retrieved information using OpenAI API."""
        try:
            # Format vector results
            vector_context = "\n\n".join([
                f"Chunk {i+1} (Similarity: {r.score:.2f}):\n{r.content}"
                for i, r in enumerate(vector_results)
            ]) if vector_results else "No relevant documents found via semantic search."
            
            # Format KG results
            if kg_results:
                kg_entries = []
                for kg_result in kg_results:
                    if isinstance(kg_result, dict):
                        entry = f"- {kg_result.get('type', 'Entity')}: {kg_result.get('value', 'Unknown')}"
                        if 'document_id' in kg_result:
                            entry += f" (Document: {kg_result['document_id']})"
                        kg_entries.append(entry)
                kg_context = "\n".join(kg_entries)
            else:
                kg_context = "No relevant entities found in knowledge graph."
            
            # Prepare the prompt for OpenAI
            prompt = ANSWER_SYNTHESIS_PROMPT.format(
                query=query,
                vector_results=vector_context,
                kg_results=kg_context
            )
            
            # Generate response using OpenAI API
            response = self._generate_text_openai(prompt, max_new_tokens=1536)
            return response
            
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}", exc_info=True)
            return f"Error generating answer: {str(e)}"
    
    def query(self, query: str, top_k: int = 5, min_score: float = 0.6) -> Dict[str, Any]:
        """Perform a RAG+KG query on the knowledge base.
        
        Args:
            query: The user query
            top_k: Maximum number of results to retrieve
            min_score: Minimum similarity score for vector results
            
        Returns:
            Dict containing the query results
        """
        logger.info(f"Processing RAG+KG query: '{query[:50]}...'")
        
        try:
            # Step 1: Semantic search using vector embeddings
            vector_results = self.processor.search(
                query=query,
                top_k=top_k,
                min_score=min_score,
                use_graph=False
            )
            logger.info(f"Vector search returned {len(vector_results)} results")
            
            # Step 2: Extract entities from query (using local LLM)
            entities = self._extract_entities_from_query(query)
            logger.info(f"Extracted entities from query: {entities}")
            
            # Step 3: Construct and execute KG queries
            kg_queries = self._construct_kg_queries(entities)
            
            # Step 4: Execute KG queries and aggregate results
            kg_results = []
            for kg_query in kg_queries:
                kg_query_results = self._execute_kg_query(kg_query)
                kg_results.extend(kg_query_results)
            logger.info(f"Knowledge graph queries returned {len(kg_results)} results")
            
            # Step 5: Synthesize answer (using OpenAI API)
            answer = self._synthesize_answer(query, vector_results, kg_results)
            
            # Return the combined results
            return {
                "success": True,
                "answer": answer,
                "vector_results": [
                    {
                        "content": r.content,
                        "score": r.score,
                        "document_id": r.document_id,
                        "metadata": r.metadata
                    }
                    for r in vector_results
                ],
                "knowledge_graph_results": kg_results,
                "extracted_entities": entities
            }
            
        except Exception as e:
            logger.error(f"RAG+KG query failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            } 