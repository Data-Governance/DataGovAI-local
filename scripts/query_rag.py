import os
import sys
import argparse
import logging
from typing import List, Dict, Tuple

import psycopg2
import psycopg2.extras # For execute_values
from psycopg2.extensions import register_adapter, AsIs
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
# Import pgvector numpy support
from pgvector.psycopg2 import register_vector

# Add project root to path for imports if needed
# Assuming the script is run from the project root or this path is adjusted
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration Loading ---

def load_config() -> Dict[str, str]:
    """Load configuration from .env file."""
    load_dotenv()
    config = {
        "postgres_connection": os.getenv("POSTGRES_CONNECTION"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2"),
        "embedding_device": os.getenv("EMBEDDING_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini") # Or your preferred chat model
    }
    if not config["postgres_connection"] or not config["openai_api_key"]:
        raise ValueError("Missing required configuration in .env file (POSTGRES_CONNECTION, OPENAI_API_KEY)")
    # Add pgvector numpy support
    # register_adapter(np.ndarray, psycopg2.extras.execute_values) <-- Old method, likely incorrect
    # psycopg2.extensions.register_adapter(np.ndarray, lambda arr: AsIs("'" + arr.tolist().__str__().replace(" ", "") + "'")) <-- Also incorrect

    # Correct way to register numpy adapter with pgvector
    # This needs to be done *after* connecting typically, but we can do it here for simplicity
    # as long as a connection is made later where this registration applies.
    # A better place might be right after getting the connection.
    # We will move it after the connection is established.
    
    return config

# --- Core RAG Functions ---

def get_db_connection(conn_string: str):
    """Establish database connection and register pgvector."""
    try:
        conn = psycopg2.connect(conn_string)
        # Register pgvector types for this connection
        register_vector(conn)
        logger.info("Database connection established and pgvector registered.")
        return conn
    except Exception as e: # Catch broader exceptions during registration
        logger.error(f"Failed to connect to database or register pgvector: {e}")
        raise

def generate_query_embedding(text: str, model: SentenceTransformer) -> np.ndarray:
    """Generate embedding for the query text."""
    logger.info(f"Generating embedding for query: '{text[:50]}...'")
    embedding = model.encode([text], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0]

def find_relevant_chunks(conn, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
    """Find top_k relevant chunk IDs using vector similarity search directly on the chunks table."""
    logger.info(f"Searching for top {top_k} relevant chunks in 'chunks' table...")
    try:
        with conn.cursor() as cur:
            # Using the cosine distance operator (<=>) from pgvector
            # Querying the chunks table directly as embeddings are stored there
            cur.execute(
                """
                SELECT chunk_id, embedding <=> %s::vector AS distance
                FROM chunks
                WHERE embedding IS NOT NULL -- Ensure embedding exists
                ORDER BY distance ASC
                LIMIT %s;
                """,
                (query_embedding, top_k)
            )
            results = cur.fetchall()
            logger.info(f"Found {len(results)} relevant chunk candidates from 'chunks' table.")
            # Return chunk IDs and their distance scores
            return [(row[0], row[1]) for row in results]
    except Exception as e:
        logger.error(f"Error during vector search in chunks table: {e}")

def get_chunk_text(conn, chunk_ids: List[str]) -> Dict[str, str]:
    """Retrieve text content for given chunk IDs."""
    if not chunk_ids:
        return {}
    logger.info(f"Retrieving text for {len(chunk_ids)} chunks...")
    try:
        with conn.cursor() as cur:
            # Use chunk_id (character varying) for lookup, not the integer id
            cur.execute(
                "SELECT chunk_id, content FROM chunks WHERE chunk_id = ANY(%s)",
                (chunk_ids,)
            )
            results = cur.fetchall()
            # Return as dict mapping chunk_id to content
            return {row[0]: row[1] for row in results}
    except Exception as e:
        logger.error(f"Error retrieving chunk text: {e}")
        conn.rollback()
        return {}

def generate_response(client: OpenAI, model_name: str, query: str, context: str) -> str:
    """Generate response using OpenAI LLM with query and context."""
    logger.info("Generating response using OpenAI...")
    system_prompt = "You are a helpful assistant answering questions based on the provided context from Utah's General Retention Schedules (GRS). Answer the user's query using ONLY the information given in the context. If the context doesn't contain the answer, state that the information is not available in the provided context."
    # Simpler f-string definition for the user prompt
    user_prompt = f"""Context:
{context}

Query: {query}

Answer:"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2 # Slightly creative but mostly factual
        )
        answer = response.choices[0].message.content
        logger.info("Response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return "Error: Could not generate response from LLM."

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Query the Knowledge Base using RAG.")
    parser.add_argument("query", type=str, help="The question to ask the knowledge base.")
    parser.add_argument("-k", "--top_k", type=int, default=5, help="Number of relevant chunks to retrieve.")
    args = parser.parse_args()

    logger.info("--- Starting RAG Query --- ")

    try:
        # 1. Load Config
        config = load_config()

        # 2. Initialize Models & DB Connection
        logger.info(f"Loading embedding model: {config['embedding_model']}")
        embedding_model = SentenceTransformer(config['embedding_model'], device=config['embedding_device'])
        
        logger.info(f"Initializing OpenAI client with model: {config['openai_model']}")
        openai_client = OpenAI(api_key=config['openai_api_key'])
        
        conn = get_db_connection(config['postgres_connection'])

        # 3. Generate Query Embedding
        query_embedding = generate_query_embedding(args.query, embedding_model)

        # 4. Find Relevant Chunks (IDs and Scores)
        relevant_chunk_data = find_relevant_chunks(conn, query_embedding, args.top_k)
        if not relevant_chunk_data:
            print("Could not find any relevant documents for the query.")
            return

        relevant_chunk_ids = [item[0] for item in relevant_chunk_data]
        logger.info(f"Relevant chunk IDs (with distances): {relevant_chunk_data}")

        # 5. Retrieve Chunk Text
        chunk_texts_map = get_chunk_text(conn, relevant_chunk_ids)
        
        # Reconstruct context string in order of relevance (lowest distance first)
        context_parts = []
        for chunk_id, _ in relevant_chunk_data:
            if chunk_id in chunk_texts_map:
                context_parts.append(chunk_texts_map[chunk_id])
            else:
                 logger.warning(f"Could not retrieve text for relevant chunk ID: {chunk_id}")
                 
        # Explicitly escape backslashes for newline characters
        context_string = "\n\n---\n\n".join(context_parts)

        if not context_string:
            print("Could not retrieve context for the relevant chunks.")
            return
            
        logger.debug(f"Retrieved Context:\n{context_string[:500]}...")

        # 6. Generate Response
        answer = generate_response(openai_client, config['openai_model'], args.query, context_string)

        # 7. Print Result
        print("\n" + "="*20 + " Query Answer " + "="*20)
        print(f"Query: {args.query}")
        print("\nAnswer:")
        print(answer)
        print("\n" + "="*54)

    except Exception as e:
        logger.error(f"An error occurred during the query process: {e}", exc_info=True)
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")
        logger.info("--- RAG Query Finished --- ")


if __name__ == "__main__":
    # Need to import torch here if using CUDA checks in load_config
    import torch 
    main() 