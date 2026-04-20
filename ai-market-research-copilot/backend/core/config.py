from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Market Research Copilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API Keys
    GEMINI_API_KEY: str = ""
    NVIDIA_API_KEY: str = "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"
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

    # Embedding provider: "nvidia" or "local"
    EMBEDDING_PROVIDER: str = "nvidia"

    # RAG retrieval settings
    RERANKER_FETCH_K: int = 20  # candidates fetched from FAISS before reranking

    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    INDEX_DIR: Path = BASE_DIR / "data" / "indexes"
    DB_DIR: Path = BASE_DIR / "data" / "db"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/db/app.db"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    # FAISS
    TOP_K_RESULTS: int = 6

    # File upload limits (MB)
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_dirs(self):
        for d in [self.UPLOAD_DIR, self.INDEX_DIR, self.DB_DIR, self.REPORTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
