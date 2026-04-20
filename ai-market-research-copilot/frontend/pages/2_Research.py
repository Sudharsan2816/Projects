import os
import streamlit as st
import requests
import time
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.styles import GLOBAL_CSS
from components.sidebar import render_sidebar

st.set_page_config(page_title="Generate Report", page_icon="🔍", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "topic" not in st.session_state:
    st.session_state.topic = ""

render_sidebar()

st.markdown("""
<div class="app-header">
    <div class="app-title">🔍 Generate Market Research Report</div>
    <div class="app-subtitle">AI-powered analysis: competitors · pricing · trends · SWOT</div>
</div>
""", unsafe_allow_html=True)

# ── Topic Input ───────────────────────────────────────────────────────────────
st.markdown("### Define Your Research Topic")

col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input(
        "Market topic",
        value=st.session_state.topic,
        placeholder="e.g. Indian protein bar market, Global EV market 2024, SaaS HR tools",
    )

with col2:
    st.markdown("<br/>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Generate Report", use_container_width=True, type="primary")

# ── Suggested topics ──────────────────────────────────────────────────────────
st.markdown("**Quick suggestions:**")
suggestions = [
    "Indian protein bar market",
    "Global electric vehicle market",
    "SaaS CRM software landscape",
    "D2C skincare brands India",
    "Cloud computing market 2024",
]
s_cols = st.columns(len(suggestions))
for col, sug in zip(s_cols, suggestions):
    with col:
        if st.button(sug, use_container_width=True, key=f"sug_{sug}"):
            st.session_state.topic = sug
            st.rerun()

st.markdown("---")

# ── Generation Logic ──────────────────────────────────────────────────────────
if generate_btn and topic.strip():
    st.session_state.topic = topic.strip()

    # Step-by-step progress UI
    st.markdown("### Generating Report…")
    steps = [
        ("🔍", "Analysing topic and context"),
        ("🏢", "Extracting competitor intelligence"),
        ("💰", "Mining pricing insights"),
        ("📈", "Identifying market trends"),
        ("⚔️", "Performing SWOT analysis"),
        ("📄", "Rendering PDF report"),
    ]
    step_placeholders = []
    for icon, label in steps:
        ph = st.empty()
        ph.markdown(f'<div class="progress-step">⬜ {icon} {label}</div>', unsafe_allow_html=True)
        step_placeholders.append((ph, icon, label))

    try:
        # Trigger report generation
        res = requests.post(
            f"{BACKEND}/api/v1/research/generate",
            json={"session_id": st.session_state.session_id, "topic": topic.strip()},
            timeout=30,
        )
        res.raise_for_status()
        report_id = res.json()["data"]["report_id"]

        # Poll for completion
        for i, (ph, icon, label) in enumerate(step_placeholders):
            ph.markdown(f'<div class="progress-step step-active">⏳ {icon} {label}…</div>', unsafe_allow_html=True)
            time.sleep(0.8)

        # Wait for backend to finish (poll up to 3 min)
        max_wait = 180
        waited = 0
        report = None

        poll_ph = st.empty()
        while waited < max_wait:
            poll_ph.info(f"⏳ AI is generating your report… ({waited}s)")
            time.sleep(4)
            waited += 4
            r = requests.get(
                f"{BACKEND}/api/v1/research/{st.session_state.session_id}/reports/{report_id}",
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                if data["status"] == "done":
                    report = data
                    break
                elif data["status"] == "failed":
                    poll_ph.error("Report generation failed on the backend.")
                    break

        poll_ph.empty()

        if report:
            # Mark all steps done
            for ph, icon, label in step_placeholders:
                ph.markdown(f'<div class="progress-step step-done">✅ {icon} {label}</div>', unsafe_allow_html=True)

            st.session_state.report_data = report
            st.success("✅ Report generated! Navigate to **View Report** to explore it.")
            if st.button("📊 View Report Now →"):
                st.switch_page("pages/3_Report.py")

    except requests.RequestException as e:
        st.error(f"Backend error: {e}")

elif generate_btn and not topic.strip():
    st.warning("Please enter a market topic first.")

# ── Show last report info if available ───────────────────────────────────────
if st.session_state.report_data and not generate_btn:
    r = st.session_state.report_data
    st.markdown("### Last Generated Report")
    st.markdown(f"""
    <div class="research-card">
        <div style="font-weight:700; font-size:1.1rem; color:#e3f2fd;">{r.get('topic','')}</div>
        <div style="font-size:0.85rem; color:#78909c; margin-top:4px;">Status:
            <span style="color:#81c784;">✓ {r.get('status','').upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📊 Open Report →"):
        st.switch_page("pages/3_Report.py")
