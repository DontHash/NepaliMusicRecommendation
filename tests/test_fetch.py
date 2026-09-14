"""Unit tests for the lyrics fetch chain."""

from __future__ import annotations

from data_collection.fetch import acceptable, fetch_candidate
from data_collection.http import HttpResult
from data_collection.models import LyricsHit
from data_collection.normalize import detect_script, lyrics_sha
from data_collection.sources import lrclib, syncedlyrics_client


class FakeClient:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_json(self, source, url, params=None, refresh=False, timeout=None):
        for key, data in self.mapping.items():
            if key in url:
                return HttpResult(ok=True, status=200, data=data)
        return HttpResult(ok=False, status=404, error="not_found")


def make_record(lyrics, *, duration=245, record_id=1):
    return {
        "id": record_id,
        "trackName": "Euta Mancheko",
        "artistName": "Narayan Gopal",
        "duration": duration,
        "plainLyrics": lyrics,
        "syncedLyrics": None,
    }


def test_strip_lrc_removes_timestamps():
    text = "[00:12.34] माया लाग्छ\n[00:15.00] तिम्रो मन"
    assert lrclib.strip_lrc(text) == "माया लाग्छ\nतिम्रो मन"


def test_record_to_hit_uses_synced_when_plain_missing():
    record = make_record("", record_id=9)
    record["syncedLyrics"] = "[00:01.00] माया लाग्छ"
    hit = lrclib.record_to_hit(record)
    assert hit is not None and hit.synced and "माया" in hit.lyrics
    assert hit.source_url == "https://lrclib.net/api/get/9"


def test_pick_best_prefers_closest_duration():
    records = [make_record("a", duration=200), make_record("b", duration=300)]
    best = lrclib.pick_best(records, duration=295, artist="Narayan Gopal", title="Euta Mancheko")
    assert best is not None and best["duration"] == 300


def test_pick_best_rejects_far_duration():
    records = [make_record("a", duration=400)]
    assert lrclib.pick_best(records, duration=200, artist="Narayan Gopal", title="Euta Mancheko") is None


def test_acceptable_rules():
    dev = LyricsHit(stage="s", lyrics="माया लाग्छ " * 30, script="devanagari", sha256="x")
    roman = LyricsHit(stage="s", lyrics="maya lagcha timi mero sathi " * 20, script="romanized", sha256="y")
    english = LyricsHit(stage="s", lyrics="hello world this is english " * 20, script="romanized", sha256="z")
    short = LyricsHit(stage="s", lyrics="माया", script="devanagari", sha256="w")
    assert acceptable(dev)[0]
    assert acceptable(roman)[0] and acceptable(roman)[1] == "romanized_nepali"
    assert not acceptable(english)[0]
    assert acceptable(short)[1] == "too_short"


def test_fetch_candidate_lrclib_get_hit():
    lyrics = "माया लाग्छ तिम्रो मन " * 20
    client = FakeClient({"lrclib.net/api/get": make_record(lyrics)})
    row = {"artist": "Narayan Gopal", "title": "Euta Mancheko", "duration_s": 245, "album": None}
    hit, attempts, _ = fetch_candidate(client, row)
    assert hit is not None and hit.stage == "lrclib"
    assert ("lrclib_get", "hit") in attempts


def test_fetch_candidate_syncedlyrics_fallback(monkeypatch):
    lyrics = "माया लाग्छ तिम्रो मन " * 20
    client = FakeClient({})
    monkeypatch.setattr(syncedlyrics_client, "fetch_lyrics", lambda title, artist, providers=None: lyrics)
    row = {"artist": "Narayan Gopal", "title": "Euta Mancheko", "duration_s": None, "album": None}
    hit, attempts, _ = fetch_candidate(client, row)
    assert hit is not None and hit.stage == "syncedlyrics"
    assert ("syncedlyrics", "hit") in attempts


def test_fetch_candidate_full_miss():
    client = FakeClient({})
    row = {"artist": "Nobody", "title": "Nothing", "duration_s": None, "album": None}
    hit, attempts, _ = fetch_candidate(client, row, stages=("lrclib",))
    assert hit is None
    assert [a[0] for a in attempts] == ["lrclib_search"]


def test_syncedlyrics_provider_isolation(monkeypatch):
    import sys as _sys

    calls = []

    class Stub:
        @staticmethod
        def search(term, providers=None, plain_only=False):
            calls.append(providers)
            if providers == ["Musixmatch"]:
                raise TypeError("'NoneType' object is not iterable")
            if providers == ["NetEase"]:
                return "माया लाग्छ " * 30
            return None

    monkeypatch.setitem(_sys.modules, "syncedlyrics", Stub)
    out = syncedlyrics_client.fetch_lyrics("t", "a")
    assert out is not None and "माया" in out
    assert calls == [["Musixmatch"], ["NetEase"]]
