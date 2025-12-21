"""
Test script for Query Normalization
Tests the complete pipeline with Hindi/Hinglish queries
"""

import os
import sys

# Set GROQ_API_KEY from .env
from dotenv import load_dotenv
load_dotenv()

from rag.query_normalizer import normalize_query
from rag.utils import generate_response


def test_normalization_only():
    """Test just the normalization step"""
    print("=" * 60)
    print("TEST 1: Query Normalization Only")
    print("=" * 60)
    
    test_cases = [
        "पोर्न कैसे अटैक करते हैं",
        "किंग कैसे चलता है",
        "queen ki movement kya hai",
        "रूक कहाँ चल सकता है",
        "बिशप कैसे मूव करता है",
        "pawn kaise attack karta hai",  # Already clean
    ]
    
    for query in test_cases:
        normalized = normalize_query(query)
        print(f"\nInput:      {query}")
        print(f"Normalized: {normalized}")
    print()


def test_full_pipeline():
    """Test the complete RAG pipeline with normalization"""
    print("=" * 60)
    print("TEST 2: Full Pipeline (Normalization + RAG + Answer)")
    print("=" * 60)
    
    test_cases = [
        ("पोर्न कैसे अटैक करते हैं", False),
        ("किंग कैसे चलता है", False),
        ("queen ki movement kya hai", True),  # With explanation
    ]
    
    for query, explain in test_cases:
        print(f"\n{'─' * 60}")
        print(f"Query: {query}")
        print(f"Explain: {explain}")
        print()
        
        try:
            response = generate_response(query, explain=explain)
            
            print(f"✅ Original:   {response.get('original_query')}")
            print(f"🔄 Normalized: {response.get('normalized_query')}")
            print(f"🎯 Answer:     {response.get('answer')}")
            
            if explain and response.get('explanation'):
                print(f"\n💡 Explanation:")
                print(f"   {response.get('explanation')[:200]}...")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()


def test_cache_performance():
    """Test LRU cache performance"""
    print("=" * 60)
    print("TEST 3: Cache Performance")
    print("=" * 60)
    
    query = "पोर्न कैसे अटैक करते हैं"
    
    import time
    
    # Clear cache first
    normalize_query.cache_clear()
    
    # First call (cache miss) - multiple iterations for measurable time
    iterations = 5
    start = time.time()
    for _ in range(iterations):
        normalize_query.cache_clear()  # Force cache miss
        result1 = normalize_query(query)
    time1 = (time.time() - start) / iterations
    
    # Cached calls - many iterations
    start = time.time()
    for _ in range(iterations * 100):
        result2 = normalize_query(query)
    time2 = (time.time() - start) / (iterations * 100)
    
    print(f"\nQuery: {query}")
    print(f"Avg uncached call: {time1:.4f}s → {result1}")
    print(f"Avg cached call:   {time2:.6f}s → {result2}")
    
    if time2 > 0:
        print(f"Speedup: {time1/time2:.0f}x faster with caching 🚀")
    
    assert result1 == result2, "Cache returned different result!"
    print("✅ Cache working correctly!")
    print()


if __name__ == "__main__":
    print("\n🧪 Query Normalization Test Suite\n")
    
    try:
        test_normalization_only()
        test_full_pipeline()
        test_cache_performance()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
