from functools import lru_cache
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded")
    return model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Return L2-normalised embeddings for a list of strings."""
    model = _load_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.array(embeddings, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string."""
    return embed_texts([query])[0]
