"""Join _index.csv metadata to on-disk audio, match against the corpus.

Outputs:
  audit/audio_index_join_summary.json
  audit/audio_index_matches.csv   (strong matches with metadata)
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\praka\Downloads\Nepali Music Collection")
CORPUS = Path(r"D:\Code\ProjectR\music_rec_artifacts\cleaned_lyrics.csv")
OUT = Path(r"D:\Code\ProjectR\audit")
AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".wav", ".flac", ".opus", ".aac", ".3gpp", ".webm"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text or "")).lower()
    text = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", text)
    text = re.sub(r"[^\w\u0900-\u097F]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    from rapidfuzz import fuzz, process

    # ---- on-disk files (basename -> path) ----
    disk = {}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTS:
            disk.setdefault(path.name.lower(), []).append(path)

    # ---- index ----
    index_rows = []
    with open(ROOT / "_index.csv", encoding="utf-8", errors="replace") as handle:
        for row in csv.DictReader(handle):
            index_rows.append(row)
    joined = 0
    by_file = {}
    durations = 0.0
    for row in index_rows:
        fname = (row.get("file") or "").strip()
        if not fname:
            continue
        base = Path(fname.replace("\\", "/")).name.lower()
        if base in disk:
            joined += 1
            by_file[base] = row
            try:
                parts = str(row.get("duration", "")).split(":")
                secs = 0.0
                for part in parts:
                    secs = secs * 60 + float(part)
                durations += secs
            except (ValueError, TypeError):
                pass
    print(f"index rows: {len(index_rows)}  joined to disk: {joined}  matched audio hours: {durations/3600:.1f}")

    # ---- corpus ----
    with open(CORPUS, encoding="utf-8") as handle:
        songs = list(csv.DictReader(handle))
    c_title = [norm(s.get("title", "")) for s in songs]
    c_artist = [norm(s.get("artist", "")) for s in songs]
    c_pair = [f"{a} {t}".strip() for a, t in zip(c_artist, c_title)]
    artist_set = sorted({a for a in c_artist if a})

    matched_songs: dict[int, float] = {}
    strong_files = 0
    probable_files = 0
    weak_files = 0
    unknown_files = 0
    query_counter = Counter()
    rows_out = []

    for base, path in sorted(disk.items()):
        meta = by_file.get(base)
        if meta:
            author = meta.get("author") or ""
            title = meta.get("title") or ""
            query_counter[meta.get("source_query") or ""] += 1
        else:
            stem = Path(base).stem
            if " - " in stem:
                author, title = stem.split(" - ", 1)
            else:
                author, title = "", stem
        na, nt = norm(author), norm(title)
        if not nt:
            unknown_files += 1
            continue
        pair = f"{na} {nt}".strip()
        s_pair = process.extractOne(pair, c_pair, scorer=fuzz.WRatio, score_cutoff=0)
        s_pair = s_pair[1] if s_pair else 0.0
        s_title = process.extractOne(nt, c_title, scorer=fuzz.WRatio, score_cutoff=0)
        s_title = s_title[1] if s_title else 0.0
        s_artist = process.extractOne(na, artist_set, scorer=fuzz.WRatio, score_cutoff=0) if na else None
        s_artist = s_artist[1] if s_artist else 0.0
        best_title = process.extractOne(nt, c_title, scorer=fuzz.WRatio, score_cutoff=0)
        best_idx = best_title[2] if best_title else None
        score = max(s_pair, 0.95 * s_title if s_artist < 80 else s_title * 0.8)
        if best_idx is not None and score >= 88 and len(nt.split()) >= 2 and (not na or s_artist >= 75 or fuzz.WRatio(na, c_artist[best_idx]) >= 75):
            strong_files += 1
            sid = int(songs[best_idx]["song_id"])
            matched_songs[sid] = max(matched_songs.get(sid, 0.0), score)
            rows_out.append({"audio": path[0].name, "author": author, "title": title, "song_id": sid, "corpus_artist": songs[best_idx]["artist"], "corpus_title": songs[best_idx]["title"], "score": round(score, 1), "source_query": (meta or {}).get("source_query", "")})
        elif score >= 75:
            probable_files += 1
        elif s_artist >= 92:
            weak_files += 1
        else:
            unknown_files += 1

    summary = {
        "index_rows": len(index_rows),
        "index_rows_joined_to_disk": joined,
        "matched_audio_hours": round(durations / 3600, 1),
        "audio_files_on_disk": sum(len(v) for v in disk.values()),
        "strong_files": strong_files,
        "probable_files_75_88": probable_files,
        "known_artist_other_titles": weak_files,
        "unmatched_or_non_nepali": unknown_files,
        "corpus_songs_with_strong_audio": len(matched_songs),
        "top_source_queries": query_counter.most_common(30),
    }
    with open(OUT / "audio_index_join_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    with open(OUT / "audio_index_matches.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_out[0].keys()) if rows_out else ["audio"])
        writer.writeheader()
        writer.writerows(rows_out)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
