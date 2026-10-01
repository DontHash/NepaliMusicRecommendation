"""SQLite run history for the pipeline runner (R_data/state/runs.sqlite)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    targets TEXT,
    options TEXT,
    git_sha TEXT
);
CREATE TABLE IF NOT EXISTS asset_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    asset TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    duration_s REAL,
    message TEXT,
    metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_asset_runs_asset ON asset_runs(asset, id DESC);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def start_run(self, *, targets, options: dict, git_sha: str | None = None) -> int:
        cursor = self.connection.execute(
            "INSERT INTO runs (started_at, status, targets, options, git_sha) "
            "VALUES (?, 'running', ?, ?, ?)",
            (utcnow(), ",".join(targets), json.dumps(options, default=str), git_sha),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str) -> None:
        self.connection.execute(
            "UPDATE runs SET finished_at = ?, status = ? WHERE id = ?",
            (utcnow(), status, run_id),
        )
        self.connection.commit()

    def record_asset(self, run_id: int, *, asset: str, status: str,
                     started_at: str | None = None, finished_at: str | None = None,
                     duration_s: float | None = None, message: str = "",
                     metadata: dict | None = None) -> None:
        self.connection.execute(
            "INSERT INTO asset_runs (run_id, asset, status, started_at, finished_at, "
            "duration_s, message, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, asset, status, started_at, finished_at, duration_s, message,
             json.dumps(metadata or {}, default=str)),
        )
        self.connection.commit()

    def last_status(self, asset: str) -> str | None:
        row = self.connection.execute(
            "SELECT status FROM asset_runs WHERE asset = ? ORDER BY id DESC LIMIT 1",
            (asset,),
        ).fetchone()
        return row["status"] if row else None

    def run_assets(self, run_id: int) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM asset_runs WHERE run_id = ? ORDER BY id", (run_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    def history(self, limit: int = 20) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def latest_assets(self, limit: int = 1) -> list[dict]:
        row = self.connection.execute(
            "SELECT id FROM runs WHERE status != 'running' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchone()
        return self.run_assets(row["id"]) if row else []

    def close(self) -> None:
        self.connection.close()
