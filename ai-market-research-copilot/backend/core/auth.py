from hmac import compare_digest

from fastapi import Header, HTTPException, status

from backend.core.config import get_settings

settings = get_settings()


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> None:
    """Require an API token only when API_AUTH_TOKEN is configured."""
    expected = settings.API_AUTH_TOKEN.strip()
    if not expected:
        return

    supplied = (x_api_key or "").strip() or _bearer_token(authorization)
    if not supplied or not compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid API credentials are required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
