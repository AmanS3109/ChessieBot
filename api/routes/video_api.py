# api/routes/video_api.py - Enhanced Video API with Bilingual Support
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal
import uuid

# Import services
from services.video_processor import process_video, cleanup_temp_files
from services.video_explainer import explain_video_concept, get_video_concepts
from rag.video_generator import generate_video_response
from services.cache_service import get_cache_stats
from config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

router = APIRouter()

# In-memory storage for transcripts (Use Redis/DB in production!)
# Format: { video_id: {"transcript": str, "title": str, "metadata": dict} }
VIDEO_STORE: Dict[str, dict] = {}


# ================================
# Request/Response Models
# ================================

class VideoProcessRequest(BaseModel):
    url: str
    force_refresh: bool = False


class VideoProcessResponse(BaseModel):
    status: str
    video_id: str
    title: Optional[str] = None
    message: str


class VideoChatRequest(BaseModel):
    video_id: str
    question: str
    language: Literal["en", "hi", "hinglish"] = "hinglish"


class VideoChatResponse(BaseModel):
    answer: str
    explanation: str
    language: str


class VideoExplainRequest(BaseModel):
    video_id: str
    topic: str
    mode: Literal["what", "why", "full"] = "full"
    language: Literal["en", "hi", "hinglish"] = "hinglish"


class VideoExplainResponse(BaseModel):
    topic: str
    explanation: str
    key_points: List[str]
    language: str
    mode: str
    status: str


class VideoConceptsResponse(BaseModel):
    video_id: str
    concepts: List[Dict[str, str]]
    count: int


# ================================
# Endpoints
# ================================

@router.post("/video/process", response_model=VideoProcessResponse)
async def process_video_endpoint(request: VideoProcessRequest):
    """
    Process a video from a URL (e.g., YouTube).
    Downloads audio, transcribes it, and stores the transcript.
    
    - **url**: Video URL (YouTube, etc.)
    - **force_refresh**: If true, bypass cache and reprocess
    """
    result = process_video(request.url, force_refresh=request.force_refresh)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    
    video_id = result.get("video_id")
    transcript = result.get("transcript")
    title = result.get("title", "Unknown Video")
    
    # Store in memory with metadata
    VIDEO_STORE[video_id] = {
        "transcript": transcript,
        "title": title,
        "detected_language": result.get("detected_language"),
        "cached": result.get("cached", False)
    }
    
    return VideoProcessResponse(
        status="success",
        video_id=video_id,
        title=title,
        message="Video processed successfully! You can now chat or get explanations."
    )


@router.post("/video/chat", response_model=VideoChatResponse)
async def chat_video_endpoint(request: VideoChatRequest):
    """
    Chat with the processed video.
    Ask questions about the video content.
    
    - **video_id**: ID from /video/process response
    - **question**: Your question (can be in Hindi/English/Hinglish)
    - **language**: Response language (en/hi/hinglish)
    """
    video_data = VIDEO_STORE.get(request.video_id)
    
    if not video_data:
        raise HTTPException(
            status_code=404, 
            detail="Video ID not found. Process the video first."
        )
    
    transcript = video_data["transcript"]
    response = generate_video_response(
        transcript, 
        request.question,
        language=request.language
    )
    
    return VideoChatResponse(
        answer=response.get("answer", ""),
        explanation=response.get("explanation", ""),
        language=request.language
    )


@router.post("/video/explain", response_model=VideoExplainResponse)
async def explain_video_endpoint(request: VideoExplainRequest):
    """
    Get AI explanation of video concepts.
    
    - **video_id**: ID from /video/process response
    - **topic**: What to explain (e.g., "opening moves", "why bishop moved")
    - **mode**: "what" (what happened), "why" (reasoning), "full" (both)
    - **language**: Response language (en/hi/hinglish)
    """
    video_data = VIDEO_STORE.get(request.video_id)
    
    if not video_data:
        raise HTTPException(
            status_code=404, 
            detail="Video ID not found. Process the video first."
        )
    
    transcript = video_data["transcript"]
    
    result = explain_video_concept(
        transcript=transcript,
        topic=request.topic,
        mode=request.mode,
        language=request.language
    )
    
    return VideoExplainResponse(
        topic=request.topic,
        explanation=result.get("explanation", ""),
        key_points=result.get("key_points", []),
        language=result.get("language", request.language),
        mode=result.get("mode", request.mode),
        status=result.get("status", "success")
    )


