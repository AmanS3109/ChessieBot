# services/video_explainer.py - AI Video Concept Explanation Service
import os
import re
from typing import Literal, List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

from config import (
    GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_TOKENS, 
    GROQ_TEMPERATURE, DEFAULT_LANGUAGE, LanguageType
)
from services.language_service import (
    get_system_prompt, get_explanation_prompt, 
    validate_language, format_not_found_message
)
from services.cache_service import cached_response

load_dotenv()

# Initialize Groq client
client = None
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    print("⚠️ Warning: GROQ_API_KEY not found - Video explainer will not work")


class VideoExplainer:
    """
    AI-powered video concept explainer.
    Analyzes video transcripts and provides explanations in multiple languages.
    """
    
    def __init__(self, language: LanguageType = DEFAULT_LANGUAGE):
        self.language = validate_language(language)
        self.client = client
        self.model = GROQ_MODEL
    
    def explain_what(self, transcript: str, topic: str) -> Dict[str, str]:
        """
        Explain WHAT is happening in the video regarding a topic.
        
        Args:
            transcript: Video transcript text
            topic: Topic to explain (e.g., "e4 opening", "castling")
            
        Returns:
            Dict with 'explanation' and 'key_points'
        """
        return self._generate_explanation(transcript, topic, "what")
    
    def explain_why(self, transcript: str, topic: str) -> Dict[str, str]:
        """
        Explain WHY something happened in the video.
        
        Args:
            transcript: Video transcript text
            topic: Topic to explain (e.g., "why bishop moved to b5")
            
        Returns:
            Dict with 'explanation' and 'key_points'
        """
        return self._generate_explanation(transcript, topic, "why")
    
    def explain_full(self, transcript: str, topic: str) -> Dict[str, str]:
        """
        Give complete (what + why) explanation about a topic.
        
        Args:
            transcript: Video transcript text
            topic: Topic to explain
            
        Returns:
            Dict with 'explanation' and 'key_points'
        """
        return self._generate_explanation(transcript, topic, "full")
    
    def extract_key_concepts(self, transcript: str) -> List[Dict[str, str]]:
        """
        Extract key chess concepts from the video transcript.
        
        Args:
            transcript: Video transcript text
            
        Returns:
            List of concepts with name and brief description
        """
        if not self.client:
            return []
        
        # Truncate long transcripts
        truncated = self._truncate_transcript(transcript)
        
        prompt = f"""Analyze this chess video transcript and extract the KEY CONCEPTS taught.

TRANSCRIPT:
{truncated}

INSTRUCTIONS:
1. Identify 3-7 main chess concepts discussed
2. For each concept give:
   - Name (e.g., "Castling", "Pin", "Fork")
   - Brief description (1 sentence)
3. Focus on concepts actually explained in the video

OUTPUT FORMAT (one per line):
CONCEPT: <name> | <brief description>

Extract the concepts:"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract chess concepts from video transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            response_text = completion.choices[0].message.content.strip()
            return self._parse_concepts(response_text)
            
        except Exception as e:
            print(f"❌ Concept extraction error: {e}")
            return []
    
    def _generate_explanation(
        self, 
        transcript: str, 
        topic: str, 
        mode: Literal["what", "why", "full"]
    ) -> Dict[str, str]:
        """Internal method to generate explanations."""
        if not self.client:
            return {
                "explanation": "AI service is not configured.",
                "key_points": [],
                "language": self.language,
                "mode": mode,
                "status": "error"
            }
        
        # Truncate transcript
        truncated = self._truncate_transcript(transcript)
        
        # Get language-specific prompts
        system_prompt = get_system_prompt(self.language)
        user_prompt = get_explanation_prompt(mode, topic, self.language)
        
        full_prompt = f"""VIDEO TRANSCRIPT:
{truncated}

USER QUESTION:
{user_prompt}

IMPORTANT:
- Answer ONLY based on what's in the transcript
- If the topic is not covered, say so politely
- Include 2-3 key points to remember
- End with encouraging words for the child

FORMAT:
EXPLANATION: <your explanation>
KEY POINTS:
- Point 1
- Point 2
- Point 3
"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS
            )
            
            response_text = completion.choices[0].message.content.strip()
            return self._parse_explanation(response_text, mode)
            
        except Exception as e:
            print(f"❌ Explanation generation error: {e}")
            return {
                "explanation": format_not_found_message(self.language),
                "key_points": [],
                "language": self.language,
                "mode": mode,
                "status": "error"
            }
    
    def _truncate_transcript(self, transcript: str, max_chars: int = 15000) -> str:
        """Truncate transcript to fit context window."""
        if len(transcript) <= max_chars:
            return transcript
        return transcript[:max_chars] + "..."
    
    def _parse_explanation(self, response: str, mode: str) -> Dict[str, str]:
        """Parse LLM response into structured format."""
        explanation = response
        key_points = []
        
        # Try to extract structured parts
        lines = response.split('\n')
        explanation_lines = []
        in_key_points = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("EXPLANATION:"):
                explanation_lines.append(line.replace("EXPLANATION:", "").strip())
            elif line.upper().startswith("KEY POINTS:"):
                in_key_points = True
            elif in_key_points and line.startswith("-"):
                key_points.append(line.lstrip("- ").strip())
            elif not in_key_points and explanation_lines:
                explanation_lines.append(line)
        
        if explanation_lines:
            explanation = " ".join(explanation_lines).strip()
        
        return {
            "explanation": explanation,
            "key_points": key_points if key_points else self._extract_bullet_points(response),
            "language": self.language,
            "mode": mode,
            "status": "success"
        }
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract any bullet points from text."""
        points = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                cleaned = re.sub(r'^[-•*\d.]+\s*', '', line)
                if cleaned:
                    points.append(cleaned)
        return points[:5]  # Max 5 points
    
    def _parse_concepts(self, response: str) -> List[Dict[str, str]]:
        """Parse concept extraction response."""
        concepts = []
        for line in response.split('\n'):
            if line.upper().startswith("CONCEPT:"):
                content = line.replace("CONCEPT:", "").strip()
                if "|" in content:
                    parts = content.split("|", 1)
                    concepts.append({
                        "name": parts[0].strip(),
                        "description": parts[1].strip() if len(parts) > 1 else ""
                    })
                elif content:
                    concepts.append({
                        "name": content,
                        "description": ""
                    })
        return concepts


# Convenience functions for direct use
def explain_video_concept(
    transcript: str,
    topic: str,
    mode: Literal["what", "why", "full"] = "full",
    language: LanguageType = DEFAULT_LANGUAGE
) -> Dict[str, str]:
    """
    Main function to explain a video concept.
    
    Args:
        transcript: Video transcript
        topic: Topic to explain
        mode: "what", "why", or "full"
        language: "en", "hi", or "hinglish"
        
    Returns:
        Explanation dict with 'explanation', 'key_points', 'language', 'mode'
    """
    explainer = VideoExplainer(language=language)
    
    if mode == "what":
        return explainer.explain_what(transcript, topic)
    elif mode == "why":
        return explainer.explain_why(transcript, topic)
    else:
        return explainer.explain_full(transcript, topic)


def get_video_concepts(transcript: str, language: LanguageType = DEFAULT_LANGUAGE) -> List[Dict[str, str]]:
    """Extract key concepts from a video transcript."""
    explainer = VideoExplainer(language=language)
    return explainer.extract_key_concepts(transcript)
