import streamlit as st
import os
import sys
import logging
from typing import List, Dict, Tuple
# Import torch early for CUDA checks
import torch 

# Disable Streamlit's file watcher - This helps avoid the torch.classes issue
os.environ['STREAMLIT_FILE_WATCHER_TYPE'] = 'none'

# Fix for Streamlit/Torch compatibility issue
import asyncio
try:
    asyncio.get_running_loop()
except RuntimeError:
    # Create an event loop if there isn't one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Monkeypatch torch.classes to avoid Streamlit watcher error
import torch.classes
if not hasattr(torch.classes, '__path__'):
    class PathFix:
        _path = []
    torch.classes.__path__ = PathFix()

import psycopg2
import psycopg2.extras # For execute_values
from psycopg2.extensions import register_adapter, AsIs
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
# Import pgvector numpy support
from pgvector.psycopg2 import register_vector

# Initialize session state right at the beginning - CRITICAL for preventing errors
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "query" not in st.session_state:
    st.session_state.query = ""
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "last_context_and_sources" not in st.session_state:
    st.session_state.last_context_and_sources = {"context": "", "sources": []}
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = False
if "last_processed_query" not in st.session_state:
    st.session_state.last_processed_query = ""

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
            
            # Verify column structure
            if chunks_exists:
                # Check if embedding column exists with correct type
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'chunks' AND column_name = 'embedding'
                    );
                """)
                embedding_exists = cur.fetchone()[0]
                
                if not embedding_exists:
                    logger.warning("Adding embedding column to chunks table")
                    try:
                        cur.execute("ALTER TABLE chunks ADD COLUMN embedding vector(768);")
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Could not add embedding column: {e}")
                        conn.rollback()
                        
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
            # First check if title column exists in documents table
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'title'
                );
            """)
            title_exists = cur.fetchone()[0]
            
            # Try the full query with document join
            try:
                if title_exists:
                    sql = """
                        SELECT c.chunk_id, c.embedding <=> %s::vector AS distance, d.title
                        FROM chunks c
                        JOIN documents d ON c.document_id = d.document_id
                        WHERE c.embedding IS NOT NULL
                        ORDER BY distance ASC
                        LIMIT %s;
                        """
                else:
                    # Use document_id as fallback if title doesn't exist
                    sql = """
                        SELECT c.chunk_id, c.embedding <=> %s::vector AS distance, d.document_id
                        FROM chunks c
                        JOIN documents d ON c.document_id = d.document_id
                        WHERE c.embedding IS NOT NULL
                        ORDER BY distance ASC
                        LIMIT %s;
                        """
                cur.execute(sql, (_query_embedding, top_k))
                results = cur.fetchall()
                logger.info(f"Found {len(results)} relevant chunk candidates with document information.")
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
            # Check if title column exists in documents table
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'documents' AND column_name = 'title'
                );
            """)
            title_exists = cur.fetchone()[0]
            
            # First try the detailed query with document join
            try:
                if title_exists:
                    sql = """
                        SELECT c.chunk_id, c.content, d.title, d.source_url, d.metadata
                        FROM chunks c
                        JOIN documents d ON c.document_id = d.document_id
                        WHERE c.chunk_id = ANY(%s)
                    """
                else:
                    # Use document_id as fallback if title doesn't exist
                    sql = """
                        SELECT c.chunk_id, c.content, d.document_id, NULL, NULL
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
def generate_response(_openai_client, model_name: str, query: str, context: str, sources: List[Dict], conversation_history=None) -> str:
    """Generate response using OpenAI LLM with query, context, source information, and conversation history."""
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
6. Conversational: Maintain a helpful and conversational tone while staying factual

Format your response with:
1. A direct answer to the query
2. Supporting evidence from the GRS documents
3. Specific references to source documents
4. Any relevant caveats or limitations"""

    # Create messages array with system prompt first
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if available
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add the current context and query
    user_prompt = f"""Context:
{context}

Sources:
{sources_text}

Query: {query}

