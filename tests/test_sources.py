"""Unit tests for source clients with a fake HTTP cache client."""

from __future__ import annotations

import pytest

from data_collection.enumerate import enumerate_artist, load_seed_artists
from data_collection.http import HttpResult
from data_collection.sources import deezer, itunes


class FakeClient:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_json(self, source, url, params=None, refresh=False, timeout=None):
        for key, data in self.mapping.items():
            if key in url:
                return HttpResult(ok=True, status=200, data=data)
        return HttpResult(ok=True, status=200, data={})


def test_best_artist_match_threshold():
    artists = [
        {"id": 1, "name": "Narayan Gopal"},
        {"id": 2, "name": "Narayan Gopal Tribute Band"},
        {"id": 3, "name": "Someone Else"},
    ]
    match = deezer.best_artist_match(artists, "narayan gopal")
    assert match is not None and match["id"] == 1
    assert deezer.best_artist_match(artists, "zzzz unrelated") is None


def test_deezer_track_mapping():
    track = {
        "id": 42,
        "title": "Euta Mancheko",
        "duration": 245,
        "preview": "https://cdns-preview.example/42.mp3",
        "isrc": "NPX12345678",
        "artist": {"name": "Narayan Gopal"},
    }
    cand = deezer.track_to_candidate(track, album="Sarangi")
    assert cand is not None
    assert (cand.source, cand.source_id, cand.duration_s, cand.album) == ("deezer", "42", 245, "Sarangi")
    assert cand.preview_url and cand.isrc == "NPX12345678"
    assert deezer.track_to_candidate({"id": 1, "artist": {}}) is None


def test_itunes_track_mapping():
    track = {
        "trackId": 7,
        "trackName": "Kehi Mitho Baat Gara",
        "artistName": "Narayan Gopal",
        "collectionName": "Classics",
        "trackTimeMillis": 251000,
        "previewUrl": "https://audio.example/7.m4a",
    }
    cand = itunes.track_to_candidate(track)
    assert cand is not None
    assert (cand.source, cand.source_id, cand.duration_s) == ("itunes", "7", 251)
    assert itunes.track_to_candidate({"trackId": 1}) is None


def test_enumerate_artist_combines_sources():
    client = FakeClient(
        {
            "search/artist": {"data": [{"id": 1, "name": "Narayan Gopal"}]},
            "artist/1/albums": {"data": [{"id": 10, "title": "Sarangi"}]},
            "album/10/tracks": {
                "data": [
                    {"id": 101, "title": "Track A", "duration": 200, "artist": {"name": "Narayan Gopal"}},
                    {"id": 102, "title": "Track B", "duration": 210, "artist": {"name": "Narayan Gopal"}},
                ]
            },
            "itunes.apple.com/search": {
                "results": [
                    {
                        "trackId": 900,
                        "trackName": "Track C",
                        "artistName": "Narayan Gopal",
                        "trackTimeMillis": 180000,
                    }
                ]
            },
        }
    )
    candidates, stats = enumerate_artist(client, "Narayan Gopal")
    assert stats["deezer_tracks"] == 2
    assert stats["itunes_tracks"] == 1
    assert len(candidates) == 3
    assert {c.title for c in candidates} == {"Track A", "Track B", "Track C"}


def test_load_seed_artists_filters_and_merges(tmp_path):
    from data_collection import state

    conn = state.open_db(tmp_path / "db.sqlite")
    state.init_db(conn)
    from data_collection.models import Candidate

    state.enqueue(conn, [Candidate(source="s", artist="Genius Romanizations", title="x")])
    seeds = tmp_path / "seeds.txt"
    seeds.write_text("# comment\nNepathya\n\n  # indented comment\nSajjan Raj Vaidya\n", encoding="utf-8")
    artists = load_seed_artists(conn, seeds)
    assert "Genius Romanizations" not in artists
    assert {"Nepathya", "Sajjan Raj Vaidya"} <= set(artists)
