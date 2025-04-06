"""
API functionality for the Knowledge Base Agent.
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models import Document, Entity, Relationship, SearchResult
from ..processor import DocumentProcessor
from .routes import router

api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate API key."""
    if not api_key or api_key != "your-api-key":  # Replace with actual key validation
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

def create_app(processor: DocumentProcessor) -> FastAPI:
    """Create FastAPI application with routes."""
    app = FastAPI(
        title="Knowledge Base Agent API",
        description="API for processing documents and querying knowledge",
        version="0.1.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routes
    app.include_router(router, prefix="/api")
    
    return app

__all__ = ["create_app"] 