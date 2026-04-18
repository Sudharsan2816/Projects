import streamlit as st
import requests
import uuid
from components.styles import GLOBAL_CSS
from components.sidebar import render_sidebar

st.set_page_config(
    page_title="AI Market Research Copilot",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000")

# ── Session bootstrap ─────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "topic" not in st.session_state:
    st.session_state.topic = ""

render_sidebar()

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">🔬 AI Market Research Copilot</div>
    <div class="app-subtitle">
        Upload documents or enter a topic — get a professional market research report powered by AI
    </div>
</div>
""", unsafe_allow_html=True)

# ── Backend health ────────────────────────────────────────────────────────────
try:
    res = requests.get(f"{BACKEND}/health", timeout=4)
    health = res.json()
    backend_ok = True
except Exception:
    health = {}
    backend_ok = False

# ── Stats Row ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
docs = st.session_state.uploaded_docs
total_chunks = sum(d.get("chunk_count", 0) for d in docs)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{len(docs)}</div>
        <div class="stat-label">Documents Indexed</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{total_chunks}</div>
        <div class="stat-label">Vector Chunks</div>
    </div>""", unsafe_allow_html=True)

with col3:
    has_report = st.session_state.report_data is not None
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number">{"✓" if has_report else "—"}</div>
        <div class="stat-label">Report Ready</div>
    </div>""", unsafe_allow_html=True)

with col4:
    provider = health.get("llm_provider", "—").upper() if backend_ok else "OFFLINE"
    color = "#81c784" if backend_ok else "#ef9a9a"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-number" style="color:{color}; font-size:1.3rem;">{provider}</div>
        <div class="stat-label">LLM Backend</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── Quick Start ───────────────────────────────────────────────────────────────
st.markdown("### How to use")
c1, c2, c3, c4 = st.columns(4)
steps = [
    ("📁", "1. Upload", "Upload PDFs, CSVs, or TXT files related to your market"),
    ("🔍", "2. Research", "Enter a market topic and generate a full AI report"),
    ("📊", "3. View", "Browse competitors, pricing, trends, and SWOT analysis"),
    ("💬", "4. Chat", "Ask specific questions about your uploaded documents"),
]
for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
    with col:
        st.markdown(f"""
        <div class="research-card" style="text-align:center; min-height:130px;">
            <div style="font-size:2rem;">{icon}</div>
            <div style="font-weight:700; color:#e3f2fd; margin:8px 0 4px;">{title}</div>
            <div style="font-size:0.85rem; color:#78909c;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Quick topic launcher ──────────────────────────────────────────────────────
st.markdown("<br/>### Quick Start — Enter a Market Topic", unsafe_allow_html=True)
col_input, col_btn = st.columns([4, 1])
with col_input:
    topic_input = st.text_input(
        "Market topic",
        placeholder="e.g. Indian protein bar market, EV charging infrastructure, SaaS CRM tools",
        label_visibility="collapsed",
    )
with col_btn:
    if st.button("→ Generate", use_container_width=True):
        if topic_input.strip():
            st.session_state.topic = topic_input.strip()
            st.switch_page("pages/2_Research.py")
        else:
            st.error("Please enter a topic")

# ── Backend status ────────────────────────────────────────────────────────────
if not backend_ok:
    st.error("⚠️ Cannot connect to backend at `http://localhost:8000`. Make sure the FastAPI server is running.")
else:
    st.success(f"Backend connected · {health.get('app','')} v{health.get('version','')}")
