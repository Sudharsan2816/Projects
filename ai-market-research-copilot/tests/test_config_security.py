from backend.core.config import Settings


def test_provider_keys_are_not_hardcoded_defaults():
    settings = Settings(_env_file=None)

    assert settings.NVIDIA_API_KEY == ""
    assert settings.GEMINI_API_KEY == ""
