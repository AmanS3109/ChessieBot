#!/usr/bin/env python3
"""
Detailed test to see the full explanation output
"""
import os
from dotenv import load_dotenv
load_dotenv()

from rag.generator import generate_llm_response

print("Testing Full Explanation Output\n")
print("="*80)

query = "Why is the King important?"
print(f"\n📝 Query: {query}")
print("-" * 80)

try:
    # Get explanation mode response
    response = generate_llm_response(query, explain=True)
    
    print(f"\n💡 FULL EXPLANATION:")
    print(response.get('explanation', 'N/A'))
    print("\n" + "="*80)
    
    # Check if it mentions characters
    explanation = response.get('explanation', '')
    characters = ['Chintu', 'Minku', 'Board', 'King', 'chocolate']
    found = [char for char in characters if char.lower() in explanation.lower()]
    
    print(f"\n✅ Character/Story References Found: {', '.join(found) if found else 'NONE'}")
    
except Exception as e:
    print(f"❌ Error: {e}\n")
