from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.utils import generate_response, retrieve_chunks

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    explain: Optional[bool] = False


class RetrieveRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


@router.post("/chat")
async def chat_with_buddy(request: ChatRequest):
    """Return a story-grounded one-word answer (and explanation if requested).

    Runs the synchronous RAG pipeline in a thread to avoid blocking the event loop.
    """
    try:
        result = await asyncio.to_thread(generate_response, request.question, request.explain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def retrieve(request: RetrieveRequest):
    """Return raw retrieved chunks (useful for debugging or showing sources in the frontend)."""
    try:
        chunks = await asyncio.to_thread(retrieve_chunks, request.question, request.top_k)
        return {"chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
