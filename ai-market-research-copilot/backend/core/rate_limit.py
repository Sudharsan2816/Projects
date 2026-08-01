from collections import defaultdict, deque
from hashlib import sha256
from time import monotonic
from typing import Deque

from fastapi import Request
from starlette.responses import JSONResponse, Response

from backend.core.config import get_settings

settings = get_settings()


class InMemoryRateLimiter:
    """Small per-process sliding-window limiter for local/API demo protection."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    def allow_request(self, key: str, now: float | None = None) -> tuple[bool, int]:
        current = monotonic() if now is None else now
        cutoff = current - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (current - hits[0])))
            return False, retry_after
        hits.append(current)
        return True, 0


rate_limiter = InMemoryRateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)


def _client_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"api:{sha256(api_key.encode()).hexdigest()}"
    authorization = request.headers.get("authorization")
    if authorization:
        return f"auth:{sha256(authorization.encode()).hexdigest()}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


async def rate_limit_middleware(request: Request, call_next) -> Response:
    if (
        not settings.RATE_LIMIT_ENABLED
        or request.url.path in settings.rate_limit_exempt_paths
    ):
        return await call_next(request)

    allowed, retry_after = rate_limiter.allow_request(_client_key(request))
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)
