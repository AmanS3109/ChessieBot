# tests/test_video_flow_mock.py - Enhanced Video Flow Tests

import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services import video_processor
from rag import video_generator
from services import video_explainer
from api.routes import video_api
from unittest.mock import MagicMock, patch


# Chess-related dummy transcript
DUMMY_TRANSCRIPT = """
In this position, white plays e4, controlling the center. Black responds with e5. 
Then white brings the knight to f3, attacking the pawn. Black defends with knight c6.
This is the standard open game. White now moves the bishop to b5, the Ruy Lopez.
The idea is to put pressure on the defender of the e5 pawn.
Center control is very important in chess. When you control the center, 
your pieces have more squares to move to.
The knight on f3 is well-placed because it attacks the center.
Always develop your pieces early in the game.
"""


async def test_process_endpoint():
    """Test the video process endpoint with mocked processor."""
    print("\n🔹 Testing /video/process endpoint")
    
    # Mock the process_video function
    with patch.object(video_api, 'process_video') as mock_process:
        mock_process.return_value = {
            "status": "success",
            "video_id": "test_video_123",
            "transcript": DUMMY_TRANSCRIPT,
            "title": "Chess Opening Tutorial",
            "cached": False
        }
        
        req = video_api.VideoProcessRequest(url="http://dummy.url/video")
        response = await video_api.process_video_endpoint(req)
        
        assert response.status == "success"
        assert response.video_id == "test_video_123"
        print(f"   ✅ Process endpoint: {response.message}")
        
        return response.video_id


async def test_chat_endpoint(video_id: str):
    """Test the video chat endpoint."""
    print("\n🔹 Testing /video/chat endpoint")
    
    # Ensure video is in store
    video_api.VIDEO_STORE[video_id] = {
        "transcript": DUMMY_TRANSCRIPT,
        "title": "Test Video"
    }
    
    # Test with different languages
    languages = ["en", "hi", "hinglish"]
    
    for lang in languages:
        if not os.getenv("GROQ_API_KEY"):
            # Mock the generator if no API key
            with patch.object(video_generator, 'generate_video_response') as mock_gen:
                mock_gen.return_value = {
                    "answer": f"Mock answer in {lang}",
                    "explanation": f"Mock explanation in {lang}",
                    "language": lang
                }
                
                req = video_api.VideoChatRequest(
                    video_id=video_id,
                    question="Why did white move the bishop?",
                    language=lang
                )
                response = await video_api.chat_video_endpoint(req)
        else:
            req = video_api.VideoChatRequest(
                video_id=video_id,
                question="Why did white move the bishop?",
                language=lang
            )
            response = await video_api.chat_video_endpoint(req)
        
        assert response.language == lang
        print(f"   ✅ Chat ({lang}): {response.answer[:50]}...")


async def test_explain_endpoint(video_id: str):
    """Test the video explain endpoint with different modes."""
    print("\n🔹 Testing /video/explain endpoint")
    
    modes = ["what", "why", "full"]
    
    for mode in modes:
        if not os.getenv("GROQ_API_KEY"):
            with patch.object(video_explainer, 'explain_video_concept') as mock_explain:
                mock_explain.return_value = {
                    "explanation": f"Mock {mode} explanation",
                    "key_points": ["Point 1", "Point 2"],
                    "language": "hinglish",
                    "mode": mode,
                    "status": "success"
                }
                
                req = video_api.VideoExplainRequest(
                    video_id=video_id,
                    topic="center control",
                    mode=mode,
                    language="hinglish"
                )
                response = await video_api.explain_video_endpoint(req)
        else:
            req = video_api.VideoExplainRequest(
                video_id=video_id,
                topic="center control",
                mode=mode,
                language="hinglish"
            )
            response = await video_api.explain_video_endpoint(req)
        
        assert response.mode == mode
        print(f"   ✅ Explain ({mode}): {response.explanation[:50]}...")


async def test_concepts_endpoint(video_id: str):
    """Test the concept extraction endpoint."""
    print("\n🔹 Testing /video/concepts endpoint")
    
    if not os.getenv("GROQ_API_KEY"):
        with patch.object(video_explainer, 'get_video_concepts') as mock_concepts:
            mock_concepts.return_value = [
                {"name": "Center Control", "description": "Controlling the center squares"},
                {"name": "Piece Development", "description": "Moving pieces out early"},
                {"name": "Ruy Lopez", "description": "A popular chess opening"}
            ]
            
            response = await video_api.get_concepts_endpoint(video_id, language="en")
    else:
        response = await video_api.get_concepts_endpoint(video_id, language="en")
    
    assert response.video_id == video_id
    assert response.count >= 0
    print(f"   ✅ Concepts: Found {response.count} concepts")
    
    for concept in response.concepts[:3]:
        print(f"      - {concept['name']}")


async def test_utility_endpoints(video_id: str):
    """Test utility endpoints."""
    print("\n🔹 Testing utility endpoints")
    
    # Test list videos
    list_response = await video_api.list_videos()
    assert "count" in list_response
    print(f"   ✅ List videos: {list_response['count']} videos")
    
    # Test get transcript
    transcript_response = await video_api.get_transcript(video_id)
    assert "transcript" in transcript_response
    print(f"   ✅ Get transcript: {len(transcript_response['transcript'])} chars")
    
    # Test cache stats
    cache_response = await video_api.cache_stats()
    assert "transcript_cache" in cache_response
    print(f"   ✅ Cache stats: {cache_response}")
    
    # Test languages
    lang_response = await video_api.get_supported_languages()
    assert "en" in lang_response["supported"]
    print(f"   ✅ Languages: {lang_response['supported']}")


async def run_all_tests():
    """Run the complete test suite."""
    print("\n" + "="*60)
    print("🚀 ChessieBot Video Flow Tests")
    print("="*60)
    
    has_api = bool(os.getenv("GROQ_API_KEY"))
    print(f"\n📡 GROQ_API_KEY: {'✅ Available' if has_api else '⚠️ Not set (using mocks)'}")
    
    # Run tests
    video_id = await test_process_endpoint()
    await test_chat_endpoint(video_id)
    await test_explain_endpoint(video_id)
    await test_concepts_endpoint(video_id)
    await test_utility_endpoints(video_id)
    
    # Cleanup
    if video_id in video_api.VIDEO_STORE:
        del video_api.VIDEO_STORE[video_id]
    
    print("\n" + "="*60)
    print("✅ All Video Flow Tests Passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
