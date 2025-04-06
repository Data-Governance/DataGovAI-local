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

# DEBUG: Print .env loading and contents
load_dotenv(verbose=True)
logger.info(f"POSTGRES_CONNECTION from env: {os.getenv('POSTGRES_CONNECTION')}")
# Explicitly set the connection string with proper password
os.environ['POSTGRES_CONNECTION'] = 'postgresql://postgres:password@127.0.0.1:5432/knowledge_base'
logger.info(f"Updated POSTGRES_CONNECTION: {os.getenv('POSTGRES_CONNECTION')}")

# --- Configuration Loading & Caching ---

# Use Streamlit's caching for expensive operations like loading models or config
@st.cache_resource # Cache resource across sessions
def load_config_and_clients():
    """Load configuration, initialize clients and models."""
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
        
        # Verify and initialize database structure if needed
        verify_db_structure(conn)
        
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database or register pgvector: {e}")
        st.error(f"Database Connection Error: {e}")
        st.stop() # Stop execution if DB connection fails

def verify_db_structure(conn):
    """Verify that the database has the required tables and structure."""
    try:
        with conn.cursor() as cur:
            # Check if chunks table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'chunks'
                );
            """)
            chunks_exists = cur.fetchone()[0]
            
            # Check if documents table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'documents'
                );
            """)
            documents_exists = cur.fetchone()[0]
            
            if not chunks_exists:
                logger.warning("Chunks table does not exist, creating...")
                # Create chunks table with minimum required fields
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT,
                        content TEXT NOT NULL,
                        embedding vector(768)
                    );
                """)
                conn.commit()
                logger.info("Created chunks table")
                
                # Insert a sample record for testing
                cur.execute("""
                    INSERT INTO chunks (chunk_id, document_id, content) 
                    VALUES ('sample_chunk_001', 'sample_doc_001', 'This is a sample document chunk for testing. It contains information about Utah GRS.') 
                    ON CONFLICT (chunk_id) DO NOTHING;
                """)
                conn.commit()
                
            if not documents_exists:
                logger.warning("Documents table does not exist, creating...")
                # Create documents table with minimum required fields
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT PRIMARY KEY,
                        title TEXT,
                        source_url TEXT,
                        metadata JSONB
                    );
                """)
                conn.commit()
                logger.info("Created documents table")
                
                # Insert a sample record for testing
                cur.execute("""
                    INSERT INTO documents (document_id, title, source_url, metadata) 
                    VALUES ('sample_doc_001', 'Sample GRS Document', 'https://archives.utah.gov/rim/retention-schedules.html', '{"type": "sample", "version": "1.0"}') 
                    ON CONFLICT (document_id) DO NOTHING;
                """)
                conn.commit()
                
            # Set up foreign key relationship if both tables exist now
            if chunks_exists and documents_exists:
                # Check if foreign key exists
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.table_constraints
                    WHERE constraint_name = 'fk_chunks_document_id'
                    AND table_name = 'chunks';
                """)
                fk_exists = cur.fetchone()[0] > 0
                
                if not fk_exists:
                    # Try to add foreign key - may fail if data integrity issues
                    try:
                        cur.execute("""
                            ALTER TABLE chunks
                            ADD CONSTRAINT fk_chunks_document_id
                            FOREIGN KEY (document_id)
                            REFERENCES documents(document_id);
                        """)
                        conn.commit()
                        logger.info("Added foreign key constraint between chunks and documents")
                    except Exception as e:
                        logger.warning(f"Could not add foreign key constraint: {e}")
                        conn.rollback()
            
            logger.info("Database structure verification completed")
            
    except Exception as e:
        logger.error(f"Error verifying database structure: {e}")
        conn.rollback()
        raise

# --- Core RAG Functions (adapted for Streamlit) ---

# @st.cache_data # Cache data retrieval based on inputs
def generate_query_embedding(_embedding_model, text: str) -> np.ndarray:
    """Generate embedding for the query text."""
    # Note: _embedding_model passed explicitly to be hashable for caching if enabled
    logger.info(f"Generating embedding for query: '{text[:50]}...'")
    embedding = _embedding_model.encode([text], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0]

# @st.cache_data
def find_relevant_chunks(conn, _query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, str]]:
    """Find top_k relevant chunks using vector similarity search, including document source."""
    logger.info(f"Searching for top {top_k} relevant chunks in 'chunks' table...")
    results = []
    try:
        with conn.cursor() as cur:
            # First try the full query with document join
            try:
                sql = """
                    SELECT c.chunk_id, c.embedding <=> %s::vector AS distance, d.title
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.document_id
                    WHERE c.embedding IS NOT NULL
                    ORDER BY distance ASC
                    LIMIT %s;
                    """
                cur.execute(sql, (_query_embedding, top_k))
                results = cur.fetchall()
                logger.info(f"Found {len(results)} relevant chunk candidates with document titles.")
                return [(row[0], row[1], row[2]) for row in results]
            except Exception as e:
                logger.warning(f"Join query failed, trying simple query: {e}")
                # Rollback on error to clear the transaction state
                conn.rollback()
                # Fallback to simple query without joins
                sql = """
                    SELECT chunk_id, embedding <=> %s::vector AS distance
                    FROM chunks
                    WHERE embedding IS NOT NULL
                    ORDER BY distance ASC
                    LIMIT %s;
                    """
                cur.execute(sql, (_query_embedding, top_k))
                results = cur.fetchall()
                logger.info(f"Found {len(results)} relevant chunk candidates (basic query).")
                return [(row[0], row[1], "Unknown Source") for row in results]
    except Exception as e:
        logger.error(f"Error during vector search in chunks table: {e}")
        # Rollback on error to clear the transaction state
        conn.rollback()
        st.warning(f"Vector search failed: {e}")
        return []

# @st.cache_data
def get_chunk_text(conn, chunk_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """Retrieve text content and metadata for given chunk IDs."""
    if not chunk_ids:
        return {}
    logger.info(f"Retrieving text for {len(chunk_ids)} chunks...")
    chunk_map = {}
    try:
        with conn.cursor() as cur:
            # First try the detailed query with document join
            try:
                sql = """
                    SELECT c.chunk_id, c.content, d.title, d.source_url, d.metadata
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.document_id
                    WHERE c.chunk_id = ANY(%s)
                """
                cur.execute(sql, (chunk_ids,))
                results = cur.fetchall()
                for row in results:
                    chunk_map[row[0]] = {
                        'content': row[1],
                        'document_title': row[2] or "Unknown Document",
                        'source_url': row[3] or "#",
                        'metadata': row[4] or {}
                    }
                if results:
                    logger.info("Retrieved chunks with document metadata.")
                    return chunk_map
            except Exception as e:
                logger.warning(f"Detailed query failed, trying basic query: {e}")
                # Rollback on error to clear the transaction state
                conn.rollback()
                
            # Fallback to basic query
            sql = "SELECT chunk_id, content FROM chunks WHERE chunk_id = ANY(%s)"
            cur.execute(sql, (chunk_ids,))
            results = cur.fetchall()
            for row in results:
                chunk_map[row[0]] = {
                    'content': row[1],
                    'document_title': "Document " + row[0][:8],
                    'source_url': "#",
                    'metadata': {}
                }
            logger.info("Retrieved basic chunk content without document metadata.")
            return chunk_map
    except Exception as e:
        logger.error(f"Error retrieving chunk text: {e}")
        # Rollback on error to clear the transaction state
        conn.rollback()
        st.warning(f"Failed to retrieve chunk text: {e}")
        return {}

# No caching for LLM call as it depends on context which changes
def generate_response(_openai_client, model_name: str, query: str, context: str, sources: List[Dict]) -> str:
    """Generate response using OpenAI LLM with query, context, and source information."""
    if not context:
        return "Could not retrieve relevant context to answer the query."
    
    logger.info("Generating response using OpenAI...")
    
    # Format sources for the prompt
    sources_text = "\n".join([
        f"- {source['document_title']} ({source['source_url']})"
        for source in sources if source['document_title'] and source['source_url']
    ])
    
    system_prompt = """You are a helpful assistant answering questions about Utah's General Retention Schedules (GRS).
