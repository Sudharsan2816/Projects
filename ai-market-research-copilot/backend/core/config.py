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
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # LLM preference: "gemini" or "ollama"
    LLM_PROVIDER: str = "gemini"

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
