import pytest
from fastapi import HTTPException

from backend.core import auth
from backend.core.config import Settings
from backend.core.rate_limit import InMemoryRateLimiter


def test_api_auth_is_disabled_without_token(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN=""))

    assert auth.require_api_key(x_api_key=None, authorization=None) is None


def test_api_auth_accepts_x_api_key(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN="secret"))

    assert auth.require_api_key(x_api_key="secret", authorization=None) is None


def test_api_auth_accepts_bearer_token(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN="secret"))

    assert auth.require_api_key(x_api_key=None, authorization="Bearer secret") is None


def test_api_auth_rejects_missing_or_wrong_token(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN="secret"))

    with pytest.raises(HTTPException) as exc:
        auth.require_api_key(x_api_key="wrong", authorization=None)

    assert exc.value.status_code == 401


def test_rate_limiter_blocks_after_window_capacity():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=10)

    assert limiter.allow_request("client", now=100.0) == (True, 0)
    assert limiter.allow_request("client", now=101.0) == (True, 0)
    allowed, retry_after = limiter.allow_request("client", now=102.0)

    assert allowed is False
    assert retry_after > 0


def test_rate_limiter_allows_after_window_expires():
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=10)

    assert limiter.allow_request("client", now=100.0) == (True, 0)
    assert limiter.allow_request("client", now=111.0) == (True, 0)
