#!/usr/bin/env python3
"""
Demo script showing one-word answers with explanations.
"""

from rag.generator import generate_llm_response

print("=" * 80)
print("🎯 ONE-WORD ANSWER MODE DEMO")
print("=" * 80)

test_questions = [
    "Who is the most important in Chess Land?",
    "Who protects the king?",
    "How does the pawn move?",
    "What is like mom in chess?",
]

for question in test_questions:
    print(f"\n❓ Question: {question}")
    print("-" * 80)
    
    result = generate_llm_response(question)
    
    if isinstance(result, dict):
        print(f"🎯 ONE-WORD ANSWER: {result['answer']}")
        print(f"\n💡 EXPLANATION (shown when user clicks 'Explain' button):")
        print(f"{result['explanation']}")
    else:
        print(f"Response: {result}")
    
    print("=" * 80)

print("\n✅ Demo complete! Run 'streamlit run streamlit_app.py' to see it in action.\n")
