import pytest

from app.config import Settings


def test_local_environment_uses_dev_only_secret_when_missing():
    settings = Settings(_env_file=None, environment="local", secret_key="")

    assert settings.jwt_secret_key == "local-development-only-jwt-secret"


def test_non_local_environment_requires_secret_key():
    settings = Settings(_env_file=None, environment="production", secret_key="")

    with pytest.raises(RuntimeError):
        _ = settings.jwt_secret_key


def test_explicit_secret_key_is_used():
    settings = Settings(_env_file=None, environment="production", secret_key="real-secret")

    assert settings.jwt_secret_key == "real-secret"
