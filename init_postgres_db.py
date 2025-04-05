"""Initializes the PostgreSQL database schema."""

import os
import sys
import logging

# Add src to path to allow importing knowledge_base_agent modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    from knowledge_base_agent.storage.postgresql.base import get_engine, init_db
    from knowledge_base_agent.config import get_config
    # Import models to ensure they are registered with Base
    import knowledge_base_agent.storage.postgresql.models 
except ImportError as e:
    print(f"Error importing necessary modules: {e}", file=sys.stderr)
    print("Ensure PYTHONPATH includes 'src' or run from project root.", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Attempting to initialize database schema...")
    try:
        # Load configuration to get connection string
        config = get_config() 
        pg_connection = config.storage.postgres_connection
        
        if not pg_connection:
            pg_connection = os.environ.get("POSTGRES_CONNECTION")

        if not pg_connection:
            logger.error("PostgreSQL connection string not found in config or environment variables.")
            sys.exit(1)
            
        logger.info(f"Using connection string: {pg_connection}")
        
        # Get engine and initialize database (this creates tables)
        engine = get_engine(connection_string=pg_connection)
        logger.info("Initializing database...")
        init_db(engine=engine) # Pass the engine directly
        logger.info("Database schema initialization complete (or tables already exist).")
        
    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")
        sys.exit(1) 