# api/middleware/error_handler.py - Centralized Error Handling
import traceback
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Union
from config import DEBUG, get_error_message, DEFAULT_LANGUAGE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ChessieBot")


class ChessieBotException(Exception):
    """Base exception for ChessieBot."""
    def __init__(
        self, 
        message: str, 
        error_code: str = "general_error",
        status_code: int = 500,
        language: str = DEFAULT_LANGUAGE
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.language = language
        super().__init__(self.message)


class VideoNotFoundError(ChessieBotException):
    """Video not found in store."""
    def __init__(self, video_id: str, language: str = DEFAULT_LANGUAGE):
        super().__init__(
            message=f"Video {video_id} not found",
            error_code="video_not_found",
            status_code=404,
            language=language
        )


class TranscriptionError(ChessieBotException):
    """Error during transcription."""
    def __init__(self, details: str = "", language: str = DEFAULT_LANGUAGE):
        super().__init__(
            message=f"Transcription failed: {details}",
            error_code="transcript_error",
            status_code=500,
            language=language
        )


class AIServiceError(ChessieBotException):
    """Error with AI service (Groq)."""
    def __init__(self, details: str = "", language: str = DEFAULT_LANGUAGE):
        super().__init__(
            message=f"AI service error: {details}",
            error_code="groq_not_configured",
            status_code=503,
            language=language
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup all exception handlers for the FastAPI app."""
    
    @app.exception_handler(ChessieBotException)
    async def chessie_exception_handler(request: Request, exc: ChessieBotException):
        """Handle custom ChessieBot exceptions."""
        logger.error(f"ChessieBotException: {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "error_code": exc.error_code,
                "message": get_error_message(exc.error_code, exc.language),
                "detail": exc.message if DEBUG else None
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": str(exc.detail),
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}")
        if DEBUG:
            logger.error(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": get_error_message("general_error", DEFAULT_LANGUAGE),
                "detail": str(exc) if DEBUG else None
            }
        )


# Request logging middleware
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"📤 {request.method} {request.url.path} -> {response.status_code}")
    
    return response
