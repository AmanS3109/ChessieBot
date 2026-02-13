import streamlit as st
import tempfile
import asyncio
import base64
import requests
import json
import time

# -------------------------------
# Configuration
# -------------------------------
API_BASE_URL = "http://localhost:8080/api"

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="Chess Buddy 🧠♟️",
    page_icon="♟️",
    layout="centered"
)

st.title("🤖 Chess Buddy — Your Magical Chess Friend!")

# -------------------------------
# API Client Helpers
# -------------------------------
def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get("http://localhost:8080/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def api_chat(question, language="hinglish"):
    """Call Chat API."""
    try:
        response = requests.post(f"{API_BASE_URL}/chat", json={
            "question": question,
            "explain": True
        })
        if response.status_code == 200:
            return response.json()
        return {"answer": "Error", "explanation": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"answer": "Error", "explanation": f"Connection Error: {str(e)}"}

def api_process_video(url):
    """Call Video Process API."""
    try:
        response = requests.post(f"{API_BASE_URL}/video/process", json={"url": url})
        if response.status_code == 200:
            return response.json()
        return {"status": "error", "message": f"API Error: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def api_video_chat(video_id, question, language="hinglish"):
    """Call Video Chat API."""
    try:
        response = requests.post(f"{API_BASE_URL}/video/chat", json={
            "video_id": video_id,
            "question": question,
            "language": language
        })
        if response.status_code == 200:
            return response.json()
        return {"answer": "Error", "explanation": f"API Error: {response.text}"}
    except Exception as e:
        return {"answer": "Error", "explanation": str(e)}

def api_video_explain(video_id, topic, mode="full", language="hinglish"):
    """Call Video Explain API."""
    try:
        response = requests.post(f"{API_BASE_URL}/video/explain", json={
            "video_id": video_id,
            "topic": topic,
            "mode": mode,
            "language": language
        })
        if response.status_code == 200:
            return response.json()
        return {"explanation": f"API Error: {response.text}"}
    except Exception as e:
        return {"explanation": str(e)}

def api_get_tts_audio(text, language="auto"):
    """Get TTS Audio from API."""
    try:
        response = requests.post(f"{API_BASE_URL}/tts", json={
            "text": text,
            "language": language
        })
        if response.status_code == 200:
            return response.content
        return None
    except:
        return None

# -------------------------------
# UI Components
# -------------------------------
def autoplay_audio(audio_bytes):
    """Play audio bytes automatically."""
    if not audio_bytes: return
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)

# -------------------------------
# Session State
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "video_messages" not in st.session_state:
    st.session_state.video_messages = []
if "current_video_id" not in st.session_state:
    st.session_state.current_video_id = None
if "language" not in st.session_state:
    st.session_state.language = "hinglish"

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status Indicator
    api_online = check_api_health()
    if api_online:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Offline")
        st.caption("Run: `python -m uvicorn main:app --port 8000`")
    
    # Language Selector
    lang_map = {"English": "en", "Hindi": "hi", "Hinglish": "hinglish"}
    selected_lang = st.selectbox("Language / भाषा", list(lang_map.keys()), index=2)
    st.session_state.language = lang_map[selected_lang]
    
    st.divider()
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.session_state.video_messages = []
        st.rerun()

# -------------------------------
# TABS Interface
# -------------------------------
tab1, tab2 = st.tabs(["📖 Story Mode", "📺 Video Tutor"])

# ==========================================
# TAB 1: STORY MODE
# ==========================================
with tab1:
    st.markdown("### Ask me about Chess Stories! 🌟")
    
    # Display history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(f"**{msg['answer']}**")
                if msg.get("explanation"):
                    with st.expander("Explanation"):
                        st.markdown(msg["explanation"])
            else:
                st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask about the King, Queen, or Stories...", key="story_input")
    if user_input:
        if not api_online:
            st.error("⚠️ API is offline. Please start the server.")
        else:
            # User message
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Assistant response
            with st.chat_message("assistant"):
                with st.spinner("Asking Chess Buddy..."):
                    resp = api_chat(user_input, st.session_state.language)
                    
                    answer = resp.get("answer", "Error")
                    expl = resp.get("explanation", "")
                    
                    st.markdown(f"**{answer}**")
                    if expl:
                        with st.expander("Explanation"):
                            st.markdown(expl)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "answer": answer,
                        "explanation": expl
                    })
                    
                    # Audio
                    audio_bytes = api_get_tts_audio(answer)
                    autoplay_audio(audio_bytes)


