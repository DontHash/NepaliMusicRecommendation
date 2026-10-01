"""Hermetic tests for the incremental append path (DE6a)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from music_rec.config import Config
from music_rec.incremental import append_new_songs

EMBED_DIM = 4
LABELS = ["joy", "sadness", "anger", "fear", "depression", "positive", "negative"]


def _write_corpus(path: Path, song_ids: list[int]) -> None:
    pd.DataFrame({
        "song_id": song_ids,
        "title": [f"T{index}" for index in song_ids],
        "artist": [f"A{index}" for index in song_ids],
        "category": ["nepali"] * len(song_ids),
        "lyrics": [f"माया गीत {index}" for index in song_ids],
        "token_count": [10 + index for index in song_ids],
    }).to_csv(path, index=False, encoding="utf-8")


def _mini_config(tmp_path: Path) -> Config:
    config = Config()
    config.project_root = tmp_path
    art = tmp_path / "artifacts"
    art.mkdir()
    config.artifacts_dir = art
    config.cleaned_lyrics_csv = art / "cleaned_lyrics.csv"
    config.embeddings_npy = art / "embeddings.npy"
    config.embedding_ids_json = art / "embedding_ids.json"
    config.window_vectors_npy = art / "window_vectors.npy"
    config.window_owners_npy = art / "window_owners.npy"
    config.sentiment_scores_csv = art / "sentiment_scores.csv"
    config.mood_probe_npz = art / "mood_probe.npz"
    config.feature_matrix_npy = art / "feature_matrix.npy"
    config.faiss_index_path = art / "lyrics.faiss"

    _write_corpus(config.cleaned_lyrics_csv, [0, 1, 2])
    np.save(config.embeddings_npy,
            np.arange(3 * EMBED_DIM, dtype=np.float32).reshape(3, EMBED_DIM))
    np.save(config.window_vectors_npy, np.zeros((5, EMBED_DIM), dtype=np.float32))
    np.save(config.window_owners_npy, np.asarray([0, 0, 1, 1, 2], dtype=np.int32))
    config.embedding_ids_json.write_text(json.dumps([0, 1, 2]), encoding="utf-8")

    scores = pd.DataFrame({"song_id": [0, 1, 2]})
    for label in LABELS:
        scores[label] = 0.1
    scores["sentiment_score"] = 0.0
    scores["sentiment_label"] = "neutral"
    scores.to_csv(config.sentiment_scores_csv, index=False, encoding="utf-8")

    np.savez(config.mood_probe_npz,
             coef=np.zeros((7, EMBED_DIM), dtype=np.float32),
             intercept=np.zeros(7, dtype=np.float32),
             labels=np.asarray(LABELS))
    return config


def _fake_encoder(texts):
    count = len(texts)
    matrix = np.ones((count, EMBED_DIM), dtype=np.float32)
    windows = np.ones((count * 2, EMBED_DIM), dtype=np.float32)
    owners = np.repeat(np.arange(count, dtype=np.int32), 2)
    return matrix, windows, owners


def test_append_only_touches_the_tail(tmp_path: Path):
    config = _mini_config(tmp_path)
    embeddings_before = np.load(config.embeddings_npy)
    windows_before = np.load(config.window_vectors_npy)
    _write_corpus(config.cleaned_lyrics_csv, [0, 1, 2, 3, 4])

    report = append_new_songs(config, encoder=_fake_encoder, rebuild=False)

    assert report["status"] == "appended"
    assert report["new_songs"] == 2 and report["new_windows"] == 4
    embeddings_after = np.load(config.embeddings_npy)
    assert embeddings_after.shape == (5, EMBED_DIM)
    assert np.array_equal(embeddings_after[:3], embeddings_before)  # prefix identical
    windows_after = np.load(config.window_vectors_npy)
    assert np.array_equal(windows_after[:5], windows_before)
    owners = np.load(config.window_owners_npy)
    assert owners.tolist() == [0, 0, 1, 1, 2, 3, 3, 4, 4]
    assert json.loads(config.embedding_ids_json.read_text(encoding="utf-8")) == [0, 1, 2, 3, 4]
    scores = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8")
    assert scores["song_id"].tolist() == [0, 1, 2, 3, 4]

    watermark = json.loads(
        (tmp_path / "R_data" / "state" / "watermarks.json").read_text(encoding="utf-8"))
    assert watermark["corpus.append"]["rows"] == 5
    assert watermark["corpus.append"]["new_songs"] == 2


def test_noop_when_no_new_rows(tmp_path: Path):
    config = _mini_config(tmp_path)
    before = config.embeddings_npy.read_bytes()
    report = append_new_songs(config, encoder=_fake_encoder, rebuild=False)
    assert report["status"] == "noop" and report["new_songs"] == 0
    assert config.embeddings_npy.read_bytes() == before


def test_prefix_mismatch_refuses(tmp_path: Path):
    config = _mini_config(tmp_path)
    _write_corpus(config.cleaned_lyrics_csv, [0, 1, 9, 3])
    with pytest.raises(ValueError, match="prefix"):
        append_new_songs(config, encoder=_fake_encoder, rebuild=False)


def test_sentiment_row_mismatch_refuses(tmp_path: Path):
    config = _mini_config(tmp_path)
    _write_corpus(config.cleaned_lyrics_csv, [0, 1, 2, 3])
    scores = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8")
    scores.iloc[:-1].to_csv(config.sentiment_scores_csv, index=False, encoding="utf-8")
    with pytest.raises(ValueError, match="sentiment"):
        append_new_songs(config, encoder=_fake_encoder, rebuild=False)


def test_report_file_written(tmp_path: Path):
    config = _mini_config(tmp_path)
    _write_corpus(config.cleaned_lyrics_csv, [0, 1, 2, 3])
    report_path = tmp_path / "text_artifacts_update_report.json"
    report = append_new_songs(config, encoder=_fake_encoder, rebuild=False,
                              report_path=report_path)
    stored = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored["new_songs"] == 1 and stored["status"] == "appended"
    assert stored["ids_digest"] == report["ids_digest"]
