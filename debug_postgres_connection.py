import psycopg2
from sqlalchemy import create_engine, make_url
from sqlalchemy.engine import URL
import os
from urllib.parse import urlparse

# --- Connection Parameters ---
# User 'majid'
user_majid = "majid"
password_majid = "password" # Replace if different

# Default 'postgres' user (often requires sudo access or specific pg_hba.conf setup)
user_postgres = "postgres"
password_postgres = None # Set password if you configured one for the postgres user, often None/blank initially

host_ip = "127.0.0.1"
host_name = "localhost"
port = 5432
dbname = "knowledge_base"

env_connection_string = os.environ.get("POSTGRES_CONNECTION")

def test_connection(method_name, connection_func):
    print(f"\n--- Testing Method: {method_name} ---")
    try:
        conn = connection_func()
        print("Connection SUCCESSFUL!")
        # Test a simple query
        try:
            if hasattr(conn, 'cursor'): # Direct psycopg2 connection
                 with conn.cursor() as cur:
                    cur.execute("SELECT current_database(), current_user")
                    db, usr = cur.fetchone()
                    print(f" -> Query successful: Connected to DB '{db}' as USER '{usr}'")
                 conn.close()
            else: # SQLAlchemy engine
                 with conn.connect() as connection:
                    result = connection.execute("SELECT current_database(), current_user")
                    db, usr = result.fetchone()
                    print(f" -> Query successful: Connected to DB '{db}' as USER '{usr}'")
                 conn.dispose()
        except Exception as qe:
            print(f" -> Query FAILED: {type(qe).__name__}: {qe}")
            if hasattr(conn, 'close'): conn.close()
            if hasattr(conn, 'dispose'): conn.dispose()
    except Exception as e:
        print(f"Connection FAILED: {type(e).__name__}: {e}")

# --- Test Cases for 'majid' user ---
print("\n=== TESTING AS USER 'majid' ===")

# 1a. Direct psycopg2 (majid): DSN String (127.0.0.1)
def connect_psycopg2_dsn_majid_ip():
    dsn = f"host={host_ip} port={port} dbname={dbname} user={user_majid} password={password_majid}"
    print(f"Attempting with psycopg2 DSN: {dsn}")
    return psycopg2.connect(dsn)
test_connection("Direct psycopg2/majid (DSN String, 127.0.0.1)", connect_psycopg2_dsn_majid_ip)

# 1b. Direct psycopg2 (majid): DSN String (localhost)
def connect_psycopg2_dsn_majid_host():
    dsn = f"host={host_name} port={port} dbname={dbname} user={user_majid} password={password_majid}"
    print(f"Attempting with psycopg2 DSN: {dsn}")
    return psycopg2.connect(dsn)
test_connection("Direct psycopg2/majid (DSN String, localhost)", connect_psycopg2_dsn_majid_host)

# 2. Direct psycopg2 (majid): Keyword Arguments (127.0.0.1)
def connect_psycopg2_kwargs_majid_ip():
    params = {"host": host_ip, "port": port, "dbname": dbname, "user": user_majid, "password": password_majid}
    print(f"Attempting with psycopg2 kwargs: {params}")
    return psycopg2.connect(**params)
test_connection("Direct psycopg2/majid (Keyword Args, 127.0.0.1)", connect_psycopg2_kwargs_majid_ip)

# 3a. SQLAlchemy (majid): Standard URL String (127.0.0.1)
def connect_sqlalchemy_url_majid_ip():
    url = f"postgresql://{user_majid}:{password_majid}@{host_ip}:{port}/{dbname}"
    print(f"Attempting with SQLAlchemy URL: {url}")
    return create_engine(url)
test_connection("SQLAlchemy/majid (Standard URL, 127.0.0.1)", connect_sqlalchemy_url_majid_ip)

# 3b. SQLAlchemy (majid): Standard URL String (localhost)
def connect_sqlalchemy_url_majid_host():
    url = f"postgresql://{user_majid}:{password_majid}@{host_name}:{port}/{dbname}"
    print(f"Attempting with SQLAlchemy URL: {url}")
    return create_engine(url)
test_connection("SQLAlchemy/majid (Standard URL, localhost)", connect_sqlalchemy_url_majid_host)

# 4. SQLAlchemy (majid): Using make_url object (127.0.0.1)
def connect_sqlalchemy_make_url_majid_ip():
    url_str = f"postgresql://{user_majid}:{password_majid}@{host_ip}:{port}/{dbname}"
    print(f"Attempting with SQLAlchemy make_url from: {url_str}")
    parsed_url = make_url(url_str)
    return create_engine(parsed_url)
