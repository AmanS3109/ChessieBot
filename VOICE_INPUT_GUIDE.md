# 🎤 Voice Input Feature Guide

## What's New?

Your Chess Buddy Streamlit app now supports **both typing and speaking** your questions!

## Features Added

### 1. **Speech-to-Text (STR)**
   - Click the 🎤 Speak button to record your voice
   - Supports both **Hindi** and **English** 
   - Automatically detects the language
   - Uses Google's free speech recognition API

### 2. **Dual Input Mode**
   - **Type**: Use the text input box (as before)
   - **Speak**: Click the microphone button and speak your question

### 3. **How It Works**
   1. User clicks "🎤 Speak" button
   2. App listens for 5-10 seconds
   3. Converts speech to text using Google Speech Recognition
   4. Automatically processes the question (same as typing)
   5. AI responds with answer + explanation + TTS voice output

## Usage Instructions

### Running the App

```bash
cd /Users/drashti/Desktop/chess\ bot/chess-buddy-ai
source .venv/bin/activate
streamlit run streamlit_app.py
```

### Using Voice Input

1. **Click the "🎤 Speak" button** (next to the text input)
2. **Allow microphone access** when prompted by your browser
3. **Start speaking** when you see "🎤 Listening... Speak now!"
4. **Speak clearly** for 5-10 seconds
5. Wait for the transcription to appear
6. The app will automatically process your question

### Tips for Best Results

✅ **Do's:**
- Speak clearly and at a normal pace
- Use simple, direct questions
- Speak in either Hindi or English
- Allow microphone permissions in your browser
- Ensure minimal background noise

❌ **Don'ts:**
- Don't speak too fast or too slow
- Avoid very long sentences (keep under 10 seconds)
- Don't use the feature in noisy environments

## Technical Details

### Libraries Used
- **SpeechRecognition**: Converts speech to text
- **PyAudio**: Handles microphone input
- **Google Speech Recognition API**: Free, no API key needed

### Language Support
- **Hindi**: `hi-IN` (primary)
- **English**: `en-IN` (fallback)

The app first tries to recognize Hindi, then falls back to English if needed.

### Code Changes

**Added to `streamlit_app.py`:**
- `listen_to_microphone()` function for speech capture
- Two-column layout for text input + microphone button
- Session state management for voice input
- Error handling for microphone issues

**Added to `requirements.txt`:**
- `SpeechRecognition`
- `pyaudio`

## Testing Voice Input

### Quick Test Questions (Hindi):
- "राजा कैसे चलता है?" (How does the king move?)
- "शतरंज का खेल कैसे खेलें?" (How to play chess?)
- "गुड्डू की कहानी सुनाओ" (Tell Guddu's story)

### Quick Test Questions (English):
- "How does the queen move?"
- "What is checkmate?"
- "Tell me a chess story"

## Troubleshooting

### Issue: Microphone not working
**Solution:** 
- Check browser permissions (allow microphone access)
- On macOS: System Settings → Privacy & Security → Microphone → Allow Terminal/Browser

### Issue: "No speech detected"
**Solution:**
- Speak louder and clearer
- Check if your microphone is properly connected
- Reduce background noise

### Issue: Speech not recognized correctly
**Solution:**
- Speak more slowly
- Use simpler phrases
- Ensure good microphone quality
- Try switching between Hindi and English

### Issue: PyAudio installation errors
**Solution (macOS):**
```bash
brew install portaudio
pip install pyaudio
```

**Solution (Linux):**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

## Next Steps

Once you've tested this in Streamlit and it works well:

1. **Test the feature thoroughly** with various questions
2. **Try both Hindi and English** inputs
3. **Check recognition accuracy** in different environments
4. **Let me know if it works well**, then I can integrate it into the FastAPI backend

### API Integration (Future)

When ready, we can add:
- `POST /api/stt` endpoint (speech-to-text)
- File upload for audio files
- WebSocket support for real-time streaming
- Combined endpoint: voice → text → answer → voice response

## Demo Flow

```
User Flow:
1. Click 🎤 Speak
2. Say: "राजा कैसे चलता है?"
3. See: "✅ You said (Hindi): राजा कैसे चलता है?"
4. AI responds: "🎯 एक कदम"
5. Hear TTS: "एक कदम" (spoken aloud)
6. Click 💡 Explain for details
```

## Files Modified

- ✅ `streamlit_app.py` - Added voice input UI and logic
- ✅ `requirements.txt` - Added SpeechRecognition, pyaudio
- ✅ Libraries installed in `.venv`

---

**Ready to test!** Run the Streamlit app and try speaking your chess questions! 🎤♟️
