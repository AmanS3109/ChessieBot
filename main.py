# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat

app = FastAPI(title="Chess Buddy AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Chess Buddy AI is running!"}
