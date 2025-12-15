# Chess Buddy AI - FastAPI Integration Guide

## 🚀 Quick Start

### Starting the API Server

```bash
cd /Users/drashti/Desktop/chess\ bot/chess-buddy-ai
source .venv/bin/activate
uvicorn main:app --reload --port 8080
```

The API will be available at: **http://localhost:8080**

---

## 📡 API Endpoints

### 1. Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Chess Buddy AI"
}
```

---

### 2. Chat (Question & Answer)
**POST** `/api/chat`

Get a story-grounded answer from Chess Buddy.

**Request Body:**
```json
{
  "question": "King ko kya kehte hain?",
  "explain": false
}
```

**Parameters:**
- `question` (string, required): The user's question
- `explain` (boolean, optional, default: false): 
  - `false` → Returns a short one-word/phrase answer
  - `true` → Returns a detailed story-based explanation

**Response:**
```json
{
  "answer": "K",
  "explanation": "Yaad hai when story mein kaha gaya:\n\"sab mujhe K bulate hain\"\n\nIsliye is sawal ka jawab K hai"
}
```

---

### 3. Retrieve Story Chunks (Debug)
**POST** `/api/retrieve`

Get raw story chunks retrieved for a question (useful for showing sources).

**Request Body:**
```json
{
  "question": "King kaise chalta hai?",
  "top_k": 5
}
```

**Parameters:**
- `question` (string, required): The search query
- `top_k` (integer, optional, default: 5): Number of chunks to retrieve

**Response:**
```json
{
  "chunks": [
    "Raja sirf ek kadam chalta hai...",
    "King ko K bulate hain...",
    "..."
  ]
}
```

---

## 🔗 Next.js Integration Example

### Installation

```bash
npm install axios
# or
npm install @tanstack/react-query axios
```

### Basic Fetch Example

```typescript
// app/api/chess-buddy.ts
export async function askChessBuddy(question: string, explain: boolean = false) {
  const response = await fetch('http://localhost:8080/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, explain }),
  });

  if (!response.ok) {
    throw new Error('Failed to get response from Chess Buddy');
  }

  return response.json();
}
```

### React Component Example

```typescript
'use client';

import { useState } from 'react';

interface ChatResponse {
  answer: string;
  explanation: string;
}

export default function ChessBuddyChat() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleAsk = async () => {
    setLoading(true);
    setShowExplanation(false);
    
    try {
      const res = await fetch('http://localhost:8080/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, explain: false }),
      });
      
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = () => {
    setShowExplanation(true);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">♟️ Chess Buddy</h1>
      
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about chess..."
          className="flex-1 px-4 py-2 border rounded-lg"
          onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
        />
        <button
          onClick={handleAsk}
          disabled={loading}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? '...' : 'Ask'}
        </button>
      </div>

      {response && (
        <div className="bg-white border rounded-lg p-6 shadow-sm">
          <div className="text-4xl font-bold text-center mb-4">
            🎯 {response.answer}
          </div>
          
          {!showExplanation ? (
            <button
              onClick={handleExplain}
              className="w-full py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              💡 Explain
            </button>
          ) : (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-bold mb-2">Explanation:</h3>
              <p className="whitespace-pre-wrap">{response.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Using React Query (Recommended)

```typescript
// hooks/useChessBuddy.ts
import { useMutation } from '@tanstack/react-query';

interface ChatRequest {
  question: string;
  explain?: boolean;
}

interface ChatResponse {
  answer: string;
  explanation: string;
}

async function askChessBuddy(data: ChatRequest): Promise<ChatResponse> {
  const response = await fetch('http://localhost:8080/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch');
  }

  return response.json();
}

export function useChessBuddy() {
  return useMutation({
    mutationFn: askChessBuddy,
  });
}

// In your component:
const { mutate, data, isPending } = useChessBuddy();

const handleAsk = () => {
  mutate({ question: userInput, explain: false });
};
```

---

## 🔧 Environment Setup

Make sure your `.env` file contains:

```bash
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

---

## 📦 CORS Configuration

The API is configured to allow all origins during development:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For Production

Update `main.py` to only allow your Next.js domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-nextjs-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🧪 Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8080/health

# Ask a question (short answer)
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "King ko kya kehte hain?", "explain": false}'

# Get detailed explanation
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "King ko kya kehte hain?", "explain": true}'

# Retrieve story chunks
curl -X POST http://localhost:8080/api/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question": "King kaise chalta hai?", "top_k": 3}'
```

### Using Postman or Thunder Client

1. Create a new POST request to `http://localhost:8080/api/chat`
2. Set Headers: `Content-Type: application/json`
3. Body (raw JSON):
```json
{
  "question": "Pawn kaise chalta hai?",
  "explain": false
}
```

---

## 🚀 Deployment

### Option 1: Render / Railway / Fly.io

1. Push your code to GitHub
2. Connect your repo to the platform
3. Set environment variables (GROQ_API_KEY, GOOGLE_API_KEY)
4. Deploy command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Build and run:
```bash
docker build -t chess-buddy-api .
docker run -p 8080:8080 --env-file .env chess-buddy-api
```

---

## 📚 Additional Features

### Add Rate Limiting (Optional)

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/chat")
@limiter.limit("10/minute")
async def chat_with_buddy(request: Request, chat_request: ChatRequest):
    # ... existing code
```

---

## 🎯 TypeScript Types

Create `types/chess-buddy.ts` in your Next.js app:

```typescript
export interface ChatRequest {
  question: string;
  explain?: boolean;
}

export interface ChatResponse {
  answer: string;
  explanation: string;
}

export interface RetrieveRequest {
  question: string;
  top_k?: number;
}

export interface RetrieveResponse {
  chunks: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
}
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -ti:8080 | xargs kill -9
```

### Module Not Found Errors
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### CORS Errors in Browser
Make sure the FastAPI server is running and CORS is properly configured in `main.py`.

---

## 📞 Support

If you encounter issues, check:
1. API server is running on http://localhost:8080
2. Environment variables are set in `.env`
3. All dependencies are installed
4. ChromaDB exists at `data/processed/chromadb` (run `python -m rag.create_embeddings` if needed)
