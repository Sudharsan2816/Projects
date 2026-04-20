import httpx
import json
from typing import List, Tuple, Dict, Any

from openai import OpenAI

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ── Gemini (lazy import — only used when LLM_PROVIDER=gemini) ────────────────

def _gemini_generate(prompt: str, system: str = "") -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system or "You are an expert market research analyst.",
            temperature=0.4,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        ),
    )
    return response.text.strip()


# ── NVIDIA NIM (OpenAI-compatible) ───────────────────────────────────────────

def _nvidia_generate(prompt: str, system: str = "") -> str:
    client = OpenAI(
        base_url=settings.NVIDIA_BASE_URL,
        api_key=settings.NVIDIA_API_KEY,
    )
    response = client.chat.completions.create(
        model=settings.NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system or "You are an expert market research analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
    )
    return response.choices[0].message.content.strip()


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_generate(prompt: str, system: str = "") -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system or "You are an expert market research analyst.",
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": settings.LLM_MAX_OUTPUT_TOKENS},
    }
    try:
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        raise RuntimeError(f"Ollama unavailable at {settings.OLLAMA_BASE_URL}: {e}") from e


# ── Public interface ──────────────────────────────────────────────────────────

def generate(prompt: str, system: str = "") -> str:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "nvidia" and settings.NVIDIA_API_KEY:
        try:
            logger.info(f"Calling NVIDIA NIM ({settings.NVIDIA_MODEL})")
            return _nvidia_generate(prompt, system)
        except Exception as e:
            logger.warning(f"NVIDIA failed: {e}")
            if settings.GEMINI_API_KEY:
                logger.info("Falling back to Gemini")
                return _gemini_generate(prompt, system)
            try:
                logger.info("Falling back to Ollama")
                return _ollama_generate(prompt, system)
            except RuntimeError as oe:
                raise RuntimeError(
                    f"All LLM providers failed. NVIDIA: {e} | Ollama: {oe}"
                ) from e

    elif provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            logger.info("Calling Gemini API")
            return _gemini_generate(prompt, system)
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
            try:
                logger.info("Falling back to Ollama")
                return _ollama_generate(prompt, system)
            except RuntimeError as oe:
                raise RuntimeError(
                    f"All LLM providers failed. Gemini: {e} | Ollama: {oe}"
                ) from e

    elif provider == "ollama":
        logger.info(f"Calling Ollama ({settings.OLLAMA_MODEL})")
        return _ollama_generate(prompt, system)

    else:
        if settings.NVIDIA_API_KEY:
            return _nvidia_generate(prompt, system)
        if settings.GEMINI_API_KEY:
            return _gemini_generate(prompt, system)
        raise RuntimeError(
            "No LLM provider configured. Set NVIDIA_API_KEY, GEMINI_API_KEY, or point OLLAMA_BASE_URL."
        )


# ── NVIDIA Reranker ───────────────────────────────────────────────────────────

def rerank(
    query: str,
    candidates: List[Tuple[Dict[str, Any], float]],
    top_k: int = None,
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
        except Exception:
            continue

    # Reranker unavailable — return top_k by FAISS score
    return candidates[:top_k]


# ── NVIDIA streaming generate ─────────────────────────────────────────────────

def generate_stream(prompt: str, system: str = ""):
    """
    Yields text chunks for streaming. Only supported for NVIDIA provider.
    Falls back to yielding the full generate() result as one chunk.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "nvidia" and settings.NVIDIA_API_KEY:
        client = OpenAI(base_url=settings.NVIDIA_BASE_URL, api_key=settings.NVIDIA_API_KEY)
        try:
            stream = client.chat.completions.create(
                model=settings.NVIDIA_MODEL,
                messages=[
                    {"role": "system", "content": system or "You are an expert market research analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return
        except Exception as e:
            logger.warning(f"NVIDIA stream failed ({e}), falling back to blocking generate")

    # Fallback: yield the full response as one chunk
    try:
        yield generate(prompt, system)
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
        raise ValueError(f"LLM returned invalid JSON: {e}")
