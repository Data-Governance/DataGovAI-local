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

# Initialize session state right at the beginning - CRITICAL for preventing errors
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
# Use a dedicated key for the text input widget's state
if "input_key" not in st.session_state:
    st.session_state.input_key = ""
if "query_to_process" not in st.session_state: # Holds query only when submit is clicked
    st.session_state.query_to_process = None
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
    
    # Enhanced system prompt for better follow-ups, especially simplification
    system_prompt = """You are a helpful assistant answering follow-up questions based on previous context and conversation about Utah's General Retention Schedules (GRS).
Your responses should:
1. Directly address the follow-up query (e.g., clarification, simplification).
2. Use the provided conversation history and the context from the *initial* query to maintain consistency.
3. If asked to simplify or explain differently, significantly rephrase the information using clearer language, analogies, or breaking down complex points. Avoid just minor re-wording.
4. Stay factual and source-aware if referring back to GRS specifics.
5. If you cannot answer based on the available information, state that clearly.

You have access to the previous conversation and context. Reference this information to maintain continuity."""

    # Create messages array with system prompt first
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add reminder of the context
    context_reminder = f"Remember that the initial answer was based on this context from GRS documents:\n\n{last_context[:1000]}..."
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
            temperature=0.4 # Slightly increased temperature for potentially more creative simplification
        )
        answer = response.choices[0].message.content
        logger.info("Follow-up response generated successfully.")
        return answer
    except Exception as e:
        logger.error(f"Error calling OpenAI API for follow-up: {e}")
        st.error(f"Error generating response from LLM: {e}")
        return "Error: Could not generate follow-up response from LLM."

# --- Streamlit UI ---

