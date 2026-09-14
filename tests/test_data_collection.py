"""Unit tests for the Phase A data_collection core."""

from __future__ import annotations

import random

from data_collection import config as dc_config
from data_collection import bootstrap, normalize, state
from data_collection.http import CachedHttp
from data_collection.models import Candidate, LyricsHit


def make_paths(tmp_path):
    raw = tmp_path / "raw"
    st = tmp_path / "state"
    corpus = tmp_path / "corpus"
    return dc_config.Paths(
        root=tmp_path,
        raw=raw,
        state=st,
        corpus=corpus,
        db=st / "work.sqlite",
        cache_index=raw / "cache_index.jsonl",
    )


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        if not self.responses:
            raise AssertionError("no fake responses left")
        return self.responses.pop(0)


def test_dedupe_key_stability_and_bucket():
    a = normalize.make_dedupe_key("Narayan Gopal", "Euta Mancheko", 185)
    b = normalize.make_dedupe_key(" narayan  gopal ", "EUTA MANCHEKO!", 187)
    c = normalize.make_dedupe_key("Narayan Gopal", "Euta Mancheko", 240)
    assert a == b
    assert a != c


def test_lyrics_sha_normalizes_whitespace_and_case():
    assert normalize.lyrics_sha("Hello   World\n") == normalize.lyrics_sha("hello world")


def test_detect_script():
    assert normalize.detect_script("माया लाग्छ") == "devanagari"
    assert normalize.detect_script("maya lagcha") == "romanized"
    assert normalize.detect_script("माया lagcha") == "mixed"
    assert normalize.detect_script("123 456") == "unknown"


def test_http_cache_hit_skips_network(tmp_path):
    paths = make_paths(tmp_path)
    session = FakeSession([FakeResponse(200, {"ok": 1})])
    client = CachedHttp(paths=paths, session=session, sleep=lambda _: None)
    first = client.get_json("test", "https://api.deezer.com/search", {"q": "x"})
    second = client.get_json("test", "https://api.deezer.com/search", {"q": "x"})
    assert first.ok and first.data == {"ok": 1} and not first.from_cache
    assert second.ok and second.from_cache
    assert session.calls == 1


def test_http_retries_5xx_then_succeeds(tmp_path):
    paths = make_paths(tmp_path)
    sleeps: list[float] = []
    session = FakeSession([FakeResponse(503), FakeResponse(200, {"ok": 2})])
    client = CachedHttp(paths=paths, session=session, sleep=sleeps.append, rng=random.Random(0))
    result = client.get_json("test", "https://api.deezer.com/search", {"q": "y"})
    assert result.ok and result.data == {"ok": 2}
    assert session.calls == 2
    assert sleeps


def test_http_404_is_definitive(tmp_path):
    paths = make_paths(tmp_path)
    session = FakeSession([FakeResponse(404)])
    client = CachedHttp(paths=paths, session=session, sleep=lambda _: None)
    result = client.get_json("lrclib", "https://lrclib.net/api/get", {"track_name": "z"})
    assert not result.ok and result.not_found
    assert session.calls == 1


def test_http_circuit_opens_after_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(dc_config, "CIRCUIT_FAIL_THRESHOLD", 2)
    paths = make_paths(tmp_path)
    session = FakeSession([FakeResponse(500) for _ in range(4)])
    client = CachedHttp(paths=paths, session=session, sleep=lambda _: None, rng=random.Random(0))
    client.get_json("test", "https://api.deezer.com/x", {"q": "1"})
    result = client.get_json("test", "https://api.deezer.com/y", {"q": "2"})
    assert not result.ok
    assert result.error and result.error.startswith("circuit_open")


def test_state_enqueue_dedupe_and_resume(tmp_path):
    paths = make_paths(tmp_path)
    conn = state.open_db(paths.db)
    state.init_db(conn)
    c1 = Candidate(source="bootstrap", artist="Nepathya", title="Bhedako Oon Jasto", duration_s=300)
    c2 = Candidate(source="deezer", artist="Nepathya", title="Bhedako Oon Jasto", duration_s=301)
    added, dupes = state.enqueue(conn, [c1, c2])
    assert (added, dupes) == (1, 1)
    batch = state.next_batch(conn)
    assert len(batch) == 1
    state.mark_fetching(conn, [batch[0]["id"]])
    assert state.stats(conn)["candidates"]["fetching"] == 1
    assert state.reset_orphaned(conn) == 1
    assert state.stats(conn)["candidates"]["new"] == 1
    hit = LyricsHit(
        stage="bootstrap",
        lyrics="माया लाग्छ",
        script="devanagari",
        sha256=normalize.lyrics_sha("माया लाग्छ"),
    )
    state.save_lyrics(conn, batch[0]["id"], hit)
    stats = state.stats(conn)
    assert stats["lyrics_total"] == 1
    assert stats["by_script"] == {"devanagari": 1}
    assert state.find_by_lyrics_sha(conn, hit.sha256) == batch[0]["id"]


def test_state_attempt_log(tmp_path):
    paths = make_paths(tmp_path)
    conn = state.open_db(paths.db)
    state.init_db(conn)
    cand = Candidate(source="t", artist="a", title="b")
    state.enqueue(conn, [cand])
    cid = state.next_batch(conn)[0]["id"]
    state.record_attempt(conn, cid, "lrclib_get", "miss")
    state.record_attempt(conn, cid, "lrclib_search", "error", error_class="timeout", latency_ms=1200)
    row = conn.execute("SELECT COUNT(*) AS n FROM attempts").fetchone()
    assert row["n"] == 2


def test_meta_roundtrip(tmp_path):
    paths = make_paths(tmp_path)
    conn = state.open_db(paths.db)
    state.init_db(conn)
    state.set_meta(conn, "run_id", "abc")
    assert state.get_meta(conn, "run_id") == "abc"
    assert state.get_meta(conn, "missing", "fallback") == "fallback"


def test_bootstrap_import_filters_and_dedupes(tmp_path):
    paths = make_paths(tmp_path)
    conn = state.open_db(paths.db)
    state.init_db(conn)
    rows = [
        {"Artist": "A", "Song Title": "One", "Lyrics": "माया लाग्छ " * 30, "Year": "2005"},
        {"Artist": "A", "Song Title": "Two", "Lyrics": ""},
        {"Artist": "B", "Song Title": "Three", "Lyrics": "hello world " * 30},
        {"Artist": "A", "Song Title": "One", "Lyrics": "माया लाग्छ " * 30},
    ]
    report = bootstrap.import_rows(conn, rows, source="test", stage="test_stage")
    assert report["added_candidates"] == 1
    assert report["lyrics_saved"] == 1
    assert report["skipped_empty"] == 1
    assert report["skipped_other_script"] == 1
    assert report["skipped_duplicate_sha"] == 1
    assert state.stats(conn)["lyrics_total"] == 1
    extra = conn.execute("SELECT extra_json FROM candidates").fetchone()["extra_json"]
    assert "2005" in extra


def test_bootstrap_import_treated_as_nepali_keeps_romanized(tmp_path):
    paths = make_paths(tmp_path)
    conn = state.open_db(paths.db)
    state.init_db(conn)
    rows = [{"Artist": "B", "Song Title": "Three", "Lyrics": "maya lagcha " * 30}]
    report = bootstrap.import_rows(conn, rows, source="test", stage="test_stage", treated_as_nepali=True)
    assert report["lyrics_saved"] == 1
    assert state.stats(conn)["by_script"] == {"romanized": 1}
