"""Refined read-only matching: which audio files are confidently Nepali/corpus songs.

Signals per audio file:
  title_score  - best WRatio of normalized title against corpus title
  artist_score - best WRatio of parsed artist against corpus artist
  strong       - title >= 88 and (artist >= 80 or no artist parsed) and non-generic title
  artist_hit   - artist_score >= 92 against a known corpus artist (any title)
Also summarizes the collection's helper files (_index.csv etc.).
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audio_inventory import AUDIO_EXTS, normalize, parse_audio_name  # noqa: E402

ROOT = Path(r"C:\Users\praka\Downloads\Nepali Music Collection")
CORPUS = Path(r"D:\Code\ProjectR\music_rec_artifacts\cleaned_lyrics.csv")
OUT = Path(r"D:\Code\ProjectR\audit")

GENERIC = {"aama", "aamaa", "aafno", "maya", "timi", "ma", "mann", "man", "sathi", "saathi", "yaad", "yaad", "prem", "sapana", "aakash", "sansar", "jindagi", "jiban", "kahani", "katha", "gita", "geet", "song", "music", "instrumental", "remix", "cover", "hits", "best", "old", "new", "nepali", "sad", "love", "trap", "beat"}


def main() -> None:
    from rapidfuzz import fuzz, process

    with open(CORPUS, encoding="utf-8") as handle:
        songs = list(csv.DictReader(handle))
    corpus_titles = [normalize(s.get("title", "")) for s in songs]
    corpus_artists = [normalize(s.get("artist", "")) for s in songs]
    artist_choices = sorted({a for a in corpus_artists if a})

    audio = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS]
    strong_ids: set[int] = set()
    buckets = Counter()
    rows = []

    for path in audio:
        artist, title = parse_audio_name(path.name)
        nt = normalize(title)
        na = normalize(artist)
        if not nt:
            buckets["no_title"] += 1
            continue
        hit = process.extractOne(nt, corpus_titles, scorer=fuzz.WRatio, score_cutoff=88)
        title_score = hit[1] if hit else 0.0
        title_idx = hit[2] if hit else None
        # allow exact or high title similarity with a distinctive title (>=2 tokens)
        distinctive = len(nt.split()) >= 2 and nt not in GENERIC
        artist_hit = None
        if na:
            a_hit = process.extractOne(na, artist_choices, scorer=fuzz.WRatio, score_cutoff=92)
            if a_hit:
                artist_hit = (a_hit[1], a_hit[2])
        artist_ok = (not na) or (artist_hit is not None) or (artist and fuzz.WRatio(na, corpus_artists[title_idx]) >= 80 if title_idx is not None else False)
        strong = bool(title_idx is not None and title_score >= 88 and distinctive and artist_ok)
        if strong:
            strong_ids.add(int(songs[title_idx]["song_id"]))
            buckets["strong"] += 1
        elif artist_hit is not None:
            buckets["artist_known"] += 1
        elif title_score >= 88:
            buckets["title_only"] += 1
        else:
            buckets["unmatched"] += 1
        if len(rows) < 999999:
            rows.append((str(path), artist, title, title_score, artist_hit[0] if artist_hit else 0.0, strong))

    print(f"audio files: {len(audio)}")
    print("buckets:", dict(buckets))
    print(f"corpus songs with strong audio: {len(strong_ids)}")
    known_artist_files = buckets.get("artist_known", 0) + buckets.get("strong", 0)
    print(f"audio with known corpus artist (any title): {known_artist_files}")

    # Writer sample lists
    with open(OUT / "audio_match_refined.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["audio", "parsed_artist", "parsed_title", "title_score", "artist_score", "strong"])
        for row in rows:
            writer.writerow([row[0], row[1], row[2], round(row[3], 1), round(row[4], 1), int(row[5])])

    print("\n--- helper files ---")
    for name in ("_index.csv", "_duplicates.csv", "_purged.csv", "_scope_purged.csv", "_scope_review.csv", "_failures.txt", "_diversity_failures.txt", "_channel_failures.txt"):
        path = ROOT / name
        if not path.exists():
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                first = handle.readline().rstrip("\n")
                count = 1 + sum(1 for _ in handle)
            print(f"{name}: {count} lines | header/first: {first[:160]}")
        except Exception as error:  # pragma: no cover
            print(f"{name}: ERROR {error}")

    print("\n--- 15 strongest examples ---")
    for row in sorted([r for r in rows if r[5]], key=lambda r: -r[3])[:15]:
        print(f"{row[3]:5.1f} | {row[1][:25]!r} - {row[2][:45]!r}")
    print("\n--- 20 unmatched examples (largest files) ---")
    for row in sorted([r for r in rows if r[3] < 70 and r[4] < 92], key=lambda r: -Path(r[0]).stat().st_size)[:20]:
        print(f"{row[3]:5.1f}/{row[4]:5.1f} | {row[1][:28]!r} - {row[2][:48]!r}")


if __name__ == "__main__":
    main()
