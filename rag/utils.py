from __future__ import annotations

from typing import List, Optional, Dict

from rag.retriever import get_relevant_stories
from rag.generator import generate_llm_response
from rag.query_normalizer import normalize_query


def generate_response(question: str, explain: Optional[bool] = False, language: str = "hinglish") -> Dict[str, str]:
    """Wrapper used by the API to run the RAG pipeline.

    This function normalizes the query before processing to handle Hindi/Hinglish input.

    Args:
        question: user's question (raw Hindi/Hinglish)
        explain: if True, request a fuller story-grounded explanation
        language: target language for the response (default: hinglish)

    Returns:
        dict with keys: 'answer', 'explanation', and 'normalized_query'
    """
    # Step 1: Normalize the query (Hindi/Hinglish → canonical Hinglish)
    normalized_question = normalize_query(question)
    
    # Step 2: Generate response using normalized query
    response = generate_llm_response(normalized_question, explain=explain, language=language)
    
    # Step 3: Add normalized query to response for transparency
    response["normalized_query"] = normalized_question
    response["original_query"] = question
    
    return response

def retrieve_chunks(question: str, top_k: int = 5) -> List[str]:
    """Return raw retrieved story chunks for the given question."""
    return get_relevant_stories(question, top_k=top_k)

