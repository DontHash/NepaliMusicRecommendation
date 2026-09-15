"""Exact window-level similarity search over chunked lyric embeddings.

Song-level vectors dilute any single line (they average all windows), so a
lyric-snippet query matches poorly against them. Scoring the query against
every window and keeping the best window per song ("max-sim aggregation")
recovers line-level matches while staying compatible with the song-id space.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .index import normalize


class WindowIndex:
    def __init__(self, vectors: np.ndarray, owners: np.ndarray, n_songs: int):
        if vectors.shape[0] != owners.shape[0]:
            raise ValueError(
                f"window vectors ({vectors.shape[0]}) and owners ({owners.shape[0]}) length mismatch"
            )
        self.vectors = normalize(vectors)
        self.owners = owners.astype(np.int64)
        self.n_songs = int(n_songs)

    @classmethod
    def load(cls, vectors_path: Path, owners_path: Path, n_songs: int) -> "WindowIndex":
        vectors = np.load(vectors_path).astype(np.float32)
        owners = np.load(owners_path)
        return cls(vectors, owners, n_songs)

    def song_scores(self, query_vec: np.ndarray) -> np.ndarray:
        query = np.asarray(query_vec, dtype=np.float32)
        norm = float(np.linalg.norm(query))
        if norm:
            query = query / norm
        sims = self.vectors @ query
        scores = np.full(self.n_songs, -np.inf, dtype=np.float32)
        np.maximum.at(scores, self.owners, sims)
        return scores

    def search(self, query_vec: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        scores = self.song_scores(query_vec)
        order = np.argsort(-scores)[:top_k]
        return [(int(sid), float(scores[sid])) for sid in order if np.isfinite(scores[sid])]
