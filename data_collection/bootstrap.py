"""Import bootstrap corpora into the work queue (offline files, no network)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .models import Candidate, LyricsHit
from .normalize import detect_script, lyrics_sha, nfc

MIN_LYRICS_CHARS = 120
KEEP_SCRIPTS = {"devanagari", "mixed"}

ARTIST_KEYS = ("artist", "artist_clean")
TITLE_KEYS = ("title", "song title", "title_clean", "name")
LYRICS_KEYS = ("lyrics", "lyrics_devanagari", "text")
CATEGORY_KEYS = ("category",)


def _pick(row: dict, keys: tuple[str, ...]) -> str:
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        value = lowered.get(key)
        if value:
            return str(value).strip()
    return ""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path, limit: int | None = None) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if limit:
        rows = rows[:limit]
    return rows


def import_rows(
    conn,
    rows: list[dict],
    *,
    source: str,
    stage: str,
    treated_as_nepali: bool = False,
) -> dict:
    report = {
        "source": source,
        "rows_read": len(rows),
        "skipped_empty": 0,
        "skipped_short": 0,
        "skipped_other_script": 0,
        "skipped_duplicate_sha": 0,
        "skipped_duplicate_key": 0,
        "attached_to_existing": 0,
        "added_candidates": 0,
        "lyrics_saved": 0,
    }
    seen_sha: set[str] = set()
    for row in rows:
        artist = _pick(row, ARTIST_KEYS)
        title = _pick(row, TITLE_KEYS)
        lyrics = nfc(_pick(row, LYRICS_KEYS))
        if not lyrics:
            report["skipped_empty"] += 1
            continue
        if len(lyrics) < MIN_LYRICS_CHARS:
            report["skipped_short"] += 1
            continue
        script = detect_script(lyrics)
        if not treated_as_nepali and script not in KEEP_SCRIPTS:
            report["skipped_other_script"] += 1
            continue
        sha = lyrics_sha(lyrics)
        if sha in seen_sha:
            report["skipped_duplicate_sha"] += 1
            continue
        existing_id = state.find_by_lyrics_sha(conn, sha)
        if existing_id is not None:
            report["skipped_duplicate_sha"] += 1
            seen_sha.add(sha)
            continue
        seen_sha.add(sha)

        category = _pick(row, CATEGORY_KEYS)
        candidate = Candidate(
            source=source,
            artist=artist,
            title=title,
            extra={"category": category} if category else {},
        )
        added, _dupes = state.enqueue(conn, [candidate])
        if added:
            row_db = state.get_by_dedupe_key(conn, candidate.dedupe_key)
            candidate_id = row_db["id"]
            report["added_candidates"] += 1
        else:
            row_db = state.get_by_dedupe_key(conn, candidate.dedupe_key)
            candidate_id = row_db["id"]
            if state.candidate_has_lyrics(conn, candidate_id):
                report["skipped_duplicate_key"] += 1
                continue
            report["attached_to_existing"] += 1

        hit = LyricsHit(stage=stage, lyrics=lyrics, script=script, sha256=sha)
        state.save_lyrics(conn, candidate_id, hit)
        report["lyrics_saved"] += 1
    return report


def write_report(report: dict, paths=None, name: str = "bootstrap") -> Path:
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"{name}_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def run_rupesh(conn, csv_path: Path, limit: int | None = None) -> dict:
    rows = read_rows(csv_path, limit=limit)
    report = import_rows(conn, rows, source="rupesh_aryal", stage="bootstrap_rupesh")
    report["input"] = str(csv_path)
    report["input_sha256"] = _sha256_file(csv_path)
    return report


def run_legacy(conn, csv_path: Path, limit: int | None = None) -> dict:
    rows = read_rows(csv_path, limit=limit)
    report = import_rows(conn, rows, source="legacy_932", stage="legacy", treated_as_nepali=True)
    report["input"] = str(csv_path)
    report["input_sha256"] = _sha256_file(csv_path)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import bootstrap corpora into the work queue.")
    parser.add_argument("target", choices=["rupesh", "legacy", "all"])
    parser.add_argument("--rupesh-csv", type=Path, default=cfg.DEFAULT_PATHS.raw / "bootstrap" / "rupesh_aryal_cleaned.csv")
    parser.add_argument("--legacy-csv", type=Path, default=cfg.PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    limit = args.limit or None
    reports = []
    if args.target in {"rupesh", "all"}:
        if not args.rupesh_csv.exists():
            raise SystemExit(f"missing input: {args.rupesh_csv}")
        reports.append(("rupesh", run_rupesh(conn, args.rupesh_csv, limit)))
    if args.target in {"legacy", "all"}:
        if not args.legacy_csv.exists():
            raise SystemExit(f"missing input: {args.legacy_csv}")
        reports.append(("legacy", run_legacy(conn, args.legacy_csv, limit)))
    for name, report in reports:
        path = write_report(report, name=f"bootstrap_{name}")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"report -> {path}")
    print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
