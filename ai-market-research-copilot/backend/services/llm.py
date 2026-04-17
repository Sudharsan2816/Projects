import httpx
import json
from typing import Optional

import google.generativeai as genai

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ── Gemini ────────────────────────────────────────────────────────────────────

def _gemini_generate(prompt: str, system: str = "") -> str:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system or "You are an expert market research analyst.",
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )
    return response.text.strip()


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_generate(prompt: str, system: str = "") -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system or "You are an expert market research analyst.",
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 4096},
    }
    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


# ── Public interface ──────────────────────────────────────────────────────────

def generate(prompt: str, system: str = "") -> str:
    """
    Generate text via configured LLM provider.
    Falls back to Ollama if Gemini fails.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            logger.info("Calling Gemini API")
            return _gemini_generate(prompt, system)
        except Exception as e:
            logger.warning(f"Gemini failed ({e}), falling back to Ollama")
            return _ollama_generate(prompt, system)

    elif provider == "ollama":
        logger.info(f"Calling Ollama ({settings.OLLAMA_MODEL})")
        return _ollama_generate(prompt, system)

    else:
        # Last resort: try Gemini anyway
        if settings.GEMINI_API_KEY:
            return _gemini_generate(prompt, system)
        raise RuntimeError(
            "No LLM provider configured. Set GEMINI_API_KEY or point OLLAMA_BASE_URL."
        )


def generate_json(prompt: str, system: str = "") -> dict:
    """Generate and parse a JSON response from the LLM."""
    json_system = (
        (system or "You are an expert market research analyst.")
        + " Always respond with valid JSON only. No markdown, no explanation."
    )
    raw = generate(prompt, json_system)

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
