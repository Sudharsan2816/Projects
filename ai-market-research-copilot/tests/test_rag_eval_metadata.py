from types import SimpleNamespace

from scripts import run_rag_eval


def test_evaluation_reports_nvidia_embedding_model_when_active(monkeypatch):
    monkeypatch.setattr(
        run_rag_eval,
        "get_settings",
        lambda: SimpleNamespace(
            EMBEDDING_PROVIDER="nvidia",
            NVIDIA_API_KEY="configured",
            NVIDIA_EMBEDDING_MODEL="nvidia/test-embedder",
            EMBEDDING_MODEL="local-model",
        ),
    )

    assert run_rag_eval.active_embedding_metadata() == (
        "nvidia",
        "nvidia/test-embedder",
    )


def test_evaluation_reports_local_fallback_without_nvidia_key(monkeypatch):
    monkeypatch.setattr(
        run_rag_eval,
        "get_settings",
        lambda: SimpleNamespace(
            EMBEDDING_PROVIDER="nvidia",
            NVIDIA_API_KEY="",
            NVIDIA_EMBEDDING_MODEL="nvidia/test-embedder",
            EMBEDDING_MODEL="all-MiniLM-L6-v2",
        ),
    )

    assert run_rag_eval.active_embedding_metadata() == (
        "local",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
