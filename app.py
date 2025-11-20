import streamlit as st
import os
import time
from google import genai
from utils.memory_store import load_memory, update_memory

# Import your existing agents
from agents.search_agent import SearchAgent
from agents.doc_agent import DocAgent
from agents.code_agent import CodeAgent
from agents.video_agent import VideoAgent

# --- CONFIGURATION ---
st.set_page_config(page_title="Study Swarm Agent", page_icon="🐝", layout="wide")
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# --- CUSTOM STYLES (Dark Mode Optimized) ---
st.markdown("""
    <style>
    .stChatMessage {
        border-radius: 10px; 
        padding: 10px; 
        border: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
# The smart intro message you liked
INTRO_MESSAGE = "Hi! I'm your **Study Swarm**. I can search the web 🌐, read your PDF 📄, watch your video 🎥, or run Python code 💻. How can I help?"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🧠 Long-Term Memory")
    
    # Load memory
    memory = load_memory()
    
    with st.expander("What I know about you", expanded=True):
        if memory["facts"]:
            for fact in memory["facts"]:
                st.markdown(f"• *{fact}*")
        else:
            st.caption("Nothing yet... tell me about yourself!")

    st.divider()
    st.header("📂 Study Materials")
    
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    pdf_path = None
    if uploaded_pdf:
        pdf_path = f"temp_{uploaded_pdf.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        st.success(f"Loaded: {uploaded_pdf.name}")

    uploaded_video = st.file_uploader("Upload Video", type=["mp4", "mov"])
    video_path = None
    if uploaded_video:
        video_path = f"temp_{uploaded_video.name}"
        with open(video_path, "wb") as f:
            f.write(uploaded_video.getbuffer())
        st.video(uploaded_video)
        st.success(f"Loaded: {uploaded_video.name}")

    st.divider()
    # FIX: Clear Chat now resets to the Intro Message, not empty
    if st.button("Clear Chat"):
        st.session_state.messages = [{"role": "assistant", "content": INTRO_MESSAGE}]
        st.rerun()

# --- INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": INTRO_MESSAGE}]

@st.cache_resource
def load_agents():
    return {
        "search": SearchAgent(),
        "doc": DocAgent(),
        "code": CodeAgent(),
        "video": VideoAgent()
    }
agents = load_agents()

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CORE LOGIC ---
if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.empty()
        
        # 1. CONTEXTUALIZE (Session Memory)
        status.markdown("🧠 Recalling context...")
        
        history_text = ""
        for msg in st.session_state.messages[-5:]:
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
            
        context_prompt = f"""
        Rewrite the LAST USER INPUT to be a standalone question based on CHAT HISTORY.
        CHAT HISTORY:
        {history_text}
        LAST USER INPUT: "{prompt}"
        REWRITTEN QUERY:
        """
        
        try:
            rewritten_query_resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=context_prompt
            )
            final_query = rewritten_query_resp.text.strip()
        except:
            final_query = prompt # Fallback

        # 2. CHECK FOR NEW MEMORY
        # FIX: If we find a memory, we save it AND rerun to update sidebar immediately
        if "my name is" in final_query.lower() or "i study" in final_query.lower() or "i like" in final_query.lower() or "i am a" in final_query.lower():
             update_memory(final_query)
             st.toast("Memory Updated! 💾")
             time.sleep(1) # Tiny pause so user sees the toast
             st.rerun() # <--- THIS FORCES THE SIDEBAR TO UPDATE INSTANTLY

        # 3. ROUTING
        response = ""
        
        if pdf_path and ("pdf" in final_query.lower() or "document" in final_query.lower() or "summarize" in final_query.lower()):
            status.markdown("📄 Reading PDF...")
            response = agents["doc"].ask_pdf(pdf_path, final_query)
            
        elif video_path and ("video" in final_query.lower() or "watch" in final_query.lower()):
            status.markdown("🎥 Analyzing Video...")
            response = agents["video"].analyze_video(video_path, final_query)

        elif "code" in final_query.lower() or "python" in final_query.lower() or "calculate" in final_query.lower():
            status.markdown("💻 Running Code...")
            response = agents["code"].solve(final_query)

        elif "search" in final_query.lower() or "who is" in final_query.lower() or "current" in final_query.lower() or "president" in final_query.lower() or "news" in final_query.lower():
            status.markdown("🌐 Searching Google...")
            response = agents["search"].research(final_query)
            
        else:
            status.markdown("🤔 Thinking...")
            memory_data = load_memory()
            system_instruction = f"You are a helpful study assistant. You know these facts about the user: {memory_data['facts']}."
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_instruction}\n\nUser: {final_query}"
            ).text

        status.empty()
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})