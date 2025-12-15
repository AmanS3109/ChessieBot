# # rag/generator.py
# import os
# import google.generativeai as genai
# from rag.retriever import get_relevant_stories
# from dotenv import load_dotenv
# load_dotenv()  # ✅ This loads environment variables from .env

# # Configure Gemini API
# genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# def generate_llm_response(user_query: str, explain=False):
#     """
#     Generate kid-friendly response using Gemini API + retrieved context.
    
#     Args:
#         user_query: The child's question
#         explain: If True, returns full explanation. If False, returns one-word answer.
    
#     Returns:
#         dict with 'answer' and 'explanation' keys
#     """
    
#     # 1️⃣ Retrieve top 3 relevant story chunks
#     relevant_chunks = get_relevant_stories(user_query)
    
#     # 🛑 If no relevant context found, return honest "don't know" response
#     if not relevant_chunks or relevant_chunks.strip() == "":
#         return {
#             "answer": "not available",
#             "explanation": "you will learn about it in future chapters!"
#         }
    
#     context = "\n\n".join(relevant_chunks) if isinstance(relevant_chunks, list) else relevant_chunks

#     # 2️⃣ Construct prompt with STRICT context-only instructions
#     if explain:
#         # Full explanation mode with detailed story narrative
#         # Make the explanation slightly longer and strictly grounded in story context.
#         # Ask for 3-6 sentences, start with Hinglish cue 'Yaad hai jab...', and quote exact dialogue when present.
#         prompt = f"""
# You are Chess Buddy, retelling a real moment from a story to a child.

# STRICT RULES (NO EXCEPTIONS):
# 1. You MUST quote exact sentences from the Story Context using quotation marks
# 2. You MUST mention who said the line (Chessy, Minku, King, etc.)
# 3. You MUST explain the answer ONLY using quoted story lines
# 4. You MUST NOT invent new dialogue or events
# 5. Speak in warm Hinglish like a real person explaining a story

# Story Context:
# {context}

# Child's Question:
# {user_query}

# Now explain by quoting the exact lines from the story that give the answer.
# Start with: "Yaad hai jab..."
# """

#     else:
#         # One-word answer mode (can be in Hinglish)
#         prompt = f"""
# You are Chess Buddy, a friendly chess teacher for kids aged 5-10 years.

# CRITICAL INSTRUCTION: Answer with ONLY ONE WORD or a very short phrase (max 2-3 words). Can be in Hinglish.

# Story Context:
# {context}

# Child's Question: {user_query}

# Instructions:
# - Read the Story Context carefully
# - Extract the main answer (like: "King", "Ek step", "Knight", "Pawn", "Aage", "Diagonal", etc.)
# - Answer with JUST that one word or short phrase (Hinglish is fine)
# - DO NOT add explanations or extra words
# - If you cannot find the answer in the context, say only: "Unknown"

# ONE-WORD ANSWER:
# """

#     # 3️⃣ Generate response via Gemini API
#     try:
#         # Initialize Gemini model with system instruction
#         model = genai.GenerativeModel(
#             model_name='gemini-2.5-flash',
#             generation_config={
#                 'temperature': 0.2 if not explain else 0.4,  # Lower temp for better story adherence
#                 'max_output_tokens': 100 if not explain else 600,  # More tokens for detailed story narratives
#                 'top_p': 0.95,
#                 'top_k': 40
#             },
#             system_instruction="You are a storyteller retelling the Chessland adventures to a child! Give DETAILED, RICH explanations by retelling what happened in the story scenes. Always mention character names (Chintu, Minku, Board, King, Queen, etc.), quote their actual dialogue, and include story analogies like 'chocolate is our King'. Paint vivid story scenes with dialogue and reactions. Respond ONLY using the story context provided - don't add anything not in the story. Use conversational Hinglish with emojis naturally."
#         )
        
#         # Generate response
#         response = model.generate_content(prompt)
        
#         # Check if response is valid
#         if not response.candidates or not response.candidates[0].content.parts:
#             return {
#                 "answer": "not available",
#                 "explanation": "you will learn about it in future chapters!"
#             }
        
#         response_text = response.text.strip()

#         # If in one-word mode, verify evidence in retrieved context before returning
#         if not explain:
#             one_word_answer = response_text

#             # Build list of chunks from the retrieved context so we can check for evidence.
#             if isinstance(relevant_chunks, list):
#                 chunks_list = relevant_chunks
#             else:
#                 # retriever joins chunks with a separator; split back into chunks
#                 chunks_list = [c.strip() for c in relevant_chunks.split("\n\n---\n\n") if c.strip()]

#             # Simple evidence check: ensure the one-word answer appears (word-boundary) in at least one chunk
#             import re
#             answer_token = one_word_answer.strip().lower()
#             evidence_found = False
#             if answer_token:
#                 for chunk in chunks_list:
#                     if re.search(r"\b" + re.escape(answer_token) + r"\b", chunk.lower()):
#                         evidence_found = True
#                         break

#             # If no direct evidence, don't return a possibly hallucinated answer
#             if not evidence_found:
#                 return {
#                     "answer": "Unknown",
#                     "explanation": "I don't have that information in the chess stories I know. Can you ask me about something from the chess tales? 📚♟️"
#                 }

#             # Evidence exists — generate explanation (kept strict)
#             explanation = generate_llm_response(user_query, explain=True)

#             return {
#                 "answer": one_word_answer,
#                 "explanation": explanation["explanation"] if isinstance(explanation, dict) else explanation
#             }

#         else:
#             # In explanation mode, ensure the explanation is faithful by returning as-is (it's generated from same context)
#             return {
#                 "answer": response_text,
#                 "explanation": response_text
#             }

#     except Exception as e:
#         print("Error:", e)
#         return {
#             "answer": "Error",
#             "explanation": "Oops! Chess Buddy is thinking too hard right now. Try again!"
#         }
# rag/generator.py
# import os
# import re
# import google.generativeai as genai
# from dotenv import load_dotenv
# from rag.retriever import get_relevant_stories

# load_dotenv()  # Load environment variables


# # -------------------------------
# # Gemini Configuration
# # -------------------------------
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise RuntimeError("❌ GOOGLE_API_KEY not found in environment or .env file")

# genai.configure(api_key=GOOGLE_API_KEY)

# GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# # -------------------------------
# # Main Generator Function
# # -------------------------------
# def generate_llm_response(user_query: str, explain: bool = False):
#     """
#     Generate kid-friendly response using Gemini API + retrieved story context.

#     Args:
#         user_query (str): Child's question
#         explain (bool): False → short answer, True → story-based explanation

#     Returns:
#         dict: { "answer": str, "explanation": str }
#     """

#     # -------------------------------
#     # Normalize common kid-style queries
#     # -------------------------------
#     normalized_query = user_query.lower()
#     # normalized_query = normalized_query.replace("k ", "king ")
#     # normalized_query = normalized_query.replace("k ka", "king ka")
#     # normalized_query = normalized_query.replace("k kise", "king kise")

#     # -------------------------------
#     # 1️⃣ Retrieve relevant story chunks
#     # -------------------------------
#     relevant_chunks = get_relevant_stories(normalized_query)

#     # If nothing relevant found
#     if not relevant_chunks or len(relevant_chunks) == 0:
#         return {
#             "answer": "not available",
#             "explanation": "Iska jawab abhi story mein nahi aaya hai 😊"
#         }

#     # Combine chunks into a single context string
#     context = "\n\n---\n\n".join(relevant_chunks)

#     # -------------------------------
#     # 2️⃣ Build Prompt
#     # -------------------------------
#     if explain:
#         # Explanation mode (story retelling with quotes)
#         prompt = f"""
# You are Chess Buddy, explaining a real moment from a children's chess story.

# STRICT RULES (NO EXCEPTIONS):
# 1. You MUST quote exact sentences from the Story Context using quotation marks
# 2. You MUST mention who said the line (Chessy, Chintu, Minku, King, etc.)
# 3. You MUST explain the answer ONLY using quoted story lines
# 4. You MUST NOT invent new dialogue, events, or facts
# 5. Speak in warm Hinglish like a real person explaining a story
# 6. Start your explanation with: "Yaad hai jab..."


# Story Context:
# {context}

# Child's Question:
# {user_query}

# Now explain by quoting the exact lines from the story that give us the answer.
# """
#     else:
#         # One-word / short-phrase answer mode
#         prompt = f"""
# You are Chess Buddy, a friendly chess teacher for kids aged 5-10 years.
# Keep basic chess terminologies in mind while answering.
# CRITICAL INSTRUCTION:
# Answer with ONLY ONE WORD or a very short phrase (maximum 2–3 words).

# Story Context:
# {context}

# Child's Question:
# {user_query}

# Instructions:
# - Read the Story Context carefully
# - Extract the direct answer from the story
# - Answer using ONLY that word or short phrase
# - Hinglish is allowed
# - DO NOT add explanations or extra words
# - If the answer is not clearly present, say ONLY: "Unknown"

# ONE-WORD ANSWER:
# """

#     # -------------------------------
#     # 3️⃣ Call Gemini API
#     # -------------------------------
#     try:
#         model = genai.GenerativeModel(
#             model_name=GEMINI_MODEL_NAME,
#             generation_config={
#                 "temperature": 0.3 if not explain else 0.4,
#                 "max_output_tokens": 60 if not explain else 500,
#                 "top_p": 0.95,
#                 "top_k": 40,
#             },
#             system_instruction=(
#                 "You are a strict story-based assistant for kids. "
#                 "You MUST answer only from the provided story context. "
#                 "Use Hinglish naturally. Never add facts outside the story."
#             ),
#         )

#         response = model.generate_content(prompt)

#         # Safety check
#         if not response or not hasattr(response, "text"):
#             return {
#                 "answer": "Unknown",
#                 "explanation": "Story se clear jawab nahi mila 😊"
#             }

#         response_text = response.text.strip()

#         # -------------------------------
#         # 4️⃣ One-word evidence check
#         # -------------------------------
#         if not explain:
#             one_word_answer = response_text.splitlines()[0].strip()

#             # Check evidence: the answer must appear in at least one chunk
#             answer_token = one_word_answer.lower()
#             evidence_found = False

#             for chunk in relevant_chunks:
#                 if re.search(r"\b" + re.escape(answer_token) + r"\b", chunk.lower()):
#                     evidence_found = True
#                     break

#             if not evidence_found:
#                 return {
#                     "answer": "Unknown",
#                     "explanation": "Iska clear mention story mein nahi mila 📘"
#                 }

#             # Generate explanation using explain=True
#             explanation = generate_llm_response(user_query, explain=True)

#             return {
#                 "answer": one_word_answer,
#                 "explanation": explanation["explanation"]
#             }

#         # -------------------------------
#         # 5️⃣ Explanation mode return
#         # -------------------------------
#         return {
#             "answer": response_text,
#             "explanation": response_text
#         }

#     except Exception as e:
#         print("❌ Gemini Error:", e)
#         return {
#             "answer": "Error",
#             "explanation": "Chess Buddy thoda confuse ho gaya 😅 Phir se try karo!"
#         }
# rag/generator.py
# rag/generator.py
# rag/generator.py
# rag/generator.py
# import os
# from dotenv import load_dotenv
# from functools import lru_cache
# from groq import Groq
# from rag.retriever import get_relevant_stories

# load_dotenv()

# # -------------------------------
# # Groq Configuration
# # -------------------------------
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# if not GROQ_API_KEY:
#     raise RuntimeError("❌ GROQ_API_KEY not found in environment or .env file")

# client = Groq(api_key=GROQ_API_KEY)

# # Best model for Hinglish + speed
# GROQ_MODEL = "llama-3.1-8b-instant"


