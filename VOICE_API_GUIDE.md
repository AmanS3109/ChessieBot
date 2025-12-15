# 🎤 Voice API Integration Guide

## Overview

Your Chess Buddy AI now has complete **Speech-to-Text (STT)** capabilities in the FastAPI backend! Users can speak their questions and get AI responses.

## New API Endpoints

### 1. **POST /api/stt** - Speech to Text
Convert audio files to text.

**Request:**
```bash
curl -X POST "http://localhost:8080/api/stt" \
  -F "audio=@recording.wav" \
  -F "language=auto"
```

**Parameters:**
- `audio` (file, required): Audio file (WAV, MP3, FLAC, OGG, M4A, WEBM)
- `language` (string, optional): `"hi-IN"`, `"en-IN"`, or `"auto"` (default: `"auto"`)

**Response:**
```json
{
  "text": "राजा कैसे चलता है",
  "language": "hi-IN",
  "confidence": null
}
```

---

### 2. **POST /api/stt/real-time** - Real-time STT
Optimized for short audio chunks (streaming).

**Request:**
```bash
curl -X POST "http://localhost:8080/api/stt/real-time" \
  -F "audio=@chunk.wav"
```

**Response:**
```json
{
  "text": "queen kaise chalti hai",
  "language": "en-IN",
  "is_final": true
}
```

---

### 3. **POST /api/voice-query** - Complete Voice Workflow
STT → Chat → Get JSON response (with optional TTS URL).

**Request:**
```bash
curl -X POST "http://localhost:8080/api/voice-query" \
  -F "audio=@question.wav" \
  -F "explain=true" \
  -F "return_audio=true"
```

**Parameters:**
- `audio` (file, required): Audio file with question
- `explain` (bool, optional): Include explanation (default: `false`)
- `return_audio` (bool, optional): Generate TTS URL (default: `true`)

**Response:**
```json
{
  "transcribed_text": "राजा कैसे चलता है",
  "detected_language": "hi-IN",
  "answer": "एक कदम",
  "explanation": "Yaad hai Guddu ki kahani...",
  "audio_url": "/api/tts?text=एक कदम"
}
```

---

### 4. **POST /api/voice-query/audio-response** - Voice In, Audio Out
Upload audio question → Get MP3 answer directly.

**Request:**
```bash
curl -X POST "http://localhost:8080/api/voice-query/audio-response" \
  -F "audio=@question.wav" \
  -F "explain=false" \
  -o answer.mp3
```

**Parameters:**
- `audio` (file, required): Audio file with question
- `explain` (bool, optional): Speak explanation too (default: `false`)

**Response:**
- Direct MP3 audio file (audio/mpeg)
- Header: `X-Transcribed-Text` contains what was heard

---

## Complete API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Text → Answer (JSON) |
| `/api/tts` | POST | Text → Audio (MP3) |
| `/api/stt` | POST | Audio → Text (JSON) |
| `/api/stt/real-time` | POST | Audio chunk → Text (streaming) |
| `/api/voice-query` | POST | Audio → JSON (text + answer + audio URL) |
| `/api/voice-query/audio-response` | POST | Audio → Audio (MP3) |

---

## Installation

The STT libraries are already installed in your environment. If you need to reinstall:

```bash
cd /Users/drashti/Desktop/chess\ bot/chess-buddy-ai
source .venv/bin/activate
pip install SpeechRecognition pyaudio
```

---

## Starting the API Server

```bash
cd /Users/drashti/Desktop/chess\ bot/chess-buddy-ai
source .venv/bin/activate

# Option 1: Direct uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Option 2: Using the startup script
./start_api.sh
```

**Server URLs:**
- Local: http://localhost:8080
- Docs: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## Testing the Voice API

### Test 1: Basic STT

```bash
# Record audio using macOS (or any audio recorder)
# Then test the endpoint:

curl -X POST "http://localhost:8080/api/stt" \
  -F "audio=@test.wav" \
  -F "language=auto"
```

### Test 2: Voice Query (JSON response)

```bash
curl -X POST "http://localhost:8080/api/voice-query" \
  -F "audio=@question.wav" \
  -F "explain=true"
```

