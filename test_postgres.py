import psycopg2

# Connection string with explicit options - use params instead of URL
conn_params = {
    "host": "127.0.0.1",  # Use explicit IP instead of 'localhost'
    "port": "5432",
    "dbname": "knowledge_base",
    "user": "majid",
    "password": "password"
}

try:
    # Connect directly with psycopg2 using keyword arguments
    print(f"Attempting connection with params: {conn_params}")
    conn = psycopg2.connect(**conn_params)
    
    # If we get here, connection succeeded
    print("Connection successful!")
    
    # Test a simple query to verify
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user")
        db, user = cur.fetchone()
        print(f"Connected to database: {db} as user: {user}")
    
    # Close the connection
    conn.close()
    
except Exception as e:
    print(f"Connection failed: {e}")
