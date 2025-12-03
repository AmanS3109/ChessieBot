# rag/utils.py
from rag.retriever import get_relevant_stories
from rag.generator import generate_llm_response

def generate_response(question: str):
    """
    Unified wrapper for RAG pipeline: retrieve + generate.
    Used by FastAPI endpoint.
    """
    # This now properly uses the working retriever and generator
    return generate_llm_response(question)
