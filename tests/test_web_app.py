"""API tests for the Mood Studio backend (skipped when artifacts are absent)."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from music_rec.config import Config
from web_app.server import app, get_recommender

WINDOW_VECTORS = Config().window_vectors_npy
pytestmark = pytest.mark.skipif(
    not WINDOW_VECTORS.exists(), reason="corpus window artifacts not built"
)

client = TestClient(app)


class FakeRecommender:
    def __init__(self, hits=None):
        self.hits = list(hits or [])

    def recommend_by_text(self, text: str):
        return list(self.hits)


class BrokenRecommender:
    def recommend_by_text(self, text: str):
        raise RuntimeError("lyric backend down")


@pytest.fixture
def recommender_override():
    def _set(recommender):
        app.dependency_overrides[get_recommender] = lambda: recommender
        return recommender

    yield _set
    app.dependency_overrides.pop(get_recommender, None)


def test_search_finds_known_song(recommender_override):
    recommender_override(FakeRecommender())
    response = client.get("/api/search", params={"q": "Ekkasi"})
    assert response.status_code == 200
    ids = [item["song_id"] for item in response.json()["results"]]
    assert 4024 in ids


def test_search_merges_lyric_hits_after_title_hits(recommender_override):
    recommender_override(
        FakeRecommender(
            [
                SimpleNamespace(song_id=4024, title="Ekkasi", artist="Yabesh Thapa", score=0.9),
                SimpleNamespace(song_id=2512, title="Mohabbat Bula Rahi Hai", artist="X", score=0.7),
            ]
        )
    )
    results = client.get("/api/search", params={"q": "Ekkasi"}).json()["results"]
    assert results[0]["song_id"] == 4024
    assert results[0]["match"] == "title"
    assert [item["song_id"] for item in results].count(4024) == 1
    lyric_hit = next(item for item in results if item["song_id"] == 2512)
    assert lyric_hit["match"] == "lyrics"
    assert lyric_hit["score"] == 0.7


def test_search_respects_limit(recommender_override):
    recommender_override(
        FakeRecommender(
            [SimpleNamespace(song_id=2500 + i, title=f"S{i}", artist="A", score=0.5) for i in range(10)]
        )
    )
    results = client.get("/api/search", params={"q": "Ekkasi", "limit": 3}).json()["results"]
    assert len(results) == 3


def test_search_survives_lyric_backend_failure(recommender_override):
    recommender_override(BrokenRecommender())
    response = client.get("/api/search", params={"q": "Ekkasi"})
    assert response.status_code == 200
    ids = [item["song_id"] for item in response.json()["results"]]
    assert 4024 in ids


def test_search_empty_query(recommender_override):
    recommender_override(FakeRecommender())
    assert client.get("/api/search", params={"q": "  "}).json() == {"results": []}


def test_song_payload_shape():
    response = client.get("/api/song/4024")
    assert response.status_code == 200
    data = response.json()
    assert data["song_id"] == 4024
    composition = data["composition"]
    assert abs(sum(composition.values()) - 1.0) < 1e-3
    assert set(composition) == {"joy", "sadness", "anger"}
    assert data["polarity"]["label"] in {"positive", "negative", "neutral"}
    assert data["lines"]
    assert all("probs" in line and "dominant" in line for line in data["lines"])


def test_song_missing_404():
    response = client.get("/api/song/999999")
    assert response.status_code == 404


def test_song_neighbors_shape():
    response = client.get("/api/song/4024/neighbors", params={"k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["song_id"] == 4024
    assert len(data["neighbors"]) == 5
    assert all(item["song_id"] != 4024 for item in data["neighbors"])
    scores = [item["score"] for item in data["neighbors"]]
    assert scores == sorted(scores, reverse=True)
    assert all({"song_id", "title", "artist", "score", "mood"} <= set(item) for item in data["neighbors"])


def test_song_neighbors_missing_404():
    response = client.get("/api/song/999999/neighbors")
    assert response.status_code == 404


def test_mood_top_shape():
    response = client.get("/api/mood/top", params={"emotion": "sadness", "k": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["emotion"] == "sadness"
    assert len(data["top"]) == 4
    scores = [item["score"] for item in data["top"]]
    assert scores == sorted(scores, reverse=True)


def test_mood_top_bad_emotion_400():
    response = client.get("/api/mood/top", params={"emotion": "fear"})
    assert response.status_code == 400


@pytest.mark.skipif(
    os.environ.get("PROJECTR_SLOW_TESTS") != "1", reason="loads the embedding model"
)
def test_search_finds_song_by_verbatim_lyric_line():
    app.dependency_overrides.pop(get_recommender, None)
    response = client.get("/api/search", params={"q": "जुदाइयाँ चल के आ रही हैं"})
    assert response.status_code == 200
    results = response.json()["results"]
    assert any(item["song_id"] == 2512 and item["match"] == "lyrics" for item in results)


@pytest.mark.skipif(
    os.environ.get("PROJECTR_SLOW_TESTS") != "1", reason="loads the embedding model"
)
def test_analyze_text_mode():
    response = client.post(
        "/api/analyze",
        json={"text": "तिमी बिना कसरी बिताउने होला जिन्दगी", "transliterate": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "text"
    assert abs(sum(payload["composition"].values()) - 1.0) < 1e-3
