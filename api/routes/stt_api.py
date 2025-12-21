"""
Speech-to-Text API endpoint for Chess Buddy AI
Converts audio files to text using Google Speech Recognition
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
import speech_recognition as sr
import tempfile
import os
from typing import Optional
import difflib

router = APIRouter()


class STTResponse(BaseModel):
    """Response model for speech-to-text conversion"""
    text: str
    language: str
    confidence: Optional[float] = None


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, FLAC, OGG)"),
    language: str = Form(default="auto", description="Language code: 'hi-IN', 'en-IN', or 'auto' for auto-detect")
):
    """
    Convert speech audio to text.
    
    Accepts audio files in common formats (WAV, MP3, FLAC, OGG) and returns the transcribed text.
    
    **Parameters:**
    - `audio`: Audio file to transcribe
    - `language`: Language for recognition ('hi-IN' for Hindi, 'en-IN' for English, 'auto' for auto-detect)
    
    **Returns:**
    - `text`: Transcribed text
    - `language`: Detected/used language
    - `confidence`: Confidence score (if available)
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8080/api/stt" \\
      -F "audio=@recording.wav" \\
      -F "language=auto"
    ```
    """
    
    # Validate file type
    allowed_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.webm']
    file_ext = os.path.splitext(audio.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    try:
        # Write uploaded content to temp file
        content = await audio.read()
        temp_file.write(content)
        temp_file.close()
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Load audio file
        with sr.AudioFile(temp_file.name) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Read the audio data
            audio_data = recognizer.record(source)
        
        # Try to recognize speech
        result_text = None
        detected_language = None
        
        if language == "auto":
            # Try Hindi first, then English
            try:
                result_text = recognizer.recognize_google(audio_data, language="hi-IN")
                detected_language = "hi-IN"
            except sr.UnknownValueError:
                # If Hindi fails, try English
                try:
                    result_text = recognizer.recognize_google(audio_data, language="en-IN")
                    detected_language = "en-IN"
                except sr.UnknownValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not understand audio. Please ensure clear speech."
                    )
        else:
            # Use specified language
            try:
                result_text = recognizer.recognize_google(audio_data, language=language)
                detected_language = language
            except sr.UnknownValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not understand audio in language: {language}"
                )
        
        # Post-process ASR output to correct common Hinglish/chess term mistakes
        def normalize_stt_text(text: str) -> str:
            import re
            
            # Direct replacements for common ASR errors (case-insensitive)
            replacements = {
                # English ASR errors
                "pownds": "pawn",
                "pawnds": "pawn",
                "ponds": "pawn",
                "pauns": "pawn",
                "pawnz": "pawn",
                "phone": "pawn",  # Common Hindi ASR error
                "fone": "pawn",
                
                # Hindi Devanagari errors
                "पॉन्ड्स": "pawn",
                "पॉन्स": "pawn",
                "फोन": "pawn",      # फोन (phone) → pawn
                "पोर्न": "pawn",    # Common mis-transcription
                "पौन": "pawn",
                "प्यान": "pawn",
                
                # King variants
                "किंग": "king",
                "राजा": "king",
                
                # Queen variants
                "क्वीन": "queen",
                "रानी": "queen",
                "क्वीं": "queen",
                
                # Rook variants
                "रूक": "rook",
                "हाथी": "rook",
                
                # Bishop variants
                "बिशप": "bishop",
                "ऊंट": "bishop",
                
                # Knight variants
                "नाइट": "knight",
                "घोड़ा": "knight",
            
                # Plant/plant-like misrecognitions -> pawn
                "प्लांट": "pawn",
                "प्लान्ट": "pawn",
                "प्लांट्स": "pawn",
                "प्लांटे": "pawn",
                "plant": "pawn",
                "प्लां": "pawn",
            }

            # Chess vocabulary for fuzzy matching
            vocab = [
                "king", "queen", "pawn", "rook", "bishop", "knight",
                "check", "checkmate", "move", "board", "game", "castle",
                "attack", "defend", "capture",
            ]

            # Apply direct replacements
            out = text
            for k, v in replacements.items():
                if k.isascii():
                    # Case-insensitive replacement for English
                    pattern = re.compile(re.escape(k), re.IGNORECASE)
                    out = pattern.sub(v, out)
                else:
                    # Exact replacement for Hindi/Devanagari
                    out = out.replace(k, v)

            # Token-level fuzzy correction for remaining English words
            tokens = out.split()
            corrected = []
            for tok in tokens:
                # only attempt fuzzy match for ascii tokens
                try:
                    tok_ascii = tok.encode('ascii')
                    is_ascii = True
                except Exception:
                    is_ascii = False

                if is_ascii and len(tok) > 2:
                    # find closest vocab match
                    match = difflib.get_close_matches(tok.lower(), vocab, n=1, cutoff=0.75)
                    if match:
                        corrected.append(match[0])
                        continue
                corrected.append(tok)

            return " ".join(corrected)

        if result_text:
            result_text = normalize_stt_text(result_text)

        if not result_text:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio file"
            )
        
        return STTResponse(
            text=result_text,
            language=detected_language,
            confidence=None  # Google API doesn't provide confidence via SpeechRecognition
        )
        
    except sr.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Speech recognition service error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass


@router.post("/stt/real-time")
async def speech_to_text_realtime(
    audio: UploadFile = File(..., description="Audio chunk (WAV format recommended)"),
):
    """
    Real-time speech-to-text for streaming audio.
    
    This endpoint is optimized for short audio chunks (1-5 seconds).
    Useful for live microphone input from web apps.
    
    **Parameters:**
    - `audio`: Short audio chunk (WAV format recommended)
    
    **Returns:**
    - `text`: Transcribed text
    - `is_final`: Whether this is a final transcription
    
    **Example:**
    ```javascript
    // In your Next.js app:
    const formData = new FormData();
    formData.append('audio', audioBlob);
    const response = await fetch('http://localhost:8080/api/stt/real-time', {
      method: 'POST',
      body: formData
    });
    ```
    """
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    try:
        content = await audio.read()
        temp_file.write(content)
        temp_file.close()
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300  # Lower threshold for real-time
        recognizer.dynamic_energy_threshold = True
        
        with sr.AudioFile(temp_file.name) as source:
            audio_data = recognizer.record(source)
        
        # Try Hindi first for real-time (faster)
        try:
            text = recognizer.recognize_google(audio_data, language="hi-IN")
            return {
                "text": text,
                "language": "hi-IN",
                "is_final": True
            }
        except sr.UnknownValueError:
            # Try English
            try:
                text = recognizer.recognize_google(audio_data, language="en-IN")
                return {
                    "text": text,
                    "language": "en-IN",
                    "is_final": True
                }
            except sr.UnknownValueError:
                return {
                    "text": "",
                    "language": "unknown",
                    "is_final": False
                }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass
