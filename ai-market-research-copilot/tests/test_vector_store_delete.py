import faiss
import numpy as np

from backend.services import vector_store
from backend.services.vector_store import FAISSVectorStore


def test_remove_document_rebuilds_index_without_deleted_chunks(tmp_path):
    store = FAISSVectorStore("delete-test")
    store.index_path = tmp_path / "delete-test.faiss"
    store.meta_path = tmp_path / "delete-test.meta"
    store.index = faiss.IndexFlatIP(2)
    store.index.add(
        np.asarray(
            [
                [1.0, 0.0],
                [0.9, 0.1],
                [0.0, 1.0],
            ],
            dtype="float32",
        )
    )
    store.metadata = [
        {"source": "remove.pdf", "text": "first"},
        {"source": "remove.pdf", "text": "second"},
        {"source": "keep.md", "text": "third"},
    ]
    store._save()

    removed = store.remove_document("remove.pdf")

    assert removed == 2
    assert store.index.ntotal == 1
    assert store.metadata == [{"source": "keep.md", "text": "third"}]


def test_remove_last_document_deletes_index_files(tmp_path):
    store = FAISSVectorStore("delete-last-test")
    store.index_path = tmp_path / "delete-last-test.faiss"
    store.meta_path = tmp_path / "delete-last-test.meta"
    store.index = faiss.IndexFlatIP(2)
    store.index.add(np.asarray([[1.0, 0.0]], dtype="float32"))
    store.metadata = [{"source": "only.txt", "text": "only chunk"}]
    store._save()

    removed = store.remove_document("only.txt")

    assert removed == 1
    assert store.index is None
    assert store.metadata == []
    assert not store.index_path.exists()
    assert not store.meta_path.exists()


def test_search_and_vector_count_are_limited_to_selected_sources(monkeypatch, tmp_path):
    store = FAISSVectorStore("selected-source-test")
    store.index_path = tmp_path / "selected-source-test.faiss"
    store.meta_path = tmp_path / "selected-source-test.meta"
    store.index = faiss.IndexFlatIP(2)
    store.index.add(
        np.asarray(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [0.8, 0.2],
            ],
            dtype="float32",
        )
    )
    store.metadata = [
        {"source": "selected.pdf", "text": "selected first"},
        {"source": "excluded.pdf", "text": "excluded but closest"},
        {"source": "selected.pdf", "text": "selected second"},
    ]
    store._save()
    monkeypatch.setattr(
        vector_store,
        "embed_query",
        lambda query: np.asarray([0.0, 1.0], dtype="float32"),
    )

    results = store.search(
        "query",
        top_k=2,
        source_filenames=["selected.pdf"],
    )

    assert [chunk["source"] for chunk, _score in results] == [
        "selected.pdf",
        "selected.pdf",
    ]
    assert store.total_vectors(["selected.pdf"]) == 2
