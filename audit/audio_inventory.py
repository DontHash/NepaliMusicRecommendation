"""Read-only inventory + corpus matching for the local audio collection.

Matches C:\\Users\\praka\\Downloads\\Nepali Music Collection audio files to
ProjectR's cleaned_lyrics.csv corpus. Writes:
  audit/audio_match.csv          - best match per audio file (score >= 60)
  audit/audio_match_summary.json - bucket counts
Never modifies the collection or the project corpus.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(r"C:\Users\praka\Downloads\Nepali Music Collection")
CORPUS = Path(r"D:\Code\ProjectR\music_rec_artifacts\cleaned_lyrics.csv")
OUT_DIR = Path(r"D:\Code\ProjectR\audit")

AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".wav", ".flac", ".opus", ".aac", ".3gpp", ".webm"}

JUNK_PATTERNS = [
    r"\(official[^)]*\)", r"\[official[^\]]*\]", r"\(lyric[^)]*\)", r"\[lyric[^\]]*\]",
    r"\(audio[^)]*\)", r"\[audio[^\]]*\]", r"\(video[^)]*\)", r"\[video[^\]]*\]",
    r"official\s+music\s+video", r"lyrical\s+video", r"lyrics\s+video",
    r"full\s+song", r"new\s+nepali\s+song", r"nepali\s+song", r"nepali\s+rap\s+song",
    r"prod\.?\s*by[^|]*", r"ft\.?\s", r"feat\.?\s", r"www\.[^\s]+", r"https?://\S+",
    r"\(\s*\d{4}\s*\)", r"\b(19|20)\d{2}\b", r"\b\dx\d+\b", r"[0-9]{3,}p\b",
    r"\(remix\)", r"\[remix\]", r"\bmusic\s+video\b", r"\bofficial\b", r"\bhd\b",
]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    for pattern in JUNK_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    # Keep Devanagari; replace everything else non-alphanumeric with space.
    text = re.sub(r"[^\w\u0900-\u097F]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def parse_audio_name(name: str) -> tuple[str, str]:
    stem = Path(name).stem
    stem = re.sub(r"\.(mp3|m4a)$", "", stem, flags=re.IGNORECASE)
    if " - " in stem:
        left, right = stem.split(" - ", 1)
        if right.strip():
            return left.strip(), right.strip()
    if " – " in stem:
        left, right = stem.split(" – ", 1)
        if right.strip():
            return left.strip(), right.strip()
    return "", stem.strip()


def main() -> None:
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("rapidfuzz not installed", file=sys.stderr)
        sys.exit(1)

    # --- corpus ---
    songs = []
    with open(CORPUS, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            songs.append(
                {
                    "song_id": int(row["song_id"]),
                    "title": row.get("title", "") or "",
                    "artist": row.get("artist", "") or "",
                }
            )
    corpus_pairs = []
    for song in songs:
        ta = f"{normalize(song['artist'])} {normalize(song['title'])}".strip()
        t = normalize(song["title"])
        corpus_pairs.append((ta, t))
    print(f"corpus songs: {len(songs)}")

    # --- audio files ---
    audio = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS]
    print(f"audio files: {len(audio)}")

    rows = []
    for path in audio:
        artist, title = parse_audio_name(path.name)
        na, nt = normalize(artist), normalize(title)
        a_pair = f"{na} {nt}".strip()
        best = None
        for idx, (c_pair, c_title) in enumerate(corpus_pairs):
            s1 = fuzz.token_set_ratio(a_pair, c_pair)
            s2 = fuzz.token_set_ratio(nt, c_title)
            score = max(s1, 0.9 * s2)
            if best is None or score > best[0]:
                best = (score, idx)
        score, idx = best
        rows.append(
            {
                "audio": str(path),
                "parsed_artist": artist,
                "parsed_title": title,
                "song_id": songs[idx]["song_id"] if score >= 60 else "",
                "corpus_title": songs[idx]["title"] if score >= 60 else "",
                "corpus_artist": songs[idx]["artist"] if score >= 60 else "",
                "score": round(float(score), 1),
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    match_path = OUT_DIR / "audio_match.csv"
    with open(match_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            if row["score"] >= 60:
                writer.writerow(row)

    def bucket(score: float) -> str:
        if score >= 92:
            return "strong"
        if score >= 82:
            return "probable"
        if score >= 70:
            return "weak"
        return "none"

    counts: dict[str, int] = {}
    for row in rows:
        counts[bucket(row["score"])] = counts.get(bucket(row["score"]), 0) + 1

    strong_ids = {int(r["song_id"]) for r in rows if r["score"] >= 92 and r["song_id"] != ""}
    probable_ids = {int(r["song_id"]) for r in rows if 82 <= r["score"] < 92 and r["song_id"] != ""}
    any_ids = {int(r["song_id"]) for r in rows if r["score"] >= 70 and r["song_id"] != ""}

    summary = {
        "audio_files": len(rows),
        "corpus_songs": len(songs),
        "audio_buckets": counts,
        "corpus_strong_covered": len(strong_ids),
        "corpus_probable_covered": len(probable_ids),
        "corpus_weak_or_better_covered": len(any_ids),
        "audio_strong_matches": counts.get("strong", 0),
    }
    with open(OUT_DIR / "audio_match_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))

    print("\n--- sample strong matches ---")
    shown = 0
    for row in rows:
        if row["score"] >= 92 and shown < 15:
            print(f"{row['score']:5.1f} | {row['parsed_artist'][:30]!r} - {row['parsed_title'][:40]!r} -> #{row['song_id']} {row['corpus_artist'][:25]!r} / {row['corpus_title'][:30]!r}")
            shown += 1

    print("\n--- sample unmatched (score < 60) ---")
    shown = 0
    for row in sorted(rows, key=lambda r: -Path(r["audio"]).stat().st_size):
        if row["score"] < 60 and shown < 15:
            print(f"{row['score']:5.1f} | {row['parsed_artist'][:35]!r} - {row['parsed_title'][:45]!r}")
            shown += 1


if __name__ == "__main__":
    main()
