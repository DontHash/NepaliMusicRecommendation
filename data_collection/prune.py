"""Prune duplicate candidates before lyrics fetching.

Dedupe key for fetch prioritisation ignores duration (metadata varies between
catalogs): two candidates with the same folded artist+title are the same song.
The candidate with the highest source priority is kept 'new'; the rest are
marked 'duplicate'.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .normalize import fold

SOURCE_PRIORITY = {
    "legacy_932": 0,
    "rupesh_aryal": 1,
    "kaggle_genius": 2,
    "site_paankopat.com": 3,
    "site_songsdiary.com": 3,
    "deezer": 4,
    "itunes": 5,
}


def priority(source: str) -> int:
    return SOURCE_PRIORITY.get(source, 6)


def prune(conn) -> dict:
    rows = conn.execute(
        """
        SELECT c.id, c.source, c.artist, c.title, c.duration_s
        FROM candidates c
        LEFT JOIN lyrics l ON l.candidate_id = c.id
        WHERE c.status = 'new' AND l.candidate_id IS NULL
        """
    ).fetchall()
    groups: dict[str, list] = defaultdict(list)
    for row in rows:
        key = f"{fold(row['artist'])}|{fold(row['title'])}"
        groups[key].append(row)

    duplicate_ids: list[int] = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda r: (priority(r["source"]), 0 if r["duration_s"] else 1, r["id"]))
        duplicate_ids.extend(row["id"] for row in members[1:])

    if duplicate_ids:
        conn.executemany(
            "UPDATE candidates SET status='duplicate', updated_at=datetime('now') WHERE id=?",
            [(cid,) for cid in duplicate_ids],
        )
        conn.commit()
    return {
        "new_before": len(rows),
        "groups": len(groups),
        "duplicates_marked": len(duplicate_ids),
        "new_after": len(rows) - len(duplicate_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prune duplicate new candidates.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    report = prune(conn)
    paths = cfg.DEFAULT_PATHS.ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"prune_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report -> {target}")


if __name__ == "__main__":
    main()
