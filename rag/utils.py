from __future__ import annotations

from typing import List, Optional

from rag.retriever import get_relevant_stories
from rag.generator import generate_llm_response


def generate_response(question: str, explain: Optional[bool] = False):
    """Wrapper used by the API to run the RAG pipeline.

    Args:
        question: user's question
        explain: if True, request a fuller story-grounded explanation

    Returns:
        dict with keys: 'answer' and 'explanation'
    """
    return generate_llm_response(question, explain=explain)

def retrieve_chunks(question: str, top_k: int = 5) -> List[str]:
    """Return raw retrieved story chunks for the given question."""
    return get_relevant_stories(question, top_k=top_k)

