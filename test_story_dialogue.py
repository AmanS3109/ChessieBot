#!/usr/bin/env python3
"""
Test the enhanced story dialogue-based explanations
"""
import os
from dotenv import load_dotenv
load_dotenv()

from rag.generator import generate_llm_response

print("Testing Story Dialogue-Based Explanations\n")
print("="*60)

test_queries = [
    "How does the King move?",
    "King kaise chalta hai?",
]

for query in test_queries:
    print(f"\n📝 Query: {query}")
    print("-" * 60)
    
    try:
        # Get explanation mode response
        response = generate_llm_response(query, explain=True)
        
        print(f"💡 EXPLANATION (Story Dialogue Style):")
        print(f"{response.get('explanation', 'N/A')}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")

print("="*60)
print("✅ Check if explanations use character voices and dialogue!")
