from backend.services import rag


class EmptyStore:
    def __init__(self, session_id):
        self.session_id = session_id

    def search(self, query, top_k=None, source_filenames=None):
        return []


def test_rag_query_does_not_fallback_to_model_knowledge(monkeypatch):
    def fail_generate(*args, **kwargs):
        raise AssertionError("generate should not be called without retrieved context")

    monkeypatch.setattr(rag, "FAISSVectorStore", EmptyStore)
    monkeypatch.setattr(rag, "generate", fail_generate)

    answer, sources = rag.rag_query("safe-session", "What is the market size?")

    assert "No indexed document context" in answer
    assert sources == []


def test_context_repairs_pdf_rupee_glyph_before_generation():
    results = [
        (
            {
                "source": "report.pdf",
                "page": 3,
                "chunk_index": 0,
                "text": "No incumbent has a credible sub-I6,000 product; I18,499 is mid-premium.",
            },
            0.8,
        )
    ]

    context = rag.build_context(results)

    assert "sub-₹6,000" in context
    assert "₹18,499" in context
    assert "I6,000" not in context
