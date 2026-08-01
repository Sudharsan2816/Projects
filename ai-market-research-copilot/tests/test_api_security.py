from fastapi.testclient import TestClient

from backend.core import auth
from backend.core.config import Settings
from backend.main import app


def test_health_stays_public_when_api_auth_is_enabled(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN="secret"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_api_route_requires_credentials_when_api_auth_is_enabled(monkeypatch):
    monkeypatch.setattr(auth, "settings", Settings(_env_file=None, API_AUTH_TOKEN="secret"))

    with TestClient(app) as client:
        response = client.get("/api/v1/upload/test-session/documents")

    assert response.status_code == 401
