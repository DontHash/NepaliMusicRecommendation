"""Proxy metrics: diversity, sentiment coherence, catalog coverage."""

from __future__ import annotations

import json
import random

import numpy as np

from .config import Config
from .recommender import MusicRecommender


def intra_list_diversity(rec: MusicRecommender, song_ids: list[int]) -> float:
    if len(song_ids) < 2:
        return 0.0
    vecs = np.vstack([rec.embeddings[rec._row_index(s)] for s in song_ids])
    sims = vecs @ vecs.T
    n = len(song_ids)
    off = (sims.sum() - np.trace(sims)) / (n * (n - 1))
    return float(1.0 - off)


def sentiment_coherence(rec: MusicRecommender, song_ids: list[int]) -> float | None:
    if rec.sentiment is None or not song_ids:
        return None
    vals = [rec._sent_score(s) for s in song_ids if rec._sent_score(s) is not None]
    if len(vals) < 2:
        return None
    return float(1.0 - np.std(vals))


def evaluate(config: Config | None = None, sample: int = 30, seed: int = 42) -> dict:
    config = config or Config()
    rec = MusicRecommender.load(config)
    rng = random.Random(seed)
    all_ids = rec.songs["song_id"].tolist()
    sample_ids = rng.sample(all_ids, min(sample, len(all_ids)))

    diversities, coherences = [], []
    recommended = set()
    for sid in sample_ids:
        results = rec.recommend_by_song(sid)
        rec_ids = [r.song_id for r in results]
        recommended.update(rec_ids)
        diversities.append(intra_list_diversity(rec, rec_ids))
        c = sentiment_coherence(rec, rec_ids)
        if c is not None:
            coherences.append(c)

    report = {
        "queries_evaluated": len(sample_ids),
        "mean_intra_list_diversity": round(float(np.mean(diversities)), 4) if diversities else None,
        "mean_sentiment_coherence": round(float(np.mean(coherences)), 4) if coherences else None,
        "catalog_coverage": round(len(recommended) / len(all_ids), 4),
        "unique_songs_recommended": len(recommended),
        "catalog_size": len(all_ids),
    }
    (config.artifacts_dir / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
