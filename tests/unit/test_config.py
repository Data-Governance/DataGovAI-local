"""
Tests for the configuration system.
"""

import os
import pytest
from tempfile import NamedTemporaryFile

from knowledge_base_agent.config import (
    Config,
    StorageConfig,
    EmbeddingConfig,
    ProcessingConfig,
    APIConfig,
    LoggingConfig,
    get_config
)

def test_default_config():
    """Test default configuration."""
    config = Config()
    
    assert isinstance(config.storage, StorageConfig)
    assert isinstance(config.embedding, EmbeddingConfig)
    assert isinstance(config.processing, ProcessingConfig)
    assert isinstance(config.api, APIConfig)
    assert isinstance(config.logging, LoggingConfig)
    
    # Check default values
    assert config.storage.document_store_type == "memory"
    assert config.embedding.model == "text-embedding-ada-002"
    assert config.processing.max_chunk_size == 1000
    assert config.api.host == "0.0.0.0"
    assert config.logging.level == "INFO"

def test_config_from_env():
    """Test configuration from environment variables."""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["EMBEDDING_MODEL"] = "test-model"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["STORAGE_PATH"] = "/test/path"
    os.environ["API_HOST"] = "localhost"
    os.environ["API_PORT"] = "8080"
    os.environ["API_DEBUG"] = "true"
    
    try:
        config = Config.from_env()
        
        # Check environment variable values
        assert config.embedding.api_key == "test-key"
        assert config.embedding.model == "test-model"
        assert config.logging.level == "DEBUG"
        assert config.storage.storage_path == "/test/path"
        assert config.api.host == "localhost"
        assert config.api.port == 8080
        assert config.api.debug is True
        
    finally:
        # Clean up environment variables
        del os.environ["OPENAI_API_KEY"]
        del os.environ["EMBEDDING_MODEL"]
        del os.environ["LOG_LEVEL"]
        del os.environ["STORAGE_PATH"]
        del os.environ["API_HOST"]
        del os.environ["API_PORT"]
        del os.environ["API_DEBUG"]

def test_config_from_env_file():
    """Test configuration from environment file."""
    # Create temporary environment file
    with NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""
OPENAI_API_KEY=test-key
EMBEDDING_MODEL=test-model
LOG_LEVEL=DEBUG
STORAGE_PATH=/test/path
API_HOST=localhost
API_PORT=8080
API_DEBUG=true
""")
        env_file = f.name
    
    try:
        config = Config.from_env(env_file)
        
        # Check environment file values
        assert config.embedding.api_key == "test-key"
        assert config.embedding.model == "test-model"
        assert config.logging.level == "DEBUG"
        assert config.storage.storage_path == "/test/path"
        assert config.api.host == "localhost"
        assert config.api.port == 8080
        assert config.api.debug is True
        
    finally:
        # Clean up
        os.unlink(env_file)

def test_storage_config():
    """Test storage configuration."""
    config = StorageConfig(
        document_store_type="sqlite",
        vector_store_type="faiss",
        knowledge_store_type="neo4j",
        storage_path="/test/path"
    )
    
    assert config.document_store_type == "sqlite"
    assert config.vector_store_type == "faiss"
    assert config.knowledge_store_type == "neo4j"
    assert config.storage_path == "/test/path"

def test_embedding_config():
    """Test embedding configuration."""
    config = EmbeddingConfig(
        model="test-model",
        api_key="test-key",
        batch_size=200,
        cache_size=2000
    )
    
    assert config.model == "test-model"
    assert config.api_key == "test-key"
    assert config.batch_size == 200
    assert config.cache_size == 2000

def test_processing_config():
    """Test processing configuration."""
    config = ProcessingConfig(
        max_chunk_size=2000,
        min_chunk_size=200,
        overlap_size=100,
        max_retries=5,
        retry_delay=2,
        extract_entities=True,
        extract_relationships=True,
        entity_types=["PERSON", "ORGANIZATION"]
    )
    
    assert config.max_chunk_size == 2000
    assert config.min_chunk_size == 200
    assert config.overlap_size == 100
    assert config.max_retries == 5
    assert config.retry_delay == 2
    assert config.extract_entities is True
    assert config.extract_relationships is True
    assert config.entity_types == ["PERSON", "ORGANIZATION"]

def test_api_config():
    """Test API configuration."""
    config = APIConfig(
        host="localhost",
        port=8080,
        debug=True,
        cors_origins=["http://localhost:3000"],
        rate_limit=200
    )
    
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.debug is True
    assert config.cors_origins == ["http://localhost:3000"]
    assert config.rate_limit == 200

def test_logging_config():
    """Test logging configuration."""
    config = LoggingConfig(
        level="DEBUG",
        format="%(levelname)s: %(message)s",
        file="/test/log.txt"
    )
    
    assert config.level == "DEBUG"
    assert config.format == "%(levelname)s: %(message)s"
    assert config.file == "/test/log.txt"

def test_get_config():
    """Test get_config function."""
    # Test with default configuration
    config = get_config()
    assert isinstance(config, Config)
    
    # Test with environment file
    with NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("OPENAI_API_KEY=test-key\n")
        env_file = f.name
    
    try:
        config = get_config(env_file)
        assert config.embedding.api_key == "test-key"
    finally:
        os.unlink(env_file) 