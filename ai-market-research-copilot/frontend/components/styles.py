GLOBAL_CSS = """
<style>
/* Suno-inspired visual system: cinematic dark, glow gradients, rounded cards */
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg-0: #07090f;
    --bg-1: #0d1220;
    --bg-2: #151c2f;
    --card: rgba(18, 24, 42, 0.72);
    --card-border: rgba(255, 255, 255, 0.12);
    --text: #f5f7ff;
    --muted: #9fa8c6;
    --accent-1: #7c3aed;
    --accent-2: #3b82f6;
    --accent-3: #ec4899;
}

@keyframes auroraShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes fadeSlideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes blinkCaret {
    0%, 49% { opacity: 1; }
    50%, 100% { opacity: 0.25; }
}

@keyframes pulseGlow {
    0% { box-shadow: 0 0 0 rgba(124, 58, 237, 0); }
    50% { box-shadow: 0 0 32px rgba(124, 58, 237, 0.36); }
    100% { box-shadow: 0 0 0 rgba(124, 58, 237, 0); }
}

@keyframes shimmerSweep {
    0% { transform: translateX(-120%); }
    100% { transform: translateX(120%); }
}

html,
body,
[data-testid="stAppViewContainer"] {
    font-family: 'Manrope', sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at 10% 5%, rgba(124, 58, 237, 0.28), transparent 34%),
        radial-gradient(circle at 85% 12%, rgba(59, 130, 246, 0.22), transparent 28%),
        radial-gradient(circle at 50% 82%, rgba(236, 72, 153, 0.17), transparent 32%),
        linear-gradient(135deg, var(--bg-0) 0%, var(--bg-1) 52%, var(--bg-2) 100%);
    background-size: 140% 140%;
    background-attachment: fixed;
    animation: auroraShift 22s ease infinite;
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(9, 12, 24, 0.92), rgba(12, 16, 28, 0.82)) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(14px);
}

[data-testid="block-container"] {
    padding-top: 2rem;
}

h1, h2, h3, h4, h5 {
    letter-spacing: -0.02em;
}

.app-header {
    position: relative;
    overflow: hidden;
    border-radius: 28px;
    padding: 2.6rem 2.4rem;
    margin-bottom: 1.4rem;
    background:
        linear-gradient(120deg, rgba(124, 58, 237, 0.24), rgba(59, 130, 246, 0.18) 55%, rgba(236, 72, 153, 0.20));
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 24px 60px rgba(3, 7, 18, 0.55);
    animation: fadeSlideIn 0.5s ease-out;
}

.app-header::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 38%);
    pointer-events: none;
}

.app-title {
    position: relative;
    z-index: 1;
    font-size: clamp(1.8rem, 3.4vw, 2.7rem);
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 0.5rem;
}

.app-subtitle {
    position: relative;
    z-index: 1;
    max-width: 860px;
    color: #d4ddf9;
    font-size: 1rem;
    font-weight: 500;
}

.research-card,
.stat-card,
.comp-card,
.trend-card,
.swot-box {
    border-radius: 22px;
    border: 1px solid var(--card-border);
    background: var(--card);
    backdrop-filter: blur(10px);
    box-shadow: 0 14px 32px rgba(6, 10, 20, 0.45);
}

.research-card,
.stat-card,
.comp-card,
.trend-card {
    padding: 1.1rem 1.2rem;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    animation: fadeSlideIn 0.45s ease-out;
    position: relative;
    overflow: hidden;
}

.reveal-1 { animation-delay: 0.06s; }
.reveal-2 { animation-delay: 0.14s; }
.reveal-3 { animation-delay: 0.22s; }
.reveal-4 { animation-delay: 0.30s; }

.research-card:hover,
.comp-card:hover,
.trend-card:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.24);
    box-shadow: 0 16px 38px rgba(3, 7, 18, 0.56);
}

.research-card::after,
.stat-card::after {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 40%;
    height: 100%;
    background: linear-gradient(110deg, transparent, rgba(255, 255, 255, 0.08), transparent);
    transform: translateX(-120%);
}

.research-card:hover::after,
.stat-card:hover::after {
    animation: shimmerSweep 0.9s ease;
}

.stat-number {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.1;
    background: linear-gradient(100deg, #ffffff 0%, #b5c3ff 45%, #f8c7f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-label {
    margin-top: 0.28rem;
    color: var(--muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
}

.stButton > button {
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.14);
    background: linear-gradient(135deg, var(--accent-1), var(--accent-2) 66%, var(--accent-3));
    color: white;
    padding: 0.56rem 1.2rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    box-shadow: 0 12px 24px rgba(76, 56, 190, 0.4);
    transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);
    filter: brightness(1.06);
    box-shadow: 0 16px 28px rgba(78, 62, 193, 0.45);
}

.stButton > button:focus-visible {
    outline: none;
    animation: pulseGlow 1.2s ease;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    color: var(--text) !important;
    background: rgba(255, 255, 255, 0.06) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(147, 197, 253, 0.85) !important;
    box-shadow: 0 0 0 1px rgba(147, 197, 253, 0.45) !important;
}

div[data-baseweb="tab-list"] {
    gap: 0.4rem;
    margin-bottom: 0.9rem;
}

button[data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #cdd5ef;
    font-weight: 700;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(124, 58, 237, 0.44), rgba(59, 130, 246, 0.36));
    border-color: rgba(147, 197, 253, 0.55);
    color: #ffffff;
}

.progress-step {
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.05);
    border-radius: 14px;
    padding: 0.72rem 0.88rem;
    margin-bottom: 0.48rem;
    color: #d4dcf3;
    animation: fadeSlideIn 0.25s ease-out;
}

.step-active {
    border-color: rgba(147, 197, 253, 0.52);
    background: rgba(59, 130, 246, 0.16);
    animation: pulseGlow 2.2s ease-in-out infinite;
}

.step-done {
    border-color: rgba(110, 231, 183, 0.58);
    background: rgba(16, 185, 129, 0.16);
}

.chat-user {
    margin: 0.65rem 0 0.65rem 14%;
    padding: 0.88rem 1.02rem;
    border-radius: 16px 16px 8px 16px;
    border: 1px solid rgba(125, 211, 252, 0.22);
    background: linear-gradient(130deg, rgba(59, 130, 246, 0.20), rgba(14, 116, 144, 0.18));
    animation: fadeSlideIn 0.25s ease-out;
}

.chat-assistant {
    margin: 0.65rem 14% 0.65rem 0;
    padding: 0.88rem 1.02rem;
    border-radius: 16px 16px 16px 8px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.06);
    animation: fadeSlideIn 0.28s ease-out;
}

.typing-caret {
    display: inline-block;
    margin-left: 0.22rem;
    color: #c7d2fe;
    animation: blinkCaret 0.9s steps(1) infinite;
}

.source-chip {
    display: inline-block;
    margin: 0.18rem 0.28rem 0 0;
    border-radius: 999px;
    padding: 0.16rem 0.56rem;
    font-size: 0.73rem;
    color: #dbeafe;
    border: 1px solid rgba(147, 197, 253, 0.34);
    background: rgba(30, 64, 175, 0.30);
}

.swot-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.8rem;
}

.swot-box {
    padding: 0.95rem 1.05rem;
}

.swot-title {
    font-weight: 800;
    margin-bottom: 0.62rem;
}

.swot-item {
    padding: 0.4rem 0.52rem;
    border-radius: 10px;
    margin-bottom: 0.34rem;
    background: rgba(255, 255, 255, 0.06);
    color: #d8dff7;
}

.swot-s { border-left: 4px solid #10b981; }
.swot-w { border-left: 4px solid #f87171; }
.swot-o { border-left: 4px solid #60a5fa; }
.swot-t { border-left: 4px solid #fbbf24; }

.impact-badge {
    margin-left: 0.4rem;
    border-radius: 999px;
    font-size: 0.69rem;
    font-weight: 800;
    padding: 0.12rem 0.44rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.badge-High {
    color: #fecaca;
    background: rgba(220, 38, 38, 0.3);
}

.badge-Medium {
    color: #fde68a;
    background: rgba(217, 119, 6, 0.3);
}

.badge-Low {
    color: #bfdbfe;
    background: rgba(37, 99, 235, 0.3);
}

.pos-Leader,
.pos-Challenger,
.pos-Niche,
.pos-Follower {
    font-size: 0.72rem;
    margin-left: 0.5rem;
    border-radius: 999px;
    padding: 0.14rem 0.46rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.pos-Leader { color: #bbf7d0; background: rgba(22, 163, 74, 0.25); }
.pos-Challenger { color: #fde68a; background: rgba(217, 119, 6, 0.24); }
.pos-Niche { color: #bfdbfe; background: rgba(59, 130, 246, 0.24); }
.pos-Follower { color: #ddd6fe; background: rgba(109, 40, 217, 0.24); }

[data-testid="stAlert"] {
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

[data-testid="stMetric"] {
    animation: fadeSlideIn 0.35s ease-out;
}

::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.04); }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.22); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

@media (max-width: 900px) {
    .swot-grid {
        grid-template-columns: 1fr;
    }
    .app-header {
        padding: 1.5rem 1.1rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation: none !important;
        transition: none !important;
    }
}

</style>
"""
