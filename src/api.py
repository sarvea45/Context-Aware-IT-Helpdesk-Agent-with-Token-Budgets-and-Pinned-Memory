import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.context_engine import ContextManager
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Context-Aware IT Helpdesk Agent")

class ChatRequest(BaseModel):
    session_id: str
    message: str
    token_limit_override: Optional[int] = None

# req-7: health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# req-1-chat-endpoint
@app.post("/v1/chat")
def chat_endpoint(request: ChatRequest):
    try:
        limit = request.token_limit_override if request.token_limit_override is not None else int(os.getenv("TOKEN_BUDGET_LIMIT", 4000))
        manager = ContextManager(request.session_id)
        reply, topic = manager.process_message(request.message, limit)
        # return schema requires "response" key
        return {"response": reply, "active_topic": topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# req-9-context-retrieval-api
@app.get("/v1/context/{session_id}")
def get_context(session_id: str):
    filepath = os.path.join("logs", f"context_{session_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Session not found")
    manager = ContextManager(session_id)
    return manager.state
