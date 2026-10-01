"""Hermetic tests for the audio index and recommender audio fusion."""

from __future__ import annotations

import csv

import numpy as np
import pandas as pd

from music_rec.audio_index import AudioIndex, normalize_rows
from music_rec.config import Config
from music_rec.recommender import MusicRecommender


def _write_audio_artifacts(tmp_path, vectors, keys, matches):
    embeddings = tmp_path / "audio_embeddings.npy"
    keys_path = tmp_path / "audio_embedding_keys.csv"
    matches_path = tmp_path / "audio_track_matches.csv"
    np.save(embeddings, np.asarray(vectors, dtype=np.float32))
    with open(keys_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["track_key", "artist", "title"])
        writer.writeheader()
        for key in keys:
            writer.writerow({"track_key": key, "artist": "", "title": ""})
    with open(matches_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["track_key", "match_song_id", "new_id"])
        writer.writeheader()
        for key in keys:
            writer.writerow({"track_key": key, "match_song_id": matches.get(key, ""), "new_id": ""})
    return embeddings, keys_path, matches_path


def test_missing_artifacts_return_none(tmp_path):
    index = AudioIndex.from_files(tmp_path / "a.npy", tmp_path / "b.csv", tmp_path / "c.csv")
    assert index is None


def test_audio_index_mapping_and_scores(tmp_path):
    vectors = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0], [0.0, -1.0]]
    keys = ["a|one", "b|two", "c|three", "d|four"]
    matches = {"a|one": "10", "b|two": "10", "c|three": "20"}  # d|four -> new song
    index = AudioIndex.from_files(*_write_audio_artifacts(tmp_path, vectors, keys, matches))
    assert index is not None
    assert index.song_ids == [10, 20]
    assert index.has_audio(10) and index.has_audio(20) and not index.has_audio(99)
    assert index.song_for_track("d|four") is None

    ids, scores = index.scores_for_song(10)
    ranked = [sid for _, sid in sorted(zip(scores, ids), reverse=True)]
    assert ranked[0] == 10 and scores[ids.index(10)] > 0.99
    assert scores[ids.index(20)] < 0.1

    ids, scores = index.scores_for_track("c|three")
    assert scores[ids.index(20)] > 0.99
    empty_ids, empty_scores = index.scores_for_track("missing|track")
    assert empty_ids == [] and empty_scores.size == 0


def test_blend_rows_keeps_songs_without_audio():
    text = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    blended = AudioIndex.blend_rows(text, [10, 20, 30], {20: 0.0}, weight=0.5)
    assert blended[0] == 1.0 and blended[2] == 1.0
    assert abs(float(blended[1]) - 0.5) < 1e-6
    zero_weight = AudioIndex.blend_rows(text, [10, 20, 30], {20: 0.0}, weight=0.0)
    assert np.allclose(zero_weight, text)


class _FakeEncoder:
    def normalize_query(self, text: str) -> str:
        return text

    def encode_text(self, text: str) -> np.ndarray:
        return np.full(8, 0.125, dtype=np.float32)


def _tiny_recommender(tmp_path):
    songs = [
        {"song_id": 0, "title": "Seed", "artist": "A", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 1, "title": "Twin", "artist": "B", "category": "nepali", "lyrics": "x", "token_count": 1},
        {"song_id": 2, "title": "Far", "artist": "C", "category": "nepali", "lyrics": "x", "token_count": 1},
    ]
    config = Config()
    config.artifacts_dir = tmp_path
    config.cleaned_lyrics_csv = tmp_path / "cleaned_lyrics.csv"
    config.embeddings_npy = tmp_path / "embeddings.npy"
    config.feature_matrix_npy = tmp_path / "feature_matrix.npy"
    config.faiss_index_path = tmp_path / "songs.faiss"
    config.sentiment_scores_csv = tmp_path / "sentiment_scores.csv"
    config.window_vectors_npy = tmp_path / "window_vectors.npy"
    config.window_owners_npy = tmp_path / "window_owners.npy"
    config.dedup_enabled = False
    config.audio_weight = 1.0
    config.audio_embeddings_npy = tmp_path / "audio_embeddings.npy"
    config.audio_embedding_keys_csv = tmp_path / "audio_embedding_keys.csv"
    config.audio_track_matches_csv = tmp_path / "audio_track_matches.csv"

    pd.DataFrame(songs).to_csv(config.cleaned_lyrics_csv, index=False, encoding="utf-8")
    # text space: song 1 is opposite to song 0, song 2 in between
    np.save(config.embeddings_npy, np.array([[1, 0], [-1, 0], [0, 1]], dtype=np.float32))
    # audio space: song 1 sounds exactly like the seed, song 2 does not
    _write_audio_artifacts(
        tmp_path,
        [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]],
        ["a|seed", "b|twin", "c|far"],
        {"a|seed": "0", "b|twin": "1", "c|far": "2"},
    )
    return MusicRecommender(config, use_features=False, query_encoder=_FakeEncoder())


def test_seed_recommendations_fuse_audio(tmp_path):
    recommender = _tiny_recommender(tmp_path)
    assert recommender.has_audio(1)
    results = recommender.recommend_by_song(0)
    assert results, "expected recommendations"
    assert results[0].song_id == 1, "audio-identical song should rank first with audio_weight=1.0"


def test_recommend_by_audio_ranks_corpus_songs(tmp_path):
    recommender = _tiny_recommender(tmp_path)
    results = recommender.recommend_by_audio("a|seed")
    assert [rec.song_id for rec in results][:2] == [1, 2]

    recommender.config.audio_enabled = False
    recommender.audio_index = None
    try:
        recommender.recommend_by_audio("a|seed")
        raise AssertionError("expected RuntimeError without audio index")
    except RuntimeError:
        pass


def test_normalize_rows():
    rows = normalize_rows(np.array([[3.0, 4.0], [0.0, 0.0]], dtype=np.float32))
    assert abs(float(np.linalg.norm(rows[0])) - 1.0) < 1e-6
    assert np.all(np.isfinite(rows[1]))
