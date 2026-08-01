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
