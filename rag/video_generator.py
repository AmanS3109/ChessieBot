# rag/video_generator.py - Enhanced Video Response Generator with Bilingual Support
import os
from groq import Groq
from dotenv import load_dotenv
from typing import Literal, Dict
from functools import lru_cache

from config import (
    GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS, 
    GROQ_TEMPERATURE, DEFAULT_LANGUAGE
)
from services.language_service import get_system_prompt, validate_language

load_dotenv()

# Initialize Groq client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)


def generate_video_response(
    transcript: str, 
    user_query: str,
    language: Literal["en", "hi", "hinglish"] = "hinglish"
) -> Dict[str, str]:
    """
    Generate a response to a user's question about a video, using its transcript.
    Supports multiple languages (English, Hindi, Hinglish).
    
    Args:
        transcript: The full text transcript of the video
        user_query: The user's question
        language: Response language ("en", "hi", "hinglish")
        
    Returns:
        dict: { "answer": str, "explanation": str, "language": str }
    """
    if not client:
        return {
            "answer": "Error",
            "explanation": "Groq API key not configured.",
            "language": language
        }
    
    # Validate language
    language = validate_language(language)
    
    # Truncate transcript if too long (Llama 3.1 8b has ~8k context)
    max_chars = 18000
    truncated_transcript = transcript[:max_chars] + ("..." if len(transcript) > max_chars else "")
    
    # Get language-specific system prompt
    system_prompt = get_system_prompt(language)
    
    # Build user prompt based on language
    prompt = _build_prompt(truncated_transcript, user_query, language)
    
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Parse response
        answer, explanation = _parse_response(response_text, language)
        
        return {
            "answer": answer,
            "explanation": explanation,
            "language": language
        }
        
    except Exception as e:
        print(f"❌ Groq generation error: {e}")
        error_msg = _get_error_message(language)
        return {
            "answer": "Error",
            "explanation": error_msg,
            "language": language
        }


def _build_prompt(transcript: str, query: str, language: str) -> str:
    """Build language-specific prompt."""
    
    prompts = {
        "en": f"""You are Chess Buddy, a friendly AI tutor analyzing a chess video.
You have the TRANSCRIPT of the video below.

TRANSCRIPT:
{transcript}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer the user's question based ONLY on the transcript provided.
2. Use simple, clear English suitable for kids.
3. If the answer is not in the transcript, say "This is not covered in the video."
4. Explain "WHY" if the user asks why.
5. Keep the explanation educational and encouraging.

FORMAT:
ANSWER: <One sentence direct answer>
EXPLANATION: <Detailed explanation in simple English>""",

        "hi": f"""आप Chess Buddy हैं, एक friendly AI tutor जो chess video analyze कर रहा है।
नीचे video का TRANSCRIPT है।

TRANSCRIPT:
{transcript}

USER QUESTION:
{query}

INSTRUCTIONS:
1. सवाल का जवाब ONLY transcript के आधार पर दो।
2. Simple Hindi use करो जो बच्चे समझ सकें।
3. अगर answer transcript में नहीं है, बोलो "यह video में नहीं है।"
4. अगर user "क्यों" पूछे तो explain करो।
5. Encouraging और educational रहो।

FORMAT:
ANSWER: <एक line में direct answer>
EXPLANATION: <Detail में Hindi में explanation>""",

        "hinglish": f"""You are Chess Buddy, ek friendly AI tutor jo chess video analyze kar raha hai.
Neeche video ka TRANSCRIPT hai.

TRANSCRIPT:
{transcript}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer the question based ONLY on the transcript.
2. Use friendly Hinglish (Hindi + English mix) suitable for Indian kids.
3. Agar answer transcript mein nahi hai, bolo "Iska jawab video mein nahi hai."
4. Agar user "why/kyun" poohe to explain karo.
5. Encouraging aur educational raho! 😊

FORMAT:
ANSWER: <Ek line mein direct answer>
EXPLANATION: <Detailed explanation in Hinglish>"""
    }
    
    return prompts.get(language, prompts["hinglish"])


def _parse_response(response_text: str, language: str) -> tuple:
    """Parse LLM response into answer and explanation."""
    answer = _get_default_answer(language)
    explanation = response_text
    
    lines = response_text.split('\n')
    for line in lines:
        if line.upper().startswith("ANSWER:"):
            answer = line.split(":", 1)[1].strip()
        elif line.upper().startswith("EXPLANATION:"):
            explanation = line.split(":", 1)[1].strip()
    
    # If parsing failed, use the whole response as explanation
    if answer == _get_default_answer(language):
        explanation = response_text
    
    return answer, explanation


def _get_default_answer(language: str) -> str:
    """Get default 'processing' answer."""
    defaults = {
        "en": "Let me explain...",
        "hi": "मैं समझाता हूं...",
        "hinglish": "Dekho..."
    }
    return defaults.get(language, "Dekho...")


def _get_error_message(language: str) -> str:
    """Get error message in specified language."""
    messages = {
        "en": "I'm having trouble thinking right now. Please try again!",
        "hi": "मुझे अभी सोचने में दिक्कत हो रही है। फिर से try करो!",
        "hinglish": "Mujhe sochne mein thodi dikkat ho rahi hai. Phir se poocho! 😅"
    }
    return messages.get(language, messages["hinglish"])


# Legacy function for backward compatibility
def generate_response_legacy(transcript: str, user_query: str) -> dict:
    """Legacy function - uses hinglish by default."""
    return generate_video_response(transcript, user_query, language="hinglish")
