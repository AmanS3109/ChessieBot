# # chess_buddy_app.py
# import streamlit as st
# from rag.generator import generate_llm_response

# st.set_page_config(
#     page_title="Chess Buddy 🧠♟️",
#     page_icon="♟️",
#     layout="centered"
# )

# # --- Title and Header ---
# st.title("🤖 Chess Buddy — Your Magical Chess Friend!")
# st.markdown("Ask me anything about chess, lessons, or your story! 🌟")

# # --- Initialize session state for chat history ---
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "show_explanation" not in st.session_state:
#     st.session_state.show_explanation = {}

# # --- Display chat history ---
# for idx, message in enumerate(st.session_state.messages):
#     with st.chat_message(message["role"]):
#         if message["role"] == "assistant":
#             # Display one-word answer in large font
#             st.markdown(f"### 🎯 {message['answer']}")
            
#             # Create unique key for each message's explain button
#             explain_key = f"explain_{idx}"
            
#             # Show explanation button
#             if st.button("💡 Explain", key=explain_key):
#                 st.session_state.show_explanation[idx] = True
            
#             # Show explanation if button was clicked
#             if st.session_state.show_explanation.get(idx, False):
#                 st.markdown("---")
#                 st.markdown("**Explanation:**")
#                 st.markdown(message.get('explanation', 'No explanation available.'))
#         else:
#             st.markdown(message["content"])

# # --- User input area ---
# user_input = st.chat_input("Type your question here...")

# if user_input:
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": user_input})
#     with st.chat_message("user"):
#         st.markdown(user_input)

#     # --- Generate AI response ---
#     with st.chat_message("assistant"):
#         with st.spinner("Thinking like a Grandmaster... 🤔"):
#             response = generate_llm_response(user_input)
            
#             # Display one-word answer in large font
#             if isinstance(response, dict):
#                 answer = response.get('answer', 'Unknown')
#                 explanation = response.get('explanation', '')
                
#                 st.markdown(f"### 🎯 {answer}")
                
#                 # Create unique key for new message
#                 new_idx = len(st.session_state.messages)
#                 explain_key = f"explain_{new_idx}"
                
#                 # Show explanation button
#                 if st.button("💡 Explain", key=explain_key):
#                     st.session_state.show_explanation[new_idx] = True
                
#                 # Show explanation if button was clicked
#                 if st.session_state.show_explanation.get(new_idx, False):
#                     st.markdown("---")
#                     st.markdown("**Explanation:**")
#                     st.markdown(explanation)
                
#                 # Add to chat history
#                 st.session_state.messages.append({
#                     "role": "assistant", 
#                     "answer": answer,
#                     "explanation": explanation
#                 })
#             else:
#                 # Fallback for old response format
#                 st.markdown(response)
#                 st.session_state.messages.append({"role": "assistant", "content": response, "answer": response, "explanation": ""})



# chess_buddy_app.py
# streamlit_app.py
# streamlit_app.py
# streamlit_app.py
import streamlit as st
import tempfile
import asyncio
import base64
import edge_tts
import speech_recognition as sr
from io import BytesIO

from rag.generator import generate_llm_response


# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Chess Buddy 🧠♟️",
    page_icon="♟️",
    layout="centered"
)

st.title("🤖 Chess Buddy — Your Magical Chess Friend!")
st.markdown("Ask me anything about chess, lessons, or your story! 🌟")


# -------------------------------
# Voice Configuration
# -------------------------------
HINDI_VOICE = "hi-IN-MadhurNeural"
ENGLISH_VOICE = "en-IN-NeerjaNeural"


# -------------------------------
# Session State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = {}

if "spoken_answers" not in st.session_state:
    st.session_state.spoken_answers = set()

if "spoken_explanations" not in st.session_state:
    st.session_state.spoken_explanations = set()


# -------------------------------
# Helpers
# -------------------------------
def is_mostly_english(text: str) -> bool:
    keywords = [
        "king", "queen", "pawn", "rook", "bishop", "knight",
        "game", "move", "step", "board", "check"
    ]
    text = text.lower()
    return any(k in text for k in keywords)


