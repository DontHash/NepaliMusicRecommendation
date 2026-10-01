"""User-event capture for the feedback loop (DE6).

SQLite store at ``R_data/state/events.sqlite`` (override
``PROJECTR_EVENTS_DB``). Events are validated against an explicit schema,
inserted in batches inside one transaction, and retained for 90 days.

Privacy: no PII is expected. Session ids are client-generated random strings;
only the fields below are stored, and ``prune_events`` enforces the retention
window.

  python -m web_app.events stats
  python -m web_app.events prune --keep-days 90
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "R_data" / "state" / "events.sqlite"
RETENTION_DAYS = 90
MAX_BATCH = 200
MAX_METADATA_BYTES = 4096
FUTURE_TOLERANCE_SECONDS = 300

EVENT_TYPES = frozenset({
    "impression", "click", "like", "skip", "search", "play_audio", "view_song",
})

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    session_id TEXT,
    user_id TEXT,
    event_type TEXT NOT NULL,
    song_id INTEGER,
    query TEXT,
    rank INTEGER,
    metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, ts);
CREATE INDEX IF NOT EXISTS idx_events_song ON events(song_id);
"""


def default_db() -> Path:
    return Path(os.environ.get("PROJECTR_EVENTS_DB", DEFAULT_DB))


def open_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path is not None else default_db()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=30.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=5000")
    connection.executescript(SCHEMA)
    connection.commit()
    return connection


def validate_event(payload) -> tuple[dict | None, str]:
    """Validate one event; returns (cleaned, "") or (None, reason)."""
    if not isinstance(payload, dict):
        return None, "event must be an object"
    event_type = payload.get("event_type")
    if event_type not in EVENT_TYPES:
        return None, f"event_type must be one of {sorted(EVENT_TYPES)}"

    cleaned: dict = {"event_type": event_type, "session_id": None, "user_id": None,
                     "song_id": None, "query": None, "rank": None, "metadata_json": None}

    timestamp = payload.get("ts")
    if timestamp is not None:
        if not isinstance(timestamp, str):
            return None, "ts must be an ISO-8601 string"
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError:
            return None, "ts is not ISO-8601"
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if (parsed - datetime.now(timezone.utc)).total_seconds() > FUTURE_TOLERANCE_SECONDS:
            return None, "ts is too far in the future"
        cleaned["ts"] = parsed.astimezone(timezone.utc).isoformat()
    else:
        cleaned["ts"] = datetime.now(timezone.utc).isoformat()

    for field in ("session_id", "user_id"):
        value = payload.get(field)
        if value is not None:
            if not isinstance(value, str) or len(value) > 64:
                return None, f"{field} must be a string up to 64 chars"
            cleaned[field] = value

    song_id = payload.get("song_id")
    if song_id is not None:
        try:
            song_id = int(song_id)
        except (TypeError, ValueError):
            return None, "song_id must be an integer"
        if song_id < 0:
            return None, "song_id must be >= 0"
        cleaned["song_id"] = song_id

    query = payload.get("query")
    if query is not None:
        if not isinstance(query, str) or len(query) > 200:
            return None, "query must be a string up to 200 chars"
        cleaned["query"] = query

    rank = payload.get("rank")
    if rank is not None:
        try:
            rank = int(rank)
        except (TypeError, ValueError):
            return None, "rank must be an integer"
        if not 0 <= rank <= 1000:
            return None, "rank must be between 0 and 1000"
        cleaned["rank"] = rank

    metadata = payload.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            return None, "metadata must be an object"
        encoded = json.dumps(metadata, ensure_ascii=False)
        if len(encoded.encode("utf-8")) > MAX_METADATA_BYTES:
            return None, "metadata is too large"
        cleaned["metadata_json"] = encoded

    return cleaned, ""


def insert_events(connection: sqlite3.Connection, events: list) -> dict:
    """Validate and insert a batch in one transaction; per-row reject reasons."""
    accepted: list[dict] = []
    rejected: list[dict] = []
    for index, payload in enumerate(events):
        cleaned, reason = validate_event(payload)
        if cleaned is None:
            rejected.append({"index": index, "reason": reason})
        else:
            accepted.append(cleaned)
    if accepted:
        with connection:  # single transaction
            connection.executemany(
                "INSERT INTO events (ts, session_id, user_id, event_type, song_id, "
                "query, rank, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(event["ts"], event["session_id"], event["user_id"], event["event_type"],
                  event["song_id"], event["query"], event["rank"], event["metadata_json"])
                 for event in accepted],
            )
    return {"accepted": len(accepted), "rejected": rejected}


def prune_events(connection: sqlite3.Connection, keep_days: int = RETENTION_DAYS) -> int:
    with connection:
        cursor = connection.execute(
            "DELETE FROM events WHERE ts < datetime('now', ?)", (f"-{int(keep_days)} days",))
    return cursor.rowcount


def event_stats(connection: sqlite3.Connection) -> dict:
    by_type = {row["event_type"]: row["n"] for row in connection.execute(
        "SELECT event_type, COUNT(*) AS n FROM events GROUP BY event_type")}
    total = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    last_24h = connection.execute(
        "SELECT COUNT(*) FROM events WHERE ts >= datetime('now', '-1 day')").fetchone()[0]
    last = connection.execute("SELECT MAX(ts) FROM events").fetchone()[0]
    return {"total": int(total), "by_type": by_type, "last_24h": int(last_24h),
            "last_ts": last}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["stats", "prune"])
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("--keep-days", type=int, default=RETENTION_DAYS)
    args = parser.parse_args()

    connection = open_db(args.db)
    try:
        if args.command == "stats":
            print(json.dumps(event_stats(connection), ensure_ascii=False, indent=2))
        else:
            removed = prune_events(connection, args.keep_days)
            print(f"pruned {removed} events older than {args.keep_days} days")
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
