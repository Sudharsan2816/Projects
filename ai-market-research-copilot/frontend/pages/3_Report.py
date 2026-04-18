import streamlit as st
import requests
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from components.styles import GLOBAL_CSS
from components.sidebar import render_sidebar
from components.charts import competitor_radar, pricing_bar, trends_impact_pie

st.set_page_config(page_title="View Report", page_icon="📊", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []
if "report_data" not in st.session_state:
    st.session_state.report_data = None

render_sidebar()

st.markdown("""
<div class="app-header">
    <div class="app-title">📊 Market Research Report</div>
    <div class="app-subtitle">AI-generated analysis with competitor intelligence, pricing insights, trends & SWOT</div>
</div>
""", unsafe_allow_html=True)

report = st.session_state.report_data

if not report:
    st.info("No report loaded yet. Generate one from the **Generate Report** page.")
    if st.button("→ Go Generate a Report"):
        st.switch_page("pages/2_Research.py")
    st.stop()

topic = report.get("topic", "")
st.markdown(f"## {topic}")

# ── Download PDF ───────────────────────────────────────────────────────────────
report_id = report.get("id")
col_dl, col_refresh = st.columns([1, 5])
with col_dl:
    if st.button("⬇️ Download PDF", use_container_width=True):
        try:
            r = requests.get(f"{BACKEND}/api/v1/report/{report_id}/download", timeout=30)
            if r.status_code == 200:
                st.download_button(
                    label="Save PDF",
                    data=r.content,
                    file_name=f"market_research_{topic[:30].replace(' ','_')}.pdf",
                    mime="application/pdf",
                )
            else:
                st.error("PDF not ready yet.")
        except Exception as e:
            st.error(f"Download error: {e}")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Executive Summary",
    "🏢 Competitors",
    "💰 Pricing & Trends",
    "⚔️ SWOT Analysis",
])

# ── Tab 1: Executive Summary ──────────────────────────────────────────────────
with tab1:
    summary = report.get("executive_summary", "")
    if summary:
        st.markdown(f"""
        <div class="research-card">
            {summary.replace(chr(10), '<br/>')}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No executive summary available.")

# ── Tab 2: Competitors ────────────────────────────────────────────────────────
with tab2:
    competitors = report.get("competitors") or []

    if competitors:
        # Radar chart
        st.plotly_chart(competitor_radar(competitors), use_container_width=True)

        st.markdown("### Competitor Profiles")
        for comp in competitors:
            name = comp.get("name", "")
            pos = comp.get("market_position", "")
            pos_class = pos.replace(" ", "") if pos in ["Leader", "Challenger", "Niche", "Follower"] else "Follower"

            col_a, col_b = st.columns([2, 3])
            with col_a:
                strengths_html = "".join(f"<li>{s}</li>" for s in comp.get("strengths", []))
                st.markdown(f"""
                <div class="comp-card">
                    <div>
                        <span class="comp-name">{name}</span>
                        <span class="comp-position pos-{pos_class}">{pos}</span>
                    </div>
                    <div style="font-size:0.85rem; color:#90a4ae; margin-top:8px;">{comp.get('description','')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                sw_col1, sw_col2 = st.columns(2)
                with sw_col1:
                    st.markdown("**Strengths**")
                    for s in comp.get("strengths", []):
                        st.markdown(f"✅ {s}")
                with sw_col2:
                    st.markdown("**Weaknesses**")
                    for w in comp.get("weaknesses", []):
                        st.markdown(f"⚠️ {w}")
            st.divider()
    else:
        st.info("No competitor data available.")

# ── Tab 3: Pricing & Trends ───────────────────────────────────────────────────
with tab3:
    pricing = report.get("pricing_insights") or []
    trends = report.get("market_trends") or []

    col_p, col_t = st.columns([1, 1])

    with col_p:
        st.markdown("### Pricing Intelligence")
        if pricing:
            st.plotly_chart(pricing_bar(pricing), use_container_width=True)
            for p in pricing:
                st.markdown(f"""
                <div class="research-card">
                    <div style="font-weight:700; color:#ffb74d;">{p.get('segment','')}</div>
                    <div style="font-size:1.1rem; color:#4fc3f7; font-weight:600;">{p.get('price_range','')}</div>
                    <div style="font-size:0.82rem; color:#90a4ae; margin-top:4px;">
                        Players: {', '.join(p.get('key_players',[]))}
                    </div>
                    <div style="font-size:0.85rem; color:#cdd9e8; margin-top:6px;">{p.get('notes','')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No pricing data.")

    with col_t:
        st.markdown("### Market Trends")
        if trends:
            st.plotly_chart(trends_impact_pie(trends), use_container_width=True)
            for t in trends:
                impact = t.get("impact", "Medium")
                st.markdown(f"""
                <div class="trend-card impact-{impact}">
                    <div>
                        <span style="font-weight:700; color:#e3f2fd;">{t.get('trend','')}</span>
                        <span class="impact-badge badge-{impact}">{impact} Impact</span>
                        <span style="font-size:0.78rem; color:#78909c; margin-left:8px;">{t.get('timeframe','')}</span>
                    </div>
                    <div style="font-size:0.86rem; color:#b0bec5; margin-top:6px;">{t.get('description','')}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No trends data.")

# ── Tab 4: SWOT ────────────────────────────────────────────────────────────────
with tab4:
    swot = report.get("swot_analysis") or {}

    if swot:
        def _swot_items(items):
            return "".join(f'<div class="swot-item">{i}</div>' for i in items)

        st.markdown(f"""
        <div class="swot-grid">
            <div class="swot-box swot-s">
                <div class="swot-title">💪 Strengths</div>
                {_swot_items(swot.get('strengths', []))}
            </div>
            <div class="swot-box swot-w">
                <div class="swot-title">⚠️ Weaknesses</div>
                {_swot_items(swot.get('weaknesses', []))}
            </div>
            <div class="swot-box swot-o">
                <div class="swot-title">🚀 Opportunities</div>
                {_swot_items(swot.get('opportunities', []))}
            </div>
            <div class="swot-box swot-t">
                <div class="swot-title">🛡️ Threats</div>
                {_swot_items(swot.get('threats', []))}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No SWOT data available.")
