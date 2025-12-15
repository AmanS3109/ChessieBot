# # rag/retriever.py
# from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import HuggingFaceEmbeddings

# def get_relevant_stories(query: str, db_path="rag/chroma_db", top_k=3):
#     """Retrieve top relevant story chunks based on query."""
#     embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
#     vectordb = Chroma(persist_directory=db_path, embedding_function=embeddings)
    
#     # results = vectordb.similarity_search(query, k=top_k)
#     # return [r.page_content for r in results]
#     results = vectordb.similarity_search_with_score(query, k=5)
#     filtered = [r for r, s in results if s > 0.7]

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
EMBED_MODEL = "distiluse-base-multilingual-cased-v1"
def get_relevant_stories(query: str, db_path="data/processed/chromadb", top_k=5, score_threshold=0.5):
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectordb = Chroma(persist_directory=db_path, embedding_function=embeddings)

    results = vectordb.similarity_search_with_score(query, k=top_k)

    chunks = []
    for doc, score in results:
        if score > score_threshold:
            chunks.append(doc.page_content)

    return chunks  # ✅ LIST
# def get_relevant_stories(query: str, db_path="data/processed/chromadb", top_k=5, score_threshold=0.7):
#     """
#     Retrieve top relevant story chunks based on query.
#     Returns a single combined context string for LLM.
    
#     Args:
#         query: User's question
#         db_path: Path to ChromaDB
#         top_k: Number of chunks to retrieve (increased to 5 for better coverage)
#         score_threshold: Minimum similarity score (lowered to 0.5 to get more context)
#     """
#     # 1️⃣ Load embeddings and ChromaDB
#     embeddings = HuggingFaceEmbeddings(model_name="distiluse-base-multilingual-cased-v1")
#     vectordb = Chroma(persist_directory=db_path, embedding_function=embeddings)

#     # 2️⃣ Retrieve results with similarity scores
#     results = vectordb.similarity_search_with_score(query, k=top_k)

#     # 3️⃣ Filter based on score threshold and log what we found
#     filtered = []
#     print(f"\n🔍 Searching for: '{query}'")
#     for doc, score in results:
#         if score > score_threshold:
#             filtered.append(doc.page_content)
#             print(f"  ✅ Score {score:.3f}: {doc.page_content[:80]}...")
#         else:
#             print(f"  ❌ Score {score:.3f}: Below threshold")

#     # 4️⃣ If no chunks pass threshold, return empty to trigger "don't know" response
#     if not filtered:
#         print("  ⚠️  No relevant context found above threshold!")
#         return ""  # Empty context will make LLM say it doesn't know

#     # 5️⃣ Combine into one context block
#     combined_context = "\n\n---\n\n".join(filtered)
#     print(f"  📦 Returning {len(filtered)} chunks as context\n")

#     return combined_context
