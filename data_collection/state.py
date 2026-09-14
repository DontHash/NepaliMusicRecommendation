"""SQLite work queue for corpus collection (WAL, resumable, idempotent)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Candidate, LyricsHit
from .normalize import make_dedupe_key

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT,
    artist TEXT NOT NULL,
    title TEXT NOT NULL,
    album TEXT,
    duration_s INTEGER,
    preview_url TEXT,
    isrc TEXT,
    dedupe_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'new',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    extra_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS lyrics (
    candidate_id INTEGER PRIMARY KEY REFERENCES candidates(id),
    stage TEXT NOT NULL,
    source_url TEXT,
    lyrics TEXT NOT NULL,
    synced INTEGER NOT NULL DEFAULT 0,
    script TEXT,
    lyrics_sha256 TEXT NOT NULL,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER,
    stage TEXT NOT NULL,
    outcome TEXT NOT NULL,
    error_class TEXT,
    latency_ms INTEGER,
    ts TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pages (
    url TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    title TEXT,
    artist TEXT,
    candidate_id INTEGER,
    discovered_at TEXT NOT NULL DEFAULT (datetime('now')),
    fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS harvested_artists (
    name TEXT PRIMARY KEY,
    records INTEGER NOT NULL DEFAULT 0,
    lyrics_saved INTEGER NOT NULL DEFAULT 0,
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_pages_domain_status ON pages(domain, status);
CREATE INDEX IF NOT EXISTS idx_lyrics_sha ON lyrics(lyrics_sha256);
"""


def open_db(path: Path | str) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def enqueue(conn: sqlite3.Connection, candidates: list[Candidate]) -> tuple[int, int]:
    added = dupes = 0
    for cand in candidates:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO candidates
                (source, source_id, artist, title, album, duration_s,
                 preview_url, isrc, dedupe_key, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cand.source,
                cand.source_id,
                cand.artist,
                cand.title,
                cand.album,
                cand.duration_s,
                cand.preview_url,
                cand.isrc,
                cand.dedupe_key,
                json.dumps(cand.extra, ensure_ascii=False) if cand.extra else None,
            ),
        )
        if cur.rowcount:
            added += 1
        else:
            dupes += 1
    conn.commit()
    return added, dupes