# # -------------------------------
# # Query Rewriting (for retrieval)
# # -------------------------------
# @lru_cache(maxsize=256)
# def rewrite_query_for_retrieval(query: str) -> str:
#     """
#     Rewrite indirect / kid-style questions into a form
#     that matches story sentences better.
#     """
#     prompt = f"""
# Rewrite the following question into a simple factual question
# that would directly match a sentence in a story.

# Do NOT answer the question.
# Only rewrite it.

# Question:
# {query}

# Rewritten question:
# """

#     completion = client.chat.completions.create(
#         model=GROQ_MODEL,
#         messages=[
#             {"role": "system", "content": "You rewrite questions for retrieval only."},
#             {"role": "user", "content": prompt},
#         ],
#         temperature=0.0,
#         max_tokens=50,
#     )

#     return completion.choices[0].message.content.strip()


# # -------------------------------
# # Main Generator Function
# # -------------------------------
# def generate_llm_response(user_query: str, explain: bool = False):
#     """
#     Option 2 + Query Rewriting (Groq):
#     - LLM self-verifies answers by quoting the story
#     - Query rewritten ONLY for retrieval
#     - No alias logic
#     - No regex checks
#     """

#     # 1️⃣ Rewrite query ONLY for retrieval
#     retrieval_query = rewrite_query_for_retrieval(user_query)

#     # 2️⃣ Retrieve relevant story chunks
#     relevant_chunks = get_relevant_stories(retrieval_query)

#     if not relevant_chunks or len(relevant_chunks) == 0:
#         return {
#             "answer": "Unknown",
#             "explanation": "Iska clear mention story mein nahi mila 📘"
#         }

#     context = "\n\n---\n\n".join(relevant_chunks)

#     # 3️⃣ Unified prompt (ANSWER + PROOF)
#     prompt = f"""
# You are Chess Buddy, a careful story-based assistant for kids.
# You must answer questions ONLY using the provided Story Context.

# ━━━━━━━━━━━━━━━━━━━━━━
# STEP 1 — Identify the QUESTION TYPE
# ━━━━━━━━━━━━━━━━━━━━━━
# First decide which category the question belongs to:

# 1. Identity / Naming  
#    (examples: "K kon hai?", "King ko kya kehte hai?", "Queen ka symbol kya hai?")

# 2. Movement / Ability  
#    (examples: "King kaise chalta hai?", "Pawn kya karta hai?")

# 3. Story Event  
#    (examples: "Story mein kya hua?", "Chintu ne kya kaha?")

# 4. Moral / Learning  
#    (examples: "Story se kya seekha?", "Raja important kyun hai?")

# ━━━━━━━━━━━━━━━━━━━━━━
# STEP 2 — Choose ALLOWED EVIDENCE (VERY STRICT)
# ━━━━━━━━━━━━━━━━━━━━━━
# Use ONLY the correct type of sentence from the story:

# • Identity / Naming  
#   → Sentences that explicitly DEFINE a name or symbol  
#   → e.g. “sab mujhe K bulate hain”, “Main hoon Chessland ka King — K”

# • Movement / Ability  
#   → Sentences that describe how a piece moves or behaves  
#   → e.g. “Raja sirf ek kadam chalta hai”

# • Story Event  
#   → Narrative actions or dialogue  
#   → e.g. “Chintu ne kaha…”, “Board ne bataya…”

# • Moral / Learning  
#   → Reflective or lesson-based sentences  
#   → e.g. “Agar raja pakda gaya, to game khatam”

# ⚠️ DO NOT use sentences that merely mention a character
# ⚠️ DO NOT mix different evidence types

# ━━━━━━━━━━━━━━━━━━━━━━
# STEP 3 — Decide ANSWER DIRECTION (for Identity questions)
# ━━━━━━━━━━━━━━━━━━━━━━
# If the story defines a relationship like:

# NAME ↔ SYMBOL (example: King ↔ K)

# Then:
# • If the question asks “King ko kya kehte hai?” → answer = SYMBOL
# • If the question asks “K kise kehte hai?” → answer = NAME

