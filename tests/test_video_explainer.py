# tests/test_video_explainer.py - Tests for Video Explainer Service
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.video_explainer import VideoExplainer, explain_video_concept, get_video_concepts
from services.language_service import validate_language, detect_language, get_system_prompt


# Sample transcript for testing
SAMPLE_TRANSCRIPT = """
In this position, white plays e4, controlling the center of the board.
This is one of the most popular opening moves in chess.
Black responds with e5, also fighting for the center.
Then white brings the knight to f3, attacking the e5 pawn.
Black defends with knight c6, protecting the pawn.
This is called the Italian Game setup.
White now moves the bishop to c4, targeting the f7 square.
The f7 square is weak because it's only protected by the king.
This is why we develop pieces towards the center.
Controlling the center gives you more space and better piece activity.
"""


def test_validate_language():
    """Test language validation."""
    print("🧪 Testing language validation...")
    
    assert validate_language("en") == "en"
    assert validate_language("hi") == "hi"
    assert validate_language("hinglish") == "hinglish"
    assert validate_language("invalid") == "hinglish"  # Default
    
    print("   ✅ Language validation passed")


def test_detect_language():
    """Test language detection."""
    print("🧪 Testing language detection...")
    
    # English text
    result = detect_language("What is the best opening move?")
    assert result == "en", f"Expected 'en', got '{result}'"
    
    # Hindi text (mostly Devanagari)
    result = detect_language("शतरंज कैसे खेलते हैं?")
    assert result == "hi", f"Expected 'hi', got '{result}'"
    
    # Hinglish text (mix of Hindi script and English)
    # Note: Romanized Hindi (like "kaise khelte hain") looks like English to simple detection
    # So we test with actual mixed script
    result = detect_language("यह move बहुत important है chess में")
    assert result == "hinglish", f"Expected 'hinglish', got '{result}'"
    
    print("   ✅ Language detection passed")


def test_get_system_prompt():
    """Test system prompt retrieval."""
    print("🧪 Testing system prompts...")
    
    en_prompt = get_system_prompt("en")
    assert "Chess Buddy" in en_prompt
    assert "English" in en_prompt
    
    hi_prompt = get_system_prompt("hi")
    assert "Chess Buddy" in hi_prompt
    
    hinglish_prompt = get_system_prompt("hinglish")
    assert "Chess Buddy" in hinglish_prompt
    assert "Hinglish" in hinglish_prompt
    
    print("   ✅ System prompts passed")


def test_video_explainer_init():
    """Test VideoExplainer initialization."""
    print("🧪 Testing VideoExplainer initialization...")
    
    explainer = VideoExplainer(language="en")
    assert explainer.language == "en"
    
    explainer = VideoExplainer(language="invalid")
    assert explainer.language == "hinglish"  # Should default
    
    print("   ✅ VideoExplainer init passed")


def test_explain_what(skip_api=True):
    """Test 'what' explanation mode."""
    print("🧪 Testing 'what' explanation...")
    
    if skip_api and not os.getenv("GROQ_API_KEY"):
        print("   ⏭️  Skipped (no GROQ_API_KEY)")
        return
    
    result = explain_video_concept(
        transcript=SAMPLE_TRANSCRIPT,
        topic="e4 opening",
        mode="what",
        language="en"
    )
    
    assert "explanation" in result
    assert result["mode"] == "what"
    assert result["language"] == "en"
    
    print(f"   Result: {result['explanation'][:100]}...")
    print("   ✅ 'what' explanation passed")


def test_explain_why(skip_api=True):
    """Test 'why' explanation mode."""
    print("🧪 Testing 'why' explanation...")
    
    if skip_api and not os.getenv("GROQ_API_KEY"):
        print("   ⏭️  Skipped (no GROQ_API_KEY)")
        return
    
    result = explain_video_concept(
        transcript=SAMPLE_TRANSCRIPT,
        topic="why is f7 weak",
        mode="why",
        language="hinglish"
    )
    
    assert "explanation" in result
    assert result["mode"] == "why"
    
    print(f"   Result: {result['explanation'][:100]}...")
    print("   ✅ 'why' explanation passed")


def test_concept_extraction(skip_api=True):
    """Test concept extraction."""
    print("🧪 Testing concept extraction...")
    
    if skip_api and not os.getenv("GROQ_API_KEY"):
        print("   ⏭️  Skipped (no GROQ_API_KEY)")
        return
    
    concepts = get_video_concepts(SAMPLE_TRANSCRIPT, language="en")
    
    assert isinstance(concepts, list)
    
    if concepts:
        print(f"   Found {len(concepts)} concepts:")
        for c in concepts[:3]:
            print(f"      - {c.get('name')}: {c.get('description', '')[:50]}")
    
    print("   ✅ Concept extraction passed")


def test_bilingual_responses(skip_api=True):
    """Test responses in all languages."""
    print("🧪 Testing bilingual responses...")
    
    if skip_api and not os.getenv("GROQ_API_KEY"):
        print("   ⏭️  Skipped (no GROQ_API_KEY)")
        return
    
    languages = ["en", "hi", "hinglish"]
    
    for lang in languages:
        result = explain_video_concept(
            transcript=SAMPLE_TRANSCRIPT,
            topic="center control",
            mode="full",
            language=lang
        )
        
        assert result["language"] == lang
        assert len(result["explanation"]) > 0
        print(f"   ✅ {lang}: {result['explanation'][:50]}...")
    
    print("   ✅ Bilingual responses passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 Running Video Explainer Tests")
    print("="*60 + "\n")
    
    # Tests that don't need API
    test_validate_language()
    test_detect_language()
    test_get_system_prompt()
    test_video_explainer_init()
    
    # Tests that need API (will skip if no key)
    has_api = bool(os.getenv("GROQ_API_KEY"))
    print(f"\n📡 API Tests (GROQ_API_KEY: {'✅ Available' if has_api else '❌ Not set'})\n")
    
    test_explain_what(skip_api=not has_api)
    test_explain_why(skip_api=not has_api)
    test_concept_extraction(skip_api=not has_api)
    test_bilingual_responses(skip_api=not has_api)
    
    print("\n" + "="*60)
    print("✅ All Tests Completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
