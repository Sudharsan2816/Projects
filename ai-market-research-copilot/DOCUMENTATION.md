# 🔬 AI Market Research Copilot - Detailed Documentation

## 1. Project Overview
The **AI Market Research Copilot** is a high-performance, full-stack application designed to automate the heavy lifting of market research. It allows users to upload proprietary documents (PDFs, CSVs, TXT) or specify a market topic to generate deep-dive intelligence reports.

### Use Cases
- **Venture Capital / Private Equity:** Quickly screen a new market segment before a deep-dive.
- **Product Management:** Analyze competitors and pricing trends to inform product roadmaps.
- **Sales & Marketing:** Generate talking points and SWOT analyses for prospective client industries.
- **Founders:** Validate startup ideas by understanding the existing landscape and gaps.

---

## 2. End-to-End Principles (How it Works)

The system operates on the **RAG (Retrieval-Augmented Generation)** principle:

1.  **Ingestion & Parsing:** Documents are uploaded and parsed into raw text.
2.  **Chunking:** Large texts are broken into smaller "chunks" (approx. 500-1000 characters) with overlap to preserve context.
3.  **Embedding:** Each chunk is converted into a numerical vector using a local embedding model (`all-MiniLM-L6-v2`).
4.  **Vector Storage:** These vectors are stored in a FAISS index, enabling "semantic search" (finding text by meaning, not just keywords).
5.  **Research Job:**
    - The system identifies key research areas: Competitors, Pricing, Trends, and SWOT.
    - For each area, it queries the Vector DB for relevant context.
    - It sends retrieved context plus a specialized prompt to NVIDIA NIM. Optional fallbacks must be explicitly enabled.
    - The job persists its progress in SQLite and resumes polling after navigation or browser tab changes.
6.  **Synthesis:** The LLM synthesizes the raw data into structured insights.
7.  **Reporting:** Results are stored in a SQLite database and can be exported as a professional PDF.

---

## 3. Project Structure

### Backend (FastAPI)
- `api/routes/`: Defines the REST API endpoints for uploading, researching, and chatting.
- `services/`: The core logic "brains" of the app.
    - `document_parser.py`: Extracts text from various formats.
    - `vector_store.py`: Manages the local FAISS index.
    - `llm.py`: NVIDIA NIM interface with optional Gemini and Ollama fallbacks.
    - `research_engine.py`: Orchestrates the multi-step research process.
- `models/`: Database schemas (SQLAlchemy) and API data shapes (Pydantic).

### Frontend (React)
- `ui/app.jsx`: Application state, report-job recovery, and navigation.
- `ui/page-*.jsx`: Upload, research, report, and chat workspaces.
- `ui/styles.css`: Responsive design tokens and accessible interaction states.

---

## 4. Supported Formats

### Input Formats
- **PDF (.pdf):** Standard reports, whitepapers, or ebooks.
- **CSV (.csv):** Structured data (e.g., pricing lists, competitor feature sets).
- **TXT (.txt) / Markdown (.md):** Raw notes or web scrapes.

### Output Formats
- **Interactive Dashboard:** Real-time charts and data tables in the browser.
- **PDF Report:** A downloadable, branded document suitable for stakeholders.
- **JSON:** The underlying data is accessible via the API for integration into other tools.

---

## 5. How to Use

### Step 1: Upload Knowledge
Go to the **Upload** page. Drag and drop your industry reports or internal data. The system will "index" them immediately.

### Step 2: Define the Topic
Go to the **Research** page. Enter the specific market you want to analyze (e.g., "The luxury watch market in Southeast Asia").

### Step 3: Generate Intelligence
Click "Generate Report". The backend will perform multiple AI-driven queries. Once finished, you'll see:
- **Competitor Profiles:** Rankings and positioning.
- **Pricing Intelligence:** Segment-wise cost breakdowns.
- **Market Trends:** Impact and timeframe analysis.
- **SWOT Analysis:** Strengths, Weaknesses, Opportunities, and Threats.

### Step 4: Interactive Chat
Use the **Chat** page to ask follow-up questions like *"What are the specific pricing tiers for Company X?"* or *"Summarize the environmental trends mentioned in the uploads."*

---

## 6. Technical Requirements
- **Python 3.11+**
- **LLM:** A working NVIDIA API key. Gemini and Ollama are disabled unless explicitly added to `LLM_FALLBACK_PROVIDERS`.
- **Local Resources:** The embedding model and vector store run locally, requiring ~2GB of RAM.
