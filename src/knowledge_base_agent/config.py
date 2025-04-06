"""
Configuration management for the Knowledge Base Agent.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

class StorageConfig(BaseModel):
    """Storage configuration."""
    document_store_type: str = Field(default="memory", description="Type of document store to use")
    vector_store_type: str = Field(default="memory", description="Type of vector store to use")
    knowledge_store_type: str = Field(default="memory", description="Type of knowledge store to use")
    storage_path: Optional[str] = Field(default=None, description="Path for persistent storage")
    postgres_connection: Optional[str] = Field(default=None, description="PostgreSQL connection string")

    @validator('postgres_connection', pre=True)
    def validate_postgres_connection(cls, v):
        """Validate and format PostgreSQL connection string."""
        if v and not v.startswith('postgresql://'):
            return f'postgresql://{v}'
        return v

class EmbeddingConfig(BaseModel):
    """Embedding configuration."""
    model: str = Field(default="text-embedding-ada-002", description="OpenAI embedding model to use")
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    batch_size: int = Field(default=100, description="Batch size for embedding generation")
    cache_size: int = Field(default=1000, description="Size of embedding cache")
    device: Optional[str] = Field(default=None, description="Device to run the model on ('cuda' or 'cpu')")

    @validator("device", pre=True)
    def validate_device(cls, v):
        """Validate device setting."""
        if v and v not in ["cuda", "cpu"]:
            raise ValueError("Device must be either 'cuda' or 'cpu'")
        return v

class ProcessingConfig(BaseModel):
    """Document processing configuration."""
    max_chunk_size: int = Field(default=1000, description="Maximum size of text chunks")
    min_chunk_size: int = Field(default=100, description="Minimum size of text chunks")
    overlap_size: int = Field(default=50, description="Size of overlap between chunks")
    max_retries: int = Field(default=3, description="Maximum number of retries for API calls")
    retry_delay: int = Field(default=1, description="Delay between retries in seconds")
    extract_entities: bool = Field(default=True, description="Whether to extract entities")
    extract_relationships: bool = Field(default=True, description="Whether to extract relationships")
    entity_types: list = Field(
        default=["PERSON", "ORGANIZATION", "LOCATION", "DATE", "EVENT"],
        description="Types of entities to extract"
    )
    cache_size: int = Field(default=1000, description="Size of processing cache")

class APIConfig(BaseModel):
    """API configuration settings."""
    host: str = "localhost"
    port: int = Field(default=8080, description="Port number for the API server")
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: List[str] = Field(default=["*"], description="CORS origins")
    rate_limit: int = Field(default=100, description="Rate limit per minute")

    @validator("port", pre=True)
    def validate_port(cls, v):
        """Convert port to integer if it's a string."""
        if isinstance(v, str):
            return int(v)
        return v

    @validator("debug", pre=True)
    def validate_debug(cls, v):
        """Convert debug to boolean if it's a string."""
        if isinstance(v, str):
            return v.lower() == "true"
        return v

    @validator("rate_limit", pre=True)
    def validate_rate_limit(cls, v):
        """Convert rate_limit to integer if it's a string."""
        if isinstance(v, str):
            return int(v)
        return v

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file: Optional[str] = Field(default=None, description="Log file path")

class ExtractorConfig(BaseModel):
    """Entity extractor configuration."""
    use_local_llm: bool = Field(default=True, description="Whether to use local LLM for extraction")
    model_name: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        description="Name of the local LLM model to use"
    )
    device: Optional[str] = Field(default=None, description="Device to run the model on ('cuda' or 'cpu')")
    load_in_4bit: bool = Field(default=True, description="Whether to use 4-bit quantization")
    max_length: int = Field(default=2048, description="Maximum sequence length for generation")
    temperature: float = Field(default=0.1, description="Temperature for text generation")

    @validator("device", pre=True)
    def validate_device(cls, v):
        """Validate device setting."""
        if v and v not in ["cuda", "cpu"]:
            raise ValueError("Device must be either 'cuda' or 'cpu'")
        return v

    @validator("temperature", pre=True)
    def validate_temperature(cls, v):
        """Validate temperature setting."""
        if isinstance(v, str):
            v = float(v)
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

class Config(BaseModel):
    """Main configuration."""
    storage: StorageConfig = Field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'Config':
        """Create configuration from environment variables."""
        # Load environment variables
        load_dotenv(env_file)
        
        # Create base config
        config = cls()
        
        # Update from environment variables
        env_mapping = {
            'OPENAI_API_KEY': ('embedding', 'api_key'),
            'EMBEDDING_MODEL': ('embedding', 'model'),
            'EMBEDDING_DEVICE': ('embedding', 'device'),
            'EMBEDDING_BATCH_SIZE': ('embedding', 'batch_size'),
            'LOG_LEVEL': ('logging', 'level'),
            'STORAGE_PATH': ('storage', 'storage_path'),
            'POSTGRES_CONNECTION': ('storage', 'postgres_connection'),
            'DOCUMENT_STORE_TYPE': ('storage', 'document_store_type'),
            'VECTOR_STORE_TYPE': ('storage', 'vector_store_type'),
            'KNOWLEDGE_STORE_TYPE': ('storage', 'knowledge_store_type'),
            'API_HOST': ('api', 'host'),
            'API_PORT': ('api', 'port'),
            'API_DEBUG': ('api', 'debug'),
            'EXTRACTOR_MODEL': ('extractor', 'model_name'),
            'EXTRACTOR_DEVICE': ('extractor', 'device'),
            'EXTRACTOR_4BIT': ('extractor', 'load_in_4bit'),
            'EXTRACTOR_MAX_LENGTH': ('extractor', 'max_length'),
            'EXTRACTOR_TEMPERATURE': ('extractor', 'temperature'),
            'USE_LOCAL_LLM': ('extractor', 'use_local_llm'),
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                current = config
                for i, key in enumerate(config_path[:-1]):
                    current = getattr(current, key)
                setattr(current, config_path[-1], value)
        
        return config

def get_config(env_file: Optional[str] = None) -> Config:
    """Get configuration instance."""
    return Config.from_env(env_file) 