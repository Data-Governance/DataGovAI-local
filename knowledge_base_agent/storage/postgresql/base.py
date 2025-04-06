"""
Base module for PostgreSQL database models and connection.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

# Create SQLAlchemy Base class for models
Base = declarative_base()

def get_engine(storage_path=None, connection_string=None):
    """
    Get a SQLAlchemy engine.
    Prioritizes connection_string arg, then POSTGRES_CONNECTION env var,
    then falls back to SQLite based on storage_path or in-memory.
    """
    # Priority: 1. connection_string param, 2. POSTGRES_CONNECTION env var
    if connection_string is None:
        connection_string = os.environ.get("POSTGRES_CONNECTION")

    # Fallback to SQLite if no PostgreSQL connection string is found
    if connection_string is None:
        if storage_path is not None:
            database_path = os.path.join(storage_path, "knowledge_base.db")
            connection_string = f"sqlite:///{database_path}"
            print(f"INFO: No PostgreSQL connection string. Using SQLite file: {database_path}")
        else:
            # Default to a SQLite in-memory database
            connection_string = "sqlite:///:memory:"
            print("INFO: No PostgreSQL connection string or storage path. Using SQLite in-memory DB.")

    # Create the engine using the determined connection string
    if connection_string.startswith('postgresql'):
        # Use pool settings for PostgreSQL
        engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        print(f"INFO: Connecting to PostgreSQL with: {connection_string.split('@')[0]}@...:{connection_string.split(':')[2].split('/')[0]}/{connection_string.split('/')[-1]}") # Mask password
    else:
        # No special pool settings for SQLite
        engine = create_engine(connection_string)

    return engine

def init_db(engine=None, storage_path=None, connection_string=None):
    """
    Initialize the database by creating all tables and the vector extension if needed.
    """
    if engine is None:
        engine = get_engine(storage_path, connection_string)

    # Enable pgvector extension if using PostgreSQL
    if engine.name == 'postgresql':
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("INFO: pgvector extension checked/created.")
        except Exception as e:
            print(f"Warning: Could not create pgvector extension (may require DB admin privileges): {e}")

    # Create all tables defined by Base's subclasses
    print("INFO: Creating database tables...")
    Base.metadata.create_all(engine)
    print("INFO: Database tables created.")

    # Create session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)

    return Session 