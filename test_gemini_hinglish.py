#!/usr/bin/env python3
"""
Quick test script to verify Gemini API migration with Hinglish support
"""
import os
from dotenv import load_dotenv
load_dotenv()

# Check if API key is set
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    print("\n📝 To fix this:")
    print("   1. Get your API key from: https://aistudio.google.com/apikey")
    print("   2. Add to .env file: GOOGLE_API_KEY=your_key_here")
    exit(1)

print("✅ GOOGLE_API_KEY found in environment")
print("\nTesting Gemini API integration with Hinglish support...\n")

# Test import
try:
    from rag.generator import generate_llm_response
    print("✅ Successfully imported generate_llm_response")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test queries
test_queries = [
    "How does the King move?",
    "King kaise chalta hai?",
    "Who is Chessy?"
]

print("\n" + "="*60)
print("Running test queries...")
print("="*60)

for query in test_queries:
    print(f"\n📝 Query: {query}")
    try:
        response = generate_llm_response(query, explain=False)
        print(f"   🎯 Answer: {response.get('answer', 'N/A')}")
        print(f"   💡 Explanation (truncated): {response.get('explanation', 'N/A')[:100]}...")
        print("   ✅ Success!")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("Test complete! Check if responses are in Hinglish 🎉")
print("="*60)