### Test 3: Voice Query (Audio response)

```bash
curl -X POST "http://localhost:8080/api/voice-query/audio-response" \
  -F "audio=@question.wav" \
  -o answer.mp3

# Play the answer
afplay answer.mp3
```

### Test 4: Complete Workflow

```bash
# 1. Record your question
# Say: "राजा कैसे चलता है?"

# 2. Get transcription
curl -X POST "http://localhost:8080/api/stt" \
  -F "audio=@my_question.wav" | jq

# 3. Get voice response
curl -X POST "http://localhost:8080/api/voice-query/audio-response" \
  -F "audio=@my_question.wav" \
  -o chess_answer.mp3

# 4. Play answer
afplay chess_answer.mp3
```

---

## Next.js Integration Examples

### Example 1: Record and Transcribe

```typescript
// components/VoiceInput.tsx
'use client'

import { useState, useRef } from 'react'

export default function VoiceInput() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcription, setTranscription] = useState('')
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<Blob[]>([])

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.current = new MediaRecorder(stream)
    
    mediaRecorder.current.ondataavailable = (e) => {
      audioChunks.current.push(e.data)
    }
    
    mediaRecorder.current.onstop = async () => {
      const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' })
      audioChunks.current = []
      
      // Send to API
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.wav')
      formData.append('language', 'auto')
      
      const response = await fetch('http://localhost:8080/api/stt', {
        method: 'POST',
        body: formData
      })
      
      const data = await response.json()
      setTranscription(data.text)
    }
    
    mediaRecorder.current.start()
    setIsRecording(true)
  }

  const stopRecording = () => {
    mediaRecorder.current?.stop()
    setIsRecording(false)
  }

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? '⏹️ Stop' : '🎤 Record'}
      </button>
      {transcription && <p>You said: {transcription}</p>}
    </div>
  )
}
```

### Example 2: Voice Question with Audio Answer

```typescript
// components/VoiceChat.tsx
'use client'

import { useState, useRef } from 'react'

export default function VoiceChat() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<Blob[]>([])

  const askVoiceQuestion = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.current = new MediaRecorder(stream)
    
    mediaRecorder.current.ondataavailable = (e) => {
      audioChunks.current.push(e.data)
    }
    
    mediaRecorder.current.onstop = async () => {
      setIsProcessing(true)
      const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' })
      audioChunks.current = []
      
      // Send to voice-query endpoint
      const formData = new FormData()
      formData.append('audio', audioBlob, 'question.wav')
      formData.append('explain', 'false')
      
      const response = await fetch('http://localhost:8080/api/voice-query/audio-response', {
        method: 'POST',
        body: formData
      })
      
      // Get audio answer
      const answerBlob = await response.blob()
      const answerUrl = URL.createObjectURL(answerBlob)
      
      // Play answer
      const audio = new Audio(answerUrl)
      audio.play()
      
      // Get transcription from header
      const transcribed = response.headers.get('X-Transcribed-Text')
      console.log('You asked:', transcribed)
      
      setIsProcessing(false)
    }
    
    mediaRecorder.current.start()
    setIsRecording(true)
  }

  const stopRecording = () => {
    mediaRecorder.current?.stop()
    setIsRecording(false)
  }

  return (
    <div>
      <button 
        onClick={isRecording ? stopRecording : askVoiceQuestion}
        disabled={isProcessing}
      >
        {isProcessing ? '⏳ Processing...' : isRecording ? '⏹️ Stop' : '🎤 Ask Question'}
      </button>
    </div>
  )
}
```

### Example 3: Complete Voice UI

