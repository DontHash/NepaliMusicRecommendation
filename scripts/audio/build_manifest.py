"""Build the audio manifest: join the local collection to the lyrics corpus.

Reads:
  - audio files under the collection root (see utils.COLLECTION_ROOT)
  - _index.csv metadata shipped with the collection (author/title/duration/source_query)
  - music_rec_artifacts/cleaned_lyrics.csv (4,157 songs)

Writes:
  - R_data/audio/audio_manifest.csv   one row per audio file
  - R_data/audio/audio_tracks.csv     one row per unique (artist, title) track
  - R_data/audio/manifest_report.json

Read-only with respect to the collection. Matching here is metadata-level; the
lyrics-based confirmation happens in build_dataset_lines.py after fetch_lyrics.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402


def parse_duration(value: str) -> float:
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        seconds = 0.0
        for part in text.split(":"):
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError:
        return 0.0


def load_index(root: Path) -> dict[str, dict]:
    path = root / "_index.csv"
    if not path.exists():
        return {}
    rows: dict[str, dict] = {}
    with open(path, encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            file_name = (row.get("file") or "").replace("\\", "/")
            base = Path(file_name).name.lower()
            if base and base not in rows:
                rows[base] = row
    return rows


def load_metadata_csv(path: Path) -> dict[str, dict]:
    """Generic audio-library input contract.

    Accepted columns (aliases in parentheses):
      file (audio_path), title, artist (author), duration (duration_s), source
    """
    rows: dict[str, dict] = {}
    if path is None or not Path(path).exists():
        return rows
    with open(path, encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            file_name = str(row.get("file") or row.get("audio_path") or "").replace("\\", "/")
            base = Path(file_name).name.lower()
            if not base:
                continue
            rows[base] = {
                "author": row.get("artist") or row.get("author") or "",
                "title": row.get("title") or "",
                "duration": row.get("duration") or row.get("duration_s") or "",
                "source_query": row.get("source_query") or row.get("source") or "",
                "status": row.get("status") or "",
            }
    return rows


def classify(title_score: float, artist_score: float, has_artist: bool, title: str) -> str:
    if not has_artist:
        return "strong" if title_score >= 95 and not utils.is_generic_title(title) else (
            "probable" if title_score >= 85 else ("weak" if title_score >= config.TITLE_WEAK else "none")
        )
    if title_score >= config.TITLE_STRONG and artist_score >= config.ARTIST_STRONG:
        return "strong"
    if title_score >= config.TITLE_PROBABLE and artist_score >= config.ARTIST_PROBABLE:
        return "probable"
    if title_score >= config.TITLE_WEAK or artist_score >= config.ARTIST_WEAK:
        return "weak"
    return "none"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", type=Path, default=utils.COLLECTION_ROOT)
    parser.add_argument("--metadata-csv", type=Path, default=None,
                        help="optional library metadata CSV (file,artist,title,duration); overrides _index.csv rows")
    args = parser.parse_args()

    from rapidfuzz import fuzz, process

    root: Path = args.collection
    if not root.exists():
        sys.exit(f"collection not found: {root}")

    corpus = utils.load_corpus()
    corpus_titles = corpus["norm_title"].tolist()
    corpus_artist_rows = corpus.drop_duplicates("norm_artist")
    corpus_artists = corpus_artist_rows["norm_artist"].tolist()
    title_to_ids: dict[str, list[int]] = defaultdict(list)
    for row in corpus.itertuples():
        title_to_ids[row.norm_title].append(int(row.song_id))

    index_rows = load_index(root)
    extra_rows = load_metadata_csv(args.metadata_csv) if args.metadata_csv else {}
    files = sorted(
        (p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in utils.AUDIO_EXTS),
        key=lambda p: str(p).lower(),
    )
    print(f"audio files: {len(files)} | index rows: {len(index_rows)}")

    file_rows: list[dict] = []
    track_map: dict[str, dict] = {}
    for path in files:
        meta = extra_rows.get(path.name.lower()) or index_rows.get(path.name.lower())
        if meta:
            artist = (meta.get("author") or "").strip()
            title = (meta.get("title") or "").strip()
            duration = parse_duration(meta.get("duration", ""))
            source_query = (meta.get("source_query") or "").strip()
            metadata_from = "index"
        else:
            artist, title = utils.parse_filename(path.name)
            duration = 0.0
            source_query = ""
            metadata_from = "filename"
        artist, title = artist.strip(), title.strip()
        if not title:
            title = utils.strip_junk(path.stem)
        key = utils.track_key(artist, title)
        file_rows.append(
            {
                "audio_name": path.name,
                "audio_relpath": str(path.relative_to(root)).replace("\\", "/"),
                "ext": path.suffix.lower(),
                "bytes": path.stat().st_size,
                "track_key": key,
                "artist": artist,
                "title": title,
                "duration_s": round(duration, 1),
                "source_query": source_query,
                "metadata_from": metadata_from,
            }
        )
        entry = track_map.setdefault(
            key,
            {
                "track_key": key,
                "artist": artist,
                "title": title,
                "durations": [],
                "n_files": 0,
                "files": [],
                "source_queries": set(),
            },
        )
        entry["n_files"] += 1
        if duration:
            entry["durations"].append(duration)
        if source_query:
            entry["source_queries"].add(source_query)
        if len(entry["files"]) < 8:
            entry["files"].append(path.name)

    print(f"unique tracks: {len(track_map)}")

    # --- metadata match against the corpus ---
    track_rows: list[dict] = []
    for key, entry in sorted(track_map.items()):
        norm_title = utils.normalize_text(entry["title"])
        norm_artist = utils.normalize_text(entry["artist"])
        primary = utils.normalize_text(utils.primary_artist(entry["artist"]))
        title_score = float(process.extractOne(norm_title, corpus_titles, scorer=fuzz.token_set_ratio, score_cutoff=0)[1]) if norm_title else 0.0
        artist_score = float(process.extractOne(norm_artist or primary, corpus_artists, scorer=fuzz.token_set_ratio, score_cutoff=0)[1]) if (norm_artist or primary) else 0.0
        # exact-title candidates get an artist-best pick
        cand_id = ""
        cand_title = cand_artist = ""
        if norm_title in title_to_ids:
            ids = title_to_ids[norm_title]
            best = max(ids, key=lambda sid: fuzz.token_set_ratio(norm_artist, corpus.loc[corpus["song_id"] == sid, "norm_artist"].iloc[0]))
            row = corpus[corpus["song_id"] == best].iloc[0]
            cand_id, cand_title, cand_artist = int(row["song_id"]), str(row["title"]), str(row["artist"])
        else:
            hit = process.extractOne(norm_title, corpus_titles, scorer=fuzz.token_set_ratio, score_cutoff=60)
            if hit is not None:
                row = corpus.iloc[hit[2]]
                cand_id, cand_title, cand_artist = int(row["song_id"]), str(row["title"]), str(row["artist"])
        if cand_id != "":
            exact_artist = corpus[corpus["song_id"] == cand_id]["norm_artist"].iloc[0]
            artist_score = max(artist_score, float(fuzz.token_set_ratio(norm_artist or primary, exact_artist)))
            title_score = max(title_score, float(fuzz.token_set_ratio(norm_title, utils.normalize_text(str(cand_title)))))
        kind = classify(title_score, artist_score, bool(norm_artist or primary), entry["title"])
        durations = entry["durations"]
        track_rows.append(
            {
                "track_key": key,
                "artist": entry["artist"],
                "title": entry["title"],
                "duration_s": round(sorted(durations)[len(durations) // 2], 1) if durations else 0.0,
                "n_files": entry["n_files"],
                "files": "|".join(entry["files"]),
                "source_query": "|".join(sorted(entry["source_queries"]))[:200],
                "cand_song_id": cand_id,
                "cand_title": cand_title,
                "cand_artist": cand_artist,
                "title_score": round(title_score, 1),
                "artist_score": round(artist_score, 1),
                "metadata_match": kind,
            }
        )
        for file_row in file_rows:
            if file_row["track_key"] == key:
                file_row["cand_song_id"] = cand_id
                file_row["cand_title"] = cand_title
                file_row["cand_artist"] = cand_artist
                file_row["title_score"] = round(title_score, 1)
                file_row["artist_score"] = round(artist_score, 1)
                file_row["metadata_match"] = kind

    utils.AUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(utils.AUDIO_DATA_DIR / "audio_manifest.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(file_rows[0].keys()))
        writer.writeheader()
        writer.writerows(file_rows)
    with open(utils.AUDIO_DATA_DIR / "audio_tracks.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(track_rows[0].keys()))
        writer.writeheader()
        writer.writerows(track_rows)

    counts: dict[str, int] = defaultdict(int)
    for row in track_rows:
        counts[row["metadata_match"]] += 1
    from datetime import datetime, timezone

    from music_rec.config import Config as MusicConfig

    report = {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": utils.git_sha(),
        "audio_files": len(file_rows),
        "unique_tracks": len(track_rows),
        "match_buckets_tracks": dict(counts),
        "tracks_with_candidate": sum(1 for row in track_rows if row["cand_song_id"] != ""),
        "collection_root": str(root),
        "corpus_songs": len(corpus),
        "inputs": {
            "_index.csv": utils.sha256_file(root / "_index.csv"),
            "metadata_csv": utils.sha256_file(args.metadata_csv) if args.metadata_csv else "",
            "cleaned_lyrics.csv": utils.sha256_file(MusicConfig().cleaned_lyrics_csv),
        },
    }
    (utils.AUDIO_DATA_DIR / "manifest_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"wrote {utils.AUDIO_DATA_DIR / 'audio_manifest.csv'}")
    print(f"wrote {utils.AUDIO_DATA_DIR / 'audio_tracks.csv'}")


if __name__ == "__main__":
    main()
