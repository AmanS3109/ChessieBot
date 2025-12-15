from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from rag.data_loader import load_all_stories

DATA_PATH = "data/hindi_stories"
DB_PATH = "data/processed/chromadb"

def build_vector_store():
    # 1️⃣ Load story files
    docs = load_all_stories(DATA_PATH)

    # 2️⃣ Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len,
    )
    texts = []
    metadatas = []
    for doc in docs:
        for chunk in splitter.split_text(doc["content"]):
            texts.append(chunk)
            metadatas.append({"source": doc["source"]})

    # 3️⃣ Create embeddings
    print("🔹 Creating embeddings using all-MiniLM-L6-v2 ...")
    embedder = HuggingFaceEmbeddings(model_name="distiluse-base-multilingual-cased-v1")

    # 4️⃣ Store in ChromaDB
    print("🔹 Storing in ChromaDB ...")
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embedder,
        metadatas=metadatas,
        persist_directory=DB_PATH
    )

    vector_store.persist()
    print("✅ Vector store created and saved at:", DB_PATH)

if __name__ == "__main__":
    build_vector_store()
