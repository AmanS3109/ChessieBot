# main.py - Enhanced FastAPI Application for ChessieBot
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import routers
from api.routes import chat_api as chat
from api.routes import tts_api as tts
from api.routes import stt_api as stt
from api.routes import voice_api as voice
from api.routes import video_api as video

# Import middleware and config
from api.middleware import setup_exception_handlers
from api.middleware.error_handler import log_requests
from config import CORS_ORIGINS, GROQ_API_KEY, ENV
from services.cache_service import get_cache_stats


# ================================
# Lifespan events (startup/shutdown)
# ================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Starting Chess Buddy AI...")
    print(f"   Environment: {ENV}")
    print(f"   Groq API: {'✅ Configured' if GROQ_API_KEY else '❌ Not configured'}")
    
    # Pre-warm services (optional)
    # You can import and initialize heavy services here
    
    yield  # Application runs
    
    # Shutdown
    print("👋 Shutting down Chess Buddy AI...")


# ================================
# Create FastAPI app
# ================================
app = FastAPI(
    title="Chess Buddy AI",
    description="""
🎯 **Chess Buddy AI** - Story-grounded RAG chatbot for kids learning chess!

## Features
- 🎥 **Video Analysis**: Process YouTube videos and ask questions
- 🗣️ **Bilingual Support**: English, Hindi, and Hinglish responses
- 📚 **Story-based Learning**: Context from chess stories
- 🎙️ **Voice Support**: Text-to-Speech and Speech-to-Text

## Video Endpoints
- `/api/video/process` - Process a YouTube video
- `/api/video/chat` - Chat with processed video
- `/api/video/explain` - Get AI explanations (what/why modes)
- `/api/video/concepts/{id}` - Extract key concepts

## Languages
- `en` - English
- `hi` - Hindi (हिंदी)
- `hinglish` - Hinglish (Hindi + English mix) ← Default
    """,
    version="2.0.0",
    lifespan=lifespan
)


# ================================
# Middleware Setup
# ================================
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers
setup_exception_handlers(app)

# Request logging (uncomment for debugging)
# app.middleware("http")(log_requests)


# ================================
# Include Routers
# ================================
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(stt.router, prefix="/api", tags=["STT"])
app.include_router(voice.router, prefix="/api", tags=["Voice"])
app.include_router(video.router, prefix="/api", tags=["Video"])


# ================================
# Root Endpoints
# ================================
@app.get("/", tags=["Status"])
def root():
    """Welcome endpoint."""
    return {
        "message": "Chess Buddy AI is running! 🏃‍♂️♟️",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Status"])
def health():
    """
    Health check endpoint.
    Returns status of all services.
    """
    groq_status = "connected" if GROQ_API_KEY else "not_configured"
    cache_stats = get_cache_stats()
    
    return {
        "status": "healthy",
        "service": "Chess Buddy AI",
        "version": "2.0.0",
        "environment": ENV,
        "services": {
            "groq_llm": groq_status,
            "whisper": "ready",
            "cache": cache_stats
        }
    }


@app.get("/api/languages", tags=["Config"])
def get_languages():
    """Get supported languages."""
    return {
        "supported": ["en", "hi", "hinglish"],
        "default": "hinglish",
        "descriptions": {
            "en": "English",
            "hi": "Hindi (हिंदी)", 
            "hinglish": "Hinglish (Hindi + English mix)"
        }
    }


# ================================
# Run with: python -m uvicorn main:app --reload
# ================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
