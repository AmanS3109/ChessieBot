from __future__ import annotations

import os
import tempfile
import asyncio
from typing import Optional

import edge_tts
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

router = APIRouter()


# Default voices copied from Streamlit app
HINDI_VOICE = "hi-IN-MadhurNeural"
ENGLISH_VOICE = "en-IN-NeerjaNeural"


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


def normalize_for_tts(text: str) -> str:
    replacements = {
        "kise": "kisse",
        "kon": "kaun",
        "kehte": "kehtey",
        "kyun": "kyon",
        "raja": "raajaa",
        "bulate": "bulaate",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def is_mostly_english(text: str) -> bool:
    keywords = [
        "king",
        "queen",
        "pawn",
        "rook",
        "bishop",
        "knight",
        "game",
        "move",
        "step",
        "board",
        "check",
    ]
    t = text.lower()
    return any(k in t for k in keywords)


async def _tts_save(text: str, voice: str, path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


@router.post("/tts")
async def tts_endpoint(req: TTSRequest, background: BackgroundTasks):
    """Generate TTS MP3 for `req.text` and return it as a FileResponse.

    The temporary file is removed after the response is sent.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    text = normalize_for_tts(req.text.strip())

    # Choose voice if not provided
    voice = req.voice if req.voice else (ENGLISH_VOICE if is_mostly_english(text) else HINDI_VOICE)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()

    try:
        # Run edge-tts save asynchronously
        await _tts_save(text, voice, tmp.name)
    except Exception as e:
        # Clean up temp file on error
        try:
            os.remove(tmp.name)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")

    # Schedule file removal after response
    background.add_task(os.remove, tmp.name)

    return FileResponse(tmp.name, media_type="audio/mpeg", filename="speech.mp3")
