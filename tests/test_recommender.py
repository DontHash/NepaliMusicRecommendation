"""Tests for recommender helper behaviour (artist intent detection)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from music_rec.config import Config
from music_rec.recommender import MusicRecommender


def _make_recommender(tmp_path, songs):
    config = Config()
    config.artifacts_dir = tmp_path
    config.cleaned_lyrics_csv = tmp_path / "cleaned_lyrics.csv"
    config.embeddings_npy = tmp_path / "embeddings.npy"
    config.feature_matrix_npy = tmp_path / "feature_matrix.npy"
    config.faiss_index_path = tmp_path / "songs.faiss"
    config.sentiment_scores_csv = tmp_path / "sentiment_scores.csv"

    pd.DataFrame(songs).to_csv(config.cleaned_lyrics_csv, index=False, encoding="utf-8")
    rng = np.random.default_rng(0)
    vectors = rng.normal(size=(len(songs), 8)).astype(np.float32)
    np.save(config.embeddings_npy, vectors)
    return MusicRecommender(config, use_features=False)


def test_artist_intent_detection(tmp_path):
    songs = [
        {"song_id": 0, "title": "A", "artist": "Narayan Gopal", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 1, "title": "B", "artist": "Narayan Gopal", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 2, "title": "C", "artist": "Sushant KC", "category": "nepali", "lyrics": "x", "token_count": 1},
    ]
    rec = _make_recommender(tmp_path, songs)
    assert rec._maybe_artist_filter("narayan gopal") == "Narayan Gopal"
    assert rec._maybe_artist_filter("NARAYAN GOPAL ") == "Narayan Gopal"
    assert rec._maybe_artist_filter("Sushant KC") is None
    assert rec._maybe_artist_filter("maya lagcha") is None


def test_artist_filter_returns_artist_songs_only(tmp_path):
    songs = [
        {"song_id": 0, "title": "A", "artist": "Narayan Gopal", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 1, "title": "B", "artist": "Narayan Gopal", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 2, "title": "C", "artist": "Sushant KC", "category": "nepali", "lyrics": "x", "token_count": 1},
    ]
    rec = _make_recommender(tmp_path, songs)
    results = rec._rank(rec.index_vectors[0], None, None, "Narayan Gopal", None)
    assert results
    assert {r.artist for r in results} == {"Narayan Gopal"}
