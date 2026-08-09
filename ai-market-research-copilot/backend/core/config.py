from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Market Research Copilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ALLOWED_ORIGINS: str = "http://localhost:8000"
    CORS_ALLOW_CREDENTIALS: bool = False
    API_AUTH_TOKEN: str = ""
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_EXEMPT_PATHS: str = "/health"
    OBSERVABILITY_ENABLED: bool = True
    LLM_INPUT_COST_PER_MILLION: float = 0.0
    LLM_OUTPUT_COST_PER_MILLION: float = 0.0

    # API Keys
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # NVIDIA models
    NVIDIA_MODEL: str = "nvidia/llama-3.3-nemotron-super-49b-v1"    # P1: best available reasoning model
    NVIDIA_EMBEDDING_MODEL: str = "nvidia/nv-embedqa-e5-v5"         # P3: retrieval embeddings (1024-dim)
    NVIDIA_RERANKER_MODEL: str = "nvidia/nv-rerankqa-mistral-4b-v3" # P2: reranker (disabled if endpoint 404)

    # Ollama (local fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # LLM preference: "nvidia", "gemini", or "ollama"
    LLM_PROVIDER: str = "nvidia"
    LLM_FALLBACK_PROVIDERS: str = ""
    LLM_REQUEST_TIMEOUT_SECONDS: float = 90.0
    REPORT_WORKER_COUNT: int = 2
    REPORT_MAX_ACTIVE_JOBS: int = 10

    # Embedding provider: "nvidia" or "local"
    EMBEDDING_PROVIDER: str = "nvidia"

    # RAG retrieval settings
    RERANKER_FETCH_K: int = 20  # candidates fetched from FAISS before reranking
    CHAT_HISTORY_DB_LIMIT: int = 20
    CHAT_HISTORY_CONTEXT_LIMIT: int = 6
    CHAT_DOCUMENT_RELEVANCE_THRESHOLD: float = 0.35
    CHAT_MAX_OUTPUT_TOKENS: int = 900

    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    INDEX_DIR: Path = BASE_DIR / "data" / "indexes"
    DB_DIR: Path = BASE_DIR / "data" / "db"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/db/app.db"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MODEL_CACHE_DIR: Path = BASE_DIR / "data" / "model_cache"

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    # FAISS
    TOP_K_RESULTS: int = 6

    # File upload limits (MB)
    MAX_FILE_SIZE_MB: int = 50

    # Token usage limits
    LLM_MAX_OUTPUT_TOKENS: int = 4096

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]
        return origins or ["http://localhost:8000"]

    @property
    def cors_allow_credentials(self) -> bool:
        return self.CORS_ALLOW_CREDENTIALS and "*" not in self.cors_origins

    @property
    def rate_limit_exempt_paths(self) -> set[str]:
        return {
            path.strip()
            for path in self.RATE_LIMIT_EXEMPT_PATHS.split(",")
            if path.strip()
        }

    @property
    def llm_fallback_providers(self) -> list[str]:
        return [
            provider.strip().lower()
            for provider in self.LLM_FALLBACK_PROVIDERS.split(",")
            if provider.strip()
        ]

    def ensure_dirs(self):
        for d in [
            self.UPLOAD_DIR,
            self.INDEX_DIR,
            self.DB_DIR,
            self.REPORTS_DIR,
            self.MODEL_CACHE_DIR,
        ]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
