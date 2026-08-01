"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "Enterprise RAG Intelligence Assistant"
    environment: str = "local"
    secret_key: str = ""
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    seed_demo_on_startup: bool = True
    observability_enabled: bool = True

    auth_db_url: str = f"sqlite:///{DATA_DIR / 'sqlite' / 'auth.db'}"
    enterprise_db_url: str = f"sqlite:///{DATA_DIR / 'sqlite' / 'enterprise.db'}"
    audit_db_url: str = f"sqlite:///{DATA_DIR / 'sqlite' / 'audit.db'}"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_index_path: str = str(DATA_DIR / "sqlite" / "faiss.index")
    vector_metadata_path: str = str(DATA_DIR / "sqlite" / "vector_metadata.json")
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def jwt_secret_key(self) -> str:
        """Require explicit JWT secrets outside local/test environments."""
        if self.secret_key.strip():
            return self.secret_key
        if self.environment.lower() in {"local", "test", "development"}:
            return "local-development-only-jwt-secret"
        raise RuntimeError("SECRET_KEY must be set outside local/test environments.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