# ==========================================
# TAB 2: VIDEO TUTOR
# ==========================================
with tab2:
    st.markdown("### 🎥 Watch & Learn")
    
    # Video Process Section
    col1, col2 = st.columns([3, 1])
    with col1:
        video_url = st.text_input("🔗 Paste YouTube URL:", placeholder="https://youtube.com/...")
    with col2:
        process_btn = st.button("🚀 Process", disabled=not api_online, use_container_width=True)
    
    if process_btn and video_url:
        with st.spinner("Downloading & Analyzing..."):
            result = api_process_video(video_url)
            if result.get("status") == "success":
                st.session_state.current_video_id = result.get("video_id")
                st.success(f"✅ Ready! Video ID: {result.get('video_id')}")
            else:
                st.error(f"❌ Error: {result.get('message')}")

    st.divider()

    # Chat Interface
    if st.session_state.current_video_id:
        st.info("Ask questions or click buttons for explanations!")
        
        # Helper Buttons for Explain API
        c1, c2, c3 = st.columns(3)
        if c1.button("🤔 What is this?"):
            with st.spinner("Thinking..."):
                res = api_video_explain(st.session_state.current_video_id, "current situation", "what", st.session_state.language)
                st.session_state.video_messages.append({"role": "assistant", "answer": "Explanation (What)", "explanation": res.get("explanation")})
        
        if c2.button("🧠 Why this move?"):
            with st.spinner("Thinking..."):
                res = api_video_explain(st.session_state.current_video_id, "latest move", "why", st.session_state.language)
                st.session_state.video_messages.append({"role": "assistant", "answer": "Explanation (Why)", "explanation": res.get("explanation")})
        
        if c3.button("📝 Key Concepts"):
            with st.spinner("Extracting..."):
                res = requests.get(f"{API_BASE_URL}/video/concepts/{st.session_state.current_video_id}").json()
                concepts = "\n".join([f"- **{c['name']}**: {c.get('description','')}" for c in res.get('concepts', [])])
                st.session_state.video_messages.append({"role": "assistant", "answer": "Key Concepts", "explanation": concepts})

        # History
        for msg in st.session_state.video_messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    st.markdown(f"**{msg['answer']}**")
                    if msg.get("explanation"):
                        st.markdown(f"_{msg['explanation']}_")
                else:
                    st.markdown(msg["content"])

        # Input
        vid_input = st.chat_input("Ask about the video...", key="video_input")
        if vid_input:
            if not api_online:
                st.error("⚠️ API is offline.")
            else:
                st.session_state.video_messages.append({"role": "user", "content": vid_input})
                with st.chat_message("user"):
                    st.markdown(vid_input)
                
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        resp = api_video_chat(st.session_state.current_video_id, vid_input, st.session_state.language)
                        
                        ans = resp.get("answer", "Error")
                        exp = resp.get("explanation", "")
                        
                        st.markdown(f"**{ans}**")
                        st.markdown(f"_{exp}_")
                        
                        st.session_state.video_messages.append({
                            "role": "assistant",
                            "answer": ans,
                            "explanation": exp
                        })
                        
                        audio_bytes = api_get_tts_audio(ans)
                        autoplay_audio(audio_bytes)
    else:
        st.markdown("Waiting for video...")

