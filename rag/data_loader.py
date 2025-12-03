import os
from PyPDF2 import PdfReader

def load_text_files(folder_path):
    """Load all .txt files from the folder"""
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            path = os.path.join(folder_path, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            documents.append({"source": filename, "content": text})
    return documents


def load_pdf_files(folder_path):
    """Load all .pdf files from the folder"""
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            path = os.path.join(folder_path, filename)
            pdf = PdfReader(path)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            documents.append({"source": filename, "content": text})
    return documents


def load_all_stories(folder_path):
    """Combine both PDF and TXT content"""
    docs = load_text_files(folder_path) + load_pdf_files(folder_path)
    print(f"✅ Loaded {len(docs)} stories/lessons from {folder_path}")
    return docs
