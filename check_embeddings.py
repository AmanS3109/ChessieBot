#!/usr/bin/env python3
"""
Check what stories have been embedded in ChromaDB.
Shows: total chunks, source files, and sample content.
"""

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

DB_PATH = "data/processed/chromadb"
STORIES_PATH = "data/stories"

print("🔍 Checking ChromaDB Embeddings Status\n")
print("="*80)

# Check if DB exists
if not os.path.exists(DB_PATH):
    print(f"❌ ChromaDB not found at: {DB_PATH}")
    print("   Run: python -m rag.create_embeddings")
    exit(1)

# Load ChromaDB
print(f"✅ ChromaDB found at: {DB_PATH}\n")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)

# Get all documents
try:
    collection = vectordb._collection
    all_docs = collection.get()
    
    total_chunks = len(all_docs['ids'])
    print(f"📦 Total chunks in database: {total_chunks}\n")
    
    # Group by source
    if 'metadatas' in all_docs and all_docs['metadatas']:
        sources = {}
        for metadata in all_docs['metadatas']:
            if metadata and 'source' in metadata:
                source = metadata['source']
                sources[source] = sources.get(source, 0) + 1
        
        print("📚 Chunks per story file:")
        print("-" * 40)
        for source, count in sorted(sources.items()):
            print(f"  {source}: {count} chunks")
        
        print("\n" + "="*80)
        
        # Check what files exist but aren't in DB
        story_files = set()
        for file in os.listdir(STORIES_PATH):
            if file.endswith(('.txt', '.pdf')):
                story_files.add(file)
        
        embedded_files = set(sources.keys())
        missing_files = story_files - embedded_files
        
        if missing_files:
            print("\n⚠️  Files NOT embedded:")
            for file in sorted(missing_files):
                print(f"  ❌ {file}")
        else:
            print("\n✅ All story files are embedded!")
        
        # Show sample chunk
        if all_docs['documents'] and len(all_docs['documents']) > 0:
            print("\n" + "="*80)
            print("📄 Sample chunk from database:")
            print("-" * 40)
            sample = all_docs['documents'][0]
            print(sample[:300] + "..." if len(sample) > 300 else sample)
        
    else:
        print("⚠️  No metadata found in chunks (this is unusual)")
        
except Exception as e:
    print(f"❌ Error reading ChromaDB: {e}")
    print("\n💡 You may need to rebuild the database:")
    print("   python -m rag.create_embeddings")

print("\n" + "="*80)
print("\n✨ To rebuild embeddings: python -m rag.create_embeddings\n")
