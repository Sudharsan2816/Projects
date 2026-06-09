from backend.services.chunker import chunk_pages


def test_chunk_pages_preserves_source_metadata():
    pages = [
        {
            "page": 3,
            "source": "market_report.pdf",
            "text": " ".join(f"word{i}" for i in range(25)),
        }
    ]

    chunks = chunk_pages(pages)

    assert chunks
    assert chunks[0]["source"] == "market_report.pdf"
    assert chunks[0]["page"] == 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["char_count"] == len(chunks[0]["text"])
