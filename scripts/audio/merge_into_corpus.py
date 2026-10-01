"""Merge audio-derived dataset lines into the corpus as a new version (v3).

New songs keep old song_ids untouched: v3 = corpus_final_v2 rows + appended
audio rows, and ``cleaned_lyrics.csv`` receives the same rows appended with the
next integer ids (the audit is *not* re-run on the whole corpus, because its
stricter dedup would silently drop existing songs and shift ids).

Rows the audit would drop (exact-lyrics or same title+artist duplicates, mostly
audio upload variants of one song) are pre-dropped and mapped to their surviving
song, so every audio file still gets a final song id.

Outputs:
  - CSVs Dataset/corpus_final_v3.csv
  - music_rec_artifacts/cleaned_lyrics.csv (regenerated via data_audit)
  - R_data/audio/merge_report_v3.json + audio_new_songs_mapping_v3.csv
  - final_song_id column added to audio_track_matches.csv / audio_file_map.csv

Run:
  python scripts/audio/merge_into_corpus.py --dry-run
  python scripts/audio/merge_into_corpus.py
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402

V2_COLUMNS = [
    "category", "title_clean", "artist_clean", "lyrics_devanagari", "line_count",
    "char_count", "script_style_original", "script_style_cleaned", "transliterated",
    "source", "stage", "source_url",
]


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", str(text or ""))


def prepare_new_rows(new_rows: list[dict], corpus) -> tuple[list[dict], list[dict]]:
    """Split audio rows into (kept, skipped) using the audit's own dedup rules.

    A skipped row carries ``maps_to``: the surviving existing ``song_id`` or the
    kept audio row's ``A-`` id, so its audio files can still resolve.
    """
    lyrics_target: dict[str, object] = {
        nfc(lyrics): int(song_id)
        for lyrics, song_id in zip(corpus["lyrics"], corpus["song_id"])
    }
    key_target: dict[tuple[str, str], object] = {
        (nfc(title), nfc(artist)): int(song_id)
        for title, artist, song_id in zip(corpus["title"], corpus["artist"], corpus["song_id"])
    }
    kept: list[dict] = []
    skipped: list[dict] = []
    for row in new_rows:
        title, artist = nfc(row["title_clean"]), nfc(row["artist_clean"])
        lyrics = nfc(row["lyrics_devanagari"])
        target = None
        reason = ""
        if lyrics in lyrics_target:
            target, reason = lyrics_target[lyrics], "exact lyrics duplicate"
        elif (title, artist) in key_target:
            target, reason = key_target[(title, artist)], "same title+artist"
        if target is not None:
            maps_to = target if isinstance(target, int) else str(target)
            skipped.append({
                "audio_song_id": row["audio_song_id"],
                "title": row["title_clean"],
                "artist": row["artist_clean"],
                "reason": reason,
                "maps_to": maps_to,
            })
            continue
        kept.append(row)
        lyrics_target[lyrics] = row["audio_song_id"]
        key_target[(title, artist)] = row["audio_song_id"]
    return kept, skipped


def resolve_target(target, alias: dict[str, str], kept_final: dict[str, int]):
    """Follow A-id aliases to a final integer song_id (or None)."""
    seen: set[str] = set()
    while isinstance(target, str) and target.startswith(config.NEW_ID_PREFIX):
        if target in kept_final:
            return kept_final[target]
        if target in seen or target not in alias:
            return None
        seen.add(target)
        target = alias[target]
    return int(target) if isinstance(target, (int, str)) and str(target).isdigit() else None


def build_v3_rows(v2_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    appended = []
    for row in new_rows:
        appended.append({
            "category": "nepali",
            "title_clean": row["title_clean"],
            "artist_clean": row["artist_clean"],
            "lyrics_devanagari": row["lyrics_devanagari"],
            "line_count": row["line_count"],
            "char_count": row["char_count"],
            "script_style_original": row["script_style_original"],
            "script_style_cleaned": row["script_style_cleaned"],
            "transliterated": row["transliterated"],
            "source": f"audio_{row['lyrics_source']}" if row["lyrics_source"] else "audio",
            "stage": "audio_fetch",
            "source_url": row["source_url"],
        })
    return v2_rows + appended


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    import pandas as pd

    from music_rec.config import Config as MusicConfig
    from music_rec.tokenization import normalize_nfc, token_count

    cleaned_path = MusicConfig().cleaned_lyrics_csv
    v2_path = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv"
    v3_path = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v3.csv"
    new_path = utils.AUDIO_DATA_DIR / "audio_new_songs_v2.csv"

    cleaned = pd.read_csv(cleaned_path, encoding="utf-8")
    v2 = pd.read_csv(v2_path, encoding="utf-8").fillna("")
    new = pd.read_csv(new_path, encoding="utf-8").fillna("")
    print(f"v2 file rows: {len(v2)} | cleaned: {len(cleaned)} | audio new songs: {len(new)}")

    if len(v2) < len(cleaned):
        sys.exit(f"v2 ({len(v2)}) has fewer rows than cleaned_lyrics ({len(cleaned)}); refusing to merge")

    kept, skipped = prepare_new_rows(new.to_dict("records"), cleaned)
    print(f"kept {len(kept)} new songs | pre-dropped {len(skipped)} audio duplicates")
    for row in skipped:
        print(f"  skip {row['audio_song_id']} {row['artist'][:24]!r} - {row['title'][:36]!r} -> {row['reason']} -> {row['maps_to']}")

    merge_report_path = utils.AUDIO_DATA_DIR / "merge_report_v3.json"
    if merge_report_path.exists():
        previous = json.loads(merge_report_path.read_text(encoding="utf-8"))
        if len(cleaned) == previous.get("cleaned_after"):
            print(f"merge already applied ({len(cleaned)} rows == merge_report_v3.cleaned_after); nothing to do")
            return

    v3_rows = build_v3_rows(v2.to_dict("records"), kept)
    v3 = pd.DataFrame(v3_rows, columns=V2_COLUMNS)
    if args.dry_run:
        print(f"dry run: would write {len(v3)} rows -> {v3_path}; cleaned would grow {len(cleaned)} -> {len(cleaned) + len(kept)}")
        return

    tmp = v3_path.with_suffix(".csv.tmp")
    v3.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, v3_path)
    print(f"wrote {v3_path} ({len(v3)} rows)")

    # Append the kept rows to cleaned_lyrics directly (never re-audit the whole
    # corpus: data_audit's stricter dedup would silently drop existing songs and
    # shift every song_id after them).
    expected = len(cleaned) + len(kept)
    next_song_id = int(cleaned["song_id"].max()) + 1  # ids are gappy; never reuse
    appended = []
    for index, row in enumerate(kept):
        lyrics = normalize_nfc(row["lyrics_devanagari"])
        tokens = token_count(lyrics)
        if tokens < MusicConfig().min_tokens:
            sys.exit(f"new song {row['audio_song_id']} has {tokens} tokens after NFC; refusing to merge")
        appended.append({
            "song_id": next_song_id + index,
            "title": normalize_nfc(row["title_clean"]),
            "artist": normalize_nfc(row["artist_clean"]),
            "category": "nepali",
            "lyrics": lyrics,
            "token_count": tokens,
        })
    merged = pd.concat([cleaned, pd.DataFrame(appended)], ignore_index=True)
    if len(merged) != expected:
        sys.exit(f"append produced {len(merged)} rows, expected {expected}")
    if not merged.iloc[: len(cleaned)][["song_id", "title", "artist", "lyrics"]].reset_index(drop=True).equals(
        cleaned[["song_id", "title", "artist", "lyrics"]].reset_index(drop=True)
    ):
        sys.exit("existing rows changed during append; refusing to write")
    tmp_cleaned = cleaned_path.with_suffix(".csv.tmp")
    merged.to_csv(tmp_cleaned, index=False, encoding="utf-8")
    os.replace(tmp_cleaned, cleaned_path)
    print(f"cleaned_lyrics appended: {len(cleaned)} -> {len(merged)} rows (existing ids untouched)")

    kept_final = {
        row["audio_song_id"]: int(merged.iloc[len(cleaned) + index]["song_id"])
        for index, row in enumerate(kept)
    }
    alias = {row["audio_song_id"]: str(row["maps_to"]) for row in skipped}
    all_ids = [row["audio_song_id"] for row in new.to_dict("records")]
    resolved = {audio_id: resolve_target(audio_id, alias, kept_final) for audio_id in all_ids}

    with open(utils.AUDIO_DATA_DIR / "audio_new_songs_mapping_v3.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["audio_song_id", "final_song_id", "status", "track_key",
                                                    "audio_artist", "audio_title"])
        writer.writeheader()
        for index, row in enumerate(new.to_dict("records")):
            writer.writerow({
                "audio_song_id": row["audio_song_id"],
                "final_song_id": resolved[row["audio_song_id"]],
                "status": "merged" if row["audio_song_id"] in kept_final else "duplicate_mapped",
                "track_key": row["track_key"],
                "audio_artist": row["audio_artist"],
                "audio_title": row["audio_title"],
            })

    # Annotate the audio maps with final ids (kept and duplicate-mapped alike).
    # Read as str so CSV round-trips cannot turn ids into floats ("1746.0").
    for name in ("audio_track_matches.csv", "audio_file_map.csv"):
        path = utils.AUDIO_DATA_DIR / name
        frame = pd.read_csv(path, encoding="utf-8", dtype=str).fillna("")
        frame["final_song_id"] = [
            "" if resolved.get(audio_id) is None else str(resolved[audio_id])
            for audio_id in frame["new_id"]
        ]
        tmp_path = path.with_suffix(".csv.tmp")
        frame.to_csv(tmp_path, index=False, encoding="utf-8")
        os.replace(tmp_path, path)

    report = {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": utils.git_sha(),
        "v2_file_rows": len(v2),
        "cleaned_before": len(cleaned),
        "cleaned_after": len(merged),
        "merged_new_songs": len(kept),
        "pre_dropped_duplicates": skipped,
        "inputs": {"corpus_final_v2.csv": utils.sha256_file(v2_path),
                   "audio_new_songs_v2.csv": utils.sha256_file(new_path)},
        "mapping": {audio_id: resolved[audio_id] for audio_id in all_ids},
        "canonical_corpus": "CSVs Dataset/corpus_final_v3.csv",
    }
    (utils.AUDIO_DATA_DIR / "merge_report_v3.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"merged {len(kept)} new songs: ids {min(kept_final.values()) if kept_final else '-'}..{max(kept_final.values()) if kept_final else '-'}")
    print("next: python scripts/audio/update_text_artifacts.py")


if __name__ == "__main__":
    main()
