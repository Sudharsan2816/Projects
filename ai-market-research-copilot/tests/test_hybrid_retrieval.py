from types import SimpleNamespace

from backend.services import rag


class LowSimilarityStore:
    chunks = [
        {
            "source": "report.pdf",
            "page": 1,
            "chunk_index": 0,
            "text": "Lead analyst: Priyanka Devanathan. Chennai is the fastest-growing metro.",
        },
        {
            "source": "report.pdf",
            "page": 2,
            "chunk_index": 0,
            "text": "KrishiKube is the fastest-growing major brand.",
        },
    ]

    def __init__(self, session_id):
        self.session_id = session_id
        self.metadata = self.chunks
        self.index = SimpleNamespace(ntotal=len(self.chunks))

    def search(self, query, top_k=None, source_filenames=None):
        return [(self.chunks[1], 0.27), (self.chunks[0], 0.24)]

    def total_vectors(self, source_filenames=None):
        return len(self.chunks)


def test_lexical_fallback_recovers_exact_fact_below_dense_threshold(monkeypatch):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)
    monkeypatch.setattr(rag, "rerank", lambda query, candidates, top_k: candidates[:top_k])

    results = rag.retrieve_results(
        "session",
        "Who is the lead analyst?",
        minimum_score=0.35,
        use_lexical_fallback=True,
    )

    assert results
    assert results[0][0]["page"] == 1
    assert "Priyanka Devanathan" in results[0][0]["text"]


def test_lexical_fallback_does_not_admit_unrelated_question(monkeypatch):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)
    monkeypatch.setattr(rag, "rerank", lambda query, candidates, top_k: candidates[:top_k])

    results = rag.retrieve_results(
        "session",
        "What is the capital of France?",
        minimum_score=0.35,
        use_lexical_fallback=True,
    )

    assert results == []


def test_lexical_fallback_ignores_conversational_filler_for_entity_queries(
    monkeypatch,
):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)
    monkeypatch.setattr(rag, "rerank", lambda query, candidates, top_k: candidates[:top_k])

    results = rag.retrieve_results(
        "session",
        "Tell me about KrishiKube",
        minimum_score=0.35,
        use_lexical_fallback=True,
    )

    assert results
    assert "KrishiKube" in results[0][0]["text"]


def test_entity_filler_fix_does_not_admit_an_unknown_entity(monkeypatch):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)
    monkeypatch.setattr(rag, "rerank", lambda query, candidates, top_k: candidates[:top_k])

    results = rag.retrieve_results(
        "session",
        "Tell me about France",
        minimum_score=0.35,
        use_lexical_fallback=True,
    )

    assert results == []


def test_report_backed_entity_typo_is_corrected_conservatively(monkeypatch):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)

    assert (
        rag.correct_document_entity_typos("session", "Tell me about Krishikub")
        == "Tell me about KrishiKube"
    )


def test_unknown_entity_is_not_fuzzy_mapped_to_report_content(monkeypatch):
    monkeypatch.setattr(rag, "FAISSVectorStore", LowSimilarityStore)

    assert (
        rag.correct_document_entity_typos("session", "Tell me about Farmlantic")
        == "Tell me about Farmlantic"
    )
