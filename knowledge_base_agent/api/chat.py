from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..processor import DocumentProcessor
from ..models import ProcessingConfig, SearchResult

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[SearchResult] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_kb(
    request: ChatRequest,
    processor: DocumentProcessor = Depends(lambda: DocumentProcessor())
):
    try:
        # Process the user's message and get relevant context from the knowledge base
        search_results = processor.search_documents(request.message)
        
        # Format the context and generate a response
        context = "\n".join([result.content for result in search_results])
        
        # For now, return a simple response with the found context
        # TODO: Integrate with a language model for more natural responses
        response = f"Based on the knowledge base, here's what I found:\n{context}"
        
        return ChatResponse(
            response=response,
            sources=search_results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 