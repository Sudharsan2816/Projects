from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import chat, report, research, upload
from backend.core.auth import require_api_key
from backend.core.config import get_settings
from backend.core.database import init_db
from backend.core.logging import get_logger
from backend.core.observability import metrics, request_observability_middleware
from backend.core.rate_limit import rate_limit_middleware
from backend.services.llm import configured_providers

settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialised")
    resumed = research.resume_incomplete_reports()
    if resumed:
        logger.info("Resumed %s incomplete report jobs", resumed)
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
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit_middleware)
if settings.OBSERVABILITY_ENABLED:
    app.middleware("http")(request_observability_middleware)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# Routers
protected_dependencies = [Depends(require_api_key)]
app.include_router(upload.router, prefix="/api/v1", dependencies=protected_dependencies)
app.include_router(research.router, prefix="/api/v1", dependencies=protected_dependencies)
app.include_router(chat.router, prefix="/api/v1", dependencies=protected_dependencies)
app.include_router(report.router, prefix="/api/v1", dependencies=protected_dependencies)


@app.get("/api/v1/metrics", dependencies=protected_dependencies)
def application_metrics():
    """Expose process-local operational metrics for demos and single-node deployments."""
    return metrics.snapshot()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "configured_providers": configured_providers(),
        "auth_enabled": bool(settings.API_AUTH_TOKEN),
        "rate_limit": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "requests": settings.RATE_LIMIT_REQUESTS,
            "window_seconds": settings.RATE_LIMIT_WINDOW_SECONDS,
        },
        "token_limits": {
            "max_output_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "chat_max_output_tokens": settings.CHAT_MAX_OUTPUT_TOKENS,
            "chat_history_db_limit": settings.CHAT_HISTORY_DB_LIMIT,
            "chat_context_messages": settings.CHAT_HISTORY_CONTEXT_LIMIT,
        },
    }


# Serve the Marketscope React UI at root.
# Mount AFTER all API routes so /api/v1/... and /health take priority.
_UI_DIR = Path(__file__).parent.parent / "ui"
if _UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIR), html=True), name="ui")