@router.post("/video/what")
async def explain_what_endpoint(
    video_id: str,
    query: str,
    language: Literal["en", "hi", "hinglish"] = "hinglish"
):
    """
    Explain WHAT is happening in the video.
    Shortcut for /video/explain with mode='what'
    """
    video_data = VIDEO_STORE.get(video_id)
    
    if not video_data:
        raise HTTPException(status_code=404, detail="Video ID not found.")
    
    result = explain_video_concept(
        transcript=video_data["transcript"],
        topic=query,
        mode="what",
        language=language
    )
    
    return result


@router.post("/video/why")
async def explain_why_endpoint(
    video_id: str,
    query: str,
    language: Literal["en", "hi", "hinglish"] = "hinglish"
):
    """
    Explain WHY something happened in the video.
    Shortcut for /video/explain with mode='why'
    """
    video_data = VIDEO_STORE.get(video_id)
    
    if not video_data:
        raise HTTPException(status_code=404, detail="Video ID not found.")
    
    result = explain_video_concept(
        transcript=video_data["transcript"],
        topic=query,
        mode="why",
        language=language
    )
    
    return result


@router.get("/video/concepts/{video_id}", response_model=VideoConceptsResponse)
async def get_concepts_endpoint(
    video_id: str,
    language: Literal["en", "hi", "hinglish"] = "hinglish"
):
    """
    Extract key chess concepts from the video.
    Returns a list of concepts with names and descriptions.
    """
    video_data = VIDEO_STORE.get(video_id)
    
    if not video_data:
        raise HTTPException(status_code=404, detail="Video ID not found.")
    
    concepts = get_video_concepts(
        transcript=video_data["transcript"],
        language=language
    )
    
    return VideoConceptsResponse(
        video_id=video_id,
        concepts=concepts,
        count=len(concepts)
    )


@router.get("/video/list")
async def list_videos():
    """List all processed videos in memory."""
    videos = []
    for vid, data in VIDEO_STORE.items():
        videos.append({
            "video_id": vid,
            "title": data.get("title", "Unknown"),
            "detected_language": data.get("detected_language"),
            "cached": data.get("cached", False)
        })
    
    return {
        "count": len(VIDEO_STORE),
        "videos": videos
    }


@router.get("/video/transcript/{video_id}")
async def get_transcript(video_id: str):
    """Get the raw transcript for a video (useful for debugging)."""
    video_data = VIDEO_STORE.get(video_id)
    
    if not video_data:
        raise HTTPException(status_code=404, detail="Video ID not found.")
    
    return {
        "video_id": video_id,
        "transcript": video_data["transcript"],
        "title": video_data.get("title")
    }


@router.delete("/video/{video_id}")
async def delete_video(video_id: str):
    """Remove a video from memory."""
    if video_id in VIDEO_STORE:
        del VIDEO_STORE[video_id]
        return {"status": "success", "message": f"Video {video_id} deleted"}
    
    raise HTTPException(status_code=404, detail="Video ID not found.")


@router.post("/video/cleanup")
async def cleanup_endpoint():
    """Clean up temporary audio files."""
    result = cleanup_temp_files()
    return result


@router.get("/video/cache-stats")
async def cache_stats():
    """Get cache statistics."""
    return get_cache_stats()


@router.get("/video/languages")
async def get_supported_languages():
    """Get list of supported languages."""
    return {
        "supported": SUPPORTED_LANGUAGES,
        "default": DEFAULT_LANGUAGE,
        "descriptions": {
            "en": "English",
            "hi": "Hindi (हिंदी)",
            "hinglish": "Hinglish (Hindi + English mix)"
        }
    }
