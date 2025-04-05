"""
Base module for PostgreSQL database models and connection.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text

# Create SQLAlchemy Base class for models
Base = declarative_base()

def get_engine(storage_path=None, connection_string=None):
    """
    Get a SQLAlchemy engine for PostgreSQL.
    
    Args:
        storage_path (str, optional): Path to storage directory, used if connection_string is not provided
        connection_string (str, optional): Direct connection string for PostgreSQL
        
    Returns:
        Engine: SQLAlchemy engine
    """
    # Priority: 1. connection_string param, 2. POSTGRES_CONNECTION env var, 3. Construct from storage_path
    if connection_string is None:
        connection_string = os.environ.get("POSTGRES_CONNECTION")
        
    if connection_string is None and storage_path is not None:
        # Construct a SQLite connection string as a fallback if storage_path is provided
        database_path = os.path.join(storage_path, "knowledge_base.db")
        connection_string = f"sqlite:///{database_path}"
    
    if connection_string is None:
        # Default to a SQLite in-memory database if no other options
        connection_string = "sqlite:///:memory:"
    
    # Create engine with connection pooling
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 minutes
    )
    
    return engine

def init_db(engine=None, storage_path=None, connection_string=None):
    """
    Initialize the database by creating all tables.
    
    Args:
        engine (Engine, optional): SQLAlchemy engine
        storage_path (str, optional): Path to storage directory
        connection_string (str, optional): Direct connection string for PostgreSQL
        
    Returns:
        Session: SQLAlchemy session factory
    """
    if engine is None:
        engine = get_engine(storage_path, connection_string)
    
    # Enable pgvector extension if using PostgreSQL
    if engine.name == 'postgresql':
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
        except Exception as e:
            # Log a warning if the extension cannot be created (e.g., permissions)
            print(f"Warning: Could not create pgvector extension: {e}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    
    return Session 