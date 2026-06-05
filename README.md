# Projects — Sudharsan

Personal engineering portfolio. AI/ML systems built end-to-end with FastAPI, React, RAG pipelines, and production-ready architecture.

---

## Projects

| Project | Domain | Stack | Status |
|---------|--------|-------|--------|
| [AI Market Research Copilot](#ai-market-research-copilot) | RAG / Full-Stack AI | FastAPI · Streamlit · FAISS · Gemini | Complete |
| [Zamri — Atelier Analytics Dashboard](#zamri--atelier-leather-co-analytics-dashboard) | Executive Dashboard | React · TypeScript | Prototype |

---

## AI Market Research Copilot

> Full-stack AI tool that turns uploaded documents or a market topic into a professional, citation-backed research report in minutes.

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-vector--search-blue)
![Gemini](https://img.shields.io/badge/Gemini-1.5--Flash-4285F4?logo=google&logoColor=white)

**Stack:** FastAPI · Streamlit · sentence-transformers · FAISS · Gemini 1.5 Flash · SQLite · Docker

**Key capabilities:**
- Upload PDF / CSV / TXT → chunk, embed (sentence-transformers), index (FAISS)
- RAG pipeline generates: competitors, pricing intelligence, market trends, SWOT analysis, PDF report
- Chat interface for follow-up questions against indexed documents
- Runs fully locally — embeddings and vector search on-device, zero cloud cost
- Docker Compose deployment with separate backend and frontend containers
- Ollama fallback for fully offline operation

→ [`ai-market-research-copilot/`](./ai-market-research-copilot/README.md)

---

## Zamri — Atelier Leather Co. Analytics Dashboard

> Executive operations liveboard for a premium leather goods brand. One view covers revenue, funnel leakage, inventory risk, payment reliability, contribution margin, returns, and supplier performance.

![React](https://img.shields.io/badge/React-SPA-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-typed-3178C6?logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?logo=tailwindcss&logoColor=white)

**Stack:** React · TypeScript · Tailwind CSS

**Key capabilities:**
- 7-section SPA: Liveboard, Purchase Funnel, Inventory, Payments, Margins, Returns, Suppliers
- KPI cards, sparklines, waterfall charts, funnel bars, donut charts — all client-side
- "Ask the data" AI assistant for natural-language retail analysis
- Presentation Tweaks panel: accent swapper, module toggles, brand-name editor
- Heritage luxury design system: cream · charcoal · oxblood · brass · serif headlines
- Designed to extend to Shopify / ERP / payment gateway data in production

→ [`Zamri/`](./Zamri/README.md)