def listen_to_microphone():
    """
    Capture audio from microphone and convert to text using Google's speech recognition.
    Returns the transcribed text or None if recognition fails.
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now!")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=1)
            # Listen for audio
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
        st.info("🔄 Processing your speech...")
        
        # Try to recognize speech using Google Speech Recognition
        # First try Hindi, then English
        try:
            text = recognizer.recognize_google(audio, language="hi-IN")
            st.success(f"✅ You said (Hindi): {text}")
            return text
        except:
            # If Hindi fails, try English
            try:
                text = recognizer.recognize_google(audio, language="en-IN")
                st.success(f"✅ You said (English): {text}")
                return text
            except:
                st.error("❌ Could not understand audio. Please try again.")
                return None
                
    except sr.WaitTimeoutError:
        st.warning("⏱️ No speech detected. Please try again.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def normalize_for_tts(text: str) -> str:
    replacements = {
        "kise": "kisse",
        "kon": "kaun",
        "kehte": "kehtey",
        "kyun": "kyon",
        "raja": "raajaa",
        "bulate": "bulaate",
    }
    out = text.lower()
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


async def _tts_async(text: str, voice: str, path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)


def speak_autoplay(text: str):
    if not text:
        return

    text = normalize_for_tts(text)
    voice = ENGLISH_VOICE if is_mostly_english(text) else HINDI_VOICE

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()

    asyncio.run(_tts_async(text, voice, tmp.name))

    audio_bytes = open(tmp.name, "rb").read()
    audio_base64 = base64.b64encode(audio_bytes).decode()

    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}">
        </audio>
        """,
        unsafe_allow_html=True
    )


# -------------------------------
# Display Chat History
# -------------------------------
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):

        if message["role"] == "assistant":
            answer = message["answer"]
            explanation = message["explanation"]

            st.markdown(f"### 🎯 {answer}")

            # 🔊 Speak answer ONCE
            ans_key = f"answer_{idx}"
            if ans_key not in st.session_state.spoken_answers:
                speak_autoplay(answer)
                st.session_state.spoken_answers.add(ans_key)

            # 💡 Explain button → ONLY set state
            if st.button("💡 Explain", key=f"explain_{idx}"):
                st.session_state.show_explanation[idx] = True

            # 🔑 Speak explanation WHEN it becomes visible
            if st.session_state.show_explanation.get(idx, False):
                st.markdown("---")
                st.markdown("**Explanation:**")
                st.markdown(explanation)

                exp_key = f"exp_{idx}"
                if exp_key not in st.session_state.spoken_explanations:
                    speak_autoplay(explanation)
                    st.session_state.spoken_explanations.add(exp_key)

        else:
            st.markdown(message["content"])


# -------------------------------
# User Input
# -------------------------------
st.markdown("### 💬 Ask Your Question")

# Create two columns for input methods
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.text_input("Type your question here...", key="text_input", label_visibility="collapsed", placeholder="Type your question or use the microphone 🎤")

with col2:
    if st.button("🎤 Speak", use_container_width=True):
        voice_input = listen_to_microphone()
        if voice_input:
            user_input = voice_input
            # Store in session state to trigger processing
            st.session_state.pending_question = voice_input

# Check if there's a pending question from voice input
if "pending_question" in st.session_state:
    user_input = st.session_state.pending_question
    del st.session_state.pending_question

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking like a Grandmaster... 🤔"):
            response = generate_llm_response(user_input)

            answer = response.get("answer", "Unknown")
            explanation = response.get("explanation", "")

            st.markdown(f"### 🎯 {answer}")

            new_idx = len(st.session_state.messages)

            # 🔊 Speak answer ONCE
            ans_key = f"answer_{new_idx}"
            if ans_key not in st.session_state.spoken_answers:
                speak_autoplay(answer)
                st.session_state.spoken_answers.add(ans_key)

            if st.button("💡 Explain", key=f"explain_{new_idx}"):
                st.session_state.show_explanation[new_idx] = True

            if st.session_state.show_explanation.get(new_idx, False):
                st.markdown("---")
                st.markdown("**Explanation:**")
                st.markdown(explanation)

                exp_key = f"exp_{new_idx}"
                if exp_key not in st.session_state.spoken_explanations:
                    speak_autoplay(explanation)
                    st.session_state.spoken_explanations.add(exp_key)

            st.session_state.messages.append({
                "role": "assistant",
                "answer": answer,
                "explanation": explanation
            })