# ━━━━━━━━━━━━━━━━━━━━━━
# FAIL-SAFE RULE
# ━━━━━━━━━━━━━━━━━━━━━━
# If the story does NOT clearly contain the required evidence,
# respond EXACTLY as follows and do not guess:

# ANSWER: Unknown  
# PROOF: Story me iska zikr nahi hai

# ━━━━━━━━━━━━━━━━━━━━━━
# STRICT OUTPUT FORMAT (NO EXTRA WORDS)
# ━━━━━━━━━━━━━━━━━━━━━━

# ANSWER: <short answer only>
# PROOF: "<exact sentence(s) copied from the story>"

# ━━━━━━━━━━━━━━━━━━━━━━
# Story Context:
# {context}

# Question:
# {user_query}

# """

#     # 4️⃣ Call Groq
#     try:
#         completion = client.chat.completions.create(
#             model=GROQ_MODEL,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a strict story-grounded assistant for kids. "
#                         "Never invent facts. Always quote the story as proof. "
#                         "Use natural Hinglish."
#                     ),
#                 },
#                 {"role": "user", "content": prompt},
#             ],
#             temperature=0.2,
#             max_tokens=250,
#         )

#         text = completion.choices[0].message.content.strip()

#         # 5️⃣ Parse ANSWER and PROOF
#         answer = "Unknown"
#         proof = ""

#         for line in text.splitlines():
#             if line.startswith("ANSWER:"):
#                 answer = line.replace("ANSWER:", "").strip()
#             elif line.startswith("PROOF:"):
#                 proof = line.replace("PROOF:", "").strip()

#         if answer.lower() == "unknown":
#             return {
#                 "answer": "Unknown",
#                 "explanation": "Iska clear mention story mein nahi mila 📘"
#             }

#         # 6️⃣ Human-style explanation
#         explanation = (
#             f"Yaad hai when story mein kaha gaya:\n"
#             f"{proof}\n\n"
#             f"Isliye is sawal ka jawab {answer} hai"
#         )

#         return {
#             "answer": answer,
#             "explanation": explanation
#         }

#     except Exception as e:
#         print("❌ Groq Error:", e)
#         return {
#             "answer": "Error",
#             "explanation": "Chess Buddy thoda confuse ho gaya Phir se try karo!"
#         }
import os
from dotenv import load_dotenv
from functools import lru_cache
from groq import Groq
from rag.retriever import get_relevant_stories

load_dotenv()

# -------------------------------
# Groq Configuration
# -------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY not found in environment or .env file")

client = Groq(api_key=GROQ_API_KEY)

# Best model for Hinglish + speed
GROQ_MODEL = "llama-3.1-8b-instant"


# -------------------------------
# Query Rewriting (for retrieval)
# -------------------------------
@lru_cache(maxsize=256)
def rewrite_query_for_retrieval(query: str) -> str:
    """
    Rewrite indirect / kid-style questions into a form
    that matches story sentences better.
    """
    prompt = f"""
Rewrite the following question into a simple factual question
that would directly match a sentence in a story.

Do NOT answer the question.
Only rewrite it.

Question:
{query}

Rewritten question:
"""

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You rewrite questions for retrieval only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=50,
    )

    return completion.choices[0].message.content.strip()


