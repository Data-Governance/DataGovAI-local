from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from ..models import Document, SearchResult, ProcessingConfig
from ..processor import DocumentProcessor
from ..config import get_config

router = APIRouter()

class ProcessDocumentRequest(BaseModel):
    content: str
    metadata: Optional[dict] = None

def get_processor():
    """Dependency to get document processor instance."""
    try:
        from ..__main__ import create_processor
        config = get_config()
        return create_processor(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents", response_model=str)
async def process_document(
    request: ProcessDocumentRequest,
    processor: DocumentProcessor = Depends(get_processor)
):
    """Process a document and store it in the knowledge base."""
    try:
        doc_id = processor.process_document(
            content=request.content,
            metadata=request.metadata
        )
        return doc_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[SearchResult])
async def search(
    query: str = Query(..., description="Search query string"),
    top_k: int = Query(5, description="Number of results to return", ge=1),
    min_score: float = Query(0.0, description="Minimum similarity score", ge=0.0, le=1.0),
    use_graph: bool = Query(True, description="Whether to use knowledge graph enrichment"),
    processor: DocumentProcessor = Depends(get_processor)
):
    """Search the knowledge base."""
    try:
        results = processor.search(
            query=query,
            top_k=top_k,
            min_score=min_score,
            use_graph=use_graph
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}", response_model=Document)
async def get_document(
    doc_id: str,
    processor: DocumentProcessor = Depends(get_processor)
):
    """Get a document by ID."""
    try:
        document = processor.document_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/{entity_id}/context")
async def get_entity_context(
    entity_id: str,
    max_depth: int = Query(2, description="Maximum depth of relationships to traverse", ge=1, le=5),
    processor: DocumentProcessor = Depends(get_processor)
):
    """Get contextual information about an entity."""
    try:
        context = processor.get_entity_context(entity_id, max_depth=max_depth)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"} 