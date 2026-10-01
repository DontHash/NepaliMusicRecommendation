"""Window-level similarity search over chunked lyric embeddings.

Song-level vectors dilute any single line (they average all windows), so a
lyric-snippet query matches poorly against them. Scoring the query against
every window and keeping the best window per song ("max-sim aggregation")
recovers line-level matches while staying compatible with the song-id space.

Exact scoring is O(windows); above ``Config.window_ann_threshold`` windows the
index can instead use an HNSW side-index (``window_index.faiss``) and re-score
only the top-k windows in full precision. ``auto`` uses ANN only where exact
scan no longer fits the latency budget; HNSW scores are cosine similarities,
so downstream fusion is unchanged.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .index import build_index, index_kind, load_index, normalize


class WindowIndex:
    def __init__(
        self,
        vectors: np.ndarray,
        owners: np.ndarray,
        n_songs: int,
        *,
        ann_index=None,
        ann_top_k: int = 2000,
    ):
        if vectors.shape[0] != owners.shape[0]:
            raise ValueError(
                f"window vectors ({vectors.shape[0]}) and owners ({owners.shape[0]}) length mismatch"
            )
        self.vectors = normalize(vectors)
        self.owners = owners.astype(np.int64)
        self.n_songs = int(n_songs)
        self.ann_index = ann_index
        self.ann_top_k = int(ann_top_k)

    @classmethod
    def load(
        cls,
        vectors_path: Path,
        owners_path: Path,
        n_songs: int,
        *,
        index_path: Path | None = None,
        ann_top_k: int = 2000,
        ann_mode: str = "auto",
        ann_threshold: int = 250_000,
    ) -> "WindowIndex":
        vectors = np.load(vectors_path).astype(np.float32)
        owners = np.load(owners_path)
        ann_index = None
        if (
            index_path is not None
            and Path(index_path).exists()
            and ann_enabled(ann_mode, len(owners), ann_threshold)
        ):
            try:
                candidate = load_index(Path(index_path))
                if candidate.ntotal == vectors.shape[0] and getattr(candidate, "d", vectors.shape[1]) == vectors.shape[1]:
                    ann_index = candidate
            except Exception:  # noqa: BLE001 - fall back to exact scoring
                ann_index = None
        return cls(vectors, owners, n_songs, ann_index=ann_index, ann_top_k=ann_top_k)

    @property
    def mode(self) -> str:
        return index_kind(self.ann_index) if self.ann_index is not None else "exact"

    def song_scores(self, query_vec: np.ndarray, *, top_k: int | None = None) -> np.ndarray:
        query = np.asarray(query_vec, dtype=np.float32)
        norm = float(np.linalg.norm(query))
        if norm:
            query = query / norm
        scores = np.full(self.n_songs, -np.inf, dtype=np.float32)
        if self.ann_index is not None:
            k = min(int(top_k or self.ann_top_k), len(self.owners))
            distances, ids = self.ann_index.search(query.reshape(1, -1), k)
            valid = ids[0] >= 0
            rows = ids[0][valid]
            np.maximum.at(scores, self.owners[rows], distances[0][valid].astype(np.float32))
            return scores
        sims = self.vectors @ query
        np.maximum.at(scores, self.owners, sims)
        return scores

    def search(self, query_vec: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        scores = self.song_scores(query_vec)
        order = np.argsort(-scores)[:top_k]
        return [(int(sid), float(scores[sid])) for sid in order if np.isfinite(scores[sid])]


def ann_enabled(mode: str, n_windows: int, threshold: int) -> bool:
    kind = (mode or "auto").lower()
    if kind == "off":
        return False
    if kind == "on":
        return True
    return n_windows >= threshold


def build_window_index(
    vectors_path: Path,
    index_path: Path,
    *,
    index_type: str = "hnsw",
    hnsw_m: int = 32,
    ef_construction: int = 200,
    ef_search: int = 64,
) -> Path:
    """Build and persist the window ANN side-index (cosine via inner product)."""
    vectors = np.load(vectors_path).astype(np.float32)
    build_index(
        vectors,
        index_path,
        index_type=index_type,
        hnsw_m=hnsw_m,
        ef_construction=ef_construction,
        ef_search=ef_search,
    )
    return index_path
