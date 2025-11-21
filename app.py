import streamlit as st
import os
import time
from google import genai
from utils.memory_store import load_memory, update_memory, delete_fact

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

    # MEMORY SECTION
    st.header("🧠 Long-Term Memory")
    memory = load_memory()
    
    with st.expander("What I know about you", expanded=True):
        if not memory["facts"]:
            st.caption("Nothing yet... tell me about yourself!")
        else:
            is_editing = st.toggle("Edit Memory", value=False)
            for i, fact in enumerate(memory["facts"]):
                if is_editing:
                    col1, col2 = st.columns([0.8, 0.2], vertical_alignment="center")
                    with col1: st.write(f"• {fact}")
                    with col2:
                        if st.button("🗑️", key=f"del_{i}", type="tertiary", help="Delete"):
                            delete_fact(fact)
                            st.rerun()
                else:
                    st.markdown(f"• *{fact}*")

    st.divider()
    
    # NEW: AI JUDGE TOGGLE
    st.header("⚙️ Advanced Settings")
    enable_judge = st.toggle("Enable AI Judge ⚖️", value=False, help="Ask a second AI to grade the response for accuracy.")
    
    st.divider()
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

# --- HELPER: THE LIVE JUDGE ---
def judge_response(user_query, agent_response):
    judge_prompt = f"""
    Act as an impartial AI Judge. Grade the following response.
    
    USER QUERY: "{user_query}"
    AGENT RESPONSE: "{agent_response}"
    
    CRITERIA:
    - Accuracy: Is the information correct?
    - Helpfulness: Did it answer the user's intent?
    - Safety: Is the content safe?
    
    OUTPUT FORMAT:
    SCORE: [1-5]
    REASON: [1 short sentence]
    """
    try:
        eval_resp = client.models.generate_content(model="gemini-2.0-flash", contents=judge_prompt).text
        return eval_resp
    except:
        return "SCORE: ?\nREASON: Judge fell asleep."

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
        CHAT HISTORY: {history_text}
        LAST USER INPUT: "{prompt}"
        INSTRUCTIONS: If user refers to "it/he/that", clarify. If standalone, keep as is.
        REWRITTEN QUERY:
        """
        try:
            rewritten_resp = client.models.generate_content(model="gemini-2.0-flash", contents=context_prompt)
            final_query = rewritten_resp.text.strip()
        except:
            final_query = prompt

        # 3. ROUTING & EXECUTION
        response = ""
        generated_images = [] 

        if pdf_path and ("pdf" in final_query.lower() or "document" in final_query.lower() or "summarize" in final_query.lower()):
            status.markdown("📄 Reading PDF...")
            response = agents["doc"].ask_pdf(pdf_path, final_query)
            
        elif video_path and ("video" in final_query.lower() or "watch" in final_query.lower()):
            status.markdown("🎥 Analyzing Video...")
            response = agents["video"].analyze_video(video_path, final_query)

        elif "code" in final_query.lower() or "python" in final_query.lower() or "calculate" in final_query.lower() or "plot" in final_query.lower():
            status.markdown("💻 Running Code...")
            result = agents["code"].solve(final_query)
            if isinstance(result, dict):
                response = result["text"]
                generated_images = result.get("images", [])
            else:
                response = str(result)

        elif "search" in final_query.lower() or "who is" in final_query.lower() or "current" in final_query.lower() or "president" in final_query.lower() or "news" in final_query.lower():
            status.markdown("🌐 Searching Google...")
            response = agents["search"].research(final_query)
            
        else:
            # General Chat
            status.markdown("🤔 Thinking...")
            memory_data = load_memory()
            sys_prompt = f"You are a helpful study assistant. USER FACTS: {memory_data['facts']}"
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=f"{sys_prompt}\n\nUser Query: {final_query}"
            ).text

        # 4. DISPLAY RESPONSE
        status.empty()
        st.markdown(response)
        
        if generated_images:
            for img_data in generated_images:
                st.image(img_data.data, caption="Generated Visualization 📊")

        st.session_state.messages.append({"role": "assistant", "content": response})

        # 5. LIVE JUDGE (The New Feature)
        if enable_judge:
            with st.status("👨‍⚖️ The Judge is reviewing...", expanded=True) as judge_status:
                evaluation = judge_response(final_query, response)
                st.info(evaluation)
                judge_status.update(label="✅ Graded", state="complete", expanded=True)