Please provide a comprehensive, evidence-based response using the format specified."""

    # Add the current query to messages
    messages.append({"role": "user", "content": user_prompt})
    
    try:
        response = _openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2 
        )
        answer = response.choices[0].message.content
        logger.info("Response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        st.error(f"Error generating response from LLM: {e}")
        return "Error: Could not generate response from LLM."

# Function to handle direct follow-up without RAG retrieval
def generate_follow_up_response(_openai_client, model_name: str, query: str, conversation_history, last_context: str) -> str:
    """Generate a follow-up response using only conversation history and last context."""
    logger.info("Generating follow-up response using OpenAI...")
    
    system_prompt = """You are a helpful assistant answering questions about Utah's General Retention Schedules (GRS).
Your responses should be:
1. Evidence-based: Only use information explicitly stated in the provided context and conversation history
2. Well-structured: Use clear paragraphs and bullet points when appropriate
3. Source-aware: Reference specific GRS documents when appropriate
4. Conversational: Maintain a helpful and conversational tone while staying factual
5. Clear about limitations: If you can't answer based on provided information, say so clearly

You have access to the previous conversation and context. Reference this information to maintain continuity."""

    # Create messages array with system prompt first
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add reminder of the context
    context_reminder = f"Remember that your answers must be based on this context from GRS documents:\n\n{last_context[:1000]}..."
    messages.append({"role": "system", "content": context_reminder})
    
    # Add truncated conversation history (keep last 10 messages maximum)
    if conversation_history:
        messages.extend(conversation_history[-10:])
    
    # Add the current query
    messages.append({"role": "user", "content": query})
    
    try:
        response = _openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.3
        )
        answer = response.choices[0].message.content
        logger.info("Follow-up response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API for follow-up: {e}")
        st.error(f"Error generating response from LLM: {e}")
        return "Error: Could not generate follow-up response from LLM."

# --- Streamlit UI ---

# Set page configuration with logo
st.set_page_config(
    page_title="DataGovAI - Utah GRS Knowledge Base Agent",
    page_icon="./logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display logo in the sidebar
st.sidebar.image("./logo.png", width=150)

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
        padding: 15px;
        margin: 10px 0;
        border-left: 5px solid #4da6ff;
    }
    .evidence-box {
        border-left: 3px solid #00acb5;
        padding-left: 10px;
        margin: 15px 0;
        background-color: #fafafa;
        padding: 10px;
        border-radius: 5px;
    }
    h1, h2, h3 {
        color: #1f497d;
    }
    .stExpander {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    footer {
        visibility: hidden;
    }
    .category-box {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #e6e6e6;
        margin-bottom: 10px;
    }
    .sample-questions {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    div[data-testid="stSidebarContent"] {
        background-color: #f8fafc;
    }
    </style>
""", unsafe_allow_html=True)

