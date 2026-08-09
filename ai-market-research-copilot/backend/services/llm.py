import json
from time import perf_counter
from typing import Any, Callable, Dict, List, Tuple

import httpx
from openai import OpenAI

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.observability import record_provider_call

logger = get_logger(__name__)
settings = get_settings()


class LLMProviderError(RuntimeError):
    """Raised after every configured provider has failed."""

    def __init__(self, diagnostics: dict[str, str]):
        self.diagnostics = diagnostics
        summary = "; ".join(f"{name}: {message}" for name, message in diagnostics.items())
        super().__init__(f"No LLM provider could complete the request. {summary}")


def _observed_generate(
    provider: str,
    model: str,
    prompt: str,
    operation: Callable[[], str],
) -> str:
    started = perf_counter()
    try:
        response = operation()
    except Exception:
        record_provider_call(
            provider=provider,
            model=model,
            prompt=prompt,
            response="",
            duration_ms=(perf_counter() - started) * 1000,
            success=False,
        )
        raise
    record_provider_call(
        provider=provider,
        model=model,
        prompt=prompt,
        response=response,
        duration_ms=(perf_counter() - started) * 1000,
        success=True,
    )
    return response


# ── Gemini (lazy import — only used when LLM_PROVIDER=gemini) ────────────────

def _gemini_generate(
    prompt: str,
    system: str = "",
    max_output_tokens: int | None = None,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai") from exc
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system or "You are an expert market research analyst.",
            temperature=0.4,
            max_output_tokens=max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response")
    return response.text.strip()


# ── NVIDIA NIM (OpenAI-compatible) ───────────────────────────────────────────

def _nvidia_generate(
    prompt: str,
    system: str = "",
    max_output_tokens: int | None = None,
) -> str:
    client = OpenAI(
        base_url=settings.NVIDIA_BASE_URL,
        api_key=settings.NVIDIA_API_KEY,
        timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
    )
    response = client.chat.completions.create(
        model=settings.NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system or "You are an expert market research analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("NVIDIA returned an empty response")
    return content.strip()


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_generate(
    prompt: str,
    system: str = "",
    max_output_tokens: int | None = None,
) -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system or "You are an expert market research analyst.",
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS,
        },
    }
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        raise RuntimeError(f"Ollama unavailable at {settings.OLLAMA_BASE_URL}: {e}") from e


# ── Public interface ──────────────────────────────────────────────────────────

def _provider_model(provider: str) -> str:
    return {
        "nvidia": settings.NVIDIA_MODEL,
        "gemini": settings.GEMINI_MODEL,
        "ollama": settings.OLLAMA_MODEL,
    }[provider]


def _provider_is_configured(provider: str) -> bool:
    if provider == "nvidia":
        return bool(settings.NVIDIA_API_KEY)
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY)
    return provider == "ollama" and bool(settings.OLLAMA_BASE_URL)


def configured_providers() -> list[str]:
    """Return active, configured provider names without exposing credentials."""
    return _provider_order()


def _provider_order(exclude: set[str] | None = None) -> list[str]:
    preferred = settings.LLM_PROVIDER.lower().strip()
    supported = ("nvidia", "gemini", "ollama")
    requested = [preferred, *settings.llm_fallback_providers]
    excluded = exclude or set()
    order: list[str] = []
    for name in requested:
        if (
            name in supported
            and name not in order
            and name not in excluded
            and _provider_is_configured(name)
        ):
            order.append(name)
    return order


def _call_provider(
    provider: str,
    prompt: str,
    system: str,
    max_output_tokens: int | None = None,
) -> str:
    operations = {
        "nvidia": lambda: _nvidia_generate(prompt, system, max_output_tokens),
        "gemini": lambda: _gemini_generate(prompt, system, max_output_tokens),
        "ollama": lambda: _ollama_generate(prompt, system, max_output_tokens),
    }
    logger.info("Calling %s provider (%s)", provider, _provider_model(provider))
    return _observed_generate(
        provider,
        _provider_model(provider),
        prompt,
        operations[provider],
    )


def _safe_provider_error(error: Exception) -> str:
    status_code = getattr(error, "status_code", None)
    message = str(error).lower()
    if status_code in {401, 403} or "authorization failed" in message or "api key" in message:
        return "authorization failed"
    if status_code == 429 or "resource_exhausted" in message or "quota exceeded" in message:
        return "quota exhausted"
    if status_code == 404 or "not found" in message:
        return "model or endpoint not found"
    if "timed out" in message or "timeout" in message:
        return "request timed out"
    if "not installed" in message or isinstance(error, ImportError):
        return "client dependency is not installed"
    if (
        "connection refused" in message
        or "all connection attempts failed" in message
        or "winerror 10061" in message
        or "unable to connect" in message
    ):
        return "service is not running or reachable"
    return "provider request failed"


