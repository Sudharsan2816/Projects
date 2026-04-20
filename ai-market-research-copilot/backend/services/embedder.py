from functools import lru_cache
from typing import List
import numpy as np
from openai import OpenAI

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ── Local embeddings (sentence-transformers fallback) ─────────────────────────

@lru_cache(maxsize=1)
def _load_local_model():
    from sentence_transformers import SentenceTransformer
    logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Local embedding model loaded")
    return model


def _local_embed(texts: List[str]) -> np.ndarray:
    model = _load_local_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.array(embeddings, dtype="float32")


# ── NVIDIA NIM embeddings ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _nvidia_client() -> OpenAI:
    return OpenAI(base_url=settings.NVIDIA_BASE_URL, api_key=settings.NVIDIA_API_KEY)


def _nvidia_embed(texts: List[str], input_type: str = "passage") -> np.ndarray:
    client = _nvidia_client()
    # NIM supports up to 50 texts per request
    batch_size = 50
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.NVIDIA_EMBEDDING_MODEL,
            input=batch,
            encoding_format="float",
            extra_body={"input_type": input_type, "truncate": "END"},
        )
        batch_embs = [e.embedding for e in sorted(response.data, key=lambda x: x.index)]
        all_embeddings.extend(batch_embs)

    arr = np.array(all_embeddings, dtype="float32")
    # L2-normalise so inner-product == cosine similarity (matches FAISS IndexFlatIP)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return arr / norms


# ── Public interface ──────────────────────────────────────────────────────────

def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of passage strings."""
    if settings.EMBEDDING_PROVIDER == "nvidia" and settings.NVIDIA_API_KEY:
        try:
            logger.info(f"NVIDIA embedding {len(texts)} passages")
            return _nvidia_embed(texts, input_type="passage")
        except Exception as e:
            logger.warning(f"NVIDIA embedding failed ({e}), falling back to local")
    return _local_embed(texts)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string."""
    if settings.EMBEDDING_PROVIDER == "nvidia" and settings.NVIDIA_API_KEY:
        try:
            return _nvidia_embed([query], input_type="query")[0]
        except Exception as e:
            logger.warning(f"NVIDIA query embed failed ({e}), falling back to local")
    return _local_embed([query])[0]
