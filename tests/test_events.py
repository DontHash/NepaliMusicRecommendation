"""Hermetic tests for the event store, validation and retention (DE6b)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from web_app import events


def _db(tmp_path: Path):
    return events.open_db(tmp_path / "events.sqlite")


def test_validate_event_accepts_and_sets_server_ts():
    cleaned, reason = events.validate_event({
        "event_type": "click", "song_id": 12, "rank": 3,
        "session_id": "abc", "metadata": {"source": "search"}})
    assert reason == ""
    assert cleaned["song_id"] == 12 and cleaned["rank"] == 3
    assert cleaned["metadata_json"] == '{"source": "search"}'
    datetime.fromisoformat(cleaned["ts"])  # server timestamp present


def test_validate_event_rejects_bad_payloads():
    cases = [
        ({}, "event_type"),
        ({"event_type": "dance"}, "event_type"),
        ({"event_type": "click", "song_id": "x"}, "song_id"),
        ({"event_type": "click", "song_id": -5}, "song_id"),
        ({"event_type": "click", "rank": 5000}, "rank"),
        ({"event_type": "click", "query": "q" * 300}, "query"),
        ({"event_type": "click", "session_id": "s" * 100}, "session_id"),
        ({"event_type": "click", "metadata": "nope"}, "metadata"),
        ({"event_type": "click", "ts": "not-a-date"}, "ts"),
        ({"event_type": "click", "ts": 12345}, "ts"),
    ]
    for payload, expected in cases:
        cleaned, reason = events.validate_event(payload)
        assert cleaned is None, payload
        assert expected in reason, (payload, reason)


def test_future_timestamp_rejected():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    cleaned, reason = events.validate_event({"event_type": "click", "ts": future})
    assert cleaned is None and "future" in reason


def test_oversized_metadata_rejected():
    cleaned, reason = events.validate_event({
        "event_type": "click", "metadata": {"blob": "x" * events.MAX_METADATA_BYTES}})
    assert cleaned is None and "large" in reason


def test_insert_batch_partial_acceptance_and_stats(tmp_path: Path):
    connection = _db(tmp_path)
    result = events.insert_events(connection, [
        {"event_type": "click", "song_id": 1},
        {"event_type": "bogus"},
        {"event_type": "impression", "song_id": 2},
    ])
    assert result["accepted"] == 2
    assert [row["index"] for row in result["rejected"]] == [1]

    stats = events.event_stats(connection)
    assert stats["total"] == 2
    assert stats["by_type"] == {"click": 1, "impression": 1}
    assert stats["last_24h"] == 2 and stats["last_ts"]


def test_prune_retention_window(tmp_path: Path):
    connection = _db(tmp_path)
    old_ts = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    events.insert_events(connection, [
        {"event_type": "click", "ts": old_ts},
        {"event_type": "click"},
    ])
    assert events.prune_events(connection, keep_days=90) == 1
    assert events.event_stats(connection)["total"] == 1


def test_env_override_db_path(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PROJECTR_EVENTS_DB", str(tmp_path / "custom.sqlite"))
    assert events.default_db() == tmp_path / "custom.sqlite"
