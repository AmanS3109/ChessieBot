# models/embedding_model.py
from langchain_community.embeddings import HuggingFaceEmbeddings

def load_embedding_model():
    return HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
