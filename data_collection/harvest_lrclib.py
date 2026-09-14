"""CLI: bulk-harvest LRCLIB catalogs for known artists.

One artist-level search returns many records, which is far more efficient (and
kinder to LRCLIB) than per-candidate queries. Records are ingested as
candidates + lyrics, adding songs beyond the enumeration lists.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .fetch import acceptable
from .http import CachedHttp
from .models import Candidate, LyricsHit
from .normalize import detect_script, lyrics_sha
from .sources import lrclib

EXCLUDED_ARTISTS = {"genius romanizations", "genius translations", "genius nepali translations", "various artists"}


def harvester_artist_list(conn) -> list[str]:
    rows = conn.execute("SELECT DISTINCT artist FROM candidates ORDER BY artist").fetchall()
    artists = [str(row["artist"]).strip() for row in rows]
    return [a for a in artists if a and a.casefold() not in EXCLUDED_ARTISTS]


def harvest_artist(conn, client: CachedHttp, artist: str) -> dict:
    stats = {"artist": artist, "records": 0, "new_candidates": 0, "lyrics_saved": 0, "rejected": 0, "duplicates": 0}
    records = lrclib.search_lyrics(client, artist=artist)
    stats["records"] = len(records)
    for record in records:
        hit = lrclib.record_to_hit(record)
        if hit is None:
            continue
        ok, _reason = acceptable(hit)
        if not ok:
            stats["rejected"] += 1
            continue
        artist_name = str(record.get("artistName") or artist).strip()
        title = str(record.get("trackName") or "").strip()
        if not title or not artist_name:
            continue
        duration = record.get("duration")
        candidate = Candidate(
            source="lrclib",
            source_id=str(record.get("id")) if record.get("id") is not None else None,
            artist=artist_name,
            title=title,
            duration_s=int(duration) if isinstance(duration, (int, float)) and duration > 0 else None,
            extra={"album": str(record.get("albumName") or "")} if record.get("albumName") else {},
        )
        existing_sha = state.find_by_lyrics_sha(conn, hit.sha256)
        added, _dupes = state.enqueue(conn, [candidate])
        db_row = state.get_by_dedupe_key(conn, candidate.dedupe_key)
        candidate_id = db_row["id"]
        if added:
            stats["new_candidates"] += 1
        if existing_sha is not None and existing_sha != candidate_id:
            stats["duplicates"] += 1
            continue
        if added or not state.candidate_has_lyrics(conn, candidate_id):
            state.save_lyrics(conn, candidate_id, hit)
            stats["lyrics_saved"] += 1
    return stats


def write_report(report: dict, paths=None) -> Path:
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"harvest_lrclib_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Harvest LRCLIB catalogs for known artists.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--limit", type=int, default=0, help="Max artists this run")
    parser.add_argument("--artist", type=str, default=None)
    parser.add_argument("--delay", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    client = CachedHttp()
    artists = [args.artist] if args.artist else harvester_artist_list(conn)
    if args.limit:
        artists = artists[: args.limit]
    print(f"artists to harvest: {len(artists)}")
    totals = {"records": 0, "new_candidates": 0, "lyrics_saved": 0, "rejected": 0, "duplicates": 0}
    per_artist = []
    for index, artist in enumerate(artists, start=1):
        try:
            stats = harvest_artist(conn, client, artist)
        except Exception as exc:
            stats = {"artist": artist, "error": f"{type(exc).__name__}: {exc}", "records": 0, "new_candidates": 0, "lyrics_saved": 0, "rejected": 0, "duplicates": 0}
        state.set_meta(conn, "harvest_lrclib:last_artist", artist)
        for key in totals:
            totals[key] += stats.get(key, 0)
        per_artist.append(stats)
        print(
            f"[{index}/{len(artists)}] {artist}: records={stats.get('records', 0)} "
            f"new={stats.get('new_candidates', 0)} lyrics={stats.get('lyrics_saved', 0)} dupes={stats.get('duplicates', 0)}"
        )
        if args.delay:
            time.sleep(args.delay)
    report = {"totals": totals, "artists": len(artists), "per_artist": per_artist}
    path = write_report(report)
    print(json.dumps(totals, ensure_ascii=False, indent=2))
    print(f"report -> {path}")
    print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