# Left Sidebar - Sample Questions and Session Management
with st.sidebar:
    # Section for session management
    st.markdown("### 💾 Session Management")
    
    # Option to save current session - use len() check which is safer than a direct boolean check
    if len(st.session_state.conversation_history) > 0:
        import json
        conversation_json = json.dumps({
            "session_id": st.session_state.session_id,
            "conversation_history": st.session_state.conversation_history,
            "last_context_and_sources": st.session_state.last_context_and_sources,
            "conversation_mode": st.session_state.conversation_mode
        }, indent=2)
        
        st.download_button(
            label="💾 Save Current Session",
            data=conversation_json,
            file_name=f"grs_session_{st.session_state.session_id[:8]}.json",
            mime="application/json",
            help="Save your current conversation to continue later"
        )
    
    # Option to upload a saved session
    uploaded_file = st.file_uploader("📤 Upload Saved Session", type="json", 
                               help="Upload a previously saved conversation to continue where you left off")
    
    if uploaded_file is not None:
        try:
            uploaded_data = json.load(uploaded_file)
            # Validate the uploaded data has the required fields
            if all(key in uploaded_data for key in ["conversation_history", "last_context_and_sources", "conversation_mode"]):
                # Update session state with uploaded data
                st.session_state.conversation_history = uploaded_data["conversation_history"]
                st.session_state.last_context_and_sources = uploaded_data["last_context_and_sources"]
                st.session_state.conversation_mode = uploaded_data["conversation_mode"]
                st.success("✅ Session loaded successfully!")
                # Rerun to reflect changes
                st.rerun()
            else:
                st.error("❌ Invalid session file format. Please upload a valid session file.")
        except Exception as e:
            st.error(f"❌ Error loading session: {e}")
    
    st.markdown("---")
    st.markdown("### 📝 Sample Questions")
    
    # Organize questions by category in expanders
    categories = {
        "Personnel & HR": {
            "Personnel Files": "What is the retention period for employee personnel files?",
            "Training Records": "How long should we keep employee training records?",
            "Job Applications": "What is the retention schedule for job applications?"
        },
        "Administrative": {
            "Correspondence": "How long should we keep general correspondence?",
            "Meeting Records": "What is the disposition for audio/video recordings of meetings?",
            "Email Management": "What are the requirements for email retention?"
        },
        "Financial & Legal": {
            "Financial Records": "What schedule covers accounts payable records?",
            "Legal Documents": "What is the retention period for contracts and agreements?",
            "Audit Records": "How long should we keep audit reports?"
        },
        "Facilities & Equipment": {
            "Facility Records": "How long should we keep building maintenance records?",
            "Equipment Logs": "What is the retention period for equipment maintenance logs?",
            "Property Files": "How long should property acquisition records be kept?"
        }
    }
    
    for category, questions in categories.items():
        with st.expander(f"📁 {category}"):
            for title, question in questions.items():
                if st.button(f"🔍 {title}", key=f"btn_{title}"):
                    st.session_state.query = question
    
    # GRS Quick Reference section in the same sidebar
    st.markdown("---")
    st.markdown("### 📋 GRS Quick Reference")
    
    with st.expander("What is GRS?"):
        st.write("General Retention Schedules (GRS) are standardized guidelines that determine how long different types of government records must be kept and what happens to them afterward.")
    
    with st.expander("Key Components"):
        st.markdown("- **Retention Period:** How long to keep records")
        st.markdown("- **Disposition:** What happens after retention period")
        st.markdown("- **Classification:** Access restrictions")
    
    with st.expander("Common Terms"):
        st.markdown("- **Permanent:** Records kept indefinitely")
        st.markdown("- **Temporary:** Records with set disposal date")
        st.markdown("- **Vital:** Essential for operations")
    
    st.markdown("[📚 View Official GRS Documentation](https://archives.utah.gov/rim/retention-schedules.html)")

# Main Content Area
st.title("DataGovAI - Utah GRS Knowledge Base Agent")

# Show session status if a conversation is in progress
if len(st.session_state.conversation_history) > 0:
    st.markdown(f"""
    <div style="background-color: #e6f7f2; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #00acb5;">
        <p style="margin: 0;"><strong>🔵 Active Session:</strong> {len(st.session_state.conversation_history) // 2} exchanges • 
        <span style="color: #666;">Session ID: {st.session_state.session_id[:8]}</span> • 
        Mode: {("Conversation" if st.session_state.conversation_mode else "New Search")}</p>
    </div>
    """, unsafe_allow_html=True)

