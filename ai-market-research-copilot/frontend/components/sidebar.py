import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 16px 0 8px;">
            <div style="font-size:2rem;">🔬</div>
            <div style="font-size:1.1rem; font-weight:800; color:#e3f2fd;">Market Research</div>
            <div style="font-size:0.8rem; color:#78909c;">AI Copilot v1.0</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Session ID
        if "session_id" not in st.session_state:
            st.session_state.session_id = None

        session_id = st.session_state.get("session_id", "")
        if session_id:
            st.markdown(f"""
            <div style="background:rgba(2,136,209,0.15); border-radius:8px; padding:10px 12px; margin:8px 0;">
                <div style="font-size:0.72rem; color:#78909c; margin-bottom:2px;">SESSION ID</div>
                <div style="font-size:0.8rem; color:#81d4fa; font-family:monospace; word-break:break-all;">
                    {session_id[:36]}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Navigation
        st.markdown("<div style='font-size:0.75rem; color:#546e7a; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Navigation</div>", unsafe_allow_html=True)
        st.page_link("app.py", label="🏠 Dashboard", use_container_width=True)
        st.page_link("pages/1_Upload.py", label="📁 Upload Documents", use_container_width=True)
        st.page_link("pages/2_Research.py", label="🔍 Generate Report", use_container_width=True)
        st.page_link("pages/3_Report.py", label="📊 View Report", use_container_width=True)
        st.page_link("pages/4_Chat.py", label="💬 Chat with Docs", use_container_width=True)

        st.divider()

        # Uploaded docs summary
        docs = st.session_state.get("uploaded_docs", [])
        if docs:
            st.markdown(f"<div style='font-size:0.75rem; color:#546e7a; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>Indexed Documents ({len(docs)})</div>", unsafe_allow_html=True)
            for doc in docs:
                st.markdown(f"""
                <div style="font-size:0.82rem; color:#90a4ae; padding:3px 0;">
                    📄 {doc['filename'][:28]}{'…' if len(doc['filename']) > 28 else ''}
                    <span style="color:#4fc3f7; margin-left:6px;">{doc.get('chunk_count',0)} chunks</span>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Settings hint
        with st.expander("⚙️ Settings"):
            st.markdown("""
            Configure in `.env` file:
            - `NVIDIA_API_KEY`
            - `NVIDIA_MODEL` (LLM)
            - `NVIDIA_EMBEDDING_MODEL`
            - `NVIDIA_RERANKER_MODEL`
            - `LLM_PROVIDER` (nvidia/gemini/ollama)
            - `EMBEDDING_PROVIDER` (nvidia/local)
            """)

        st.markdown("""
        <div style="position:absolute; bottom:16px; left:0; right:0; text-align:center; font-size:0.72rem; color:#37474f;">
            Built with FastAPI · FAISS · NVIDIA NIM
        </div>
        """, unsafe_allow_html=True)
