import streamlit as st
import os
import sys
import logging
from typing import List, Dict, Tuple
# Import torch early for CUDA checks
import torch 

import psycopg2
import psycopg2.extras # For execute_values
from psycopg2.extensions import register_adapter, AsIs
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
# Import pgvector numpy support
from pgvector.psycopg2 import register_vector

# Configure logging (optional for Streamlit, but can be helpful)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration Loading & Caching ---

# Use Streamlit's caching for expensive operations like loading models or config
@st.cache_resource # Cache resource across sessions
def load_config_and_clients():
    """Load configuration, initialize clients and models."""
    load_dotenv()
    # Cleaned up dictionary definition
    config = {
        "postgres_connection": os.getenv("POSTGRES_CONNECTION"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2"),
        "embedding_device": os.getenv("EMBEDDING_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
    }
    if not config["postgres_connection"] or not config["openai_api_key"]:
        st.error("Missing required configuration in .env file (POSTGRES_CONNECTION, OPENAI_API_KEY)")
        st.stop()

    try:
        logger.info(f"Loading embedding model: {config['embedding_model']}")
        embedding_model = SentenceTransformer(config['embedding_model'], device=config['embedding_device'])
        logger.info("Embedding model loaded.")
        
        logger.info(f"Initializing OpenAI client with model: {config['openai_model']}")
        openai_client = OpenAI(api_key=config['openai_api_key'])
        logger.info("OpenAI client initialized.")

        return config, embedding_model, openai_client
    except Exception as e:
        st.error(f"Error initializing models or clients: {e}")
        logger.error(f"Initialization Error: {e}", exc_info=True)
        st.stop()

# Separate function for DB connection (not cached as resource, needs re-connecting)
def get_db_connection(conn_string: str):
    """Establish database connection and register pgvector."""
    try:
        conn = psycopg2.connect(conn_string)
        register_vector(conn) # Register pgvector types for this connection
        logger.info("Database connection established and pgvector registered.")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database or register pgvector: {e}")
        st.error(f"Database Connection Error: {e}")
        st.stop() # Stop execution if DB connection fails

# --- Core RAG Functions (adapted for Streamlit) ---

# @st.cache_data # Cache data retrieval based on inputs
def generate_query_embedding(_embedding_model, text: str) -> np.ndarray:
    """Generate embedding for the query text."""
    # Note: _embedding_model passed explicitly to be hashable for caching if enabled
    logger.info(f"Generating embedding for query: '{text[:50]}...'")
    embedding = _embedding_model.encode([text], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0]

# @st.cache_data
def find_relevant_chunks(conn, _query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
    """Find top_k relevant chunk IDs using vector similarity search directly on the chunks table."""
    logger.info(f"Searching for top {top_k} relevant chunks in 'chunks' table...")
    results = []
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT chunk_id, embedding <=> %s::vector AS distance
                FROM chunks
                WHERE embedding IS NOT NULL
                ORDER BY distance ASC
                LIMIT %s;
                """
            cur.execute(sql, (_query_embedding, top_k))
            results = cur.fetchall()
            logger.info(f"Found {len(results)} relevant chunk candidates from 'chunks' table.")
            return [(row[0], row[1]) for row in results]
    except Exception as e:
        logger.error(f"Error during vector search in chunks table: {e}")
        st.warning(f"Vector search failed: {e}")
        return [] # Return empty list on error
    # Note: Removed rollback as SELECT doesn't modify data

# @st.cache_data
def get_chunk_text(conn, chunk_ids: List[str]) -> Dict[str, str]:
    """Retrieve text content for given chunk IDs."""
    if not chunk_ids:
        return {}
    logger.info(f"Retrieving text for {len(chunk_ids)} chunks...")
    chunk_map = {}
    try:
        with conn.cursor() as cur:
            sql = "SELECT chunk_id, content FROM chunks WHERE chunk_id = ANY(%s)"
            cur.execute(sql, (chunk_ids,))
            results = cur.fetchall()
            chunk_map = {row[0]: row[1] for row in results}
            return chunk_map
    except Exception as e:
        logger.error(f"Error retrieving chunk text: {e}")
        st.warning(f"Failed to retrieve chunk text: {e}")
        return {} # Return empty dict on error
    # Note: Removed rollback as SELECT doesn't modify data

# No caching for LLM call as it depends on context which changes
def generate_response(_openai_client, model_name: str, query: str, context: str) -> str:
    """Generate response using OpenAI LLM with query and context."""
    if not context:
        return "Could not retrieve relevant context to answer the query."
    
    logger.info("Generating response using OpenAI...")
    system_prompt = "You are a helpful assistant answering questions based on the provided context from Utah's General Retention Schedules (GRS). Answer the user's query using ONLY the information given in the context. If the context doesn't contain the answer, state that the information is not available in the provided context."
    user_prompt = f"""Context:
{context}

Query: {query}

Answer:"""
    
    try:
        response = _openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2 
        )
        answer = response.choices[0].message.content
        logger.info("Response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        st.error(f"Error generating response from LLM: {e}")
        return "Error: Could not generate response from LLM."

# --- Streamlit UI ---

st.set_page_config(page_title="GRS Knowledge Base Agent", layout="wide")

st.title("Utah GRS Knowledge Base Agent")
st.markdown("Ask questions about Utah's General Retention Schedules (GRS). This agent uses Retrieval-Augmented Generation (RAG) to find relevant information from the GRS documents and generate answers.")

# Load models and config once
config, embedding_model, openai_client = load_config_and_clients()

# Sample Questions Expander
with st.expander("Sample Questions"):
    st.markdown("- What is the retention period for employee personnel files?")
    st.markdown("- How long should we keep general correspondence?")
    st.markdown("- What is the disposition for audio/video recordings of meetings?")
    st.markdown("- Are there specific requirements for storing electronic records?")
    st.markdown("- What schedule covers accounts payable records?")

# User Input
st.markdown("## Ask a Question")
query = st.text_input("Enter your question about the GRS:", key="query_input")

if query:
    st.markdown("--- ")
    # Establish DB connection for this query
    conn = get_db_connection(config['postgres_connection'])
    
    if conn:
        try:
            # 1. Generate Query Embedding
            with st.spinner("Generating query embedding..."):
                query_embedding = generate_query_embedding(embedding_model, query)
            
            # 2. Find Relevant Chunks
            with st.spinner("Searching for relevant information..."):
                relevant_chunk_data = find_relevant_chunks(conn, query_embedding, top_k=5)
            
            if not relevant_chunk_data:
                st.warning("Could not find relevant documents for the query in the knowledge base.")
            else:
                relevant_chunk_ids = [item[0] for item in relevant_chunk_data]
                logger.info(f"Relevant chunk IDs (with distances): {relevant_chunk_data}")
                
                # 3. Retrieve Chunk Text
                with st.spinner("Retrieving context..."):
                    chunk_texts_map = get_chunk_text(conn, relevant_chunk_ids)
                
                # Reconstruct context string in order of relevance
                context_parts = []
                retrieved_context_details = [] # For display
                for chunk_id, distance in relevant_chunk_data:
                    if chunk_id in chunk_texts_map:
                        context_parts.append(chunk_texts_map[chunk_id])
                        retrieved_context_details.append(f"- Chunk ID: `{chunk_id}` (Distance: {distance:.4f})")
                    else:
                        logger.warning(f"Could not retrieve text for relevant chunk ID: {chunk_id}")
                        st.warning(f"Context retrieval issue for chunk {chunk_id}")
                
                context_string = "\n\n---\n\n".join(context_parts)

                # 4. Generate Response
                if not context_string:
                    st.error("Failed to retrieve context for the relevant chunks.")
                else:
                    with st.spinner("Generating answer..."):
                        answer = generate_response(openai_client, config['openai_model'], query, context_string)
                    
                    # 5. Display Result
                    st.markdown("### Answer")
                    st.markdown(answer)
                    
                    # Optional: Display retrieved context details
                    with st.expander("Retrieved Context Details"):
                        st.markdown("\n".join(retrieved_context_details))
                        st.text_area("Full Context Sent to LLM", context_string, height=200)
                        
        except Exception as e:
            st.error(f"An error occurred during the query process: {e}")
            logger.error(f"Error during Streamlit query execution: {e}", exc_info=True)
        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed for query.")

# Need torch for CUDA check in load_config
# if 'torch' not in sys.modules: # Remove this check at the end
#     try:
#         import torch
#     except ImportError:
#         logger.warning("Torch is not installed, CUDA check might fail.")
 