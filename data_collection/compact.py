"""CLI: compact the work store into corpus_raw.csv snapshots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .fetch import MIN_LYRICS_CHARS, acceptable
from .models import LyricsHit
from .normalize import fold
from .prune import priority

KEEP_SNAPSHOTS = 5
CSV_FIELDS = [
    "Category",
    "Title",
    "Artist",
    "Lyrics",
    "source",
    "source_url",
    "stage",
    "script",
    "sha256",
    "duration_s",
    "album",
    "preview_url",
    "fetched_at",
]


def _category(script: str) -> str:
    if script == "romanized":
        return "romanized"
    return "nepali"


def compact(conn, output: Path, *, keep_snapshots: int = KEEP_SNAPSHOTS) -> dict:
    rows = list(state.iter_with_lyrics(conn))
    report = {
        "store_songs": len(rows),
        "kept": 0,
        "dropped_script": 0,
        "dropped_short": 0,
        "dropped_exact_duplicate": 0,
        "dropped_near_duplicate": 0,
    }
    accepted = []
    seen_sha: set[str] = set()
    for row in rows:
        hit = LyricsHit(
            stage=row["stage"],
            lyrics=row["lyrics"],
            source_url=row["source_url"],
            script=row["script"],
            sha256=row["lyrics_sha256"],
        )
        if len(hit.lyrics) < MIN_LYRICS_CHARS or not hit.lyrics.strip():
            report["dropped_short"] += 1
            continue
        ok, _reason = acceptable(hit)
        if not ok:
            report["dropped_script"] += 1
            continue
        if hit.sha256 in seen_sha:
            report["dropped_exact_duplicate"] += 1
            continue
        seen_sha.add(hit.sha256)
        accepted.append(row)

    groups: dict[str, list] = defaultdict(list)
    for row in accepted:
        groups[f"{fold(row['artist'])}|{fold(row['title'])}"].append(row)
    kept = []
    for members in groups.values():
        if len(members) > 1:
            script_rank = {"devanagari": 0, "mixed": 1, "romanized": 2, "unknown": 3}
            members.sort(
                key=lambda r: (
                    priority(r["source"]),
                    script_rank.get(r["script"], 3),
                    -1 if r["synced"] else 0,
                    r["id"],
                )
            )
            report["dropped_near_duplicate"] += len(members) - 1
        kept.append(members[0])
    report["kept"] = len(kept)
    kept.sort(key=lambda r: (fold(r["artist"]), fold(r["title"])))

    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".csv.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in kept:
            extra = json.loads(row["extra_json"]) if row["extra_json"] else {}
            writer.writerow(
                {
                    "Category": _category(row["script"]),
                    "Title": row["title"],
                    "Artist": row["artist"],
                    "Lyrics": row["lyrics"],
                    "source": row["source"],
                    "source_url": row["source_url"] or extra.get("url", ""),
                    "stage": row["stage"],
                    "script": row["script"],
                    "sha256": row["lyrics_sha256"],
                    "duration_s": row["duration_s"] or "",
                    "album": row["album"] or "",
                    "preview_url": row["preview_url"] or "",
                    "fetched_at": row["fetched_at"] or "",
                }
            )
    os.replace(tmp, output)

    snapshots_dir = output.parent / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = snapshots_dir / f"{output.stem}_{stamp}.csv"
    data = output.read_bytes()
    snapshot.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    (snapshot.with_suffix(".csv.sha256")).write_text(digest + "\n", encoding="utf-8")
    stale = sorted(snapshots_dir.glob(f"{output.stem}_*.csv"))
    for old in stale[:-keep_snapshots]:
        old.unlink(missing_ok=True)
        old.with_suffix(".csv.sha256").unlink(missing_ok=True)

    report["output"] = str(output)
    report["snapshot"] = str(snapshot)
    report["sha256"] = digest
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compact store into corpus_raw.csv.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--output", type=Path, default=cfg.DEFAULT_PATHS.corpus / "corpus_raw.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    report = compact(conn, args.output)
    paths = cfg.DEFAULT_PATHS.ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"compact_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report -> {target}")


if __name__ == "__main__":
    main()
