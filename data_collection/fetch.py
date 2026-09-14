"""CLI: fetch lyrics for queued candidates (LRCLIB -> syncedlyrics)."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .http import CachedHttp
from .models import LyricsHit
from .normalize import detect_script, looks_like_nepali_romanized, lyrics_sha
from .sources import lrclib, syncedlyrics_client

MIN_LYRICS_CHARS = 120
ALL_STAGES = ("lrclib", "syncedlyrics")


def acceptable(hit: LyricsHit) -> tuple[bool, str]:
    if len(hit.lyrics) < MIN_LYRICS_CHARS:
        return False, "too_short"
    script = hit.script or detect_script(hit.lyrics)
    if script in {"devanagari", "mixed"}:
        return True, "ok"
    if script == "romanized" and looks_like_nepali_romanized(hit.lyrics):
        return True, "romanized_nepali"
    return False, f"script_rejected:{script}"


def fetch_candidate(client: CachedHttp, candidate, stages: tuple[str, ...] = ALL_STAGES):
    attempts: list[tuple[str, str]] = []
    artist = str(candidate["artist"] or "")
    title = str(candidate["title"] or "")
    duration = candidate["duration_s"]
    album = candidate["album"]

    if "lrclib" in stages:
        record = None
        if duration:
            started = time.perf_counter()
            record = lrclib.get_lyrics(client, artist=artist, title=title, album=album, duration=duration)
            attempts.append(("lrclib_get", "hit" if record else "miss"))
            elapsed = int((time.perf_counter() - started) * 1000)
        else:
            elapsed = 0
        if record is None:
            records = lrclib.search_lyrics(client, artist=artist, title=title)
            attempts.append(("lrclib_search", "hit" if records else "miss"))
            record = lrclib.pick_best(records, duration=duration, artist=artist, title=title)
        if record is not None:
            hit = lrclib.record_to_hit(record)
            if hit is not None:
                return hit, attempts, elapsed

    if "syncedlyrics" in stages:
        started = time.perf_counter()
        text = syncedlyrics_client.fetch_lyrics(title, artist)
        elapsed = int((time.perf_counter() - started) * 1000)
        attempts.append(("syncedlyrics", "hit" if text else "miss"))
        if text:
            hit = LyricsHit(
                stage="syncedlyrics",
                lyrics=text,
                script=detect_script(text),
                sha256=lyrics_sha(text),
            )
            return hit, attempts, elapsed

    return None, attempts, 0


def write_report(report: dict, paths=None) -> Path:
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"fetch_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch lyrics for queued candidates.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--stages", nargs="+", choices=ALL_STAGES, default=["lrclib"])
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-missed", action="store_true", help="Requeue previously missed candidates")
    parser.add_argument("--delay", type=float, default=0.0, help="Sleep seconds between candidates")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    if args.retry_missed:
        count = state.requeue(conn, status="missed", reset_attempts=True)
        print(f"requeued {count} missed candidates")
    batch = state.next_batch(conn, limit=args.limit or None, status="new", max_attempts=args.max_attempts)
    print(f"candidates to fetch: {len(batch)}")
    client = CachedHttp()
    stats = {"processed": 0, "hits": 0, "misses": 0, "rejected": 0, "by_stage": {}, "reject_reasons": {}}
    for index, row in enumerate(batch, start=1):
        try:
            state.mark_fetching(conn, [row["id"]])
            hit, attempts, _latency = fetch_candidate(client, row, stages=tuple(args.stages))
            for stage, outcome in attempts:
                state.record_attempt(conn, row["id"], stage, outcome)
            if hit is not None:
                ok, reason = acceptable(hit)
                if ok:
                    state.save_lyrics(conn, row["id"], hit)
                    stats["hits"] += 1
                    stats["by_stage"][hit.stage] = stats["by_stage"].get(hit.stage, 0) + 1
                else:
                    state.mark_status(conn, row["id"], "missed", reason)
                    stats["rejected"] += 1
                    stats["reject_reasons"][reason] = stats["reject_reasons"].get(reason, 0) + 1
            else:
                state.mark_status(conn, row["id"], "missed", "all_stages_missed")
                stats["misses"] += 1
        except Exception as exc:
            state.mark_status(conn, row["id"], "new", f"error:{type(exc).__name__}")
            state.record_attempt(conn, row["id"], "pipeline", "error", error_class=type(exc).__name__)
        stats["processed"] += 1
        if index % 25 == 0 or index == len(batch):
            print(
                f"[{index}/{len(batch)}] hits={stats['hits']} misses={stats['misses']} "
                f"rejected={stats['rejected']}"
            )
        if args.delay:
            time.sleep(args.delay)
    path = write_report(stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"report -> {path}")
    print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
