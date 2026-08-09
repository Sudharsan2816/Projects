import json
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.safety import normalize_session_id

from .embedder import embed_query, embed_texts

logger = get_logger(__name__)
settings = get_settings()


class FAISSVectorStore:
    """Per-session FAISS index with chunk metadata store."""

    def __init__(self, session_id: str):
        self.session_id = normalize_session_id(session_id)
        self.index_path = settings.INDEX_DIR / f"{self.session_id}.faiss"
        self.meta_path = settings.INDEX_DIR / f"{self.session_id}.meta"
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict[str, Any]] = []

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            self.metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
            logger.info(
                f"[{self.session_id}] Loaded FAISS index: {self.index.ntotal} vectors"
            )
        else:
            self.index = None
            self.metadata = []

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        self.meta_path.write_text(json.dumps(self.metadata, ensure_ascii=True), encoding="utf-8")
        logger.info(
            f"[{self.session_id}] Saved FAISS index: {self.index.ntotal} vectors"
        )

    # ── Indexing ─────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """Embed and index a list of chunk dicts; returns total vector count."""
        self._load()

        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        dim = embeddings.shape[1]

        # If an existing index has a different dimension (e.g. switched embedding
        # provider from local 384-dim to NVIDIA 1024-dim), rebuild from scratch.
        if self.index is not None and self.index.d != dim:
            logger.warning(
                f"[{self.session_id}] Embedding dim changed "
                f"({self.index.d} → {dim}). Rebuilding index."
            )
            self.index = None
            self.metadata = []

        if self.index is None:
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(embeddings)
        self.metadata.extend(chunks)
        self._save()
        return self.index.ntotal

    # ── Search ───────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = None,
        source_filenames: List[str] | None = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Return [(chunk_dict, score)] sorted by relevance."""
        self._load()
        if self.index is None or self.index.ntotal == 0:
            return []

        requested_k = top_k or settings.TOP_K_RESULTS
        selected_sources = set(source_filenames or [])
        # Search the whole session index when sources are selected, then filter.
        # Otherwise, a relevant chunk from a selected document could be hidden by
        # higher-scoring chunks from documents that were not chosen for this report.
        k = self.index.ntotal if selected_sources else min(requested_k, self.index.ntotal)
        q_emb = embed_query(query).reshape(1, -1)
        scores, indices = self.index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx >= 0 and idx < len(self.metadata):
                chunk = self.metadata[idx]
                if selected_sources and chunk.get("source") not in selected_sources:
                    continue
                results.append((chunk, float(score)))
                if len(results) >= requested_k:
                    break
        return results

    # ── Stats ────────────────────────────────────────────────────────────────

    def total_vectors(self, source_filenames: List[str] | None = None) -> int:
        self._load()
        if not self.index:
            return 0
        selected_sources = set(source_filenames or [])
        if not selected_sources:
            return self.index.ntotal
        return sum(
            1 for chunk in self.metadata if chunk.get("source") in selected_sources
        )

    def remove_document(self, filename: str) -> int:
        """Remove every vector whose source matches a deleted document."""
        self._load()
        if self.index is None or not self.metadata:
            return 0

        keep_indices = [
            index
            for index, chunk in enumerate(self.metadata)
            if chunk.get("source") != filename
        ]
        removed = len(self.metadata) - len(keep_indices)
        if removed == 0:
            return 0

        if not keep_indices:
            self.index = None
            self.metadata = []
            for path in (self.index_path, self.meta_path):
                if path.exists():
                    path.unlink()
            return removed

        vectors = np.vstack(
            [self.index.reconstruct(index) for index in keep_indices]
        ).astype("float32")
        rebuilt = faiss.IndexFlatIP(self.index.d)
        rebuilt.add(vectors)
        self.index = rebuilt
        self.metadata = [self.metadata[index] for index in keep_indices]
        self._save()
        return removed

    def delete(self):
        """Remove FAISS index files for this session."""
        for p in [self.index_path, self.meta_path]:
            if p.exists():
                p.unlink()
        logger.info(f"[{self.session_id}] Deleted FAISS index")
