"""Lease, retry-budget and DLQ tests for the collection work queue."""

from __future__ import annotations

import csv
import sqlite3
import threading
from pathlib import Path

from data_collection import state
from data_collection.models import Candidate


def _seed(conn, count: int, prefix: str = "song") -> None:
    candidates = [
        Candidate(source="deezer", artist=f"Artist {index}", title=f"{prefix} {index}",
                  duration_s=200 + index)
        for index in range(count)
    ]
    state.enqueue(conn, candidates)


def _open(tmp_path: Path):
    conn = state.open_db(tmp_path / "db.sqlite")
    state.init_db(conn)
    return conn


def test_claim_batch_is_atomic_under_concurrency(tmp_path: Path):
    db = tmp_path / "work.sqlite"
    setup = state.open_db(db)
    state.init_db(setup)
    _seed(setup, 12)
    setup.close()

    results: dict[str, list[int]] = {}
    barrier = threading.Barrier(2)

    def worker(name: str) -> None:
        conn = state.open_db(db)
        state.init_db(conn)
        barrier.wait()
        results[name] = [row["id"] for row in state.claim_batch(conn, name, limit=8)]
        conn.close()

    threads = [threading.Thread(target=worker, args=(f"worker-{i}",)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    first, second = results["worker-0"], results["worker-1"]
    assert first and second
    assert set(first).isdisjoint(second)
    assert sorted(first + second) == list(range(1, 13))


def test_live_lease_survives_reset_and_expired_recovers(tmp_path: Path):
    conn = _open(tmp_path)
    _seed(conn, 2)
    claimed = state.claim_batch(conn, "w1", lease_seconds=900)
    assert len(claimed) == 2

    assert state.reset_orphaned(conn) == 0  # live leases are not stolen
    conn.execute("UPDATE candidates SET lease_expires_at=datetime('now', '-1 seconds')")
    conn.commit()
    assert state.reset_orphaned(conn) == 2
    assert state.stats(conn)["candidates"].get("new") == 2


def test_attempt_budget_sweep_dlq_and_requeue(tmp_path: Path):
    conn = _open(tmp_path)
    _seed(conn, 1)
    candidate_id = state.claim_batch(conn, "w1", max_attempts=1)[0]["id"]
    state.mark_status(conn, candidate_id, "new", "error:timeout", owner="w1")

    assert state.sweep_exhausted(conn, max_attempts=1) == 1
    row = conn.execute("SELECT status, last_error FROM candidates WHERE id=?",
                       (candidate_id,)).fetchone()
    assert row["status"] == "dead" and row["last_error"]

    out = tmp_path / "dlq.csv"
    assert state.export_dead_letters(conn, out) == 1
    exported = list(csv.DictReader(out.open(encoding="utf-8")))
    assert exported[0]["id"] == str(candidate_id)

    assert state.requeue(conn, status="dead", reset_attempts=True) == 1
    row = conn.execute("SELECT status, attempt_count FROM candidates WHERE id=?",
                       (candidate_id,)).fetchone()
    assert row["status"] == "new" and row["attempt_count"] == 0


def test_mark_status_respects_other_workers_lease(tmp_path: Path):
    conn = _open(tmp_path)
    _seed(conn, 1)
    candidate_id = state.claim_batch(conn, "w1")[0]["id"]

    assert state.mark_status(conn, candidate_id, "missed", "nope", owner="intruder") == 0
    assert state.stats(conn)["candidates"]["fetching"] == 1
    assert state.mark_status(conn, candidate_id, "missed", "done by owner", owner="w1") == 1
    assert state.stats(conn)["candidates"]["missed"] == 1


def test_claim_pages_retry_budget_and_orphans(tmp_path: Path):
    conn = _open(tmp_path)
    state.register_pages(conn, ["https://d/1", "https://d/2"], domain="d")

    claimed = state.claim_pages(conn, "c1", domain="d", max_attempts=2)
    assert {row["url"] for row in claimed} == {"https://d/1", "https://d/2"}
    assert state.claim_pages(conn, "c2", domain="d", max_attempts=2) == []  # all leased
    assert state.reset_orphaned_pages(conn) == 0  # live lease

    assert state.retry_page(conn, "https://d/1", "parse_failed", max_attempts=2) == "new"
    assert state.retry_page(conn, "https://d/2", "fetch_failed", max_attempts=1) == "dead"
    again = state.claim_pages(conn, "c2", domain="d", max_attempts=2)
    assert [row["url"] for row in again] == ["https://d/1"]


def test_migration_adds_lease_columns_to_existing_store(tmp_path: Path):
    db = tmp_path / "old.sqlite"
    raw = sqlite3.connect(db)
    raw.executescript(
        """
        CREATE TABLE candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL, source_id TEXT, artist TEXT NOT NULL, title TEXT NOT NULL,
            album TEXT, duration_s INTEGER, preview_url TEXT, isrc TEXT,
            dedupe_key TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'new',
            attempt_count INTEGER NOT NULL DEFAULT 0, last_error TEXT, extra_json TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE pages (
            url TEXT PRIMARY KEY, domain TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
            title TEXT, artist TEXT, candidate_id INTEGER,
            discovered_at TEXT NOT NULL DEFAULT (datetime('now')), fetched_at TEXT
        );
        """
    )
    raw.commit()
    raw.close()

    conn = state.open_db(db)
    state.init_db(conn)
    candidate_columns = {row["name"] for row in conn.execute("PRAGMA table_info(candidates)")}
    page_columns = {row["name"] for row in conn.execute("PRAGMA table_info(pages)")}
    assert {"lease_owner", "lease_expires_at"} <= candidate_columns
    assert {"attempt_count", "last_error", "lease_owner", "lease_expires_at"} <= page_columns
