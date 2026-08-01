from app.observability import metrics, query_fingerprint
from tests.conftest import login


def test_request_id_and_latency_headers(client):
    response = client.get("/health", headers={"X-Request-ID": "enterprise-test-request"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "enterprise-test-request"
    assert response.headers["Server-Timing"].startswith("app;dur=")


def test_metrics_are_role_protected(client):
    engineer_token = login(client, "engineer", "EngineerPass123!")
    denied = client.get("/metrics", headers={"Authorization": f"Bearer {engineer_token}"})
    assert denied.status_code == 403

    admin_token = login(client, "admin", "AdminPass123!")
    allowed = client.get("/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert allowed.status_code == 200
    assert "requests" in allowed.json()


def test_query_fingerprint_is_stable_and_redacted():
    fingerprint = query_fingerprint("employee salary details")

    assert fingerprint == query_fingerprint("employee salary details")
    assert "salary" not in fingerprint
    assert len(fingerprint) == 12


def test_metrics_registry_tracks_outcomes():
    metrics.reset()
    metrics.record_outcome("access_denied")

    assert metrics.snapshot()["query_outcomes"] == {"access_denied": 1}
