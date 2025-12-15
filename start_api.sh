#!/bin/bash

# Chess Buddy AI - FastAPI Server Startup Script

echo "🚀 Starting Chess Buddy AI FastAPI Server..."

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Make sure to create .env with:"
    echo "   GROQ_API_KEY=your_key"
    echo "   GOOGLE_API_KEY=your_key"
fi

# Check if embeddings exist
if [ ! -d "data/processed/chromadb" ]; then
    echo "⚠️  Warning: ChromaDB not found"
    echo "   Run: python -m rag.create_embeddings"
    echo "   to create embeddings first"
fi

# Start the server
echo "🌐 Server will be available at: http://localhost:8080"
echo "📚 API docs at: http://localhost:8080/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn main:app --reload --port 8080
