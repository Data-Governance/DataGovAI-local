from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Knowledge Base Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[dict] = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_kb(request: ChatRequest):
    try:
        # For now, return a simple response
        response = f"You said: {request.message}\nThis is a test response from the knowledge base."
        return ChatResponse(
            response=response,
            sources=[{"content": "Test source", "metadata": {"title": "Test Document"}}]
        )
    except Exception as e:
        return {"error": str(e)} 