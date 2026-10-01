"""Diagnose suspicious new dataset lines: corpus duplicates and language."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from scripts.audio import utils  # noqa: E402

new_rows = list(csv.DictReader(open(ROOT / "R_data" / "audio" / "audio_new_songs_v2.csv", encoding="utf-8")))
corpus = utils.load_corpus()
raw_by_key = {}
for line in open(ROOT / "R_data" / "audio" / "audio_lyrics.jsonl", encoding="utf-8"):
    if line.strip():
        row = json.loads(line)
        if row.get("found"):
            raw_by_key[row["track_key"]] = row

for row in new_rows:
    key = row["track_key"]
    title = utils.normalize_text(row["audio_title"])
    same_title = corpus[corpus["norm_title"] == title]
    raw = raw_by_key.get(key, {})
    raw_text = utils.sanitize_provider_lyrics(raw.get("plain_lyrics", "") or "")
    raw_dev = utils.devanagari_share(raw_text)
    raw_ascii = sum(1 for ch in raw_text if ch.isascii() and ch.isalpha()) / max(len(raw_text), 1)
    print(f"--- {row['audio_song_id']} | {row['audio_artist'][:25]} - {row['audio_title'][:35]}")
    print(f"    script_original={row['script_style_original']} raw_dev={raw_dev:.2f} ascii_alpha={raw_ascii:.2f}")
    if not same_title.empty:
        for corpus_row in same_title.itertuples():
            sim = utils.lyrics_similarity(row["lyrics_devanagari"], str(corpus_row.lyrics))
            print(f"    CORPUS DUPLICATE? #{corpus_row.song_id} {corpus_row.artist[:25]} sim={sim}")
    else:
        print("    no exact corpus title")
