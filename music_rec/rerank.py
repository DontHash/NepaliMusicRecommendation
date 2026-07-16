"""MMR reranking and sentiment-alignment helpers for ANN candidates."""

from __future__ import annotations

import numpy as np


def _cosine_matrix(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = vectors / norms
    return unit @ unit.T


def mmr_rerank(
    candidate_ids: np.ndarray,
    relevance: np.ndarray,
    candidate_vectors: np.ndarray,
    top_k: int,
    mmr_lambda: float = 0.7,
) -> list[int]:
    """Greedy MMR: balance relevance vs diversity."""
    if len(candidate_ids) == 0:
        return []

    sim = _cosine_matrix(candidate_vectors)
    selected: list[int] = []
    remaining = list(range(len(candidate_ids)))

    rel = relevance.astype(np.float64)
    rmin, rmax = rel.min(), rel.max()
    rel = (rel - rmin) / (rmax - rmin) if rmax > rmin else np.ones_like(rel)

    while remaining and len(selected) < top_k:
        if not selected:
            best = max(remaining, key=lambda i: rel[i])
        else:
            def mmr_score(i: int) -> float:
                redundancy = max(sim[i][j] for j in selected)
                return mmr_lambda * rel[i] - (1 - mmr_lambda) * redundancy

            best = max(remaining, key=mmr_score)
        selected.append(best)
        remaining.remove(best)

    return [int(candidate_ids[i]) for i in selected]


def sentiment_alignment(
    candidate_sentiment: np.ndarray, target_sentiment: float | None
) -> np.ndarray:
    """1 - normalized distance between candidate and target sentiment score."""
    if target_sentiment is None:
        return np.zeros(len(candidate_sentiment))
    dist = np.abs(candidate_sentiment - target_sentiment)
    return 1.0 - np.clip(dist, 0.0, 1.0)
