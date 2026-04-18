GLOBAL_CSS = """
<style>
/* ── Base ─────────────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a2a4a 100%);
    color: #e0e6f0;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #112244 100%);
    border-right: 1px solid #1e3a5f;
}
[data-testid="stSidebar"] * { color: #cdd9e8 !important; }

/* ── Cards ────────────────────────────────────────────────────────────── */
.research-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 20px 24px;
    margin: 10px 0;
    backdrop-filter: blur(10px);
}
.stat-card {
    background: linear-gradient(135deg, rgba(2,136,209,0.15), rgba(26,35,126,0.2));
    border: 1px solid rgba(2,136,209,0.3);
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.stat-number {
    font-size: 2.2rem;
    font-weight: 800;
    color: #4fc3f7;
}
.stat-label {
    font-size: 0.85rem;
    color: #90a4ae;
    margin-top: 4px;
}

/* ── SWOT ─────────────────────────────────────────────────────────────── */
.swot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 10px 0; }
.swot-box { border-radius: 10px; padding: 16px 18px; }
.swot-s { background: rgba(46,125,50,0.2); border: 1px solid rgba(46,125,50,0.5); }
.swot-w { background: rgba(198,40,40,0.2); border: 1px solid rgba(198,40,40,0.5); }
.swot-o { background: rgba(2,119,189,0.2); border: 1px solid rgba(2,119,189,0.5); }
.swot-t { background: rgba(245,124,0,0.2); border: 1px solid rgba(245,124,0,0.5); }
.swot-title { font-weight: 700; font-size: 1rem; margin-bottom: 10px; }
.swot-s .swot-title { color: #81c784; }
.swot-w .swot-title { color: #ef9a9a; }
.swot-o .swot-title { color: #4fc3f7; }
.swot-t .swot-title { color: #ffcc80; }
.swot-item { font-size: 0.875rem; color: #cdd9e8; padding: 3px 0; }
.swot-item::before { content: "• "; }

/* ── Competitor card ─────────────────────────────────────────────────── */
.comp-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.comp-card:hover { border-color: rgba(2,136,209,0.5); }
.comp-name { font-size: 1.1rem; font-weight: 700; color: #e3f2fd; }
.comp-position {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 10px;
}
.pos-Leader { background: #1b5e20; color: #a5d6a7; }
.pos-Challenger { background: #0d47a1; color: #90caf9; }
.pos-Niche { background: #e65100; color: #ffcc80; }
.pos-Follower { background: #37474f; color: #b0bec5; }

/* ── Trend badge ─────────────────────────────────────────────────────── */
.trend-card {
    background: rgba(255,255,255,0.04);
    border-left: 4px solid #0288d1;
    border-radius: 0 10px 10px 0;
    padding: 12px 18px;
    margin: 8px 0;
}
.impact-High { border-left-color: #e53935; }
.impact-Medium { border-left-color: #fb8c00; }
.impact-Low { border-left-color: #43a047; }
.impact-badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-left: 8px;
}
.badge-High { background: rgba(229,57,53,0.25); color: #ef9a9a; }
.badge-Medium { background: rgba(251,140,0,0.25); color: #ffcc80; }
.badge-Low { background: rgba(67,160,71,0.25); color: #a5d6a7; }

/* ── Chat ─────────────────────────────────────────────────────────────── */
.chat-user {
    background: rgba(2,136,209,0.15);
    border: 1px solid rgba(2,136,209,0.3);
    border-radius: 12px 12px 2px 12px;
    padding: 12px 16px;
    margin: 8px 0 8px 20%;
    color: #e3f2fd;
}
.chat-assistant {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px 12px 12px 2px;
    padding: 12px 16px;
    margin: 8px 20% 8px 0;
    color: #e0e6f0;
}
.source-chip {
    display: inline-block;
    background: rgba(2,119,189,0.2);
    border: 1px solid rgba(2,119,189,0.4);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: #81d4fa;
    margin: 3px 4px 3px 0;
}

/* ── Progress ─────────────────────────────────────────────────────────── */
.progress-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    color: #90a4ae;
    font-size: 0.9rem;
}
.step-done { color: #81c784; }
.step-active { color: #4fc3f7; font-weight: 600; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0288d1, #1565c0);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

/* ── Header ──────────────────────────────────────────────────────────── */
.app-header {
    background: linear-gradient(90deg, #0d47a1, #01579b);
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
}
.app-title { font-size: 1.9rem; font-weight: 800; color: white; margin: 0; }
.app-subtitle { color: #90caf9; font-size: 1rem; margin-top: 4px; }
</style>
"""
