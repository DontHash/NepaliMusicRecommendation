"""Diagnose which new rows the audit dropped during merge."""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

audit = json.loads((ROOT / "music_rec_artifacts" / "audit_report.json").read_text(encoding="utf-8"))
print("audit report:", {k: audit[k] for k in ("total_rows", "exact_duplicates", "near_duplicates_same_title_artist", "short_songs_removed", "rows_after_cleaning")})

v3 = pd.read_csv(ROOT / "CSVs Dataset" / "corpus_final_v3.csv", encoding="utf-8").fillna("")
merged = pd.read_csv(ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv", encoding="utf-8").fillna("")
new = pd.read_csv(ROOT / "R_data" / "audio" / "audio_new_songs_v2.csv", encoding="utf-8").fillna("")

def nfc(text):
    return unicodedata.normalize("NFC", str(text))

merged_keys = set()
for row in merged.itertuples():
    merged_keys.add((nfc(getattr(row, "title")), nfc(str(getattr(row, "artist")))))

dropped = [row for row in new.to_dict("records") if (nfc(row["title_clean"]), nfc(row["artist_clean"])) not in merged_keys]
print(f"\nnew rows missing from merged: {len(dropped)}")
for row in dropped:
    title, artist = nfc(row["title_clean"]), nfc(row["artist_clean"])
    # exact title+artist in old corpus?
    old_t = v3.iloc[:4185]
    hit = old_t[(old_t["title_clean"].map(nfc) == title) & (old_t["artist_clean"].map(nfc) == artist)]
    exact_lyrics = v3[v3["lyrics_devanagari"].map(nfc) == nfc(row["lyrics_devanagari"])]
    print(f"- {row['audio_song_id']} {row['audio_artist'][:28]!r} - {row['audio_title'][:38]!r}")
    print(f"    title+artist matches in v2: {len(hit)} | exact-lyrics matches in v3: {len(exact_lyrics)} | tokens={row['token_count']}")
    if len(exact_lyrics):
        for match in exact_lyrics.head(3).itertuples():
            print(f"      exact-lyrics -> {match.title_clean[:40]!r} / {match.artist_clean[:30]!r}")
