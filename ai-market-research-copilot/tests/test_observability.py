from fastapi.testclient import TestClient

from backend.core.observability import (
    estimate_tokens,
    metrics,
    query_fingerprint,
    record_provider_call,
)
from backend.main import app


def test_request_id_and_server_timing_headers_are_returned():
    metrics.reset()
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"
    assert response.headers["Server-Timing"].startswith("app;dur=")
    assert metrics.snapshot()["requests"]["count"] >= 1


def test_metrics_endpoint_reports_process_local_counters():
    metrics.reset()
    with TestClient(app) as client:
        client.get("/health")
        response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    assert response.json()["requests"]["count"] >= 1


def test_provider_usage_estimation_updates_metrics():
    metrics.reset()
    record_provider_call(
        provider="fixture",
        model="fixture-model",
        prompt="abcd" * 10,
        response="answer",
        duration_ms=12.5,
        success=True,
    )

    provider_metrics = metrics.snapshot()["providers"]
    assert estimate_tokens("abcd") == 1
    assert provider_metrics["calls"] == 1
    assert provider_metrics["estimated_input_tokens"] == 10


def test_query_fingerprint_is_stable_without_exposing_query():
    fingerprint = query_fingerprint("confidential market question")

    assert fingerprint == query_fingerprint("confidential market question")
    assert "confidential" not in fingerprint
    assert len(fingerprint) == 12
