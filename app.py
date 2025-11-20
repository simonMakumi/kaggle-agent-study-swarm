import streamlit as st
import os
import time
from google import genai
from utils.memory_store import load_memory, update_memory

# Import Agents
from agents.search_agent import SearchAgent
from agents.doc_agent import DocAgent
from agents.code_agent import CodeAgent
from agents.video_agent import VideoAgent

# --- CONFIGURATION ---
st.set_page_config(page_title="Study Swarm Agent", page_icon="🐝", layout="wide")
API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=API_KEY)

# --- CUSTOM STYLES ---
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
INTRO_MESSAGE = "Hi! I'm your **Study Swarm**. I can search the web 🌐, read your PDF 📄, watch your video 🎥, or run Python code 💻. How can I help?"

# --- SIDEBAR ---
with st.sidebar:
    # SECTION 1: STUDY MATERIALS (Moved to Top)
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

    # SECTION 2: MEMORY (Moved Below)
    st.header("🧠 Long-Term Memory")
    memory = load_memory()
    
    with st.expander("What I know about you", expanded=True):
        if memory["facts"]:
            for fact in memory["facts"]:
                st.markdown(f"• *{fact}*")
        else:
            st.caption("Nothing yet... tell me about yourself!")

    st.divider()
    
    # SECTION 3: ACTIONS
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

# Display Chat History
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
        
        # 1. MEMORY UPDATE
        lower_prompt = prompt.lower()
        if "my name is" in lower_prompt or "i am a" in lower_prompt or "i study" in lower_prompt:
             update_memory(prompt)
             st.toast("Memory Updated! 💾")
             
             reply_text = f"Got it! I've added that to my memory: *'{prompt}'*."
             st.session_state.messages.append({"role": "assistant", "content": reply_text})
             
             time.sleep(1)
             st.rerun()

        # 2. CONTEXTUALIZE
        status.markdown("🧠 Recalling context...")
        
        history_text = ""
        for msg in st.session_state.messages[-5:]:
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
            
        context_prompt = f"""
        Rewrite the LAST USER INPUT based on CHAT HISTORY.
        CHAT HISTORY:
        {history_text}
        LAST USER INPUT: "{prompt}"
        INSTRUCTIONS:
        1. If the user refers to "it", "he", "that", use history to clarify.
        2. If the user asks a standalone question, leave it alone.
        REWRITTEN QUERY:
        """
        
        try:
            rewritten_query_resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=context_prompt
            )
            final_query = rewritten_query_resp.text.strip()
        except:
            final_query = prompt

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
            # General Chat
            status.markdown("🤔 Thinking...")
            memory_data = load_memory()
            system_instruction = f"""
            You are a helpful study assistant. 
            USER FACTS: {memory_data['facts']}
            INSTRUCTION: Be helpful and concise.
            """
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_instruction}\n\nUser Query: {final_query}"
            ).text

        status.empty()
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})