# -------------------------------
# Main Generator Function
# -------------------------------
def generate_llm_response(user_query: str, explain: bool = False):
    """
    Option 2 + Query Rewriting (Groq):
    - LLM self-verifies answers by quoting the story
    - Query rewritten ONLY for retrieval
    - No alias logic
    - No regex checks
    """

    # 1️⃣ Rewrite query ONLY for retrieval
    retrieval_query = rewrite_query_for_retrieval(user_query)

    # 2️⃣ Retrieve relevant story chunks
    relevant_chunks = get_relevant_stories(retrieval_query)

    if not relevant_chunks or len(relevant_chunks) == 0:
        return {
            "answer": "Unknown",
            "explanation": "Iska clear mention story mein nahi mila 📘"
        }

    context = "\n\n---\n\n".join(relevant_chunks)

    # 3️⃣ Unified prompt (ANSWER + PROOF)
    prompt = f"""
You are Chess Buddy, a careful story-based assistant for kids.
You must answer questions ONLY using the provided Story Context.

━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — Identify the QUESTION TYPE
━━━━━━━━━━━━━━━━━━━━━━
First decide which category the question belongs to:

1. Identity / Naming
   (examples: "K kon hai?", "King ko kya kehte hai?", "Queen ka symbol kya hai?")

2. Movement / Ability  
   (examples: "King kaise chalta hai?", "Pawn kya karta hai?")

3. Story Event  
   (examples: "Story mein kya hua?", "Chintu ne kya kaha?")

4. Moral / Learning  
   (examples: "Story se kya seekha?", "Raja important kyun hai?")

5. You should consider upper case and lower case letters as same, like K is same as k, Q is same as q and hence answer accordingly.
━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — Choose ALLOWED EVIDENCE (VERY STRICT)
━━━━━━━━━━━━━━━━━━━━━━
Use ONLY the correct type of sentence from the story:

• Identity / Naming  
  → Sentences that explicitly DEFINE a name or symbol  
  → e.g. “sab mujhe K bulate hain”, “Main hoon Chessland ka King — K”

• Movement / Ability  
  → Sentences that describe how a piece moves or behaves  
  → e.g. “Raja sirf ek kadam chalta hai”

• Story Event  
  → Narrative actions or dialogue  
  → e.g. “Chintu ne kaha…”, “Board ne bataya…”

• Moral / Learning  
  → Reflective or lesson-based sentences  
  → e.g. “Agar raja pakda gaya, to game khatam”

⚠️ DO NOT use sentences that merely mention a character
⚠️ DO NOT mix different evidence types

━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — Decide ANSWER DIRECTION (for Identity questions)
━━━━━━━━━━━━━━━━━━━━━━
If the story defines a relationship like:

NAME ↔ SYMBOL (example: King ↔ K)

Then:
• If the question asks “King ko kya kehte hai?” → answer = SYMBOL
• If the question asks “K kise kehte hai?” → answer = NAME

━━━━━━━━━━━━━━━━━━━━━━
FAIL-SAFE RULE
━━━━━━━━━━━━━━━━━━━━━━
If the story does NOT clearly contain the required evidence,
respond EXACTLY as follows and do not guess:

ANSWER: Unknown  
PROOF: Story me iska zikr nahi hai

━━━━━━━━━━━━━━━━━━━━━━
STRICT OUTPUT FORMAT (NO EXTRA WORDS)
━━━━━━━━━━━━━━━━━━━━━━

ANSWER: <short answer only>
PROOF: "<exact sentence(s) copied from the story>"

━━━━━━━━━━━━━━━━━━━━━━
Story Context:
{context}

Question:
{user_query}

"""

    # 4️⃣ Call Groq
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict story-grounded assistant for kids. "
                        "Never invent facts. Always quote the story as proof. "
                        "Use natural Hinglish."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=250,
        )

        text = completion.choices[0].message.content.strip()

        # 5️⃣ Parse ANSWER and PROOF
        answer = "Unknown"
        proof = ""

        for line in text.splitlines():
            if line.startswith("ANSWER:"):
                answer = line.replace("ANSWER:", "").strip()
            elif line.startswith("PROOF:"):
                proof = line.replace("PROOF:", "").strip()

        if answer.lower() == "unknown":
            return {
                "answer": "Unknown",
                "explanation": "Iska clear mention story mein nahi mila 📘"
            }

        # 6️⃣ Human-style explanation
        explanation = (
            f"Yaad hai when story mein kaha gaya:\n"
            f"{proof}\n\n"
            f"Isliye is sawal ka jawab {answer} hai "
        )

        return {
            "answer": answer,
            "explanation": explanation
        }

    except Exception as e:
        print("❌ Groq Error:", e)
        return {
            "answer": "Error",
            "explanation": "Chess Buddy thoda confuse ho gaya, Phir se try karo!"
        }
    