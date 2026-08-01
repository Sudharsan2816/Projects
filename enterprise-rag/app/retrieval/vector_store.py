"""FAISS vector store with a lightweight fallback embedding path."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.config import settings

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None


class EmbeddingModel:
    """Embedding wrapper that prefers sentence-transformers and falls back safely."""

    def __init__(self) -> None:
        self.model = None
        self.dimension = 384
        if SentenceTransformer:
            try:
                self.model = SentenceTransformer(settings.embedding_model, local_files_only=True)
            except Exception:
                self.model = None

    def encode(self, texts: list[str]) -> np.ndarray:
        if self.model:
            vectors = self.model.encode(texts, normalize_embeddings=True)
            return np.asarray(vectors, dtype="float32")
        return np.vstack([self._hash_embedding(text) for text in texts]).astype("float32")

    def _hash_embedding(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimension, dtype="float32")
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimension
            vector[index] += 1.0
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector


class VectorStore:
    """Persistent vector index for unstructured enterprise text chunks."""

    def __init__(self) -> None:
        self.index_path = Path(settings.vector_index_path)
        self.metadata_path = Path(settings.vector_metadata_path)
        self.embedding_model = EmbeddingModel()
        self.dimension = self.embedding_model.dimension
        self.metadata: list[dict] = []
        self.index = None
        self._load()

    def _new_index(self):
        if faiss:
            return faiss.IndexFlatIP(self.dimension)
        return []

    def _load(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        if self.metadata_path.exists():
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if faiss and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = self._new_index()
            if self.metadata and not faiss:
                self.index = [item["embedding"] for item in self.metadata if "embedding" in item]

    def _persist(self) -> None:
        if faiss and self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
            public_metadata = [{k: v for k, v in item.items() if k != "embedding"} for item in self.metadata]
            self.metadata_path.write_text(json.dumps(public_metadata, indent=2), encoding="utf-8")
        else:
            self.metadata_path.write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")

    def add_texts(self, texts: list[str], metadatas: list[dict]) -> int:
        if not texts:
            return 0
        vectors = self.embedding_model.encode(texts)
        if faiss:
            self.index.add(vectors)
            self.metadata.extend(metadatas)
        else:
            for vector, metadata in zip(vectors, metadatas, strict=True):
                metadata = metadata.copy()
                metadata["embedding"] = vector.tolist()
                self.metadata.append(metadata)
                self.index.append(vector.tolist())
        self._persist()
        return len(texts)

    def has_source(self, source: str | Path) -> bool:
        expected = Path(source).resolve()
        return any(
            Path(str(item.get("source", ""))).resolve() == expected
            for item in self.metadata
            if item.get("source")
        )

    def search(self, query: str, allowed_permissions: set[str], top_k: int = 5) -> list[dict]:
        if not self.metadata:
            return []
        query_vector = self.embedding_model.encode([query])
        if faiss and self.index.ntotal:
            scores, indexes = self.index.search(query_vector, min(top_k * 3, self.index.ntotal))
            candidates = [
                {**self.metadata[idx], "score": float(score)}
                for score, idx in zip(scores[0], indexes[0], strict=True)
                if idx >= 0
            ]
        else:
            query_arr = query_vector[0]
            candidates = []
            for item in self.metadata:
                vector = np.asarray(item.get("embedding", []), dtype="float32")
                if vector.size != self.dimension:
                    continue
                candidates.append({**item, "score": float(np.dot(query_arr, vector))})
            candidates.sort(key=lambda item: item["score"], reverse=True)

        filtered = [
            item
            for item in candidates
            if item.get("permission") in allowed_permissions and item.get("content")
        ]
        return filtered[:top_k]


vector_store = VectorStore()