test_connection("SQLAlchemy/majid (make_url object, 127.0.0.1)", connect_sqlalchemy_make_url_majid_ip)

# 5. SQLAlchemy (majid): Using URL object (127.0.0.1)
def connect_sqlalchemy_url_obj_majid_ip():
    url_obj = URL.create(
        drivername="postgresql",
        username=user_majid,
        password=password_majid,
        host=host_ip,
        port=port,
        database=dbname
    )
    print(f"Attempting with SQLAlchemy URL object: {url_obj}")
    return create_engine(url_obj)
test_connection("SQLAlchemy/majid (URL object, 127.0.0.1)", connect_sqlalchemy_url_obj_majid_ip)

# 6. SQLAlchemy (majid): Reading from Environment Variable (Uses whatever is in .env)
def connect_sqlalchemy_env_majid():
    if env_connection_string:
        print(f"Attempting with SQLAlchemy using ENV POSTGRES_CONNECTION: {env_connection_string}")
        return create_engine(env_connection_string)
    else:
        print("ENV POSTGRES_CONNECTION not set, skipping test.")
        raise ValueError("Environment variable not set")
test_connection("SQLAlchemy/majid (from Environment Variable)", connect_sqlalchemy_env_majid)

# 7. SQLAlchemy (majid): URL with SSL modes (127.0.0.1)
for mode in ["disable", "allow", "prefer", "require"]:
    def create_connect_func(sslmode=mode):
        def connect_sqlalchemy_ssl_majid_ip():
            url = f"postgresql://{user_majid}:{password_majid}@{host_ip}:{port}/{dbname}?sslmode={sslmode}"
            print(f"Attempting with SQLAlchemy URL: {url}")
            # Add connect_args for psycopg2 compatibility if needed, but try simple first
            return create_engine(url)
        return connect_sqlalchemy_ssl_majid_ip
    test_connection(f"SQLAlchemy/majid (URL, 127.0.0.1, sslmode={mode})", create_connect_func(mode))


# --- Test Cases for 'postgres' user ---
print("\n=== TESTING AS USER 'postgres' ===")

# 8a. Direct psycopg2 (postgres): DSN String (127.0.0.1)
def connect_psycopg2_dsn_postgres_ip():
    dsn_parts = [f"host={host_ip}", f"port={port}", f"dbname={dbname}", f"user={user_postgres}"]
    if password_postgres:
        dsn_parts.append(f"password={password_postgres}")
    dsn = " ".join(dsn_parts)
    print(f"Attempting with psycopg2 DSN: {dsn}")
    return psycopg2.connect(dsn)
test_connection("Direct psycopg2/postgres (DSN String, 127.0.0.1)", connect_psycopg2_dsn_postgres_ip)

# 8b. Direct psycopg2 (postgres): DSN String (localhost)
def connect_psycopg2_dsn_postgres_host():
    dsn_parts = [f"host={host_name}", f"port={port}", f"dbname={dbname}", f"user={user_postgres}"]
    if password_postgres:
        dsn_parts.append(f"password={password_postgres}")
    dsn = " ".join(dsn_parts)
    print(f"Attempting with psycopg2 DSN: {dsn}")
    return psycopg2.connect(dsn)
test_connection("Direct psycopg2/postgres (DSN String, localhost)", connect_psycopg2_dsn_postgres_host)

# 9. Direct psycopg2 (postgres): Keyword Arguments (127.0.0.1)
def connect_psycopg2_kwargs_postgres_ip():
    params = {"host": host_ip, "port": port, "dbname": dbname, "user": user_postgres}
    if password_postgres:
        params["password"] = password_postgres
    print(f"Attempting with psycopg2 kwargs: {params}")
    return psycopg2.connect(**params)
test_connection("Direct psycopg2/postgres (Keyword Args, 127.0.0.1)", connect_psycopg2_kwargs_postgres_ip)

# 10a. SQLAlchemy (postgres): Standard URL String (127.0.0.1)
def connect_sqlalchemy_url_postgres_ip():
    pw_str = f":{password_postgres}" if password_postgres else ""
    url = f"postgresql://{user_postgres}{pw_str}@{host_ip}:{port}/{dbname}"
    print(f"Attempting with SQLAlchemy URL: {url}")
    return create_engine(url)
test_connection("SQLAlchemy/postgres (Standard URL, 127.0.0.1)", connect_sqlalchemy_url_postgres_ip)

# 10b. SQLAlchemy (postgres): Standard URL String (localhost)
def connect_sqlalchemy_url_postgres_host():
    pw_str = f":{password_postgres}" if password_postgres else ""
    url = f"postgresql://{user_postgres}{pw_str}@{host_name}:{port}/{dbname}"
    print(f"Attempting with SQLAlchemy URL: {url}")
    return create_engine(url)
