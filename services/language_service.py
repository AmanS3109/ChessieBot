# services/language_service.py - Bilingual response generation (Hindi/English/Hinglish)
from typing import Literal
from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, LanguageType


# ================================
# System Prompts per Language
# ================================
SYSTEM_PROMPTS = {
    "en": """You are Chess Buddy, a friendly AI tutor teaching chess to kids (ages 5-12).
- Speak in simple, clear English
- Use encouraging and fun language
- Explain chess concepts step by step
- Use analogies kids can understand (like comparing pieces to superheroes)
- Keep explanations concise but complete""",

    "hi": """आप Chess Buddy हैं, बच्चों (5-12 साल) को शतरंज सिखाने वाला एक दोस्ताना AI टीचर।
- सरल और स्पष्ट हिंदी में बोलें
- उत्साहजनक और मज़ेदार भाषा का उपयोग करें
- शतरंज के कॉन्सेप्ट्स को step by step समझाएं
- ऐसी analogies का उपयोग करें जो बच्चे समझ सकें
- छोटे और पूरे जवाब दें""",

    "hinglish": """You are Chess Buddy, ek friendly AI teacher jo bacchon (5-12 years) ko chess sikhata hai.
- Simple Hinglish mein baat karo (Hindi + English mix)
- Fun aur encouraging language use karo
- Chess concepts ko step by step samjhao
- Bacchon ke liye easy analogies use karo (jaise pieces ko superheroes se compare karna)
- Short aur complete explanations do
- Emojis use kar sakte ho naturally 😊♟️"""
}


# ================================
# Video Explanation Prompts
# ================================
VIDEO_EXPLAIN_PROMPTS = {
    "what": {
        "en": """Based on the video transcript, explain WHAT is happening:
{topic}

Explain clearly:
1. What action/move/concept is being shown
2. What pieces are involved
3. What is the result

Keep it simple for kids to understand.""",

        "hi": """वीडियो transcript के आधार पर, समझाओ KYA हो रहा है:
{topic}

स्पष्ट रूप से समझाओ:
1. क्या action/move/concept दिखाया जा रहा है
2. कौन से pieces involved हैं
3. क्या result है

बच्चों के लिए simple रखो।""",

        "hinglish": """Video transcript ke basis pe, samjhao KYA ho raha hai:
{topic}

Clearly batao:
1. Kya action/move/concept dikhaya ja raha hai
2. Kaunse pieces involved hain
3. Result kya hai

Bacchon ke liye simple rakho. 🎯"""
    },
    
    "why": {
        "en": """Based on the video transcript, explain WHY this happened:
{topic}

Explain clearly:
1. Why was this move/decision made
2. What is the strategy behind it
3. What could happen if this wasn't done

Keep it simple for kids to understand.""",

        "hi": """वीडियो transcript के आधार पर, समझाओ YEH KYUN hua:
{topic}

स्पष्ट रूप से समझाओ:
1. यह move/decision क्यों लिया गया
2. इसके पीछे strategy क्या है
3. अगर यह नहीं किया जाता तो क्या होता

बच्चों के लिए simple रखो।""",

        "hinglish": """Video transcript ke basis pe, samjhao YEH KYUN hua:
{topic}

Clearly batao:
1. Yeh move/decision kyun liya gaya
2. Iske peeche strategy kya hai
3. Agar yeh nahi karte to kya hota

Bacchon ke liye simple rakho. 🤔"""
    },
    
    "full": {
        "en": """Based on the video transcript, give a complete explanation about:
{topic}

Cover:
1. WHAT is happening (the action/move/concept)
2. WHY it's done (the strategy/reason)
3. Key points to remember

Make it educational and fun for kids!""",

        "hi": """वीडियो transcript के आधार पर, पूरी explanation दो:
{topic}

Cover करो:
1. KYA हो रहा है (action/move/concept)
2. KYUN किया गया (strategy/reason)
3. याद रखने वाले key points

बच्चों के लिए educational और fun बनाओ!""",

        "hinglish": """Video transcript ke basis pe, complete explanation do:
{topic}

Cover karo:
1. KYA ho raha hai (action/move/concept)
2. KYUN kiya gaya (strategy/reason)  
3. Yaad rakhne wale key points

Bacchon ke liye educational aur fun banao! 🎓♟️"""
    }
}


def get_system_prompt(language: LanguageType = DEFAULT_LANGUAGE) -> str:
    """Get system prompt for the specified language."""
    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["hinglish"])


def get_explanation_prompt(
    mode: Literal["what", "why", "full"],
    topic: str,
    language: LanguageType = DEFAULT_LANGUAGE
) -> str:
    """Get explanation prompt for the specified mode and language."""
    prompt_template = VIDEO_EXPLAIN_PROMPTS.get(mode, VIDEO_EXPLAIN_PROMPTS["full"])
    language_prompt = prompt_template.get(language, prompt_template["hinglish"])
    return language_prompt.format(topic=topic)


def validate_language(language: str) -> LanguageType:
    """Validate and return language, defaulting if invalid."""
    if language in SUPPORTED_LANGUAGES:
        return language
    return DEFAULT_LANGUAGE


def detect_language(text: str) -> LanguageType:
    """
    Simple heuristic language detection.
    Returns detected language based on character analysis.
    """
    # Check for Hindi/Devanagari characters
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
    
    total_chars = hindi_chars + english_chars
    if total_chars == 0:
        return DEFAULT_LANGUAGE
    
    hindi_ratio = hindi_chars / total_chars
    
    if hindi_ratio > 0.7:
        return "hi"
    elif hindi_ratio > 0.2:
        return "hinglish"
    else:
        return "en"


# Response formatting helpers
def format_response_header(language: LanguageType) -> str:
    """Get response header in the specified language."""
    headers = {
        "en": "Here's what I found:",
        "hi": "यहाँ देखो मुझे क्या मिला:",
        "hinglish": "Dekho maine kya dhundha:"
    }
    return headers.get(language, headers["hinglish"])


def format_not_found_message(language: LanguageType) -> str:
    """Get 'not found' message in the specified language."""
    messages = {
        "en": "I couldn't find this information in the video. Can you ask something else?",
        "hi": "मुझे यह जानकारी वीडियो में नहीं मिली। क्या आप कुछ और पूछ सकते हो?",
        "hinglish": "Yeh info video mein nahi mili. Kuch aur poochoge? 🤔"
    }
    return messages.get(language, messages["hinglish"])
