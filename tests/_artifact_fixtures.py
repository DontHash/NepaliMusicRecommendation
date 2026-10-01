"""Shared fixture artifacts for manifest/publish tests (not collected by pytest)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from data_engineering.artifacts import Artifact

FAKE_ARTIFACTS = (
    Artifact("cleaned_lyrics", "art/cleaned_lyrics.csv", "csv", text=True, schema="cleaned_lyrics"),
    Artifact("embedding_ids", "art/embedding_ids.json", "json", text=True),
    Artifact("embeddings", "art/embeddings.npy", "npy"),
    Artifact("feature_meta", "art/feature_meta.json", "json", text=True),
    Artifact("feature_matrix", "art/feature_matrix.npy", "npy"),
    Artifact("mood_probe", "art/mood_probe.npz", "npz"),
    Artifact("mood_vectors", "art/mood_vectors.csv", "csv", text=True),
    Artifact("sentiment_scores", "art/sentiment_scores.csv", "csv", text=True,
             schema="sentiment_scores"),
    Artifact("window_vectors", "art/window_vectors.npy", "npy", required=False),
    Artifact("window_owners", "art/window_owners.npy", "npy", required=False),
    Artifact("audio_embedding_keys", "art/audio_embedding_keys.csv", "csv", text=True),
    Artifact("audio_track_matches", "art/audio_track_matches.csv", "csv", text=True),
    Artifact("audio_embeddings", "art/audio_embeddings.npy", "npy", required=False),
)


def fake_tree(root: Path, *, song_ids=(0, 1, 2), embed_dim: int = 4, feature_dim: int = 5,
              owners=(0, 0, 1, 1, 2, 2), probe_width: int = 4,
              embeddings_rows: int | None = None) -> None:
    art = root / "art"
    art.mkdir(parents=True, exist_ok=True)
    songs = list(song_ids)
    titles = ["A", "B", "C", "D"][: len(songs)]
    pd.DataFrame({
        "song_id": songs,
        "title": titles,
        "artist": ["X", "Y", "Z", "W"][: len(songs)],
        "category": ["nepali"] * len(songs),
        "lyrics": ["तिम्रो माया", "माया नै माया", "दुःखको कथा", "आँखै न हट्ने"][: len(songs)],
        "token_count": [4, 5, 3, 6][: len(songs)],
    }).to_csv(art / "cleaned_lyrics.csv", index=False, encoding="utf-8")
    (art / "embedding_ids.json").write_text(json.dumps(songs), encoding="utf-8")

    rows = len(songs) if embeddings_rows is None else embeddings_rows
    np.save(art / "embeddings.npy",
            np.arange(rows * embed_dim, dtype=np.float32).reshape(rows, embed_dim))
    (art / "feature_meta.json").write_text(
        json.dumps({"embedding_dim": embed_dim, "feature_dim": feature_dim}), encoding="utf-8")
    np.save(art / "feature_matrix.npy",
            np.zeros((len(songs), feature_dim), dtype=np.float32))
    np.savez(art / "mood_probe.npz",
             coef=np.zeros((7, probe_width), dtype=np.float32),
             intercept=np.zeros(7, dtype=np.float32))

    pd.DataFrame({"song_id": songs, "joy": [0.1] * len(songs)}) \
        .to_csv(art / "mood_vectors.csv", index=False, encoding="utf-8")
    pd.DataFrame({"song_id": songs, "sentiment_score": [0.0] * len(songs),
                  "sentiment_label": ["neutral"] * len(songs)}) \
        .to_csv(art / "sentiment_scores.csv", index=False, encoding="utf-8")

    owner_array = np.asarray(owners, dtype=np.int32)
    np.save(art / "window_vectors.npy", np.zeros((len(owner_array), embed_dim), dtype=np.float32))
    np.save(art / "window_owners.npy", owner_array)

    tracks = pd.DataFrame({"track_key": ["a|b", "c|d", "e|f"]})
    tracks.to_csv(art / "audio_embedding_keys.csv", index=False, encoding="utf-8")
    tracks.to_csv(art / "audio_track_matches.csv", index=False, encoding="utf-8")
    np.save(art / "audio_embeddings.npy", np.zeros((3, embed_dim), dtype=np.float32))
