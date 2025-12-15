"""
Combined Voice API endpoint for Chess Buddy AI
Handles the complete voice workflow: STT → Chat → TTS
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import speech_recognition as sr
import tempfile
import os
import asyncio
from typing import Optional
import edge_tts

from rag.utils import generate_response

router = APIRouter()

# Voice configuration
HINDI_VOICE = "hi-IN-MadhurNeural"
ENGLISH_VOICE = "en-IN-NeerjaNeural"


class VoiceQueryResponse(BaseModel):
    """Response model for voice query"""
    transcribed_text: str
    detected_language: str
    answer: str
    explanation: Optional[str] = None
    audio_url: Optional[str] = None


def normalize_for_tts(text: str) -> str:
    """Normalize text for better TTS pronunciation"""
    replacements = {
        "kise": "kisse",
        "kon": "kaun",
        "kehte": "kehtey",
        "kyun": "kyon",
        "raja": "raajaa",
        "bulate": "bulaate",
    }
    out = text.lower()
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def is_mostly_english(text: str) -> bool:
    """Detect if text is primarily English"""
    keywords = [
        "king", "queen", "pawn", "rook", "bishop", "knight",
        "game", "move", "step", "board", "check"
    ]
    text_lower = text.lower()
    return any(k in text_lower for k in keywords)


async def _tts_save(text: str, voice: str, path: str):
    """Generate TTS audio and save to file"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


@router.post("/voice-query")
async def voice_query(
    audio: UploadFile = File(..., description="Audio file with the question"),
    explain: bool = Form(default=False, description="Whether to return explanation"),
    return_audio: bool = Form(default=True, description="Whether to generate TTS audio response")
):
    """
    Complete voice workflow: Speech → Answer → Voice
    
    This endpoint handles the full voice interaction:
    1. Converts speech audio to text (STT)
    2. Processes the question through Chess Buddy AI
    3. Optionally generates voice response (TTS)
    
    **Parameters:**
    - `audio`: Audio file with the question (WAV, MP3, FLAC, OGG)
    - `explain`: Include detailed explanation in response
    - `return_audio`: Generate and return audio URL for the answer
    
    **Returns:**
    - `transcribed_text`: What you said
    - `detected_language`: Language detected (hi-IN or en-IN)
    - `answer`: Short answer from AI
    - `explanation`: Detailed explanation (if requested)
    - `audio_url`: URL to download answer audio (if requested)
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8080/api/voice-query" \\
      -F "audio=@question.wav" \\
      -F "explain=true" \\
      -F "return_audio=true"
    ```
    """
    
    # Step 1: Speech-to-Text
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    try:
        content = await audio.read()
        temp_audio.write(content)
        temp_audio.close()
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_audio.name) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        # Try Hindi first, then English
        transcribed_text = None
        detected_language = None
        
        try:
            transcribed_text = recognizer.recognize_google(audio_data, language="hi-IN")
            detected_language = "hi-IN"
        except sr.UnknownValueError:
            try:
                transcribed_text = recognizer.recognize_google(audio_data, language="en-IN")
                detected_language = "en-IN"
            except sr.UnknownValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Could not understand audio. Please speak clearly."
                )
        
        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio"
            )
        
    except sr.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Speech recognition service error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        )
    finally:
        try:
            os.unlink(temp_audio.name)
        except:
            pass
    
    # Step 2: Generate AI Response
    try:
        response = await asyncio.to_thread(
            generate_response,
            transcribed_text,
            explain
        )
        
        answer = response.get("answer", "Unknown")
        explanation = response.get("explanation", "") if explain else None
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
    
    # Step 3: Text-to-Speech (optional)
    audio_url = None
    if return_audio:
        # For now, we'll indicate where the TTS endpoint is
        # In production, you might generate and store the file, then return a URL
        audio_url = f"/api/tts?text={answer}"
    
    return VoiceQueryResponse(
        transcribed_text=transcribed_text,
        detected_language=detected_language,
        answer=answer,
        explanation=explanation,
        audio_url=audio_url
    )


@router.post("/voice-query/audio-response")
async def voice_query_audio_response(
    audio: UploadFile = File(..., description="Audio file with the question"),
    explain: bool = Form(default=False, description="Whether to speak the explanation too")
):
    """
    Voice query with direct audio response (streaming).
    
    This endpoint returns the answer as an audio file directly,
    perfect for immediate playback in your Next.js app.
    
    **Flow:**
    1. Upload audio question
    2. Get MP3 audio answer back
    
    **Example:**
    ```javascript
    // In Next.js:
    const formData = new FormData();
    formData.append('audio', audioBlob);
    
    const response = await fetch('http://localhost:8080/api/voice-query/audio-response', {
      method: 'POST',
      body: formData
    });
    
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    new Audio(audioUrl).play();
    ```
    """
    
    # Step 1: STT
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    transcribed_text = None
    
    try:
        content = await audio.read()
        temp_audio.write(content)
        temp_audio.close()
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_audio.name) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        try:
            transcribed_text = recognizer.recognize_google(audio_data, language="hi-IN")
        except sr.UnknownValueError:
            try:
                transcribed_text = recognizer.recognize_google(audio_data, language="en-IN")
            except sr.UnknownValueError:
                raise HTTPException(status_code=400, detail="Could not understand audio")
    
    finally:
        try:
            os.unlink(temp_audio.name)
        except:
            pass
    
    if not transcribed_text:
        raise HTTPException(status_code=400, detail="No speech detected")
    
    # Step 2: Generate answer
    response = await asyncio.to_thread(generate_response, transcribed_text, explain)
    answer = response.get("answer", "Unknown")
    
    if explain:
        explanation = response.get("explanation", "")
        text_to_speak = f"{answer}. {explanation}"
    else:
        text_to_speak = answer
    
    # Step 3: Generate TTS
    text_to_speak = normalize_for_tts(text_to_speak)
    voice = ENGLISH_VOICE if is_mostly_english(text_to_speak) else HINDI_VOICE
    
    temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    temp_mp3.close()
    
    try:
        await _tts_save(text_to_speak, voice, temp_mp3.name)
        
        def iterfile():
            with open(temp_mp3.name, "rb") as f:
                yield from f
            # Clean up after streaming
            os.unlink(temp_mp3.name)
        
        return StreamingResponse(
            iterfile(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=answer.mp3",
                "X-Transcribed-Text": transcribed_text
            }
        )
    
    except Exception as e:
        try:
            os.unlink(temp_mp3.name)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")
