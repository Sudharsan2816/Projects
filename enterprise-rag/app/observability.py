"""Structured request and retrieval observability."""

from __future__ import annotations

import json
import logging
import sys
from collections import Counter
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from hashlib import sha256
from threading import Lock
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from fastapi import Request, Response

_request_id: ContextVar[str] = ContextVar("request_id", default="-")
_STANDARD_FIELDS = set(logging.makeLogRecord({}).__dict__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": _request_id.get(),
        }
        for key, value in record.__dict__.items():
            if key not in _STANDARD_FIELDS and key not in {"message", "asctime"}:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=True)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self.requests = 0
            self.request_latency_ms = 0.0
            self.status_codes: Counter[str] = Counter()
            self.retrievals = 0
            self.retrieval_latency_ms = 0.0
            self.authorized_chunks = 0
            self.query_outcomes: Counter[str] = Counter()

    def record_request(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self.requests += 1
            self.request_latency_ms += duration_ms
            self.status_codes[str(status_code)] += 1

    def record_retrieval(self, duration_ms: float, chunk_count: int) -> None:
        with self._lock:
            self.retrievals += 1
            self.retrieval_latency_ms += duration_ms
            self.authorized_chunks += chunk_count

    def record_outcome(self, outcome: str) -> None:
        with self._lock:
            self.query_outcomes[outcome] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "requests": {
                    "count": self.requests,
                    "average_latency_ms": round(
                        self.request_latency_ms / self.requests if self.requests else 0.0, 2
                    ),
                    "status_codes": dict(self.status_codes),
                },
                "retrieval": {
                    "count": self.retrievals,
                    "average_latency_ms": round(
                        self.retrieval_latency_ms / self.retrievals if self.retrievals else 0.0,
                        2,
                    ),
                    "authorized_chunks": self.authorized_chunks,
                },
                "query_outcomes": dict(self.query_outcomes),
            }


metrics = MetricsRegistry()


def _set_request_id(value: str) -> Token[str]:
    return _request_id.set(value)


def _reset_request_id(token: Token[str]) -> None:
    _request_id.reset(token)


def query_fingerprint(query: str) -> str:
    return sha256(query.encode("utf-8")).hexdigest()[:12]


def record_retrieval(
    *,
    query: str,
    role: str,
    source_types: list[str],
    contexts: list[dict],
    duration_ms: float,
) -> None:
    metrics.record_retrieval(duration_ms, len(contexts))
    logging.getLogger("enterprise.retrieval").info(
        "retrieval_complete",
        extra={
            "event": "retrieval_complete",
            "query_fingerprint": query_fingerprint(query),
            "query_length": len(query),
            "role": role,
            "source_types": source_types,
            "authorized_chunk_count": len(contexts),
            "authorized_sources": sorted({str(item.get("source")) for item in contexts}),
            "duration_ms": round(duration_ms, 2),
        },
    )


async def request_observability_middleware(
    request: Request,
    call_next: Callable[[Request], Any],
) -> Response:
    request_id = request.headers.get("X-Request-ID", "").strip()[:128] or str(uuid4())
    token = _set_request_id(request_id)
    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logging.getLogger("enterprise.request").exception(
            "request_failed",
            extra={"event": "request_failed", "method": request.method, "path": request.url.path},
        )
        raise
    finally:
        duration_ms = (perf_counter() - started) * 1000
        metrics.record_request(status_code, duration_ms)
        logging.getLogger("enterprise.request").info(
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
        _reset_request_id(token)
