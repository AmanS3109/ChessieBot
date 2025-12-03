# test_strict_context.py
"""
Test script to verify LLM answers ONLY from retrieved context.
Run this to see:
1. Which chunks are retrieved
2. Their similarity scores
3. Whether the answer stays within context
"""

from rag.generator import generate_llm_response

def test_question(question):
    print("\n" + "="*80)
    print(f"❓ QUESTION: {question}")
    print("="*80)
    
    answer = generate_llm_response(question)
    
    print("\n💬 ANSWER:")
    print(answer)
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print("\n🧪 Testing Strict Context-Only Responses\n")
    
    # Test 1: Question that SHOULD be in your stories
    test_question("Who protects the king?")
    
    # Test 2: Question that MIGHT be in your stories
    test_question("How does a pawn move?")
    
    # Test 3: Question that's UNLIKELY to be in your stories
    test_question("What is the Sicilian Defense?")
    
    # Test 4: Question completely outside chess stories
    test_question("What's the weather today?")
    
    print("\n✅ Test complete! Check if answers stayed within context.")
    print("⚠️  If any answer made up information, adjust temperature or prompt further.\n")
