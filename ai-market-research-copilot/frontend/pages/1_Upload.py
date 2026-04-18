import streamlit as st
import requests
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.styles import GLOBAL_CSS
from components.sidebar import render_sidebar

st.set_page_config(page_title="Upload Documents", page_icon="📁", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

render_sidebar()

st.markdown("""
<div class="app-header">
    <div class="app-title">📁 Upload Documents</div>
    <div class="app-subtitle">Upload PDFs, CSVs, or TXT files to build your research knowledge base</div>
</div>
""", unsafe_allow_html=True)

# ── Upload area ───────────────────────────────────────────────────────────────
st.markdown("### Select files to upload")
uploaded_files = st.file_uploader(
    "Drag and drop files here",
    type=["pdf", "csv", "txt", "md"],
    accept_multiple_files=True,
    help="Supported: PDF, CSV, TXT, Markdown. Max 50MB per file.",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected**")

    if st.button("🚀 Index All Files", use_container_width=False):
        progress = st.progress(0, text="Starting...")
        status_box = st.empty()
        results = []

        for i, file in enumerate(uploaded_files):
            status_box.markdown(f"""
            <div class="progress-step step-active">
                ⏳ Parsing and indexing <b>{file.name}</b> ({file.size/1024:.1f} KB)…
            </div>
            """, unsafe_allow_html=True)
            progress.progress((i) / len(uploaded_files), text=f"Processing {file.name}…")

            try:
                response = requests.post(
                    f"{BACKEND}/api/v1/upload/",
                    files={"file": (file.name, file.getvalue(), file.type)},
                    data={"session_id": st.session_state.session_id},
                    timeout=120,
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.session_id = data["session_id"]
                    results.append({"status": "success", **data})
                    # Update sidebar doc list
                    st.session_state.uploaded_docs.append({
                        "filename": data["filename"],
                        "chunk_count": data["chunk_count"],
                        "file_type": data["file_type"],
                    })
                else:
                    results.append({"status": "error", "filename": file.name, "detail": response.json().get("detail", "Unknown error")})
            except Exception as e:
                results.append({"status": "error", "filename": file.name, "detail": str(e)})

        progress.progress(1.0, text="Done!")
        status_box.empty()

        # Results summary
        st.markdown("### Indexing Results")
        for r in results:
            if r["status"] == "success":
                st.markdown(f"""
                <div class="research-card">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="font-size:1.5rem;">✅</span>
                        <div>
                            <div style="font-weight:700; color:#e3f2fd;">{r['filename']}</div>
                            <div style="font-size:0.85rem; color:#78909c;">
                                {r['chunk_count']} chunks indexed · {r['file_type'].upper()}
                            </div>
                            <div style="font-size:0.82rem; color:#4fc3f7; margin-top:2px;">{r['message']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="research-card" style="border-color:rgba(239,83,80,0.4);">
                    <span style="font-size:1.5rem;">❌</span>
                    <b style="color:#ef9a9a;">{r['filename']}</b>
                    <div style="font-size:0.85rem; color:#ef9a9a;">{r.get('detail','')}</div>
                </div>
                """, unsafe_allow_html=True)

        if any(r["status"] == "success" for r in results):
            st.success("Documents indexed! Go to **Generate Report** to create your analysis.")

# ── Already indexed docs ──────────────────────────────────────────────────────
if st.session_state.uploaded_docs:
    st.markdown("---")
    st.markdown("### Indexed in Current Session")
    cols = st.columns(3)
    for i, doc in enumerate(st.session_state.uploaded_docs):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="research-card">
                <div style="font-size:1.3rem;">{'📄' if doc['file_type']=='pdf' else '📊' if doc['file_type']=='csv' else '📝'}</div>
                <div style="font-weight:600; color:#e3f2fd; margin-top:8px;">{doc['filename']}</div>
                <div style="font-size:0.8rem; color:#78909c;">{doc['chunk_count']} chunks · {doc['file_type'].upper()}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Tips ──────────────────────────────────────────────────────────────────────
with st.expander("💡 Tips for best results"):
    st.markdown("""
    - **PDFs**: Market research reports, industry whitepapers, annual reports work great
    - **CSVs**: Pricing data, competitor lists, survey results
    - **TXT/MD**: News articles, analyst notes, interview transcripts
    - Upload **multiple files** — they all get merged into one searchable index
    - The more relevant documents you upload, the more grounded and accurate the report
    """)
