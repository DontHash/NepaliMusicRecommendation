"""Fetch lyrics for audio tracks from LRCLIB (resumable, disk-cached, rate-limited).

Reads R_data/audio/audio_tracks.csv (built by build_manifest.py) and writes
R_data/audio/audio_lyrics.jsonl one line per unique track. Re-running skips
tracks already present, so it is safe to stop and resume.

Usage:
  python scripts/audio/fetch_lyrics.py --limit 40          # validation sample
  python scripts/audio/fetch_lyrics.py                     # all gaps
  python scripts/audio/fetch_lyrics.py --all --deep        # everything, 3rd search fallback
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402


def already_done(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["track_key"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def fetch_one(client, track: dict, *, deep: bool, with_fallback: bool) -> dict:
    from data_collection.sources import lrclib

    artist = utils.primary_artist(track["artist"]).strip() or track["artist"]
    title = utils.strip_junk(track["title"]).strip() or track["title"]
    duration = int(float(track["duration_s"])) if track.get("duration_s") else None

    record = None
    provider = ""
    try:
        record = lrclib.get_lyrics(client, artist=artist, title=title, duration=duration)
        if record:
            provider = "lrclib_get"
        if record is None:
            results = lrclib.search_lyrics(client, artist=artist, title=title)
            record = lrclib.pick_best(results or [], duration=duration, artist=artist, title=title)
            if record:
                provider = "lrclib_search"
        if record is None and deep:
            results = lrclib.search_lyrics(client, query=title)
            record = lrclib.pick_best(results or [], duration=duration, artist=artist, title=title)
            if record:
                provider = "lrclib_query"
    except Exception as error:  # noqa: BLE001 - keep the batch alive
        return {"found": False, "provider": "error", "error": str(error)[:300]}

    if record is None and with_fallback:
        from data_collection.sources.syncedlyrics_client import fetch_lyrics

        text = fetch_lyrics(title, artist)
        if text:
            return {
                "found": True,
                "provider": "syncedlyrics",
                "plain_lyrics": text,
                "synced": False,
                "score": None,
                "matched_track": "",
                "matched_artist": "",
                "matched_duration": None,
                "lrclib_id": None,
                "source_url": "",
            }

    if record is None:
        return {"found": False, "provider": "", "error": ""}

    hit = lrclib.record_to_hit(record, stage=provider)
    return {
        "found": bool(hit),
        "provider": provider,
        "plain_lyrics": hit.lyrics if hit else "",
        "synced": bool(hit.synced) if hit else False,
        "score": None,
        "matched_track": str(record.get("trackName") or ""),
        "matched_artist": str(record.get("artistName") or ""),
        "matched_duration": record.get("duration"),
        "lrclib_id": record.get("id"),
        "source_url": hit.source_url if hit else "",
        "error": "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample", type=int, default=None, help="random sample of pending tracks (validation)")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--buckets", default=None, help="comma list of metadata_match buckets to include (strong,probable,weak,none)")
    parser.add_argument("--min-artist-score", type=float, default=None)
    parser.add_argument("--all", action="store_true", help="include tracks with a strong metadata match")
    parser.add_argument("--deep", action="store_true", help="third fallback: query-only LRCLIB search")
    parser.add_argument("--with-fallback", action="store_true", help="use syncedlyrics (Musixmatch/NetEase) after LRCLIB misses")
    args = parser.parse_args()

    from data_collection.http import CachedHttp

    tracks_path = utils.AUDIO_DATA_DIR / "audio_tracks.csv"
    if not tracks_path.exists():
        sys.exit(f"missing {tracks_path}; run build_manifest.py first")
    out_path = utils.AUDIO_DATA_DIR / "audio_lyrics.jsonl"
    done = already_done(out_path)

    with open(tracks_path, encoding="utf-8") as handle:
        tracks = list(csv.DictReader(handle))

    pending = [
        row for row in tracks
        if row["track_key"] not in done and (args.all or row["metadata_match"] != "strong")
    ]
    if args.buckets:
        wanted = {part.strip() for part in args.buckets.split(",")}
        pending = [row for row in pending if row["metadata_match"] in wanted]
    if args.min_artist_score is not None:
        pending = [row for row in pending if float(row["artist_score"] or 0) >= args.min_artist_score]
    if args.sample:
        import random

        random.Random(args.seed).shuffle(pending)
        pending = pending[: args.sample]
    if args.limit:
        pending = pending[: args.limit]
    print(f"tracks: {len(tracks)} | already done: {len(done)} | pending this run: {len(pending)}")

    client = CachedHttp()
    counters: Counter = Counter()
    started = time.time()
    with open(out_path, "a", encoding="utf-8") as handle:
        for position, track in enumerate(pending, start=1):
            outcome = fetch_one(client, track, deep=args.deep, with_fallback=args.with_fallback)
            status = "found" if outcome["found"] else ("error" if outcome.get("error") else "miss")
            row = {
                "track_key": track["track_key"],
                "artist": track["artist"],
                "title": track["title"],
                "duration_s": track["duration_s"],
                "status": status,
                "schema_version": config.SCHEMA_VERSION,
                **outcome,
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            counters["found" if outcome["found"] else "miss"] += 1
            counters[outcome["provider"] or "none"] += 1
            if position % 25 == 0 or position == len(pending):
                elapsed = time.time() - started
                rate = position / elapsed if elapsed else 0.0
                print(
                    f"[{position}/{len(pending)}] found={counters['found']} miss={counters['miss']} "
                    f"({rate:.2f} tracks/s)",
                    flush=True,
                )

    total = counters["found"] + counters["miss"]
    print(json.dumps({
        "processed": total,
        "found": counters["found"],
        "hit_rate": round(counters["found"] / total, 3) if total else 0.0,
        "by_provider": {key: value for key, value in counters.items() if key not in {"found", "miss"}},
    }, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
