import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(verbose=True)

# Print PostgreSQL connection string
postgres_conn = os.getenv("POSTGRES_CONNECTION")
print(f"POSTGRES_CONNECTION: {postgres_conn}")

# Print EMBEDDING_MODEL and related variables
print(f"EMBEDDING_MODEL: {os.getenv('EMBEDDING_MODEL')}")
print(f"EMBEDDING_DEVICE: {os.getenv('EMBEDDING_DEVICE')}")

# Check if all required config is present
required_vars = ["POSTGRES_CONNECTION", "OPENAI_API_KEY", "EMBEDDING_MODEL"]
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f"Missing required variables: {', '.join(missing)}")
else:
    print("All required environment variables are present.")

# Test PG connection
try:
    import psycopg2
    from pgvector.psycopg2 import register_vector
    
    # Get connection string
    conn_string = os.getenv("POSTGRES_CONNECTION")
    print(f"Attempting to connect using: {conn_string}")
    
    # Connect
    conn = psycopg2.connect(conn_string)
    register_vector(conn)
    
    # Test query
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user;")
        db, user = cur.fetchone()
        print(f"Successfully connected to database '{db}' as user '{user}'")
        
        # Check pgvector
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        if cur.fetchone():
            print("pgvector extension is installed and working")
        else:
            print("pgvector extension is NOT installed")
    
    # Close connection
    conn.close()
    print("Database connection test completed successfully")
    
except Exception as e:
    print(f"Database connection error: {e}") 