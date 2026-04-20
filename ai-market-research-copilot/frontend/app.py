import os
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

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

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
has_report = st.session_state.report_data is not None
provider = health.get("llm_provider", "—").upper() if backend_ok else "OFFLINE"
provider_color = "#86efac" if backend_ok else "#fca5a5"

# ── Hero + status spotlight ───────────────────────────────────────────────────
col_hero, col_state = st.columns([2.1, 1.2], gap="medium")
with col_hero:
    st.markdown(
        """
        <div class="app-header reveal-1">
            <div class="app-title">Discover Markets Like a Pro</div>
            <div class="app-subtitle">
                Turn raw docs into strategic intelligence in minutes: competitors, pricing, trends,
                and a downloadable report crafted by AI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_state:
    st.markdown(
        f"""
        <div class="research-card reveal-2" style="height:100%;">
            <div style="font-size:0.76rem; letter-spacing:0.1em; text-transform:uppercase; color:#9fb0df;">
                Live Session
            </div>
            <div style="margin-top:10px; font-size:1.5rem; font-weight:800; color:#f6f8ff;">
                {"Ready to Generate" if backend_ok else "Backend Offline"}
            </div>
            <div style="font-size:0.86rem; margin-top:6px; color:#b8c4ea;">
                Provider:
                <span style="font-weight:800; color:{provider_color};">{provider}</span>
            </div>
            <div style="font-size:0.86rem; margin-top:6px; color:#b8c4ea;">
                Session:
                <span style="font-family:monospace; color:#dbe7ff;">{st.session_state.session_id[:10]}...</span>
            </div>
            <div style="margin-top:12px; font-size:0.82rem; color:#9fb0df;">
                {("Connected to " + health.get("app", "service")) if backend_ok else "Start FastAPI service to continue."}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col1:
    st.markdown(f"""
    <div class="stat-card reveal-1">
        <div class="stat-number">{len(docs)}</div>
        <div class="stat-label">Documents Indexed</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card reveal-2">
        <div class="stat-number">{total_chunks}</div>
        <div class="stat-label">Vector Chunks</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card reveal-3">
        <div class="stat-number">{"✓" if has_report else "—"}</div>
        <div class="stat-label">Report Ready</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card reveal-4">
        <div class="stat-number" style="color:{provider_color}; font-size:1.3rem;">{provider}</div>
        <div class="stat-label">LLM Backend</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

if backend_ok:
    token_limits = health.get("token_limits", {})
    if token_limits:
        st.markdown("### Token Usage Limits")
        t1, t2, t3 = st.columns(3)
        with t1:
            st.markdown(
                f"""
                <div class="research-card reveal-1" style="text-align:center;">
                    <div style="font-size:1.5rem;">🧮</div>
                    <div style="font-weight:800; font-size:1.3rem; color:#f0f4ff;">{token_limits.get("max_output_tokens", "—")}</div>
                    <div style="font-size:0.8rem; color:#9fb0df;">Max output tokens / response</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with t2:
            st.markdown(
                f"""
                <div class="research-card reveal-2" style="text-align:center;">
                    <div style="font-size:1.5rem;">🗂️</div>
                    <div style="font-weight:800; font-size:1.3rem; color:#f0f4ff;">{token_limits.get("chat_history_db_limit", "—")}</div>
                    <div style="font-size:0.8rem; color:#9fb0df;">Stored chat messages / session</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with t3:
            st.markdown(
                f"""
                <div class="research-card reveal-3" style="text-align:center;">
                    <div style="font-size:1.5rem;">🧠</div>
                    <div style="font-weight:800; font-size:1.3rem; color:#f0f4ff;">{token_limits.get("chat_context_messages", "—")}</div>
                    <div style="font-size:0.8rem; color:#9fb0df;">Messages used as active context</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Quick Start ───────────────────────────────────────────────────────────────
st.markdown("### Workflow")
c1, c2, c3, c4 = st.columns(4)
steps = [
    ("📁", "1. Curate Data", "Import market PDFs, pricing sheets, and notes."),
    ("🧠", "2. Generate Insight", "Run AI analysis over your chosen topic."),
    ("📊", "3. Inspect Report", "Review competitors, trends, SWOT, and pricing."),
    ("💬", "4. Ask Anything", "Chat with sources and cite-backed answers."),
]
for col, (icon, title, desc) in zip([c1, c2, c3, c4], steps):
    with col:
        st.markdown(f"""
        <div class="research-card reveal-2" style="text-align:center; min-height:130px;">
            <div style="font-size:2rem;">{icon}</div>
            <div style="font-weight:700; color:#e9edff; margin:8px 0 4px;">{title}</div>
            <div style="font-size:0.85rem; color:#9fb0df;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Topic launcher + actions ──────────────────────────────────────────────────
st.markdown("<br/>### Start a New Insight Session", unsafe_allow_html=True)
left, right = st.columns([2.4, 1], gap="medium")
with left:
    st.markdown(
        """
        <div class="research-card">
            <div style="font-weight:800; font-size:1.1rem; color:#eef2ff; margin-bottom:4px;">
                Prompt Your Market
            </div>
            <div style="font-size:0.88rem; color:#9fb0df; margin-bottom:8px;">
                Enter a market space and jump straight into report generation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    topic_input = st.text_input(
        "Market topic",
        placeholder="e.g. India fintech lending market, AI note-taking tools, EV charging infra",
        label_visibility="collapsed",
    )
    if st.button("Generate Report from Topic", use_container_width=False, type="primary"):
        if topic_input.strip():
            st.session_state.topic = topic_input.strip()
            st.switch_page("pages/2_Research.py")
        else:
            st.error("Please enter a topic")

with right:
    st.markdown(
        """
        <div class="research-card">
            <div style="font-weight:800; color:#eef2ff;">Jump to</div>
            <div style="font-size:0.85rem; color:#9fb0df; margin-top:6px;">
                Open any step directly.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Upload", use_container_width=True):
        st.switch_page("pages/1_Upload.py")
    if st.button("Open Last Report", use_container_width=True, disabled=not has_report):
        st.switch_page("pages/3_Report.py")
    if st.button("Open Chat", use_container_width=True, disabled=not docs):
        st.switch_page("pages/4_Chat.py")

# ── Backend status ────────────────────────────────────────────────────────────
if not backend_ok:
    st.error("⚠️ Cannot connect to backend at `http://localhost:8000`. Make sure the FastAPI server is running.")
else:
    st.success(f"Backend connected · {health.get('app','')} v{health.get('version','')}")
