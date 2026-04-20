GLOBAL_CSS = """
<style>
/* ── Glassmorphism Theme ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: radial-gradient(circle at top right, #2a1b4d 0%, #1a1a2e 40%),
                radial-gradient(circle at bottom left, #16213e 0%, #0f3460 100%);
    background-attachment: fixed;
    color: #e0e0e0;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.7) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* ── Generic Glass Container ────────────────────────────────────────── */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

/* ── Research & Stat Cards ──────────────────────────────────────────── */
.research-card, .stat-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(16px);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 24px;
    transition: all 0.3s ease;
}

.research-card:hover {
    transform: translateY(-5px);
    border-color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.08);
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #ff8a00, #e52e71);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── Header Redesign ─────────────────────────────────────────────────── */
.app-header {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 40px;
    margin-bottom: 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: "";
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(229, 46, 113, 0.1) 0%, transparent 70%);
    pointer-events: none;
}

.app-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 10px;
    background: linear-gradient(120deg, #ffffff 0%, #a5a5a5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.app-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 300;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 1rem;
    box-shadow: 0 10px 15px -3px rgba(168, 85, 247, 0.4);
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 20px 25px -5px rgba(168, 85, 247, 0.4);
}

/* ── Input Fields ─────────────────────────────────────────────────────── */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    color: white !important;
    padding: 12px 16px !important;
}

/* ── SWOT Grid ───────────────────────────────────────────────────────── */
.swot-box {
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(5px);
}
.swot-s { border-left: 4px solid #10b981; }
.swot-w { border-left: 4px solid #ef4444; }
.swot-o { border-left: 4px solid #3b82f6; }
.swot-t { border-left: 4px solid #f59e0b; }

/* ── Chat Bubbles ────────────────────────────────────────────────────── */
.chat-user {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 24px 24px 4px 24px;
    padding: 16px 20px;
    margin: 10px 0 10px 15%;
}

.chat-assistant {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 24px 24px 24px 4px;
    padding: 16px 20px;
    margin: 10px 15% 10px 0;
}

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

</style>
"""