st.set_page_config(
    page_title="DataGovAI - Utah GRS Knowledge Base Agent", # Updated title
    page_icon="./logo.png", # Use logo as icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# Display logo in the sidebar
st.sidebar.image("./logo.png", width=150) # Ensure logo path is correct

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

# --- Callback Function ---
# Function to update the text input's state without submitting
def set_input_text(text):
    st.session_state.input_key = text

# Left Sidebar - Sample Questions
with st.sidebar:
    st.markdown("### 📝 Sample Questions")
    
    # Organize questions by category in expanders (Updated with more questions)
    categories = {
        "Personnel & HR": {
            "Personnel Files": "What is the retention period for employee personnel files?",
            "Training Records": "How long should we keep employee training records?",
            "Job Applications": "What is the retention schedule for job applications?",
            "Volunteer Records": "Retention for volunteer records?",
            "Disciplinary Actions": "How are disciplinary action files handled?",
            "I-9 Forms": "What's the schedule for I-9 forms?"
        },
        "Administrative": {
            "Correspondence": "How long should we keep general correspondence?",
            "Meeting Minutes": "Disposition rules for meeting minutes?",
            "Meeting Recordings": "What is the disposition for audio/video recordings of meetings?",
            "Email Management": "What are the requirements for email retention?",
            "Policy Drafts": "How long must policy drafts be kept?",
            "Internal Memos": "Schedule for internal memos?"
        },
        "Financial & Legal": {
            "Financial Records": "What schedule covers accounts payable records?",
            "Contracts": "What is the retention period for contracts and agreements?",
            "Audit Records": "How long should we keep audit reports?",
            "Grant Records": "Retention schedule for grant records?",
            "Litigation Files": "How long to keep litigation files?",
            "Procurement Records": "Disposition of procurement records?"
        },
        "Facilities & Equipment": {
            "Facility Records": "How long should we keep building maintenance records?",
            "Equipment Logs": "What is the retention period for equipment maintenance logs?",
            "Property Files": "How long should property acquisition records be kept?",
            "Vehicle Logs": "Retention for vehicle maintenance logs?",
            "Compliance Reports": "Schedule for environmental compliance reports?",
            "Safety Inspections": "How long are safety inspection records kept?"
        }
    }
    
    for category, questions in categories.items():
        with st.expander(f"📁 {category}"):
            for title, question in questions.items():
                # Use the callback to update the input field's state
                st.button(
                    f"🔍 {title}",
                    key=f"btn_{title}",
                    on_click=set_input_text,
                    args=(question,) # Pass the question text to the callback
                )
    
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
    
    # -- Moved Upload/Save Section Here --
        # Section for session management
    st.markdown("### 💾 Session Management")
    # -- Save button moved down --
    st.markdown("---") # Add a separator
    st.markdown("### 📤 Upload/Save Session") # Updated title

    # Option to save current session
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
        st.markdown("<br>", unsafe_allow_html=True) # Add some space

    # Option to upload a saved session
    uploaded_file = st.file_uploader("Load a saved session", type="json", 
                               label_visibility="collapsed", # Make label less prominent
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

    st.markdown("---") # Add another separator
    st.markdown("[📚 View Official GRS Documentation](https://archives.utah.gov/rim/retention-schedules.html)")

# Main Content Area
st.title("DataGovAI - Utah GRS Knowledge Base Agent") # Updated Title

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

# Query input form
if st.session_state.conversation_mode:
    query_label = "💬 Continue the conversation:"
    submit_button_label = "Send Message"
else:
    query_label = "❓ Ask any question. For GRS information, include terms like 'retention period', 'schedule', etc.:"
    submit_button_label = "Ask Question"

# Use st.form for explicit submission
with st.form(key="query_form", clear_on_submit=True):
    # Bind text_input to the session state key
    query_typed_in = st.text_input(query_label, key="input_key")
    submit_button = st.form_submit_button(label=submit_button_label)

    # Process only when the form's submit button is clicked
    if submit_button and st.session_state.input_key:
        # Set the query to be processed in the next rerun using the state variable
        st.session_state.query_to_process = st.session_state.input_key

# --- Add "Explain Last Answer" Button --- 
# Only show if there's history and the last message was from the assistant
if st.session_state.conversation_history and st.session_state.conversation_history[-1]["role"] == "assistant":
    if st.button("💡 Explain Last Answer in Simpler Terms", key="explain_button"):
        # Set the specific follow-up query
        st.session_state.query_to_process = "Explain the previous answer in simpler terms."
        # Ensure we are in conversation mode for this type of follow-up
        st.session_state.conversation_mode = True 
        # Trigger a rerun to process the explanation query
        st.rerun() 

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
    # Check if a query was submitted via the form in the *previous* run
    if st.session_state.get("query_to_process"):
        query = st.session_state.query_to_process
        st.session_state.query_to_process = None # Clear the flag immediately

        logger.info(f"Processing submitted query: {query}")

        # Add user query to history *before* processing
        st.session_state.conversation_history.append({"role": "user", "content": query})

        # --- Determine Query Type and Process ---
        # **MODIFIED LOGIC**: Prioritize conversation_mode for follow-ups
        if st.session_state.conversation_mode and st.session_state.last_context_and_sources["context"]:
             # --- Follow-up Query in Conversation Mode (GRS or General) ---
            logger.info("Handling follow-up query in conversation mode.")
            with st.spinner("Generating follow-up response..."): # <-- ADDED SPINNER
                last_context = st.session_state.last_context_and_sources["context"]
                answer = generate_follow_up_response(
                    openai_client, config["openai_model"], query, st.session_state.conversation_history[:-1], last_context
                )

        elif is_grs_related(query):
             # --- RAG Process for New GRS Query ---
            logger.info("GRS-related query detected. Performing RAG retrieval.")
            # Ensure conversation mode is OFF for a new RAG search if it wasn't explicitly turned on
            st.session_state.conversation_mode = False 
            conn = None # Initialize conn
            try:
                # Get DB connection inside the processing block
                conn = get_db_connection(config["postgres_connection"])
                
                with st.spinner("Analyzing question and searching GRS documents..."): # <-- ADDED SPINNER
                    query_embedding = generate_query_embedding(embedding_model, query)
                    relevant_chunks_info = find_relevant_chunks(conn, query_embedding, top_k=5)
                    relevant_chunk_ids = [chunk_id for chunk_id, _, _ in relevant_chunks_info]

                    logger.info(f"Relevant chunk IDs (with distances): {[(cid, dist, doc) for cid, dist, doc in relevant_chunks_info]}")

                    chunk_details = get_chunk_text(conn, relevant_chunk_ids)

                # Format context and sources
                context_parts = []
                sources = []
                processed_chunk_ids = set() # Ensure unique sources

                # Order context by relevance (distance)
                for chunk_id, distance, doc_title_or_id in relevant_chunks_info:
                     if chunk_id in chunk_details and chunk_id not in processed_chunk_ids:
                         detail = chunk_details[chunk_id]
                         context_parts.append(f"Source: {detail.get('document_title', 'Unknown')}\nContent: {detail['content']}")
                         sources.append({
                             "chunk_id": chunk_id,
                             "distance": distance,
                             "document_title": detail.get('document_title', 'Unknown'),
                             "source_url": detail.get('source_url', '#'),
                             "content_preview": detail['content'][:150] + "..." # Add preview
                         })
                         processed_chunk_ids.add(chunk_id)

                context = "\n\n---\n\n".join(context_parts)
                st.session_state.last_context_and_sources = {"context": context, "sources": sources} # Store for potential follow-up

                # Generate response using RAG context
                with st.spinner("Generating GRS response..."): # <-- ADDED SPINNER
                    answer = generate_response(
                        openai_client, config["openai_model"], query, context, sources, st.session_state.conversation_history[:-1] # Pass history *before* current query
                    )
                # Automatically enable conversation mode after a successful RAG query
                st.session_state.conversation_mode = True 
                
            except Exception as e:
                logger.error(f"Error during GRS query processing: {e}", exc_info=True)
                st.error(f"An error occurred while processing your GRS query: {e}")
                answer = "Sorry, I encountered an error trying to answer your GRS question."
                # Ensure context is cleared on error so next query isn't treated as follow-up
                st.session_state.last_context_and_sources = {"context": "", "sources": []} 
                st.session_state.conversation_mode = False
            finally:
                 if conn:
                     conn.close()
                     logger.info("Database connection closed for query.")

        else:
            # --- General Question (Non-GRS, New Search) ---
            logger.info("Handling general non-GRS query.")
            # Ensure conversation mode is OFF
            st.session_state.conversation_mode = False 
            st.session_state.last_context_and_sources = {"context": "", "sources": []} # Clear context
            try:
                # Simple call to OpenAI for general questions
                with st.spinner("Generating general response..."): # <-- ADDED SPINNER
                    answer = generate_direct_response(
                         openai_client, 
                         config["openai_model"], 
                         query, 
                         st.session_state.conversation_history[:-1] # Pass previous history
                    )
            except Exception as e:
                logger.error(f"Error calling OpenAI for general query: {e}")
                st.error(f"An error occurred while processing your general query: {e}")
                answer = "Sorry, I encountered an error trying to answer your general question."

        # Add assistant response to history
        st.session_state.conversation_history.append({"role": "assistant", "content": answer})
        st.session_state.last_processed_query = query # Store the actually processed query

        # Rerun Streamlit to update the UI with the new messages and results
        st.rerun()

    # Find the last assistant message to display sources/evidence if available
    last_assistant_message = None
    for msg in reversed(st.session_state.conversation_history):
        if msg["role"] == "assistant":
            last_assistant_message = msg["content"]
            break

    if last_assistant_message:
        # Display evidence/sources only if the *last* processed query was GRS-related
        # Check against the stored last_processed_query
        if is_grs_related(st.session_state.last_processed_query):
            st.markdown("### 📖 Evidence & Sources")
            sources = st.session_state.last_context_and_sources.get("sources", [])
            if sources:
                 with st.expander("View Sources Used", expanded=False):
                     for i, source in enumerate(sources):
                         st.markdown(f"""
                         <div class="source-box">
                             <strong>Source {i+1}: {source.get('document_title', 'Unknown')}</strong> (Relevance: {1-source.get('distance', 0):.2f})<br>
                             <small><a href="{source.get('source_url', '#')}" target="_blank">{source.get('source_url', 'No URL')}</a></small>
                             <p style="font-size: 0.9em; color: #555;">{source.get('content_preview', 'No preview available.')}</p>
                         </div>
                         """, unsafe_allow_html=True)
            else:
                 st.info("No specific GRS sources were retrieved for the last response.")

            # Display the raw context used (optional, for debugging/transparency)
            # context = st.session_state.last_context_and_sources.get("context", "")
            # if context:
            #     with st.expander("View Raw Context Used", expanded=False):
            #         st.text_area("Context", value=context, height=200, disabled=True)

    # Add a footer or separator
    st.markdown("---")
    st.caption("DataGovAI - Utah Office of Data Privacy | GRS Knowledge Base Agent")

except Exception as e:
    st.error(f"❌ Application Error: {e}")
    logger.error(f"Critical Application Error: {e}", exc_info=True)
    # Remove the user query we added if there was an error
    if len(st.session_state.conversation_history) > 0:
        st.session_state.conversation_history.pop()
        st.session_state.last_processed_query = ""
 