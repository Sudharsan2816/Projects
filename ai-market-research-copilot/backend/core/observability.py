"""Request, retrieval, and provider observability primitives."""

from __future__ import annotations

from collections import Counter
from contextvars import ContextVar, Token
from hashlib import sha256
from threading import Lock
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from fastapi import Request, Response

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


class MetricsRegistry:
    """Small process-local metrics registry for portfolio and local deployments."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", Lock()):
            self.request_count = 0
            self.request_latency_ms = 0.0
            self.status_codes: Counter[str] = Counter()
            self.retrieval_count = 0
            self.retrieval_latency_ms = 0.0
            self.retrieved_candidates = 0
            self.selected_chunks = 0
            self.provider_calls = 0
            self.provider_errors = 0
            self.estimated_input_tokens = 0
            self.estimated_output_tokens = 0
            self.estimated_cost_usd = 0.0

    def record_request(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self.request_count += 1
            self.request_latency_ms += duration_ms
            self.status_codes[str(status_code)] += 1

    def record_retrieval(
        self,
        duration_ms: float,
        candidate_count: int,
        selected_count: int,
    ) -> None:
        with self._lock:
            self.retrieval_count += 1
            self.retrieval_latency_ms += duration_ms
            self.retrieved_candidates += candidate_count
            self.selected_chunks += selected_count

    def record_provider(
        self,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        success: bool,
    ) -> None:
        with self._lock:
            self.provider_calls += 1
            self.provider_errors += 0 if success else 1
            self.estimated_input_tokens += input_tokens
            self.estimated_output_tokens += output_tokens
            self.estimated_cost_usd += estimated_cost_usd

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            request_avg = (
                self.request_latency_ms / self.request_count if self.request_count else 0.0
            )
            retrieval_avg = (
                self.retrieval_latency_ms / self.retrieval_count
                if self.retrieval_count
                else 0.0
            )
            return {
                "requests": {
                    "count": self.request_count,
                    "average_latency_ms": round(request_avg, 2),
                    "status_codes": dict(self.status_codes),
                },
                "retrieval": {
                    "count": self.retrieval_count,
                    "average_latency_ms": round(retrieval_avg, 2),
                    "candidate_chunks": self.retrieved_candidates,
                    "selected_chunks": self.selected_chunks,
                },
                "providers": {
                    "calls": self.provider_calls,
                    "errors": self.provider_errors,
                    "estimated_input_tokens": self.estimated_input_tokens,
                    "estimated_output_tokens": self.estimated_output_tokens,
                    "estimated_cost_usd": round(self.estimated_cost_usd, 6),
                },
            }


metrics = MetricsRegistry()


def get_request_id() -> str:
    return _request_id.get()


def set_request_id(value: str) -> Token[str]:
    return _request_id.set(value)


def reset_request_id(token: Token[str]) -> None:
    _request_id.reset(token)


def query_fingerprint(query: str) -> str:
    """Identify a query in traces without logging its potentially sensitive text."""
    return sha256(query.encode("utf-8")).hexdigest()[:12]


def estimate_tokens(text: str) -> int:
    """Conservative provider-independent token estimate for cost telemetry."""
    return max(1, (len(text) + 3) // 4) if text else 0


def record_provider_call(
    *,
    provider: str,
    model: str,
    prompt: str,
    response: str,
    duration_ms: float,
    success: bool,
) -> None:
    from backend.core.config import get_settings
    from backend.core.logging import get_logger

    settings = get_settings()
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response)
    estimated_cost = (
        input_tokens * settings.LLM_INPUT_COST_PER_MILLION
        + output_tokens * settings.LLM_OUTPUT_COST_PER_MILLION
    ) / 1_000_000
    metrics.record_provider(input_tokens, output_tokens, estimated_cost, success)
    get_logger("provider").info(
        "provider_call",
        extra={
            "event": "provider_call",
            "provider": provider,
            "model": model,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": round(estimated_cost, 6),
        },
    )


def record_retrieval_trace(
    *,
    session_id: str,
    query: str,
    duration_ms: float,
    candidate_count: int,
    selected: list[tuple[dict[str, Any], float]],
) -> None:
    from backend.core.logging import get_logger

    metrics.record_retrieval(duration_ms, candidate_count, len(selected))
    get_logger("retrieval").info(
        "retrieval_trace",
        extra={
            "event": "retrieval_trace",
            "session_id": session_id,
            "query_fingerprint": query_fingerprint(query),
            "query_length": len(query),
            "duration_ms": round(duration_ms, 2),
            "candidate_count": candidate_count,
            "selected_count": len(selected),
            "sources": [
                {
                    "source": chunk.get("source", "unknown"),
                    "chunk_index": chunk.get("chunk_index", 0),
                    "score": round(float(score), 4),
                }
                for chunk, score in selected
            ],
        },
    )


async def request_observability_middleware(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    """Attach a request ID and emit one structured latency record per request."""
    from backend.core.logging import get_logger

    supplied_id = request.headers.get("X-Request-ID", "").strip()
    request_id = supplied_id[:128] or str(uuid4())
    token = set_request_id(request_id)
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        get_logger("request").exception(
            "request_failed",
            extra={"event": "request_failed", "method": request.method, "path": request.url.path},
        )
        raise
    finally:
        duration_ms = (perf_counter() - started) * 1000
        metrics.record_request(status_code, duration_ms)
        get_logger("request").info(
            "request_complete",
            extra={
                "event": "request_complete",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        if "response" in locals():
            response.headers["X-Request-ID"] = request_id
            response.headers["Server-Timing"] = f'app;dur={duration_ms:.2f}'
        reset_request_id(token)
