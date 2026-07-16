"""Fuse lyric embeddings with optional sentiment/metadata into per-song vectors."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import Config


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_feature_matrix(
    config: Config | None = None,
    sentiment_weight: float = 0.3,
    metadata_weight: float = 0.2,
) -> np.ndarray:
    config = config or Config()
    df = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8")
    embeddings = np.load(config.embeddings_npy).astype(np.float32)
    embeddings = _normalize_rows(embeddings)

    parts = [embeddings]

    if config.sentiment_scores_csv.exists():
        sent = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8")
        sent_map = dict(zip(sent["song_id"], sent["sentiment_score"]))
        scores = np.array([sent_map.get(sid, 0.0) for sid in df["song_id"]], dtype=np.float32)
        scores01 = ((scores + 1.0) / 2.0).reshape(-1, 1) * sentiment_weight
        parts.append(scores01.astype(np.float32))

    if "category" in df.columns:
        cats = pd.get_dummies(df["category"].fillna("unknown")).to_numpy(dtype=np.float32)
        parts.append(cats * metadata_weight)

    if "artist" in df.columns:
        counts = df["artist"].fillna("unknown").value_counts()
        freq = df["artist"].fillna("unknown").map(counts).to_numpy(dtype=np.float32)
        freq = (freq / freq.max()).reshape(-1, 1) if freq.max() > 0 else freq.reshape(-1, 1)
        parts.append(freq * metadata_weight)

    matrix = np.hstack(parts).astype(np.float32)
    np.save(config.feature_matrix_npy, matrix)

    meta = {
        "embedding_dim": int(embeddings.shape[1]),
        "feature_dim": int(matrix.shape[1]),
        "has_sentiment": config.sentiment_scores_csv.exists(),
        "sentiment_weight": sentiment_weight,
        "metadata_weight": metadata_weight,
    }
    (config.artifacts_dir / "feature_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[features] built {matrix.shape} (embedding {embeddings.shape[1]} + extras)")
    return matrix
