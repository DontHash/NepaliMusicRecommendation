"""Inspection CLI: queue stats, random samples, duplicate checks."""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from pathlib import Path

from . import config as cfg
from . import state


def duplicate_checks(conn: sqlite3.Connection) -> dict:
    sha_dupes = conn.execute(
        """
        SELECT COUNT(*) AS n FROM (
            SELECT lyrics_sha256 FROM lyrics GROUP BY lyrics_sha256 HAVING COUNT(*) > 1
        )
        """
    ).fetchone()["n"]
    key_dupes = conn.execute(
        """
        SELECT COUNT(*) AS n FROM (
            SELECT dedupe_key FROM candidates GROUP BY dedupe_key HAVING COUNT(*) > 1
        )
        """
    ).fetchone()["n"]
    return {"duplicate_lyrics_hashes": sha_dupes, "duplicate_dedupe_keys": key_dupes}


def samples(conn: sqlite3.Connection, count: int, seed: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.id, c.source, c.artist, c.title, l.script, l.stage,
               substr(l.lyrics, 1, 80) AS snippet
        FROM candidates c JOIN lyrics l ON l.candidate_id = c.id
        """
    ).fetchall()
    rng = random.Random(seed)
    picked = rng.sample(rows, min(count, len(rows)))
    return [
        {
            "id": row["id"],
            "source": row["source"],
            "artist": row["artist"],
            "title": row["title"],
            "script": row["script"],
            "stage": row["stage"],
            "snippet": row["snippet"].replace("\n", " "),
        }
        for row in picked
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the Phase A work queue.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--samples", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.db.exists():
        raise SystemExit(f"no database at {args.db}; run bootstrap/enumeration first")
    conn = state.open_db(args.db)
    payload = state.stats(conn)
    payload["duplicates"] = duplicate_checks(conn)
    if args.samples:
        payload["samples"] = samples(conn, args.samples, args.seed)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
