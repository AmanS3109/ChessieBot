# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat_api as chat
from api.routes import tts_api as tts
from api.routes import stt_api as stt
from api.routes import voice_api as voice

app = FastAPI(
    title="Chess Buddy AI",
    description="Story-grounded RAG chatbot for kids learning chess",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(stt.router, prefix="/api", tags=["STT"])
app.include_router(voice.router, prefix="/api", tags=["Voice"])

@app.get("/")
def root():
    return {"message": "Chess Buddy AI is running!"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Chess Buddy AI"}