Your responses should be:
1. Evidence-based: Only use information explicitly stated in the provided context
2. Well-structured: Use clear paragraphs and bullet points when appropriate
3. Source-aware: Reference specific GRS documents when providing information
4. Comprehensive: Cover all relevant aspects from the context
5. Clear about limitations: If information is not in the context, say so explicitly

Format your response with:
1. A direct answer to the query
2. Supporting evidence from the GRS documents
3. Specific references to source documents
4. Any relevant caveats or limitations"""

    user_prompt = f"""Context:
{context}

Sources:
{sources_text}

Query: {query}

Please provide a comprehensive, evidence-based response using the format specified."""
    
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

st.set_page_config(
    page_title="Utah GRS Knowledge Base Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-bottom: 10px;
    }
    .source-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .evidence-box {
        border-left: 3px solid #00acb5;
        padding-left: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Utah GRS Knowledge Base Agent")
st.markdown("""
This AI assistant helps you find information about Utah's General Retention Schedules (GRS).
It provides evidence-based answers using official GRS documentation.
""")

# Load models and config once
config, embedding_model, openai_client = load_config_and_clients()

# Initialize session state
if "query" not in st.session_state:
    st.session_state.query = ""

# Sample Questions in Sidebar
st.sidebar.markdown("### 📝 Sample Questions")
sample_questions = {
    "Personnel Records": "What is the retention period for employee personnel files?",
    "Correspondence": "How long should we keep general correspondence?",
    "Meeting Records": "What is the disposition for audio/video recordings of meetings?",
    "Electronic Records": "Are there specific requirements for storing electronic records?",
    "Financial Records": "What schedule covers accounts payable records?",
    "Training Records": "How long should we keep employee training records?",
    "Legal Documents": "What is the retention period for contracts and agreements?",
    "Email Management": "What are the requirements for email retention?",
    "Facility Records": "How long should we keep building maintenance records?",
    "HR Documents": "What is the retention schedule for job applications?"
}

st.sidebar.markdown("Click any sample question or type your own:")
for category, question in sample_questions.items():
    if st.sidebar.button(f"🔍 {category}", key=f"btn_{category}"):
        st.session_state.query = question

# User Input
st.markdown("## ❓ Ask a Question")
query = st.text_input("Enter your question about the GRS:", key="query_input", value=st.session_state.get("query", ""))

# Main app logic wrapped in try-except for robust error handling
try:
    if query:
        st.markdown("---")
        # Establish DB connection for this query
        conn = get_db_connection(config['postgres_connection'])
        
        if conn:
            try:
                # 1. Generate Query Embedding
                with st.spinner("🔍 Analyzing your question..."):
                    query_embedding = generate_query_embedding(embedding_model, query)
                
                # 2. Find Relevant Chunks
                with st.spinner("📚 Searching through GRS documents..."):
                    relevant_chunk_data = find_relevant_chunks(conn, query_embedding, top_k=5)
                
                if not relevant_chunk_data:
                    st.warning("⚠️ Could not find relevant documents for the query in the knowledge base.")
                else:
                    relevant_chunk_ids = [item[0] for item in relevant_chunk_data]
                    logger.info(f"Relevant chunk IDs (with distances): {relevant_chunk_data}")
                    
                    # 3. Retrieve Chunk Text and Metadata
                    with st.spinner("📄 Gathering context..."):
                        chunk_texts_map = get_chunk_text(conn, relevant_chunk_ids)
                    
                    # Prepare context and sources
                    context_parts = []
                    sources = []
                    for chunk_id, distance, doc_title in relevant_chunk_data:
                        if chunk_id in chunk_texts_map:
                            chunk_info = chunk_texts_map[chunk_id]
                            context_parts.append(chunk_info['content'])
                            sources.append({
                                'document_title': chunk_info['document_title'],
                                'source_url': chunk_info['source_url']
                            })
                        else:
                            logger.warning(f"Could not retrieve text for relevant chunk ID: {chunk_id}")
                    
                    context_string = "\n\n---\n\n".join(context_parts)

                    # 4. Generate Response
                    if not context_string:
                        st.error("❌ Failed to retrieve context for the relevant chunks.")
                    else:
                        with st.spinner("🤔 Generating comprehensive answer..."):
                            answer = generate_response(openai_client, config['openai_model'], query, context_string, sources)
                        
                        # 5. Display Result
                        st.markdown("### 📝 Answer")
                        st.markdown(answer)
                        
                        # Display Sources
                        with st.expander("📚 Source Documents"):
                            st.markdown("This answer was generated based on the following GRS documents:")
                            for source in sources:
                                if source['document_title'] and source['source_url']:
                                    st.markdown(f"""
                                    <div class='source-box'>
                                        📄 <b>{source['document_title']}</b><br>
                                        🔗 <a href="{source['source_url']}" target="_blank">View Source Document</a>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                            st.markdown("""
                            <small>Note: The response is generated based on the content of these documents. 
                            Always verify critical information by consulting the original source documents.</small>
                            """, unsafe_allow_html=True)
                        
                        # Display Raw Context (for transparency)
                        with st.expander("🔍 View Retrieved Context"):
                            st.markdown("The AI used the following excerpts to generate the answer:")
                            for chunk_id, distance, _ in relevant_chunk_data:
                                if chunk_id in chunk_texts_map:
                                    chunk_info = chunk_texts_map[chunk_id]
                                    st.markdown(f"""
                                    <div class='evidence-box'>
                                        <small>From: {chunk_info['document_title']}</small><br>
                                        {chunk_info['content']}
                                    </div>
                                    """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"❌ An error occurred during the query process: {e}")
                logger.error(f"Error during Streamlit query execution: {e}", exc_info=True)
            finally:
                if conn:
                    conn.close()
                    logger.info("Database connection closed for query.")
except Exception as e:
    st.error(f"❌ Application Error: {e}")
    logger.error(f"Critical Application Error: {e}", exc_info=True)

# Footer
st.markdown("---")
st.markdown("""
<small>💡 This AI assistant uses Retrieval-Augmented Generation (RAG) to provide accurate, 
evidence-based answers from Utah's GRS documentation. All responses are generated based on 
official documents and include references to source materials.</small>
""", unsafe_allow_html=True)
 