# Main introduction
st.markdown("""
<div style="background-color: #f5f7f9; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p style="margin-bottom: 10px;">This AI assistant can answer both general questions and questions about Utah's <strong>General Retention Schedules (GRS)</strong>.</p>
    <ul style="margin-bottom: 0;">
        <li><strong>General questions:</strong> Answered directly using GPT-4o</li>
        <li><strong>GRS questions:</strong> Answered using evidence from official GRS documentation</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Main content area - Question Input and Results
st.markdown("## ❓ Ask a Question")

# Display conversation history with improved formatting
if len(st.session_state.conversation_history) > 0:
    st.markdown("""
    <div style="background-color: #f5f7f9; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <h3 style="color: #1f497d; margin-top: 0;">💬 Conversation History</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Only show the last 6 exchanges (12 messages) to keep the UI clean
    display_history = st.session_state.conversation_history[-12:] if len(st.session_state.conversation_history) > 12 else st.session_state.conversation_history
    
    for message in display_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div style="background-color: #e6f3ff; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                <strong>You:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)
        elif message["role"] == "assistant":
            st.markdown(f"""
            <div style="background-color: #f0f0f0; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                <strong>Assistant:</strong> {message['content']}
            </div>
            """, unsafe_allow_html=True)
    
    # Add options for conversation control with better UI
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🗑️ Clear Conversation", key="clear_convo"):
            st.session_state.conversation_history = []
            st.session_state.last_context_and_sources = {"context": "", "sources": []}
            st.session_state.conversation_mode = False
            st.session_state.last_processed_query = ""
            st.rerun()
    
    with col2:
        if st.session_state.conversation_mode:
            if st.button("🔍 New Search", key="new_search"):
                st.session_state.conversation_mode = False
                # Keep conversation history but reset context
                st.session_state.last_context_and_sources = {"context": "", "sources": []}
        else:
            if st.button("💬 Continue Chat", key="cont_chat"):
                st.session_state.conversation_mode = True
    
    with col3:
        if st.button("📥 Save Conversation", key="save_convo"):
            # Create a downloadable version of the conversation
            import json
            conversation_json = json.dumps(st.session_state.conversation_history, indent=2)
            st.download_button(
                label="Download Conversation",
                data=conversation_json,
                file_name=f"conversation_{st.session_state.session_id[:8]}.json",
                mime="application/json"
            )

# Query input with improved UI based on conversation state
if st.session_state.conversation_mode:
    query_label = "💬 Continue the conversation:"
    submit_button_label = "Send Message"
else:
    query_label = "❓ Ask any question. For GRS information, include terms like 'retention period', 'schedule', etc.:"
    submit_button_label = "Ask Question"

# Create a form for the query input to handle submission better
with st.form(key="query_form", clear_on_submit=True):
    query = st.text_input(query_label, key="query_input", value=st.session_state.get("query", ""))
    submit_button = st.form_submit_button(label=submit_button_label)
    
    # Only process if there's a query and the submit button is clicked
    if submit_button and query:
        st.session_state.query = query

# Load models and config once
config, embedding_model, openai_client = load_config_and_clients()

# Function to determine if a query is about GRS
def is_grs_related(query: str) -> bool:
    """
    Determine if a query is related to GRS (General Retention Schedules).
    This is a simple keyword-based approach that can be improved with ML techniques.
    """
    grs_keywords = [
        'grs', 'general retention', 'retention schedule', 'retention period', 
        'document retention', 'record retention', 'records management',
        'disposition', 'archive', 'archives', 'records', 'record keeping',
        'utah archives', 'utah records', 'retain', 'retention', 'schedule',
        'disposal', 'preserve', 'preservation', 'destroy', 'destruction',
        'permanent record', 'temporary record', 'vital record'
    ]
    
    # Convert query to lowercase for case-insensitive matching
    query = query.lower()
    
    # Check if any of the GRS keywords are in the query
    return any(keyword in query for keyword in grs_keywords)

# Function to generate a direct response without RAG for general questions
def generate_direct_response(_openai_client, model_name: str, query: str, conversation_history=None) -> str:
    """Generate a direct response using GPT-4o without RAG for general questions."""
    logger.info("Generating direct response using OpenAI for general question...")
    
    system_prompt = """You are a helpful assistant who can answer general questions as well as questions about Utah's General Retention Schedules (GRS).
For general questions, provide helpful, accurate, and conversational responses.
For questions about GRS, direct the user to ask specifically about retention schedules, as you'll need to search the knowledge base."""

    # Create messages array with system prompt first
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add truncated conversation history (keep last 10 messages maximum)
    if conversation_history:
        messages.extend(conversation_history[-10:])
    
    # Add the current query
    messages.append({"role": "user", "content": query})
    
    try:
        response = _openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7  # Slightly higher temperature for general conversation
        )
        answer = response.choices[0].message.content
        logger.info("Direct response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API for direct response: {e}")
        st.error(f"Error generating response from LLM: {e}")
        return "Error: Could not generate a response."

