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
GENUINE_SOURCES = ("legacy_932", "rupesh_aryal", "kaggle_genius", "site_paankopat.com", "site_songsdiary.com")
DEFAULT_SEEDS = Path(__file__).resolve().parent / "seeds" / "nepali_artists.txt"


def harvester_artist_list(conn, *, all_artists: bool = False, seeds_path: Path | None = None) -> list[str]:
    if all_artists:
        rows = conn.execute("SELECT DISTINCT artist FROM candidates ORDER BY artist").fetchall()
    else:
        placeholders = ",".join("?" for _ in GENUINE_SOURCES)
        rows = conn.execute(
            f"SELECT DISTINCT artist FROM candidates WHERE source IN ({placeholders}) ORDER BY artist",
            GENUINE_SOURCES,
        ).fetchall()
    ordered: list[str] = []
    seen: set[str] = set()
    for row in rows:
        name = str(row["artist"]).strip()
        folded = name.casefold()
        if not name or folded in EXCLUDED_ARTISTS or folded in seen:
            continue
        seen.add(folded)
        ordered.append(name)
    seeds_path = seeds_path if seeds_path is not None else DEFAULT_SEEDS
    if seeds_path.exists():
        for line in seeds_path.read_text(encoding="utf-8").splitlines():
            name = line.strip()
            folded = name.casefold()
            if not name or name.startswith("#") or folded in seen:
                continue
            seen.add(folded)
            ordered.append(name)
    harvested = {name.casefold() for name in state.harvested_names(conn)}
    return [name for name in ordered if name.casefold() not in harvested]


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
    parser.add_argument(
        "--all-artists",
        action="store_true",
        help="Use every distinct artist in the store (default: genuine sources + seeds)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    client = CachedHttp()
    if args.artist:
        artists = [args.artist]
    else:
        artists = harvester_artist_list(conn, all_artists=args.all_artists)
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
        if "error" not in stats:
            state.mark_harvested(conn, artist, stats.get("records", 0), stats.get("lyrics_saved", 0))
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
    print(json.dumps(state.harvested_stats(conn), ensure_ascii=False, indent=2))
    print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
