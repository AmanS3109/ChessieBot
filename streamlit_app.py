# chess_buddy_app.py
import streamlit as st
from rag.generator import generate_llm_response

st.set_page_config(
    page_title="Chess Buddy 🧠♟️",
    page_icon="♟️",
    layout="centered"
)

# --- Title and Header ---
st.title("🤖 Chess Buddy — Your Magical Chess Friend!")
st.markdown("Ask me anything about chess, lessons, or your story! 🌟")

# --- Initialize session state for chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = {}

# --- Display chat history ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Display one-word answer in large font
            st.markdown(f"### 🎯 {message['answer']}")
            
            # Create unique key for each message's explain button
            explain_key = f"explain_{idx}"
            
            # Show explanation button
            if st.button("💡 Explain", key=explain_key):
                st.session_state.show_explanation[idx] = True
            
            # Show explanation if button was clicked
            if st.session_state.show_explanation.get(idx, False):
                st.markdown("---")
                st.markdown("**Explanation:**")
                st.markdown(message.get('explanation', 'No explanation available.'))
        else:
            st.markdown(message["content"])

# --- User input area ---
user_input = st.chat_input("Type your question here...")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # --- Generate AI response ---
    with st.chat_message("assistant"):
        with st.spinner("Thinking like a Grandmaster... 🤔"):
            response = generate_llm_response(user_input)
            
            # Display one-word answer in large font
            if isinstance(response, dict):
                answer = response.get('answer', 'Unknown')
                explanation = response.get('explanation', '')
                
                st.markdown(f"### 🎯 {answer}")
                
                # Create unique key for new message
                new_idx = len(st.session_state.messages)
                explain_key = f"explain_{new_idx}"
                
                # Show explanation button
                if st.button("💡 Explain", key=explain_key):
                    st.session_state.show_explanation[new_idx] = True
                
                # Show explanation if button was clicked
                if st.session_state.show_explanation.get(new_idx, False):
                    st.markdown("---")
                    st.markdown("**Explanation:**")
                    st.markdown(explanation)
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "answer": answer,
                    "explanation": explanation
                })
            else:
                # Fallback for old response format
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response, "answer": response, "explanation": ""})

