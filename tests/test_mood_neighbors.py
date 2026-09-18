"""Unit tests for mood-space neighbours and per-emotion top charts."""

from __future__ import annotations

import pandas as pd
import pytest

from music_rec.mood_neighbors import MoodNeighbors


def _engine(tmp_path) -> MoodNeighbors:
    vectors = pd.DataFrame(
        {
            "song_id": [1, 2, 3, 4],
            "joy": [0.9, 0.8, 0.1, 0.2],
            "sadness": [0.05, 0.1, 0.9, 0.7],
            "anger": [0.05, 0.1, 0.1, 0.2],
        }
    )
    lyrics = pd.DataFrame(
        {
            "song_id": [1, 2, 3, 4],
            "title": ["J1", "J2", "S1", "S2"],
            "artist": ["A", "A", "B", "B"],
        }
    )
    vectors_path = tmp_path / "mood_vectors.csv"
    lyrics_path = tmp_path / "cleaned_lyrics.csv"
    vectors.to_csv(vectors_path, index=False)
    lyrics.to_csv(lyrics_path, index=False)
    return MoodNeighbors(vectors_path=vectors_path, lyrics_path=lyrics_path)


def test_neighbors_exclude_self_and_sort(tmp_path):
    engine = _engine(tmp_path)
    out = engine.neighbors(1, k=2)
    assert [item["song_id"] for item in out] == [2, 4]
    assert all(item["song_id"] != 1 for item in out)
    assert out[0]["score"] >= out[1]["score"]
    assert out[0]["title"] == "J2"
    assert set(out[0]["mood"]) == {"joy", "sadness", "anger"}


def test_neighbors_clamp_and_missing_song(tmp_path):
    engine = _engine(tmp_path)
    assert len(engine.neighbors(3, k=99)) == 3
    with pytest.raises(KeyError):
        engine.neighbors(999)


def test_top_ranks_by_emotion(tmp_path):
    engine = _engine(tmp_path)
    out = engine.top("sadness", k=2)
    assert [item["song_id"] for item in out] == [3, 4]
    assert out[0]["score"] >= out[1]["score"]
    with pytest.raises(ValueError):
        engine.top("fear")


def test_missing_vectors_file(tmp_path):
    engine = MoodNeighbors(vectors_path=tmp_path / "absent.csv", lyrics_path=tmp_path / "absent.csv")
    with pytest.raises(FileNotFoundError):
        engine.top("joy")
