from typing import List, Dict, Any
from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def chunk_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Split parsed page-dicts into fixed-size overlapping chunks.
    Each chunk retains source metadata for citation.
    """
    chunks = []
    size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP

    for page in pages:
        text: str = page["text"]
        source: str = page["source"]
        page_num: int = page.get("page", 1)

        # Split on sentence boundaries where possible
        words = text.split()
        start = 0
        chunk_idx = 0

        while start < len(words):
            end = min(start + size, len(words))
            chunk_text = " ".join(words[start:end])

            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "page": page_num,
                    "chunk_index": chunk_idx,
                    "char_count": len(chunk_text),
                })
                chunk_idx += 1

            if end == len(words):
                break
            start += size - overlap

    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks
