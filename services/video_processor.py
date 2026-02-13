# services/video_processor.py - Enhanced Video Processing with Caching
import os
import yt_dlp
from faster_whisper import WhisperModel
from typing import Dict, Optional
import hashlib

from config import (
    TEMP_AUDIO_DIR, WHISPER_MODEL, WHISPER_DEVICE, 
    WHISPER_COMPUTE_TYPE, DOWNLOAD_TIMEOUT
)
from services.cache_service import get_cached_transcript, cache_transcript

# Ensure temp directory exists
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

# Initialize Whisper model (lazy loading)
_whisper_model: Optional[WhisperModel] = None


def get_whisper_model() -> WhisperModel:
    """Lazy load whisper model to avoid slow startup."""
    global _whisper_model
    if _whisper_model is None:
        print(f"🔄 Loading Whisper model: {WHISPER_MODEL}")
        _whisper_model = WhisperModel(
            WHISPER_MODEL, 
            device=WHISPER_DEVICE, 
            compute_type=WHISPER_COMPUTE_TYPE
        )
        print(f"✅ Whisper model loaded successfully")
    return _whisper_model


def generate_video_id(video_url: str) -> str:
    """Generate a consistent ID for a video URL."""
    return hashlib.md5(video_url.encode()).hexdigest()[:12]


def download_audio(video_url: str) -> Dict[str, str]:
    """
    Download audio from a video URL using yt-dlp.
    Returns dict with file path and video metadata.
    Tries with browser cookies first, falls back to without.
    """
    base_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(TEMP_AUDIO_DIR, '%(id)s.%(ext)s'),
        # Removed FFmpeg postprocessor to avoid dependency
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': DOWNLOAD_TIMEOUT,
        'retries': 3,
        'extractor_args': {'youtube': {'player_client': ['web', 'mweb', 'android']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        },
    }

    # Build list of option sets to try: with cookies first, then without
    attempts = []
    for browser in ['chrome', 'edge', 'firefox']:
        opts_with_cookies = dict(base_opts)
        opts_with_cookies['cookiesfrombrowser'] = (browser,)
        attempts.append((f"with {browser} cookies", opts_with_cookies))
    attempts.append(("without cookies", dict(base_opts)))

    last_error = ""
    for attempt_name, ydl_opts in attempts:
        try:
            print(f"   🔑 Trying {attempt_name}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=True)
                video_id = info_dict.get('id', generate_video_id(video_url))
                title = info_dict.get('title', 'Unknown')
                duration = info_dict.get('duration', 0)
                
                # Find the downloaded file (extension varies)
                downloaded_file = None
                for file in os.listdir(TEMP_AUDIO_DIR):
                    if file.startswith(video_id):
                        downloaded_file = os.path.join(TEMP_AUDIO_DIR, file)
                        break
                
                if not downloaded_file:
                    raise Exception("Downloaded file not found")
                
                print(f"   ✅ Download succeeded ({attempt_name}): {downloaded_file}")
                return {
                    "status": "success",
                    "file_path": downloaded_file,
                    "video_id": video_id,
                    "title": title,
                    "duration": duration
                }
        except Exception as e:
            last_error = str(e)
            # Clean error message (remove ANSI color codes)
            import re
            last_error = re.sub(r'\x1b\[[0-9;]*m', '', last_error)
            print(f"   ⚠️ {attempt_name} failed: {last_error[:80]}")
            continue

    return {
        "status": "error",
        "message": f"Download failed: {last_error}"
    }


def transcribe_audio(file_path: str, language: str = None) -> Dict[str, str]:
    """
    Transcribe audio file using faster-whisper.
    Returns dict with transcript and detected language.
    """
    try:
        model = get_whisper_model()
        
        # Transcribe with beam search for accuracy
        segments, info = model.transcribe(
            file_path, 
            beam_size=5,
            language=language,  # None = auto-detect
            vad_filter=True,  # Filter out silence for speed
        )
        
        # Collect all segments
        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text.strip())
        
        full_transcript = " ".join(transcript_parts)
        
        return {
            "status": "success",
            "transcript": full_transcript,
            "language": info.language,
            "duration": info.duration
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Transcription failed: {str(e)}"
        }


def process_video(video_url: str, force_refresh: bool = False) -> Dict[str, str]:
    """
    Full pipeline: Download audio -> Transcribe.
    Uses caching to avoid re-processing same videos.
    
    Args:
        video_url: URL of the video (YouTube, etc.)
        force_refresh: If True, bypass cache and reprocess
        
    Returns:
        Dict with video_id, transcript, title, and status
    """
    # Generate consistent video ID
    url_hash = generate_video_id(video_url)
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = get_cached_transcript(url_hash)
        if cached:
            print(f"✅ Cache hit for video: {url_hash}")
            return {
                "status": "success",
                "video_id": url_hash,
                "transcript": cached,
                "cached": True
            }
    
    try:
        # Step 1: Download audio
        print(f"📥 Downloading audio from: {video_url}")
        download_result = download_audio(video_url)
        
        if download_result.get("status") == "error":
            return download_result
        
        audio_path = download_result["file_path"]
        title = download_result.get("title", "Unknown")
        video_id = download_result.get("video_id", url_hash)
        
        # Step 2: Transcribe
        print(f"🎤 Transcribing audio...")
        transcribe_result = transcribe_audio(audio_path)
        
        if transcribe_result.get("status") == "error":
            return transcribe_result
        
        transcript = transcribe_result["transcript"]
        detected_lang = transcribe_result.get("language", "unknown")
        
        # Step 3: Cache the transcript
        cache_transcript(url_hash, transcript)
        print(f"✅ Video processed and cached: {url_hash}")
        
        # Clean up audio file (optional)
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass  # Non-critical
        
        return {
            "status": "success",
            "video_id": url_hash,
            "youtube_id": video_id,
            "transcript": transcript,
            "title": title,
            "detected_language": detected_lang,
            "cached": False
        }
        
    except Exception as e:
        print(f"❌ Video processing error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def cleanup_temp_files() -> Dict[str, int]:
    """Clean up temporary audio files."""
    count = 0
    try:
        for filename in os.listdir(TEMP_AUDIO_DIR):
            file_path = os.path.join(TEMP_AUDIO_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                count += 1
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    return {"status": "success", "deleted": count}