test_connection("SQLAlchemy/postgres (Standard URL, localhost)", connect_sqlalchemy_url_postgres_host)

# --- GRS Document Test Data and Queries ---
print("\n=== GRS DOCUMENT TEST DATA AND QUERIES ===")

# Sample table creation SQL
grs_tables_sql = """
-- Document metadata table
CREATE TABLE IF NOT EXISTS grs_documents (
    id SERIAL PRIMARY KEY,
    grs_number VARCHAR(20) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),
    retention_period TEXT,
    disposition TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document content and embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES grs_documents(id),
    chunk_text TEXT NOT NULL,
    chunk_embedding vector(384),  -- Using all-mpnet-base-v2 embeddings
    chunk_number INTEGER,
    UNIQUE(document_id, chunk_number)
);

-- Entity extraction
CREATE TABLE IF NOT EXISTS extracted_entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES grs_documents(id),
    entity_type VARCHAR(50),
    entity_value TEXT,
    confidence FLOAT
);

-- Document relationships
CREATE TABLE IF NOT EXISTS document_relationships (
    id SERIAL PRIMARY KEY,
    source_doc_id INTEGER REFERENCES grs_documents(id),
    target_doc_id INTEGER REFERENCES grs_documents(id),
    relationship_type VARCHAR(50),
    UNIQUE(source_doc_id, target_doc_id, relationship_type)
);
"""

# Sample test data
test_documents = [
    {
        "grs_number": "GRS-1234",
        "title": "Financial Audit Reports",
        "category": "financial",
        "subcategory": "audit",
        "retention_period": "Retain for 7 years",
        "disposition": "Destroy",
        "content": "This schedule governs the retention of financial audit reports..."
    },
    {
        "grs_number": "GRS-5678",
        "title": "Personnel Files",
        "category": "personnel",
        "subcategory": "employee_records",
        "retention_period": "Retain for 65 years after termination",
        "disposition": "Transfer to Archives",
        "content": "This schedule applies to employee personnel files including..."
    }
]

# Sample queries for testing
test_queries = {
    "basic_search": """
        SELECT grs_number, title, retention_period 
        FROM grs_documents 
        WHERE category = 'financial';
    """,
    
    "full_text_search": """
        SELECT d.grs_number, d.title, c.chunk_text 
        FROM grs_documents d 
        JOIN document_chunks c ON d.id = c.document_id 
        WHERE to_tsvector('english', c.chunk_text) @@ to_tsquery('english', 'audit & retention');
    """,
    
    "vector_similarity": """
        SELECT d.grs_number, d.title, c.chunk_text,
               (c.chunk_embedding <=> %s) as similarity
        FROM grs_documents d 
        JOIN document_chunks c ON d.id = c.document_id 
        ORDER BY similarity ASC 
        LIMIT 5;
    """,
    
    "related_documents": """
        SELECT d2.grs_number, d2.title, r.relationship_type
        FROM grs_documents d1
        JOIN document_relationships r ON d1.id = r.source_doc_id
        JOIN grs_documents d2 ON r.target_doc_id = d2.id
        WHERE d1.grs_number = %s;
    """
}

def test_grs_queries(connection):
    """Test GRS document queries on the database"""
    try:
        with connection.cursor() as cur:
            # Test table creation
            cur.execute(grs_tables_sql)
            print("Successfully created GRS tables")
            
            # Insert test data
            cur.execute("""
                INSERT INTO grs_documents (grs_number, title, category, subcategory, retention_period, disposition)
                VALUES (%(grs_number)s, %(title)s, %(category)s, %(subcategory)s, %(retention_period)s, %(disposition)s)
                ON CONFLICT (grs_number) DO NOTHING
                RETURNING id;
            """, test_documents[0])
            print("Successfully inserted test document")
            
            # Test basic search
            cur.execute(test_queries["basic_search"])
            results = cur.fetchall()
            print(f"Found {len(results)} documents in basic search")
            
    except Exception as e:
        print(f"Error testing GRS queries: {type(e).__name__}: {e}")

# Add GRS testing to the main connection tests if desired
for method_name, connection_func in [
    ("SQLAlchemy/postgres (Standard URL, localhost)", connect_sqlalchemy_url_postgres_host)
]:
    try:
        engine = connection_func()
        with engine.connect() as conn:
            test_grs_queries(conn)
    except Exception as e:
        print(f"Failed to test GRS queries with {method_name}: {type(e).__name__}: {e}")

print("\n--- GRS Testing Finished ---")
print("\n--- Debugging Script Finished ---") 