import os
from contextvars import ContextVar
from functools import lru_cache
from typing import List

import numpy as np
from openai import OpenAI

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_last_embedding_model: ContextVar[str | None] = ContextVar(
    "last_embedding_model",
    default=None,
)


def get_last_embedding_model() -> str | None:
    """Return the model that completed the latest embedding call in this context."""
    return _last_embedding_model.get()


# Local embeddings (sentence-transformers fallback)

@lru_cache(maxsize=1)
def _load_local_model():
    settings.MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(settings.MODEL_CACHE_DIR))
    os.environ.setdefault("HF_HUB_CACHE", str(settings.MODEL_CACHE_DIR / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(settings.MODEL_CACHE_DIR / "transformers"))
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
    model = SentenceTransformer(
        settings.EMBEDDING_MODEL,
        cache_folder=str(settings.MODEL_CACHE_DIR),
    )
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


# NVIDIA NIM embeddings

@lru_cache(maxsize=1)
def _nvidia_client() -> OpenAI:
    return OpenAI(base_url=settings.NVIDIA_BASE_URL, api_key=settings.NVIDIA_API_KEY)


def _nvidia_embed(texts: List[str], input_type: str = "passage") -> np.ndarray:
    client = _nvidia_client()
    # NIM supports up to 50 texts per request.
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
    # L2-normalise so inner-product == cosine similarity (matches FAISS IndexFlatIP).
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    return arr / norms


# Public interface

def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed passage strings and record the model that actually succeeded."""
    if settings.EMBEDDING_PROVIDER == "nvidia" and settings.NVIDIA_API_KEY:
        try:
            logger.info(f"NVIDIA embedding {len(texts)} passages")
            embeddings = _nvidia_embed(texts, input_type="passage")
            _last_embedding_model.set(settings.NVIDIA_EMBEDDING_MODEL)
            return embeddings
        except Exception as error:
            logger.warning("NVIDIA embedding failed (%s), falling back to local", error)

    embeddings = _local_embed(texts)
    _last_embedding_model.set(f"sentence-transformers/{settings.EMBEDDING_MODEL}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """Embed a query and record the model that actually succeeded."""
    if settings.EMBEDDING_PROVIDER == "nvidia" and settings.NVIDIA_API_KEY:
        try:
            embedding = _nvidia_embed([query], input_type="query")[0]
            _last_embedding_model.set(settings.NVIDIA_EMBEDDING_MODEL)
            return embedding
        except Exception as error:
            logger.warning("NVIDIA query embed failed (%s), falling back to local", error)

    embedding = _local_embed([query])[0]
    _last_embedding_model.set(f"sentence-transformers/{settings.EMBEDDING_MODEL}")
    return embedding
