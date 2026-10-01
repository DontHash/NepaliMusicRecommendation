"""Structured metrics stream for pipeline runs (R_data/state/metrics.jsonl)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class MetricsWriter:
    """Append-only JSONL writer: one line per event, thread-safe."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def emit(self, kind: str, **fields) -> dict:
        record = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, **fields}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock, self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return record


def read_metrics(path: Path, limit: int | None = None) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    return records[-limit:] if limit else records
