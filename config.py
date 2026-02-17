# config.py - Centralized configuration for ChessieBot
import os
from dotenv import load_dotenv
from typing import Literal

load_dotenv()

# ================================
# Environment & Mode
# ================================
ENV = os.getenv("ENV", "development")
DEBUG = ENV == "development"

# ================================
# Supported Languages
# ================================
SUPPORTED_LANGUAGES = ["en", "hi", "hinglish"]
DEFAULT_LANGUAGE = "hinglish"
LanguageType = Literal["en", "hi", "hinglish"]

# ================================
# Groq LLM Configuration (FREE TIER)
# ================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast, free model
GROQ_MAX_TOKENS = 500
GROQ_TEMPERATURE = 0.2
GROQ_TIMEOUT = 30  # seconds

# ================================
# Whisper Configuration (LOCAL/FREE)
# ================================
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # Options: tiny, base, small
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ================================
# Video Processing
# ================================
TEMP_AUDIO_DIR = "temp_audio"
MAX_VIDEO_DURATION = 3600  # 1 hour max
DOWNLOAD_TIMEOUT = 300  # 5 minutes

# ================================
# Caching Configuration
# ================================
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1 hour
TRANSCRIPT_CACHE_TTL = 86400  # 24 hours (transcripts don't change)
RESPONSE_CACHE_MAX_SIZE = 256

# ================================
# RAG Configuration
# ================================
CHROMA_DB_PATH = "data/processed/chromadb"
EMBEDDING_MODEL = "distiluse-base-multilingual-cased-v1"
RETRIEVAL_TOP_K = 5
RETRIEVAL_SCORE_THRESHOLD = 0.5

# ================================
# API Configuration
# ================================
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")  # Set in Railway for production

# ================================
# Error Messages (Bilingual)
# ================================
ERROR_MESSAGES = {
    "groq_not_configured": {
        "en": "AI service is not configured. Please check API key.",
        "hi": "AI सेवा कॉन्फ़िगर नहीं है। कृपया API key जांचें।",
        "hinglish": "AI service configure nahi hai. API key check karo."
    },
    "video_not_found": {
        "en": "Video not found. Please process the video first.",
        "hi": "वीडियो नहीं मिला। पहले वीडियो प्रोसेस करें।",
        "hinglish": "Video nahi mila. Pehle video process karo."
    },
    "transcript_error": {
        "en": "Could not transcribe the video. Please try again.",
        "hi": "वीडियो ट्रांसक्राइब नहीं हो सका। फिर से कोशिश करें।",
        "hinglish": "Video transcribe nahi ho paya. Phir se try karo."
    },
    "general_error": {
        "en": "Something went wrong. Please try again.",
        "hi": "कुछ गड़बड़ हो गई। फिर से कोशिश करें।",
        "hinglish": "Kuch gadbad ho gayi. Phir se try karo."
    }
}

def get_error_message(error_key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """Get error message in specified language."""
    if error_key in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_key].get(language, ERROR_MESSAGES[error_key]["en"])
    return ERROR_MESSAGES["general_error"].get(language, "An error occurred.")
