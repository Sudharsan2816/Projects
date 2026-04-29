from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.core.config import get_settings
from backend.core.database import init_db
from backend.core.logging import get_logger
from backend.api.routes import upload, research, chat, report

settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Market Research Copilot — RAG + FAISS + Gemini/Ollama",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "token_limits": {
            "max_output_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "chat_history_db_limit": settings.CHAT_HISTORY_DB_LIMIT,
            "chat_context_messages": settings.CHAT_HISTORY_CONTEXT_LIMIT,
        },
    }


# Serve the Marketscope React UI at root.
# Mount AFTER all API routes so /api/v1/... and /health take priority.
_UI_DIR = Path(__file__).parent.parent / "ui"
if _UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
