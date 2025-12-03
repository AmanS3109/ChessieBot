# test_generator.py
from rag.generator import generate_llm_response

if __name__ == "__main__":
    question = "Who everyone protects?"
    result = generate_llm_response(question)
    
    if isinstance(result, dict):
        print("🎯 ONE-WORD ANSWER:", result.get('answer'))
        print("\n💡 EXPLANATION:")
        print(result.get('explanation'))
    else:
        print("🤖 Chess Buddy says:\n", result)
