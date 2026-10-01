"""Turn audio metadata + fetched lyrics into dataset lines and audio-song links.

Reads:
  - R_data/audio/audio_tracks.csv / audio_manifest.csv  (build_manifest.py)
  - R_data/audio/audio_lyrics.jsonl                     (fetch_lyrics.py)

Writes:
  - R_data/audio/audio_track_matches.csv   one row per unique track with verdict
  - R_data/audio/audio_new_songs_v2.csv    new corpus-shaped dataset lines
  - R_data/audio/audio_file_map.csv        every audio file -> linked song
  - R_data/audio/dataset_report.json

Verdicts:
  lyrics_confirmed   fetched lyrics match an existing corpus song
  metadata_only      strong metadata match, no fetched lyrics (link kept, unverified)
  metadata_candidate metadata candidate but no lyrics and not strong (review)
  new_lyrics         fetched lyrics did not match the corpus -> new dataset line
  no_lyrics          nothing found
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


def decide(best_sim: float, metadata_sim: float, nepali_ratio: float, has_candidate: bool) -> str:
    """Pure verdict function (unit-tested).

    Returns one of: lyrics_confirmed, lyrics_ambiguous_linked,
    new_lyrics_non_nepali, new_lyrics. ``nepali_ratio`` is measured on the raw
    provider text (see utils.nepali_ratio).
    """
    if best_sim >= config.CONFIRM_SIM or metadata_sim >= config.CONFIRM_SIM_METADATA:
        return "lyrics_confirmed"
    if nepali_ratio < config.NEPALI_MIN_RATIO:
        return "new_lyrics_non_nepali"
    if best_sim >= config.AMBIGUOUS_SIM or metadata_sim >= config.AMBIGUOUS_SIM:
        return "lyrics_ambiguous_linked"
    return "new_lyrics"


def load_lyrics(path: Path) -> dict[str, dict]:
    found: dict[str, dict] = {}
    if not path.exists():
        return found
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = row.get("track_key", "")
            if not key:
                continue
            if row.get("found") and key not in found:
                found[key] = row
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-new", type=int, default=None, help="cap new dataset lines (debug)")
    args = parser.parse_args()

    import hashlib

    import numpy as np

    from music_rec.lexical import LexicalIndex
    from music_rec.tokenization import token_count

    corpus = utils.load_corpus()
    corpus = corpus[corpus["lyrics"].astype(str).str.len() > 20].reset_index(drop=True)
    print(f"corpus rows: {len(corpus)}")

    print("building BM25 candidate index ...")
    lexical = LexicalIndex(corpus["lyrics"].astype(str).tolist(), fuzzy_enabled=False)
    print(f"BM25 index: {lexical.n_songs} documents")

    def corpus_search(text: str, top: int = 5) -> list[tuple[int, float]]:
        scores = lexical.song_scores(text)
        order = np.argsort(-scores)[:top]
        return [(int(corpus.iloc[i]["song_id"]), float(scores[i])) for i in order if scores[i] > 0]

    with open(utils.AUDIO_DATA_DIR / "audio_tracks.csv", encoding="utf-8") as handle:
        tracks = list(csv.DictReader(handle))
    lyrics_by_key = load_lyrics(utils.AUDIO_DATA_DIR / "audio_lyrics.jsonl")
    print(f"tracks: {len(tracks)} | tracks with fetched lyrics: {len(lyrics_by_key)}")

    track_rows: list[dict] = []
    new_rows: list[dict] = []
    new_counter = 0

    for track in tracks:
        key = track["track_key"]
        row = dict(track)
        row["match_song_id"] = ""
        row["new_id"] = ""
        row["lyrics_sim"] = ""
        row["match_basis"] = ""
        row["nepali_ratio"] = ""
        lyrics = lyrics_by_key.get(key)
        if not lyrics:
            if track["metadata_match"] == "strong" and track["cand_song_id"]:
                row["match_song_id"] = track["cand_song_id"]
                row["match_basis"] = "metadata_only"
            elif track["cand_song_id"]:
                row["match_basis"] = "metadata_candidate"
            else:
                row["match_basis"] = "no_lyrics"
            track_rows.append(row)
            continue

        raw_lyrics = utils.sanitize_provider_lyrics(lyrics["plain_lyrics"])
        if len([line for line in raw_lyrics.splitlines() if line.strip()]) < config.MIN_NEW_LINES:
            row["match_basis"] = "new_lyrics_too_short"
            track_rows.append(row)
            continue
        share = utils.nepali_ratio(raw_lyrics)
        processed = utils.process_lyrics(
            raw_lyrics,
            title=track["title"],
            artist=track["artist"],
            source=lyrics.get("provider", "lrclib"),
            stage="audio_fetch",
            source_url=lyrics.get("source_url", ""),
        )
        text = processed["lyrics_devanagari"]
        if token_count(text) < config.MIN_NEW_TOKENS or processed["line_count"] < config.MIN_NEW_LINES:
            row["match_basis"] = "new_lyrics_too_short"
            track_rows.append(row)
            continue

        best_song, best_sim = "", 0.0
        for song_id, _ in corpus_search(text):
            corpus_row = corpus[corpus["song_id"] == song_id].iloc[0]
            sim = utils.lyrics_similarity(text, str(corpus_row["lyrics"]))
            if sim > best_sim:
                best_song, best_sim = song_id, sim
        metadata_sim = 0.0
        if track["cand_song_id"]:
            corpus_row = corpus[corpus["song_id"] == int(track["cand_song_id"])]
            if not corpus_row.empty:
                metadata_sim = utils.lyrics_similarity(text, str(corpus_row.iloc[0]["lyrics"]))

        row["lyrics_sim"] = round(max(best_sim, metadata_sim), 2)
        row["nepali_ratio"] = round(share, 3)
        basis = decide(best_sim, metadata_sim, share, bool(track["cand_song_id"]))
        row["match_basis"] = basis
        if basis == "lyrics_confirmed":
            row["match_song_id"] = best_song if best_sim >= metadata_sim else int(track["cand_song_id"])
        elif basis == "lyrics_ambiguous_linked":
            row["match_song_id"] = best_song or track["cand_song_id"]
        elif basis == "new_lyrics":
            new_counter += 1
            new_id = f"{config.NEW_ID_PREFIX}{hashlib.sha1(key.encode('utf-8')).hexdigest()[:10]}"
            row["new_id"] = new_id
            new_rows.append(
                {
                    "audio_song_id": new_id,
                    "track_key": key,
                    "audio_artist": track["artist"],
                    "audio_title": track["title"],
                    "duration_s": track["duration_s"],
                    "n_files": track["n_files"],
                    "lyrics_source": lyrics.get("provider", ""),
                    "source_url": lyrics.get("source_url", ""),
                    "category": "nepali",
                    "title_clean": processed["title_clean"],
                    "artist_clean": processed["artist_clean"],
                    "lyrics_devanagari": text,
                    "line_count": processed["line_count"],
                    "char_count": processed["char_count"],
                    "script_style_original": processed["script_style_original"],
                    "script_style_cleaned": processed["script_style_cleaned"],
                    "transliterated": processed["transliterated"],
                    "token_count": token_count(text),
                }
            )
        track_rows.append(row)

    if args.max_new:
        new_rows = new_rows[: args.max_new]

    # --- write outputs ---
    with open(utils.AUDIO_DATA_DIR / "audio_track_matches.csv", "w", encoding="utf-8", newline="") as handle:
        fields = ["track_key", "artist", "title", "duration_s", "n_files", "files", "source_query",
                  "cand_song_id", "cand_title", "cand_artist", "title_score", "artist_score",
                  "metadata_match", "match_song_id", "new_id", "match_basis", "lyrics_sim", "nepali_ratio"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in track_rows:
            writer.writerow({field: row.get(field, "") for field in fields})

    new_path = utils.AUDIO_DATA_DIR / "audio_new_songs_v2.csv"
    if new_rows:
        with open(new_path, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(new_rows[0].keys()))
            writer.writeheader()
            writer.writerows(new_rows)
        print(f"wrote {new_path}")

    with open(utils.AUDIO_DATA_DIR / "audio_manifest.csv", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    verdict_by_key = {row["track_key"]: row for row in track_rows}
    with open(utils.AUDIO_DATA_DIR / "audio_file_map.csv", "w", encoding="utf-8", newline="") as handle:
        fields = ["audio_name", "audio_relpath", "track_key", "artist", "title", "metadata_match",
                  "cand_song_id", "match_song_id", "new_id", "match_basis"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in manifest:
            verdict = verdict_by_key.get(item["track_key"], {})
            writer.writerow({
                "audio_name": item["audio_name"],
                "audio_relpath": item["audio_relpath"],
                "track_key": item["track_key"],
                "artist": item["artist"],
                "title": item["title"],
                "metadata_match": item.get("metadata_match", ""),
                "cand_song_id": item.get("cand_song_id", ""),
                "match_song_id": verdict.get("match_song_id", ""),
                "new_id": verdict.get("new_id", ""),
                "match_basis": verdict.get("match_basis", ""),
            })

    buckets: dict[str, int] = defaultdict(int)
    for row in track_rows:
        buckets[row["match_basis"]] += 1
    from datetime import datetime, timezone

    report = {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": utils.git_sha(),
        "tracks": len(track_rows),
        "with_fetched_lyrics": len(lyrics_by_key),
        "verdicts": dict(buckets),
        "linked_existing_songs": len({row["match_song_id"] for row in track_rows if row["match_song_id"]}),
        "new_songs": len(new_rows),
        "new_songs_tokens_median": sorted(r["token_count"] for r in new_rows)[len(new_rows) // 2] if new_rows else 0,
        "thresholds": {
            "confirm_sim": config.CONFIRM_SIM,
            "confirm_sim_metadata": config.CONFIRM_SIM_METADATA,
            "ambiguous_sim": config.AMBIGUOUS_SIM,
            "nepali_min_ratio": config.NEPALI_MIN_RATIO,
        },
    }
    (utils.AUDIO_DATA_DIR / "dataset_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
