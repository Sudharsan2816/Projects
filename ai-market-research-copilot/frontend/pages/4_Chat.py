import streamlit as st
import requests
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.styles import GLOBAL_CSS
from components.sidebar import render_sidebar

st.set_page_config(page_title="Chat with Docs", page_icon="💬", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

render_sidebar()

st.markdown("""
<div class="app-header">
    <div class="app-title">💬 Chat with Your Documents</div>
    <div class="app-subtitle">Ask questions about uploaded documents — AI answers with source citations</div>
</div>
""", unsafe_allow_html=True)

# ── Guard: no documents ───────────────────────────────────────────────────────
if not st.session_state.uploaded_docs:
    st.warning("No documents indexed yet. Upload documents first for grounded answers.")

# ── Suggested questions ───────────────────────────────────────────────────────
st.markdown("**Suggested questions:**")
suggestions = [
    "Who are the top competitors?",
    "What are the key market trends?",
    "What are the pricing strategies used?",
    "What growth opportunities exist?",
    "What are the biggest threats in this market?",
]
cols = st.columns(len(suggestions))
for col, q in zip(cols, suggestions):
    with col:
        if st.button(q, use_container_width=True, key=f"q_{q}"):
            st.session_state._pending_question = q
            st.rerun()

st.divider()

# ── Chat history ──────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user"><b>You</b><br/>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            sources = msg.get("sources", [])
            sources_html = ""
            if sources:
                chips = "".join(
                    f'<span class="source-chip">📄 {s["filename"]} (p.{s.get("chunk_index",0)+1}) · {s["relevance_score"]:.2f}</span>'
                    for s in sources[:4]
                )
                sources_html = f"<div style='margin-top:10px;'><span style='font-size:0.75rem; color:#78909c;'>Sources: </span>{chips}</div>"

            st.markdown(
                f'<div class="chat-assistant"><b>AI</b><br/>{msg["content"].replace(chr(10),"<br/>")}{sources_html}</div>',
                unsafe_allow_html=True,
            )

# ── Input ─────────────────────────────────────────────────────────────────────
col_input, col_send, col_clear = st.columns([7, 1, 1])

pending = st.session_state.pop("_pending_question", None)

with col_input:
    user_input = st.text_input(
        "Ask a question",
        value=pending or "",
        placeholder="e.g. What pricing strategies are used in the premium segment?",
        label_visibility="collapsed",
        key="chat_input",
    )
with col_send:
    send = st.button("Send", use_container_width=True, type="primary")
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.chat_history = []
        try:
            requests.delete(f"{BACKEND}/api/v1/chat/{st.session_state.session_id}/history", timeout=10)
        except Exception:
            pass
        st.rerun()

# ── Send message ──────────────────────────────────────────────────────────────
if (send or pending) and (user_input or pending):
    question = (user_input or pending).strip()
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.spinner("AI is thinking…"):
            try:
                res = requests.post(
                    f"{BACKEND}/api/v1/chat/",
                    json={"session_id": st.session_state.session_id, "message": question},
                    timeout=90,
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": data["content"],
                        "sources": data.get("sources", []),
                    })
                else:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Error: {res.json().get('detail', 'Unknown error')}",
                        "sources": [],
                    })
            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Connection error: {e}",
                    "sources": [],
                })
        st.rerun()