def update_metadata(
    conn: sqlite3.Connection,
    candidate_id: int,
    *,
    album: str | None = None,
    duration_s: int | None = None,
    preview_url: str | None = None,
    isrc: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE candidates SET
            album = COALESCE(album, ?),
            duration_s = COALESCE(duration_s, ?),
            preview_url = COALESCE(preview_url, ?),
            isrc = COALESCE(isrc, ?),
            updated_at = datetime('now')
        WHERE id = ?
        """,
        (album, duration_s, preview_url, isrc, candidate_id),
    )
    conn.commit()


def record_attempt(
    conn: sqlite3.Connection,
    candidate_id: int | None,
    stage: str,
    outcome: str,
    error_class: str | None = None,
    latency_ms: int | None = None,
) -> None:
    conn.execute(
        "INSERT INTO attempts(candidate_id, stage, outcome, error_class, latency_ms) VALUES (?, ?, ?, ?, ?)",
        (candidate_id, stage, outcome, error_class, latency_ms),
    )
    conn.commit()


def mark_fetching(conn: sqlite3.Connection, candidate_ids: list[int]) -> None:
    conn.executemany(
        "UPDATE candidates SET status='fetching', attempt_count=attempt_count+1, updated_at=datetime('now') WHERE id=?",
        [(cid,) for cid in candidate_ids],
    )
    conn.commit()


def reset_orphaned(conn: sqlite3.Connection) -> int:
    cur = conn.execute("UPDATE candidates SET status='new', updated_at=datetime('now') WHERE status='fetching'")
    conn.commit()
    return cur.rowcount


def mark_status(conn: sqlite3.Connection, candidate_id: int, status: str, error: str | None = None) -> None:
    conn.execute(
        "UPDATE candidates SET status=?, last_error=?, updated_at=datetime('now') WHERE id=?",
        (status, error, candidate_id),
    )
    conn.commit()


def requeue(conn: sqlite3.Connection, status: str = "missed", reset_attempts: bool = False) -> int:
    clause = "status='new', attempt_count=0" if reset_attempts else "status='new'"
    cur = conn.execute(f"UPDATE candidates SET {clause}, updated_at=datetime('now') WHERE status=?", (status,))
    conn.commit()
    return cur.rowcount


def save_lyrics(conn: sqlite3.Connection, candidate_id: int, hit: LyricsHit) -> None:
    conn.execute(
        """
        INSERT INTO lyrics(candidate_id, stage, source_url, lyrics, synced, script, lyrics_sha256)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(candidate_id) DO UPDATE SET
            stage=excluded.stage,
            source_url=excluded.source_url,
            lyrics=excluded.lyrics,
            synced=excluded.synced,
            script=excluded.script,
            lyrics_sha256=excluded.lyrics_sha256,
            fetched_at=datetime('now')
        """,
        (
            candidate_id,
            hit.stage,
            hit.source_url,
            hit.lyrics,
            int(hit.synced),
            hit.script,
            hit.sha256,
        ),
    )
    mark_status(conn, candidate_id, "done")


def next_batch(conn: sqlite3.Connection, limit: int | None = None, status: str = "new", max_attempts: int = 3) -> list[sqlite3.Row]:
    query = "SELECT * FROM candidates WHERE status=? AND attempt_count<? ORDER BY id"
    params: list = [status, max_attempts]
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    return conn.execute(query, params).fetchall()


def stats(conn: sqlite3.Connection) -> dict:
    status_rows = conn.execute("SELECT status, COUNT(*) AS n FROM candidates GROUP BY status").fetchall()
    source_rows = conn.execute("SELECT source, COUNT(*) AS n FROM candidates GROUP BY source").fetchall()
    script_rows = conn.execute("SELECT script, COUNT(*) AS n FROM lyrics GROUP BY script").fetchall()
    stage_rows = conn.execute("SELECT stage, COUNT(*) AS n FROM lyrics GROUP BY stage").fetchall()
    total_lyrics = conn.execute("SELECT COUNT(*) AS n FROM lyrics").fetchone()["n"]
    attempts = conn.execute("SELECT COUNT(*) AS n FROM attempts").fetchone()["n"]
    return {
        "candidates": {row["status"]: row["n"] for row in status_rows},
        "by_source": {row["source"]: row["n"] for row in source_rows},
        "lyrics_total": total_lyrics,
        "by_stage": {row["stage"]: row["n"] for row in stage_rows},
        "by_script": {row["script"]: row["n"] for row in script_rows},
        "attempts": attempts,
    }


def iter_with_lyrics(conn: sqlite3.Connection):
    return conn.execute(
        """
        SELECT c.id, c.source, c.source_id, c.artist, c.title, c.album, c.duration_s,
               c.preview_url, c.isrc, c.extra_json,
               l.stage, l.source_url, l.lyrics, l.synced, l.script, l.lyrics_sha256, l.fetched_at
        FROM candidates c
        JOIN lyrics l ON l.candidate_id = c.id
        ORDER BY c.id
        """
    )


def find_by_lyrics_sha(conn: sqlite3.Connection, sha: str) -> int | None:
    row = conn.execute("SELECT candidate_id FROM lyrics WHERE lyrics_sha256=? LIMIT 1", (sha,)).fetchone()
    return row["candidate_id"] if row else None


def get_by_dedupe_key(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM candidates WHERE dedupe_key=?", (key,)).fetchone()


def candidate_has_lyrics(conn: sqlite3.Connection, candidate_id: int) -> bool:
    row = conn.execute("SELECT 1 FROM lyrics WHERE candidate_id=?", (candidate_id,)).fetchone()
    return row is not None


def existing_dedupe_keys(conn: sqlite3.Connection) -> set[str]:
    return {row["dedupe_key"] for row in conn.execute("SELECT dedupe_key FROM candidates")}


def register_pages(conn: sqlite3.Connection, urls: list[str], domain: str) -> int:
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO pages(url, domain) VALUES (?, ?)",
        [(url, domain) for url in urls],
    )
    conn.commit()
    return conn.total_changes - before


def next_pages(conn: sqlite3.Connection, domain: str | None = None, limit: int | None = None, status: str = "new") -> list[sqlite3.Row]:
    query = "SELECT * FROM pages WHERE status=?"
    params: list = [status]
    if domain:
        query += " AND domain=?"
        params.append(domain)
    query += " ORDER BY url"
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    return conn.execute(query, params).fetchall()


def mark_page(
    conn: sqlite3.Connection,
    url: str,
    status: str,
    *,
    candidate_id: int | None = None,
    title: str | None = None,
    artist: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE pages SET status=?, candidate_id=COALESCE(?, candidate_id),
               title=COALESCE(?, title), artist=COALESCE(?, artist),
               fetched_at=datetime('now')
        WHERE url=?
        """,
        (status, candidate_id, title, artist, url),
    )
    conn.commit()


def update_candidate_meta(conn: sqlite3.Connection, candidate_id: int, *, artist: str | None = None, title: str | None = None) -> bool:
    row = conn.execute(
        "SELECT artist, title, duration_s FROM candidates WHERE id=?", (candidate_id,)
    ).fetchone()
    if row is None:
        return False
    new_artist = artist or row["artist"]
    new_title = title or row["title"]
    new_key = make_dedupe_key(new_artist, new_title, row["duration_s"])
    try:
        conn.execute(
            "UPDATE candidates SET artist=?, title=?, dedupe_key=?, updated_at=datetime('now') WHERE id=?",
            (new_artist, new_title, new_key, candidate_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE candidates SET artist=?, title=?, updated_at=datetime('now') WHERE id=?",
            (new_artist, new_title, candidate_id),
        )
        conn.commit()
        return False


def page_stats(conn: sqlite3.Connection) -> dict:
    rows = conn.execute("SELECT domain, status, COUNT(*) AS n FROM pages GROUP BY domain, status").fetchall()
    out: dict[str, dict[str, int]] = {}
    for row in rows:
        out.setdefault(row["domain"], {})[row["status"]] = row["n"]
    return out


def mark_harvested(conn: sqlite3.Connection, name: str, records: int = 0, lyrics_saved: int = 0) -> None:
    conn.execute(
        """
        INSERT INTO harvested_artists(name, records, lyrics_saved) VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            records=excluded.records,
            lyrics_saved=excluded.lyrics_saved,
            fetched_at=datetime('now')
        """,
        (name, records, lyrics_saved),
    )
    conn.commit()


def harvested_names(conn: sqlite3.Connection) -> set[str]:
    return {row["name"] for row in conn.execute("SELECT name FROM harvested_artists")}


def harvested_stats(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS artists, SUM(records) AS records, SUM(lyrics_saved) AS lyrics FROM harvested_artists"
    ).fetchone()
    return {
        "artists": row["artists"] or 0,
        "records": row["records"] or 0,
        "lyrics_saved": row["lyrics"] or 0,
    }
