from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from rag.utils import generate_response, retrieve_chunks
from config import GROQ_API_KEY

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    explain: Optional[bool] = False
    language: Optional[str] = "hinglish"


class PuzzleHintRequest(BaseModel):
    puzzle_title: str
    prompt_text: str
    learning_objective: Optional[str] = ""
    difficulty: Optional[str] = "Easy"
    piece_type: Optional[str] = ""
    hint_level: Optional[str] = "gentle"  # "gentle" or "direct"
    language: Optional[str] = "hinglish"


class PuzzleHintResponse(BaseModel):
    hint: str
    encouragement: str
    language: str


class ChatResponse(BaseModel):
    answer: str
    explanation: str
    normalized_query: str
    original_query: str


class RetrieveRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


@router.post("/chat", response_model=ChatResponse)
async def chat_with_buddy(request: ChatRequest):
    """Return a story-grounded one-word answer (and explanation if requested).

    Runs the synchronous RAG pipeline in a thread to avoid blocking the event loop.
    Now includes query normalization for Hindi/Hinglish input.
    
    Response includes:
    - answer: One-word or short answer
    - explanation: Story-grounded explanation (if explain=True)
    - normalized_query: Canonical Hinglish question
    - original_query: Original user input
    """
    try:
        result = await asyncio.to_thread(
            generate_response, 
            request.question, 
            request.explain,
            request.language
        )
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


@router.post("/puzzle-hint", response_model=PuzzleHintResponse)
async def get_puzzle_hint(request: PuzzleHintRequest):
    """Generate a kid-friendly puzzle hint using Groq LLM.

    This does NOT use the RAG pipeline — it generates chess-knowledge hints
    based on the puzzle context, tailored for children aged 5-10.
    """
    from groq import Groq
    from config import GROQ_MODEL

    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Groq API not configured")

    # Language instructions
    lang_map = {
        "en": "Respond in simple English a 6-year-old would understand.",
        "hi": "Simple Hindi mein jawab do jo 6 saal ke bacche samajh sake.",
        "hinglish": "Hinglish mein jawab do — mix of Hindi aur English, jaise bacche bolte hain.",
    }
    lang_instruction = lang_map.get(request.language, lang_map["hinglish"])

    # Hint intensity
    if request.hint_level == "direct":
        hint_style = "Give a clear, specific direction about what to do (but still do NOT reveal the exact answer square)."
    else:
        hint_style = "Give a gentle, encouraging nudge. Be playful and indirect."

    prompt = f"""You are Chessie 🐱, a cute and friendly chess cat who helps kids solve chess puzzles.
A child is stuck on a puzzle and needs your help!

PUZZLE INFO:
- Title: {request.puzzle_title}
- What the puzzle asks: {request.prompt_text}
- Learning goal: {request.learning_objective}
- Difficulty: {request.difficulty}
- Chess piece involved: {request.piece_type or "not specified"}

YOUR TASK:
1. Give a SHORT hint (1-2 sentences max) that helps the child think about the answer.
2. {hint_style}
3. NEVER reveal the exact answer or the exact square to click.
4. Use chess knowledge to guide them (e.g., how pieces move, what they can do).
5. {lang_instruction}

OUTPUT FORMAT (strict):
HINT: <your hint here>
ENCOURAGEMENT: <a short motivational line, 1 sentence>
"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Chessie, a playful chess cat assistant for kids aged 5-10. "
                        "Be warm, encouraging, and use simple words. "
                        f"{lang_instruction}"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=150,
        )

        text = completion.choices[0].message.content.strip()

        # Parse HINT and ENCOURAGEMENT
        hint = ""
        encouragement = ""
        for line in text.splitlines():
            if line.upper().startswith("HINT:"):
                hint = line.split(":", 1)[1].strip()
            elif line.upper().startswith("ENCOURAGEMENT:"):
                encouragement = line.split(":", 1)[1].strip()

        # Fallback if parsing fails
        if not hint:
            hint = text.split("\n")[0] if text else "Sochke dekho, answer paas mein hai! 🐱"
        if not encouragement:
            encouragement = "Tum kar sakte ho! 💪✨"

        return PuzzleHintResponse(
            hint=hint,
            encouragement=encouragement,
            language=request.language or "hinglish",
        )

    except Exception as e:
        print(f"❌ Puzzle hint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

