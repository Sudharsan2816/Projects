from backend.services import chunker


def test_chunk_pages_preserves_source_metadata():
    pages = [
        {
            "page": 3,
            "source": "market_report.pdf",
            "text": " ".join(f"word{i}" for i in range(25)),
        }
    ]

    chunks = chunker.chunk_pages(pages)

    assert chunks
    assert chunks[0]["source"] == "market_report.pdf"
    assert chunks[0]["page"] == 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["char_count"] == len(chunks[0]["text"])


def test_chunk_pages_uses_fixed_size_and_overlap(monkeypatch):
    monkeypatch.setattr(chunker.settings, "CHUNK_SIZE", 10)
    monkeypatch.setattr(chunker.settings, "CHUNK_OVERLAP", 2)
    page = {
        "page": 1,
        "source": "fixed-window.txt",
        "text": " ".join(f"word{i}" for i in range(25)),
    }

    chunks = chunker.chunk_pages([page])

    assert len(chunks) == 3
    assert chunks[0]["text"].split() == [f"word{i}" for i in range(10)]
    assert chunks[1]["text"].split() == [f"word{i}" for i in range(8, 18)]
    assert chunks[2]["text"].split() == [f"word{i}" for i in range(16, 25)]
