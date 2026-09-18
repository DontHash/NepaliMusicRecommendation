"""API tests for the Mood Studio backend (skipped when artifacts are absent)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from music_rec.config import Config
from web_app.server import app

WINDOW_VECTORS = Config().window_vectors_npy
pytestmark = pytest.mark.skipif(
    not WINDOW_VECTORS.exists(), reason="corpus window artifacts not built"
)

client = TestClient(app)


def test_search_finds_known_song():
    response = client.get("/api/search", params={"q": "Ekkasi"})
    assert response.status_code == 200
    ids = [item["song_id"] for item in response.json()["results"]]
    assert 4024 in ids


def test_search_empty_query():
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
