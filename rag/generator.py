# rag/generator.py
import os
from groq import Groq
from rag.retriever import get_relevant_stories
from dotenv import load_dotenv
load_dotenv()  # ✅ This loads environment variables from .env

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_llm_response(user_query: str, explain=False):
    """
    Generate kid-friendly response using Groq + retrieved context.
    
    Args:
        user_query: The child's question
        explain: If True, returns full explanation. If False, returns one-word answer.
    
    Returns:
        dict with 'answer' and 'explanation' keys
    """
    
    # 1️⃣ Retrieve top 3 relevant story chunks
    relevant_chunks = get_relevant_stories(user_query)
    
    # 🛑 If no relevant context found, return honest "don't know" response
    if not relevant_chunks or relevant_chunks.strip() == "":
        return {
            "answer": "not available",
            "explanation": "you will learn about it in future chapters!"
        }
    
    context = "\n\n".join(relevant_chunks) if isinstance(relevant_chunks, list) else relevant_chunks

    # 2️⃣ Construct prompt with STRICT context-only instructions
    if explain:
        # Full explanation mode
        prompt = f"""
You are Chess Buddy, a friendly chess teacher for kids aged 5-10 years.

CRITICAL RULES - YOU MUST FOLLOW THESE:
1. Answer ONLY using information from the Story Context below
2. Provide a detailed but kid-friendly explanation (2-3 sentences)
3. DO NOT make up new characters, events, or chess rules
4. DO NOT add information that isn't in the Story Context
5. Use simple, fun language suitable for kids

Story Context:
{context}

Child's Question: {user_query}

Instructions:
- Read the Story Context carefully
- Provide a warm, detailed explanation based on the context
- Use emojis and friendly language
"""
    else:
        # One-word answer mode
        prompt = f"""
You are Chess Buddy, a friendly chess teacher for kids aged 5-10 years.

CRITICAL INSTRUCTION: Answer with ONLY ONE WORD (or a very short phrase, max 2-3 words).

Story Context:
{context}

Child's Question: {user_query}

Instructions:
- Read the Story Context carefully
- Extract the main answer (like: "King", "Queen", "Knight", "Pawn", "Forward", "Diagonal", etc.)
- Answer with JUST that one word or short phrase
- DO NOT add explanations or extra words
- If you cannot find the answer in the context, say only: "Unknown"

ONE-WORD ANSWER:
"""

    # 3️⃣ Generate response via Groq API
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are Chess Buddy. You MUST answer only using the provided Story Context. Never invent information not present in the context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1 if not explain else 0.3,  # Very low for one-word, slightly higher for explanation
            max_tokens=10 if not explain else 200  # Short for one-word, longer for explanation
        )

        response_text = completion.choices[0].message.content.strip()

        # If in one-word mode, verify evidence in retrieved context before returning
        if not explain:
            one_word_answer = response_text

            # Build list of chunks from the retrieved context so we can check for evidence.
            if isinstance(relevant_chunks, list):
                chunks_list = relevant_chunks
            else:
                # retriever joins chunks with a separator; split back into chunks
                chunks_list = [c.strip() for c in relevant_chunks.split("\n\n---\n\n") if c.strip()]

            # Simple evidence check: ensure the one-word answer appears (word-boundary) in at least one chunk
            import re
            answer_token = one_word_answer.strip().lower()
            evidence_found = False
            if answer_token:
                for chunk in chunks_list:
                    if re.search(r"\b" + re.escape(answer_token) + r"\b", chunk.lower()):
                        evidence_found = True
                        break

            # If no direct evidence, don't return a possibly hallucinated answer
            if not evidence_found:
                return {
                    "answer": "Unknown",
                    "explanation": "I don't have that information in the chess stories I know. Can you ask me about something from the chess tales? 📚♟️"
                }

            # Evidence exists — generate explanation (kept strict)
            explanation = generate_llm_response(user_query, explain=True)

            return {
                "answer": one_word_answer,
                "explanation": explanation["explanation"] if isinstance(explanation, dict) else explanation
            }

        else:
            # In explanation mode, ensure the explanation is faithful by returning as-is (it's generated from same context)
            return {
                "answer": response_text,
                "explanation": response_text
            }

    except Exception as e:
        print("Error:", e)
        return {
            "answer": "Error",
            "explanation": "Oops! Chess Buddy is thinking too hard right now. Try again!"
        }
