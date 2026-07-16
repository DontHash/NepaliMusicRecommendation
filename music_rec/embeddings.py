"""Compute multilingual lyric embeddings into embeddings.npy."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import Config


def _load_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def compute_embeddings(config: Config | None = None, log_every: int = 500) -> np.ndarray:
    config = config or Config()
    df = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8")
    texts = df["lyrics"].fillna("").astype(str).tolist()
    song_ids = df["song_id"].tolist()

    model = _load_model(config.embedding_model)

    embeddings: list[np.ndarray] = []
    bs = config.embed_batch_size
    for start in range(0, len(texts), bs):
        batch = texts[start : start + bs]
        vecs = model.encode(
            batch,
            batch_size=bs,
            convert_to_numpy=True,
            normalize_embeddings=False,  # normalization happens at index build
            show_progress_bar=False,
        )
        embeddings.append(vecs.astype(np.float32))
        done = min(start + bs, len(texts))
        if done % log_every < bs or done == len(texts):
            print(f"[embeddings] {done}/{len(texts)} songs encoded")

    matrix = np.vstack(embeddings).astype(np.float32)
    np.save(config.embeddings_npy, matrix)
    config.embedding_ids_json.write_text(json.dumps(song_ids), encoding="utf-8")
    print(f"[embeddings] saved {matrix.shape} -> {config.embeddings_npy.name}")
    return matrix


if __name__ == "__main__":
    compute_embeddings()
