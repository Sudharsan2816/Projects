import pytest

from backend.services import llm


def test_generate_falls_through_every_configured_provider(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "nvidia")
    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_PROVIDERS", "gemini,ollama")
    monkeypatch.setattr(llm.settings, "NVIDIA_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    calls = []

    def fake_call(provider, prompt, system):
        calls.append(provider)
        if provider != "ollama":
            raise RuntimeError("provider unavailable")
        return "OK"

    monkeypatch.setattr(llm, "_call_provider", fake_call)

    assert llm.generate("hello") == "OK"
    assert calls == ["nvidia", "gemini", "ollama"]


def test_generate_returns_secret_free_provider_diagnostics(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_PROVIDERS", "nvidia,ollama")
    monkeypatch.setattr(llm.settings, "NVIDIA_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    def fake_call(provider, prompt, system):
        error = RuntimeError("api key super-secret-value was rejected")
        error.status_code = 403
        raise error

    monkeypatch.setattr(llm, "_call_provider", fake_call)

    with pytest.raises(llm.LLMProviderError) as captured:
        llm.generate("hello")

    message = str(captured.value)
    assert "super-secret-value" not in message
    assert "authorization failed" in message
    assert set(captured.value.diagnostics) == {"gemini", "nvidia", "ollama"}


def test_nvidia_only_mode_does_not_call_other_configured_providers(monkeypatch):
    monkeypatch.setattr(llm.settings, "LLM_PROVIDER", "nvidia")
    monkeypatch.setattr(llm.settings, "LLM_FALLBACK_PROVIDERS", "")
    monkeypatch.setattr(llm.settings, "NVIDIA_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "GEMINI_API_KEY", "configured")
    monkeypatch.setattr(llm.settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    calls = []

    def fake_call(provider, prompt, system):
        calls.append(provider)
        return "OK"

    monkeypatch.setattr(llm, "_call_provider", fake_call)

    assert llm.generate("hello") == "OK"
    assert calls == ["nvidia"]
    assert llm.configured_providers() == ["nvidia"]


def test_provider_error_categories_are_actionable():
    quota_error = RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded")
    quota_error.status_code = 429

    assert llm._safe_provider_error(quota_error) == "quota exhausted"
    assert (
        llm._safe_provider_error(RuntimeError("[WinError 10061] connection refused"))
        == "service is not running or reachable"
    )