# Main app logic wrapped in try-except for robust error handling
try:
    # Get the query from session state (set by the form)
    query = st.session_state.get("query", "")
    
    # Check if this query is new (not the same as the last processed query)
    if query and query != st.session_state.last_processed_query:
        # Save the current query as the last processed query to prevent duplicates
        st.session_state.last_processed_query = query
        
        # Save the user query to conversation history
        st.session_state.conversation_history.append({"role": "user", "content": query})
        
        # Determine if we're in conversation mode or RAG search mode
        if st.session_state.conversation_mode and st.session_state.last_context_and_sources["context"]:
            # Follow-up conversation mode - use last context and conversation history
            with st.spinner("🤔 Generating response..."):
                answer = generate_follow_up_response(
                    openai_client,
                    config['openai_model'],
                    query,
                    st.session_state.conversation_history[:-1],  # Exclude the query we just added
                    st.session_state.last_context_and_sources["context"]
                )
                
            # Save to conversation history
            st.session_state.conversation_history.append({"role": "assistant", "content": answer})
            
            # Display the answer
            st.markdown("### 📝 Answer")
            st.markdown(answer)
            
            # Display Sources from the previous RAG query
            with st.expander("📚 Source Documents (from initial search)"):
                st.markdown("This conversation is based on these GRS documents:")
                for source in st.session_state.last_context_and_sources["sources"]:
                    doc_title = source['document_title']
                    doc_id = ""
                    
                    # Try to extract GRS document ID from title
                    if "GRS-" in doc_title or "RS-" in doc_title:
                        doc_id = doc_title
                    else:
                        # Extract any document IDs from the title
                        import re
                        id_match = re.search(r'(GRS-\d+|RS-\d+)', doc_title)
                        if id_match:
                            doc_id = id_match.group(0)
                        else:
                            doc_id = doc_title
                    
                    st.markdown(f"""
                    <div class='source-box'>
                        📄 <b>{doc_title}</b>
                        <br>
                        📋 Document ID: {doc_id}
                    </div>
                    """, unsafe_allow_html=True)
            
            # After generating the response, clear the query and reset processing state
            st.session_state.query = ""
            st.session_state.last_processed_query = ""
            # Force a rerun to show the updated conversation and clear the input
            st.rerun()
        
        else:
            # Check if this is a GRS-related question or a general question
            if is_grs_related(query):
                # GRS-related question - use RAG search
                st.markdown("---")
                # Clear conversation mode flag when doing a new search
                st.session_state.conversation_mode = False
                
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
                            # Remove the user query we added since we couldn't find an answer
                            if len(st.session_state.conversation_history) > 0:
                                st.session_state.conversation_history.pop()
                            # Clear the query and reset processing state
                            st.session_state.query = ""
                            st.session_state.last_processed_query = ""
                            st.rerun()
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
                                # Remove the user query we added since we couldn't find an answer
                                if len(st.session_state.conversation_history) > 0:
                                    st.session_state.conversation_history.pop()
                                # Clear the query and reset processing state
                                st.session_state.query = ""
                                st.session_state.last_processed_query = ""
                                st.rerun()
                            else:
                                with st.spinner("🤔 Generating comprehensive answer..."):
                                    answer = generate_response(
                                        openai_client, 
                                        config['openai_model'], 
                                        query, 
                                        context_string, 
                                        sources, 
                                        st.session_state.conversation_history[:-1]  # Exclude the query we just added
                                    )
                                
                                # Save context and sources for future follow-ups
                                st.session_state.last_context_and_sources = {
                                    "context": context_string,
                                    "sources": sources
                                }
                                
                                # Save to conversation history
                                st.session_state.conversation_history.append({"role": "assistant", "content": answer})
                                
                                # 5. Display Result
                                st.markdown("### 📝 Answer")
                                st.markdown(answer)
                                
                                # Display Sources
                                with st.expander("📚 Source Documents"):
                                    st.markdown("This answer was generated based on the following GRS documents:")
                                    for source in sources:
                                        doc_title = source['document_title']
                                        doc_id = ""
                                        
                                        # Try to extract GRS document ID from title or content if available
                                        if "GRS-" in doc_title or "RS-" in doc_title:
                                            doc_id = doc_title
                                        else:
                                            # Extract any document IDs from the title
                                            import re
                                            id_match = re.search(r'(GRS-\d+|RS-\d+)', doc_title)
                                            if id_match:
                                                doc_id = id_match.group(0)
                                            else:
                                                doc_id = doc_title
                                        
                                        st.markdown(f"""
                                        <div class='source-box'>
                                            📄 <b>{doc_title}</b>
                                            <br>
                                            📋 Document ID: {doc_id}
                                            <br>
                                            <small>Note: Direct document links are not available in this demo. In a production environment, 
                                            these would link to the official Utah Archives GRS documents.</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                # Display Raw Context (for transparency)
                                with st.expander("🔍 View Retrieved Context"):
                                    st.markdown("The AI used the following excerpts to generate the answer:")
                                    for chunk_id, distance, _ in relevant_chunk_data:
                                        if chunk_id in chunk_texts_map:
                                            chunk_info = chunk_texts_map[chunk_id]
                                            # Try to extract document ID
                                            content = chunk_info['content']
                                            doc_title = chunk_info['document_title']
                                            
                                            # Look for GRS codes in the content
                                            import re
                                            grs_match = re.search(r'(GRS-\d+|RS-\d+)', content + " " + doc_title)
                                            grs_id = grs_match.group(0) if grs_match else "Unknown GRS"
                                            
                                            # Format for display
                                            st.markdown(f"""
                                            <div class='evidence-box'>
                                                <div style='background-color: #f5f5f5; padding: 5px; margin-bottom: 5px; border-radius: 3px;'>
                                                    <strong>Source:</strong> {doc_title} <span style='color: #666;'>({grs_id})</span><br>
                                                    <span style='color: #888; font-size: 0.8em;'>Relevance score: {1.0 - float(distance):.2f}</span>
                                                </div>
                                                {content}
                                            </div>
                                            """, unsafe_allow_html=True)
                                
                                # Enable conversation mode after first RAG query
                                st.session_state.conversation_mode = True
                                # Clear the query and reset processing state
                                st.session_state.query = ""
                                st.session_state.last_processed_query = ""
                                st.rerun()
                                        
                    except Exception as e:
                        st.error(f"❌ An error occurred during the query process: {e}")
                        logger.error(f"Error during Streamlit query execution: {e}", exc_info=True)
                        # Remove the user query we added since we couldn't find an answer
                        if len(st.session_state.conversation_history) > 0:
                            st.session_state.conversation_history.pop()
                        # Clear the query and reset processing state
                        st.session_state.query = ""
                        st.session_state.last_processed_query = ""
                        st.rerun()
                    finally:
                        if conn:
                            conn.close()
                            logger.info("Database connection closed for query.")
            else:
                # General question - use direct GPT-4o response without RAG
                with st.spinner("🤔 Generating response..."):
                    answer = generate_direct_response(
                        openai_client,
                        config['openai_model'],
                        query,
                        st.session_state.conversation_history[:-1]  # Exclude the query we just added
                    )
                
                # Save to conversation history
                st.session_state.conversation_history.append({"role": "assistant", "content": answer})
                
                # Display the answer
                st.markdown("### 📝 Answer")
                st.markdown(answer)
                
                # Note about general question
                st.info("This was a general question answered directly by GPT-4o. For questions about Utah's General Retention Schedules (GRS), the system will search the knowledge base for relevant information.")

                # Clear the query and reset processing state
                st.session_state.query = ""
                st.session_state.last_processed_query = ""
                st.rerun()
        
        # Clear the query input after processing
        st.session_state.query = ""
        
except Exception as e:
    st.error(f"❌ Application Error: {e}")
    logger.error(f"Critical Application Error: {e}", exc_info=True)
    # Remove the user query we added if there was an error
    if len(st.session_state.conversation_history) > 0:
        st.session_state.conversation_history.pop()
        st.session_state.last_processed_query = ""

# Footer
st.markdown("---")
st.markdown("""
<small>💡 This AI assistant uses Retrieval-Augmented Generation (RAG) to provide accurate, 
evidence-based answers from Utah's GRS documentation. All responses are generated based on 
official documents and include references to source materials.</small>
""", unsafe_allow_html=True)
 