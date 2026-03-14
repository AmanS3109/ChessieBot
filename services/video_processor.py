# services/video_processor.py - Enhanced Video Processing with Caching
import os
import re
import yt_dlp
from faster_whisper import WhisperModel
from typing import Dict, Optional
import hashlib

from config import (
    TEMP_AUDIO_DIR, WHISPER_MODEL, WHISPER_DEVICE, 
    WHISPER_COMPUTE_TYPE, DOWNLOAD_TIMEOUT
)
from services.cache_service import get_cached_transcript, cache_transcript

# Try to import youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
    print("✅ youtube-transcript-api available")
except ImportError:
    HAS_TRANSCRIPT_API = False
    print("⚠️ youtube-transcript-api not installed, using yt-dlp + Whisper only")

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


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript_via_api(video_url: str) -> Dict[str, str]:
    """
    Get transcript using youtube-transcript-api (no download needed).
    This bypasses YouTube's bot detection entirely.
    """
    youtube_id = extract_youtube_id(video_url)
    if not youtube_id:
        return {"status": "error", "message": "Could not extract YouTube video ID from URL"}
    
    try:
        print(f"   📝 Fetching transcript via YouTube API for: {youtube_id}")
        
        # Try to get transcript - prefer English, Hindi, then auto-generated
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.fetch(youtube_id)
        
        # Combine all transcript segments into full text
        full_transcript = " ".join([entry.text for entry in transcript_list])
        
        if not full_transcript.strip():
            return {"status": "error", "message": "Transcript is empty"}
        
        print(f"   ✅ Transcript fetched successfully ({len(full_transcript)} chars)")
        
        return {
            "status": "success",
            "transcript": full_transcript,
            "video_id": youtube_id,
            "language": "auto",
            "method": "youtube-transcript-api"
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ⚠️ Transcript API failed: {error_msg[:100]}")
        return {"status": "error", "message": f"Transcript API failed: {error_msg}"}


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

    # Build list of option sets to try
    # Skip browser cookies in production/Docker (no browsers installed)
    attempts = []
    env = os.getenv("ENV", "development")
    if env == "development":
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
    Full pipeline: Try YouTube Transcript API first, fallback to Download + Whisper.
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
        # ========================================
        # Method 1: YouTube Transcript API (fast, no download needed)
        # ========================================
        if HAS_TRANSCRIPT_API and extract_youtube_id(video_url):
            print(f"📝 Trying YouTube Transcript API first...")
            api_result = get_transcript_via_api(video_url)
            
            if api_result.get("status") == "success":
                transcript = api_result["transcript"]
                
                # Cache the transcript
                cache_transcript(url_hash, transcript)
                print(f"✅ Video processed via Transcript API and cached: {url_hash}")
                
                return {
                    "status": "success",
                    "video_id": url_hash,
                    "youtube_id": api_result.get("video_id", url_hash),
                    "transcript": transcript,
                    "title": f"YouTube Video ({api_result.get('video_id', 'unknown')})",
                    "detected_language": api_result.get("language", "auto"),
                    "cached": False,
                    "method": "transcript-api"
                }
            else:
                print(f"⚠️ Transcript API failed, falling back to yt-dlp + Whisper...")
        
        # ========================================
        # Method 2: yt-dlp + Whisper (fallback)
        # ========================================
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
        print(f"✅ Video processed via Whisper and cached: {url_hash}")
        
        # Clean up audio file
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
            "cached": False,
            "method": "whisper"
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