def generate(
    prompt: str,
    system: str = "",
    exclude: set[str] | None = None,
    max_output_tokens: int | None = None,
) -> str:
    diagnostics: dict[str, str] = {}
    providers = _provider_order(exclude)
    if not providers:
        raise LLMProviderError({"configuration": "no provider is configured"})

    for provider in providers:
        try:
            if max_output_tokens is None:
                return _call_provider(provider, prompt, system)
            return _call_provider(provider, prompt, system, max_output_tokens)
        except Exception as error:
            reason = _safe_provider_error(error)
            diagnostics[provider] = reason
            logger.warning("%s provider failed: %s", provider, reason)

    raise LLMProviderError(diagnostics)


def check_provider(provider: str) -> dict[str, Any]:
    """Run a minimal provider-specific prompt and return secret-free diagnostics."""
    provider = provider.lower().strip()
    if provider not in {"nvidia", "gemini", "ollama"}:
        raise ValueError(f"Unsupported provider: {provider}")
    if not _provider_is_configured(provider):
        return {"provider": provider, "configured": False, "status": "not_configured"}

    started = perf_counter()
    try:
        response = _call_provider(provider, "Reply with exactly: OK", "You are a connectivity check.")
        return {
            "provider": provider,
            "model": _provider_model(provider),
            "configured": True,
            "status": "ok" if response.strip() else "empty_response",
            "latency_ms": round((perf_counter() - started) * 1000, 1),
        }
    except Exception as error:
        return {
            "provider": provider,
            "model": _provider_model(provider),
            "configured": True,
            "status": "failed",
            "error": _safe_provider_error(error),
            "latency_ms": round((perf_counter() - started) * 1000, 1),
        }


# ── NVIDIA Reranker ───────────────────────────────────────────────────────────

def rerank(
    query: str,
    candidates: List[Tuple[Dict[str, Any], float]],
    top_k: int | None = None,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Rerank (chunk, score) pairs using NVIDIA NIM reranker.
    Returns top_k pairs sorted by reranker score descending.
    Falls back to original order if reranker is unavailable.
    """
    if not settings.NVIDIA_API_KEY or not candidates:
        return candidates

    top_k = top_k or settings.TOP_K_RESULTS
    passages = [{"text": chunk["text"][:2000]} for chunk, _ in candidates]

    # Try both known NVIDIA reranker endpoint paths
    reranker_endpoints = [
        f"https://ai.api.nvidia.com/v1/retrieval/{settings.NVIDIA_RERANKER_MODEL}/reranking",
        f"{settings.NVIDIA_BASE_URL}/ranking",
    ]
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.NVIDIA_RERANKER_MODEL,
        "query": {"text": query},
        "passages": passages,
        "truncate": "END",
    }
    for endpoint in reranker_endpoints:
        try:
            response = httpx.post(endpoint, headers=headers, json=payload, timeout=30)
            if response.status_code == 404:
                continue
            response.raise_for_status()
            rankings = response.json()["rankings"]
            reranked = sorted(
                [(candidates[r["index"]], r["logit"]) for r in rankings],
                key=lambda x: x[1],
                reverse=True,
            )
            return [(chunk, score) for (chunk, _), score in reranked[:top_k]]
        except Exception as error:
            logger.warning(
                "NVIDIA reranker endpoint failed: %s",
                _safe_provider_error(error),
            )
            continue

    # Reranker unavailable — return top_k by FAISS score
    return candidates[:top_k]


# ── NVIDIA streaming generate ─────────────────────────────────────────────────

def generate_stream(
    prompt: str,
    system: str = "",
    max_output_tokens: int | None = None,
):
    """
    Yields text chunks for streaming. Only supported for NVIDIA provider.
    Falls back to yielding the full generate() result as one chunk.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "nvidia" and settings.NVIDIA_API_KEY:
        client = OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=settings.NVIDIA_API_KEY,
            timeout=settings.LLM_REQUEST_TIMEOUT_SECONDS,
        )
        started = perf_counter()
        emitted = []
        try:
            stream = client.chat.completions.create(
                model=settings.NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": system or "You are an expert market research analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=max_output_tokens or settings.LLM_MAX_OUTPUT_TOKENS,
                stream=True,
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    emitted.append(delta)
                    yield delta
            record_provider_call(
                provider="nvidia",
                model=settings.NVIDIA_MODEL,
                prompt=prompt,
                response="".join(emitted),
                duration_ms=(perf_counter() - started) * 1000,
                success=True,
            )
            return
        except Exception as e:
            record_provider_call(
                provider="nvidia",
                model=settings.NVIDIA_MODEL,
                prompt=prompt,
                response="".join(emitted),
                duration_ms=(perf_counter() - started) * 1000,
                success=False,
            )
            logger.warning(f"NVIDIA stream failed ({e}), falling back to blocking generate")

    # Fallback: yield the full response as one chunk
    try:
        yield generate(
            prompt,
            system,
            exclude={"nvidia"},
            max_output_tokens=max_output_tokens,
        )
    except Exception as e:
        yield f"[Error generating response: {e}]"


def generate_json(prompt: str, system: str = "") -> dict:
    json_system = (
        (system or "You are an expert market research analyst.")
        + " Always respond with valid JSON only. No markdown, no explanation."
    )
    raw = generate(prompt, json_system)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        raise ValueError(f"LLM returned invalid JSON: {e}") from e
