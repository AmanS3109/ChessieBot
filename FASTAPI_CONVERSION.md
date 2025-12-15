# Chess Buddy AI - FastAPI Conversion Complete ✅

Your Streamlit app has been successfully converted to a FastAPI backend that you can use with your Next.js frontend!

## 🎯 What Changed

### Old Structure (Streamlit)
- `streamlit_app.py` - Interactive web UI with TTS
- Session state management in Streamlit
- Direct browser audio playback via edge-tts

### New Structure (FastAPI)
- `main.py` - FastAPI application entry point
- `api/routes/chat_api.py` - REST API endpoints
- `rag/utils.py` - Updated to support explain flag
- Works with any frontend (Next.js, React, Vue, etc.)

## 🚀 Quick Start

### Start the API Server

```bash
# Option 1: Using the startup script
./start_api.sh

# Option 2: Manual start
source .venv/bin/activate
uvicorn main:app --reload --port 8080
```

The API will be available at: **http://localhost:8080**

Interactive API docs: **http://localhost:8080/docs**

## 📡 Available Endpoints

### 1. **POST** `/api/chat`
Get a story-grounded answer from Chess Buddy.

**Request:**
```json
{
  "question": "King ko kya kehte hain?",
  "explain": false
}
```

**Response:**
```json
{
  "answer": "K",
  "explanation": "Yaad hai when story mein kaha gaya:\n\"Main hoon Chessland ka King—sab mujhe K bulate hain\"\n\nIsliye is sawal ka jawab K hai"
}
```

### 2. **POST** `/api/retrieve`
Get raw story chunks (for debugging/showing sources).

**Request:**
```json
{
  "question": "King kaise chalta hai?",
  "top_k": 3
}
```

**Response:**
```json
{
  "chunks": [
    "Minku looks curious and asks, \"King ji, aap Queen ki tarah zoom-zoom chal sakte ho?\"...",
    "..."
  ]
}
```

### 3. **GET** `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Chess Buddy AI"
}
```

## 🔗 Next.js Integration

See **[API_INTEGRATION.md](./API_INTEGRATION.md)** for:
- Complete Next.js example code
- React components
- TypeScript types
- Error handling
- Deployment guide

### Quick Example

```typescript
// In your Next.js app
const response = await fetch('http://localhost:8080/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    question: 'King ko kya kehte hain?', 
    explain: false 
  }),
});

const data = await response.json();
console.log(data.answer); // "K"
console.log(data.explanation); // Story-based explanation
```

## 📦 Requirements

All dependencies are in `requirements.txt`:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `groq` - LLM API (currently used in generator)
- `edge-tts` - Text-to-speech (used in Streamlit app)
- All RAG dependencies (langchain, chromadb, etc.)

## 🔧 Configuration

### Environment Variables (.env)
```bash
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### CORS Settings
Currently allowing all origins for development. Update `main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-nextjs-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Testing

### Using cURL

```bash
# Health check
curl http://localhost:8080/health

# Ask a question
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Pawn kaise chalta hai?", "explain": false}'

# Get detailed explanation
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Pawn kaise chalta hai?", "explain": true}'
```

### Using Browser
Visit **http://localhost:8080/docs** for interactive API documentation (Swagger UI).

## 📁 File Structure

```
chess-buddy-ai/
├── main.py                    # FastAPI app entry point
├── start_api.sh              # Startup script
├── API_INTEGRATION.md        # Detailed Next.js integration guide
├── requirements.txt          # Updated with groq, edge-tts
├── api/
│   ├── __init__.py
│   └── routes/
│       └── chat_api.py       # API endpoints (chat, retrieve)
├── rag/
│   ├── generator.py          # LLM response generation (using Groq)
│   ├── retriever.py          # Story chunk retrieval
│   └── utils.py              # Wrapper functions for API
├── data/
│   ├── hindi_stories/        # Source story files
│   └── processed/
│       └── chromadb/         # Vector embeddings
└── streamlit_app.py          # Original Streamlit UI (still works!)
```

## 🎨 Features Preserved

✅ **Story-grounded RAG** - All responses are based on retrieved story chunks  
✅ **One-word + Explain mode** - Short answer with optional detailed explanation  
✅ **Evidence checking** - LLM must quote story lines as proof  
✅ **Hinglish support** - Natural kid-friendly language mixing  
✅ **Query rewriting** - Better retrieval through query optimization  

## 🔄 Both UIs Still Work!

### Run Streamlit (Original)
```bash
streamlit run streamlit_app.py
```

### Run FastAPI (New)
```bash
./start_api.sh
# or
uvicorn main:app --reload --port 8080
```

You can run both simultaneously on different ports!

## 🚀 Deployment Options

### Option 1: Render / Railway
1. Push code to GitHub
2. Connect repo
3. Set env vars (GROQ_API_KEY, GOOGLE_API_KEY)
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Vercel
Deploy Next.js frontend on Vercel, deploy FastAPI backend separately.

### Option 3: Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 🐛 Troubleshooting

### Port already in use
```bash
lsof -ti:8080 | xargs kill -9
```

### Module not found
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### ChromaDB not found
```bash
python -m rag.create_embeddings
```

### CORS errors
Check that FastAPI server is running and CORS is configured in `main.py`.

## 📚 Documentation

- **API_INTEGRATION.md** - Complete Next.js integration guide with examples
- **http://localhost:8080/docs** - Interactive API documentation (when server is running)
- **http://localhost:8080/redoc** - Alternative API documentation

## ✨ Next Steps

1. **Test the API**: Start the server and test with cURL or Postman
2. **Build Next.js UI**: Use the examples in API_INTEGRATION.md
3. **Add features**: 
   - User authentication
   - Rate limiting
   - Conversation history
   - TTS on frontend (Web Speech API)
4. **Deploy**: Choose a deployment platform and go live!

## 🎉 Success!

Your Chess Buddy AI is now a production-ready REST API that can be consumed by any frontend framework. The conversion maintains all the core RAG functionality while making it accessible to your Next.js application.

**Happy coding! 🚀♟️**
