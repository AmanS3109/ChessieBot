# api/routes/chat.py
from fastapi import APIRouter
from pydantic import BaseModel
from rag.utils import generate_response

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
async def chat_with_buddy(request: ChatRequest):
    answer = generate_response(request.question)
    return {"answer": answer}
