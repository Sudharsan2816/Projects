from backend.services import rag


class EmptyStore:
    def __init__(self, session_id):
        self.session_id = session_id

    def search(self, query, top_k=None):
        return []


def test_rag_query_does_not_fallback_to_model_knowledge(monkeypatch):
    def fail_generate(*args, **kwargs):
        raise AssertionError("generate should not be called without retrieved context")

    monkeypatch.setattr(rag, "FAISSVectorStore", EmptyStore)
    monkeypatch.setattr(rag, "generate", fail_generate)

    answer, sources = rag.rag_query("safe-session", "What is the market size?")

    assert "No indexed document context" in answer
    assert sources == []
