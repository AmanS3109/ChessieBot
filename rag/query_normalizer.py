"""
Query Normalization Module
Rewrites Hindi/Hinglish user questions into canonical Hinglish chess questions.
Uses Groq LLM with strict prompting and LRU caching.
"""

import os
from functools import lru_cache
from groq import Groq


# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@lru_cache(maxsize=256)
def normalize_query(raw_query: str) -> str:
    """
    Normalize a Hindi/Hinglish chess question into canonical form.
    
    This function ONLY rewrites questions - it does NOT answer them.
    
    Args:
        raw_query: Raw text from STT or user typing (Hindi, Hinglish, or mixed)
    
    Returns:
        Canonical Hinglish question (single line, standard chess terms, no punctuation)
    
    Examples:
        "पोर्न कैसे अटैक करते हैं" → "pawn kaise attack karta hai"
        "किंग कैसे चलता है" → "king kaise chalta hai"
        "queen ki movement kya hai" → "queen kaise chalti hai"
    """
    
    # If query is very short or already clean, return as-is
    if len(raw_query.strip()) < 3:
        return raw_query.strip()
    
    # Strict normalization prompt
    system_prompt = """You are a QUERY REWRITER for a kids chess learning app.

YOUR ONLY JOB: Rewrite Hindi/Hinglish questions into clean canonical Hinglish.

RULES (STRICT):
1. Output ONLY the rewritten question - NO explanation, NO answer
2. Use standard chess terms in English: king, queen, pawn, rook, bishop, knight, board, move, attack, capture, check, checkmate
3. Keep Hindi grammar words: kaise, kya, kahan, kab, kaun, kitne, etc.
4. Prefer singular form: "pawn kaise chalta hai" not "pawns kaise chalte hain"
5. No punctuation at the end
6. One single line only
7. If already clean, return unchanged
8. Fix common ASR errors: पोर्न→pawn, किंग→king, क्वीन→queen

EXAMPLES:
Input: "पोर्न कैसे अटैक करते हैं"
Output: pawn kaise attack karta hai

Input: "किंग कैसे चलता है"
Output: king kaise chalta hai

Input: "queen ki movement kya hai"
Output: queen kaise chalti hai

Input: "रूक कहाँ चल सकता है"
Output: rook kahan chal sakta hai

DO NOT:
- Answer the question
- Add explanations
- Change the question intent
- Add punctuation
- Use multiple lines

REMEMBER: You are a REWRITER, not an ANSWERER."""

    user_prompt = f"Rewrite this question:\n{raw_query}"
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,  # Zero creativity - strict rewriting only
            max_tokens=50,  # Questions are short
            top_p=1.0,
        )
        
        normalized = response.choices[0].message.content.strip()
        
        # Safety check: if LLM returns something too long or off-topic, use original
        if len(normalized) > 200 or '\n' in normalized:
            return raw_query.strip()
        
        return normalized
        
    except Exception as e:
        # On error, return original query
        print(f"Query normalization error: {e}")
        return raw_query.strip()


def normalize_query_batch(queries: list[str]) -> list[str]:
    """
    Normalize multiple queries at once (for testing/batch processing).
    
    Args:
        queries: List of raw queries
    
    Returns:
        List of normalized queries
    """
    return [normalize_query(q) for q in queries]


# Test function for development
def _test_normalizer():
    """Test the query normalizer with sample inputs."""
    test_cases = [
        "पोर्न कैसे अटैक करते हैं",
        "किंग कैसे चलता है",
        "queen ki movement kya hai",
        "रूक कहाँ चल सकता है",
        "pawn kaise attack karta hai",  # Already clean
        "क्वीन की ताकत क्या है",
        "बिशप कैसे मूव करता है",
    ]
    
    print("Query Normalization Test:\n")
    for raw in test_cases:
        normalized = normalize_query(raw)
        print(f"Input:  {raw}")
        print(f"Output: {normalized}")
        print()


if __name__ == "__main__":
    _test_normalizer()
