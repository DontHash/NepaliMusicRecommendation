"""Tests for recommender helper behaviour (artist intent detection)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from music_rec.config import Config
from music_rec.recommender import MusicRecommender


def _make_recommender(tmp_path, songs, vectors=None, encoder=None):
    config = Config()
    config.artifacts_dir = tmp_path
    config.cleaned_lyrics_csv = tmp_path / "cleaned_lyrics.csv"
    config.embeddings_npy = tmp_path / "embeddings.npy"
    config.feature_matrix_npy = tmp_path / "feature_matrix.npy"
    config.faiss_index_path = tmp_path / "songs.faiss"
    config.sentiment_scores_csv = tmp_path / "sentiment_scores.csv"
    config.window_vectors_npy = tmp_path / "window_vectors.npy"
    config.window_owners_npy = tmp_path / "window_owners.npy"

    pd.DataFrame(songs).to_csv(config.cleaned_lyrics_csv, index=False, encoding="utf-8")
    if vectors is None:
        rng = np.random.default_rng(0)
        vectors = rng.normal(size=(len(songs), 8)).astype(np.float32)
    np.save(config.embeddings_npy, np.asarray(vectors, dtype=np.float32))
    return MusicRecommender(
        config, use_features=False, query_encoder=encoder or _FakeEncoder()
    )


class _FakeEncoder:
    """Deterministic stand-in for the sentence-transformer query encoder."""

    def normalize_query(self, text: str) -> str:
        return text

    def encode_text(self, text: str) -> np.ndarray:
        return np.full(8, 0.125, dtype=np.float32)


class _FixedEncoder(_FakeEncoder):
    def __init__(self, vector):
        self.vector = np.asarray(vector, dtype=np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        return self.vector.copy()


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


def test_verbatim_lyric_line_returns_source_song(tmp_path):
    songs = [
        {"song_id": 0, "title": "A", "artist": "X", "category": "nepali", "lyrics": "माया गर्छु तिमीलाई माया", "token_count": 4},
        {"song_id": 1, "title": "B", "artist": "Y", "category": "nepali", "lyrics": "तिमी मेरो साथ नहुँदा दुख्छ मन", "token_count": 6},
        {"song_id": 2, "title": "C", "artist": "Z", "category": "nepali", "lyrics": "पार्टी गीत नाच्ने रमाइलो", "token_count": 4},
    ]
    rec = _make_recommender(tmp_path, songs)
    results = rec.recommend_by_text("तिमी मेरो साथ नहुँदा")
    assert results
    assert results[0].song_id == 1


def test_unknown_text_still_returns_dense_results(tmp_path):
    songs = [
        {"song_id": 0, "title": "A", "artist": "X", "category": "nepali", "lyrics": "माया गर्छु तिमीलाई माया", "token_count": 4},
        {"song_id": 1, "title": "B", "artist": "Y", "category": "nepali", "lyrics": "तिमी मेरो साथ नहुँदा दुख्छ मन", "token_count": 6},
    ]
    rec = _make_recommender(tmp_path, songs)
    results = rec.recommend_by_text("कुनै अज्ञात शब्दावली")
    assert results


def test_duplicate_upload_is_collapsed_in_results(tmp_path):
    songs = [
        {"song_id": 0, "title": "A", "artist": "X", "category": "nepali", "lyrics": "तिमी मेरो साथ नहुँदा दुख्छ मन", "token_count": 6},
        {"song_id": 1, "title": "A - Romanized", "artist": "Y", "category": "nepali", "lyrics": "तिमी मेरो साथ नहुँदा दुख्छ मन", "token_count": 6},
    ]
    rec = _make_recommender(tmp_path, songs)
    results = rec.recommend_by_text("तिमी मेरो साथ नहुँदा")
    assert len(results) == 1
    assert results[0].song_id in {0, 1}


def test_short_keyword_query_skips_lexical_fusion(tmp_path):
    songs = [
        {"song_id": 0, "title": "Lexical", "artist": "X", "category": "nepali", "lyrics": "माया लाग्छ तिमीलाई", "token_count": 3},
        {"song_id": 1, "title": "Dense", "artist": "Y", "category": "nepali", "lyrics": "असम्बन्धित शब्दहरू", "token_count": 2},
    ]
    vectors = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    rec = _make_recommender(tmp_path, songs, vectors=vectors, encoder=_FixedEncoder([1.0, 0.0]))
    results = rec.recommend_by_text("माया लाग्छ")
    assert results[0].song_id == 1


def test_lyric_line_query_uses_lexical_fusion(tmp_path):
    songs = [
        {"song_id": 0, "title": "Lexical", "artist": "X", "category": "nepali", "lyrics": "माया लाग्छ तिमीलाई", "token_count": 3},
        {"song_id": 1, "title": "Dense", "artist": "Y", "category": "nepali", "lyrics": "असम्बन्धित शब्दहरू", "token_count": 2},
    ]
    vectors = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    rec = _make_recommender(tmp_path, songs, vectors=vectors, encoder=_FixedEncoder([1.0, 0.0]))
    results = rec.recommend_by_text("माया लाग्छ तिमीलाई")
    assert results[0].song_id == 0


def test_recommend_by_lexical_ignores_dense_scores(tmp_path):
    songs = [
        {"song_id": 0, "title": "Lexical", "artist": "X", "category": "nepali", "lyrics": "माया लाग्छ तिमीलाई", "token_count": 3},
        {"song_id": 1, "title": "Dense", "artist": "Y", "category": "nepali", "lyrics": "असम्बन्धित शब्दहरू", "token_count": 2},
    ]
    vectors = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    rec = _make_recommender(tmp_path, songs, vectors=vectors, encoder=_FixedEncoder([1.0, 0.0]))
    results = rec.recommend_by_lexical("माया लाग्छ तिमीलाई")
    assert results
    assert results[0].song_id == 0


def test_recommend_by_lexical_returns_empty_for_generic_keywords(tmp_path):
    songs = [
        {"song_id": 0, "title": "Lexical", "artist": "X", "category": "nepali", "lyrics": "माया लाग्छ तिमीलाई", "token_count": 3},
    ]
    rec = _make_recommender(tmp_path, songs)
    assert rec.recommend_by_lexical("माया लाग्छ") == []
