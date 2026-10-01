"""Quantify local re-encoding drift vs the stored (Kaggle-built) embeddings."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from music_rec.config import Config  # noqa: E402
from music_rec.embeddings import _encode_chunked, _load_model  # noqa: E402

config = Config()
cleaned = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8").fillna("")
ids = [int(x) for x in json.loads(config.embedding_ids_json.read_text(encoding="utf-8"))]
stored = np.load(config.embeddings_npy).astype(np.float32)
stored_n = stored / np.maximum(np.linalg.norm(stored, axis=1, keepdims=True), 1e-12)
row_of = {sid: i for i, sid in enumerate(ids)}
by_song = cleaned.set_index("song_id")["lyrics"]

rng = np.random.default_rng(0)
sample = [int(x) for x in rng.choice(ids, size=100, replace=False)]
model = _load_model(config.embedding_model)
matrix, _, _ = _encode_chunked(model, [str(by_song.loc[sid]) for sid in sample],
                               config.embed_batch_size, 48, 24, 10**9, quiet=True)
matrix = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)

cos = np.array([float(matrix[i] @ stored_n[row_of[sid]]) for i, sid in enumerate(sample)])
print(f"n={len(sample)} cos: min={cos.min():.4f} p10={np.percentile(cos,10):.4f} "
      f"p50={np.percentile(cos,50):.4f} p90={np.percentile(cos,90):.4f} max={cos.max():.4f}")
for threshold in (0.99, 0.95, 0.90, 0.80):
    print(f"  cos < {threshold}: {(cos < threshold).sum()}")
worst = np.argsort(cos)[:10]
print("worst songs:")
for i in worst:
    sid = sample[i]
    row = cleaned[cleaned["song_id"] == sid].iloc[0]
    print(f"  {sid:5d} cos={cos[i]:.4f} tokens={row['token_count']:>5} | {str(row['artist'])[:24]:24s} - {str(row['title'])[:34]}")
