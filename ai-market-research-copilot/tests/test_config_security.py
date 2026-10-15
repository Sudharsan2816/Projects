from backend.core.config import Settings


def test_provider_keys_are_not_hardcoded_defaults():
    settings = Settings(_env_file=None)

    assert settings.NVIDIA_API_KEY == ""
    assert settings.GEMINI_API_KEY == ""
    assert settings.LLM_PROVIDER == "nvidia"
    assert settings.llm_fallback_providers == []


def test_cors_defaults_are_not_wildcard_with_credentials():
    settings = Settings(_env_file=None)

    assert "*" not in settings.cors_origins
    assert settings.cors_allow_credentials is False


def test_wildcard_cors_disables_credentials_even_if_requested():
    settings = Settings(
        _env_file=None,
        CORS_ALLOWED_ORIGINS="*",
        CORS_ALLOW_CREDENTIALS=True,
    )

    assert settings.cors_origins == ["*"]
    assert settings.cors_allow_credentials is False


def test_vercel_uses_writable_temporary_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    settings = Settings(_env_file=None)
    runtime_root = tmp_path / "market-research-copilot"

    assert settings.UPLOAD_DIR == runtime_root / "data" / "uploads"
    assert settings.INDEX_DIR == runtime_root / "data" / "indexes"
    assert settings.DB_DIR == runtime_root / "data" / "db"
    assert settings.REPORTS_DIR == runtime_root / "reports"
    assert settings.MODEL_CACHE_DIR == runtime_root / "data" / "model_cache"
    assert settings.DATABASE_URL == f"sqlite:///{runtime_root / 'data' / 'db' / 'app.db'}"