```typescript
// app/voice/page.tsx
'use client'

import { useState } from 'react'

interface VoiceResponse {
  transcribed_text: string
  detected_language: string
  answer: string
  explanation?: string
  audio_url?: string
}

export default function VoicePage() {
  const [response, setResponse] = useState<VoiceResponse | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleVoiceQuery = async (audioBlob: Blob) => {
    setIsProcessing(true)
    
    const formData = new FormData()
    formData.append('audio', audioBlob, 'question.wav')
    formData.append('explain', 'true')
    formData.append('return_audio', 'true')
    
    try {
      const res = await fetch('http://localhost:8080/api/voice-query', {
        method: 'POST',
        body: formData
      })
      
      const data: VoiceResponse = await res.json()
      setResponse(data)
      
      // Optionally play the audio
      if (data.audio_url) {
        const audioRes = await fetch(`http://localhost:8080${data.audio_url}`)
        const audioBlob = await audioRes.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        new Audio(audioUrl).play()
      }
    } catch (error) {
      console.error('Voice query error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">🎤 Voice Chess Buddy</h1>
      
      {/* Recording controls */}
      <button 
        className="px-6 py-3 bg-blue-500 text-white rounded-lg"
        disabled={isProcessing}
      >
        {isProcessing ? '⏳ Processing...' : isRecording ? '⏹️ Stop' : '🎤 Ask Question'}
      </button>
      
      {/* Response display */}
      {response && (
        <div className="mt-6 p-4 border rounded-lg">
          <p className="text-sm text-gray-600">You said ({response.detected_language}):</p>
          <p className="font-medium">{response.transcribed_text}</p>
          
          <div className="mt-4">
            <p className="text-2xl font-bold text-blue-600">{response.answer}</p>
          </div>
          
          {response.explanation && (
            <div className="mt-4 p-3 bg-gray-50 rounded">
              <p className="text-sm">{response.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

---

## Audio Format Support

### Supported Input Formats
- ✅ WAV (recommended for best accuracy)
- ✅ MP3
- ✅ FLAC
- ✅ OGG
- ✅ M4A
- ✅ WEBM

### Recording Tips
- Use 16kHz or 44.1kHz sample rate
- Mono channel recommended
- 16-bit depth
- Keep recordings under 1 minute for best results

---

## Language Support

### Automatic Detection
The API tries Hindi first, then English:
```python
language="auto"  # Tries hi-IN, then en-IN
```

### Manual Selection
```python
language="hi-IN"  # Force Hindi
language="en-IN"  # Force English
```

---

## Error Handling

### Common Errors

**400 - Could not understand audio**
```json
{
  "detail": "Could not understand audio. Please ensure clear speech."
}
```
**Solution:** Speak more clearly, reduce background noise

**400 - Unsupported audio format**
```json
{
  "detail": "Unsupported audio format. Allowed: .wav, .mp3, .flac, .ogg, .m4a, .webm"
}
```
**Solution:** Convert audio to supported format

**503 - Service error**
```json
{
  "detail": "Speech recognition service error: ..."
}
```
**Solution:** Check internet connection (Google API requires internet)

---

## API Documentation

Once server is running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

You can test all endpoints directly from the browser!

---

## Complete Workflow Examples

### Workflow 1: Text Only
```
User types → /api/chat → Get answer
```

### Workflow 2: Voice to Text
```
User speaks → /api/stt → Get text → User confirms → /api/chat → Get answer
```

### Workflow 3: Voice to Voice (JSON)
```
User speaks → /api/voice-query → Get JSON → Client plays TTS URL
```

### Workflow 4: Voice to Voice (Direct)
```
User speaks → /api/voice-query/audio-response → Get MP3 → Auto-play
```

---

## Production Considerations

### Security
- [ ] Replace `allow_origins=["*"]` with specific domains
- [ ] Add rate limiting for voice endpoints
- [ ] Implement authentication/API keys
- [ ] Validate audio file size limits

### Performance
- [ ] Add caching for repeated questions
- [ ] Consider using WebSockets for real-time streaming
- [ ] Implement audio compression
- [ ] Add CDN for audio file delivery

### Monitoring
- [ ] Log transcription accuracy
- [ ] Track language detection rates
- [ ] Monitor API response times
- [ ] Set up error alerting

---

## Files Created

1. ✅ `api/routes/stt_api.py` - Speech-to-text endpoints
2. ✅ `api/routes/voice_api.py` - Combined voice workflow endpoints
3. ✅ `main.py` - Updated to include STT and Voice routers
4. ✅ `requirements.txt` - Already has SpeechRecognition, pyaudio

---

**Your Chess Buddy AI now has complete voice capabilities!** 🎤♟️

Test it out and let me know how it works!
