"""Which rows does the audit drop on v3, and are they old or new rows?"""
from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Code\ProjectR")


def nfc(x):
    return unicodedata.normalize("NFC", str(x or ""))


v3 = pd.read_csv(ROOT / "CSVs Dataset" / "corpus_final_v3.csv", encoding="utf-8").fillna("")
merged = pd.read_csv(ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv", encoding="utf-8").fillna("")

merged_pairs = Counter()
for row in merged.itertuples():
    merged_pairs[(nfc(getattr(row, "title")), nfc(str(getattr(row, "artist"))))] += 1

missing = []
for row in v3.itertuples():
    key = (nfc(getattr(row, "title_clean")), nfc(getattr(row, "artist_clean")))
    if merged_pairs[key] > 0:
        merged_pairs[key] -= 1
    else:
        missing.append(row)

print(f"v3={len(v3)} merged={len(merged)} missing={len(missing)}")
audio_new = sum(1 for row in missing if str(row.source).startswith("audio_"))
print(f"missing: audio rows={audio_new} old rows={len(missing)-audio_new}")

print("\nfirst 40 missing:")
for row in missing[:40]:
    text = nfc(row.lyrics_devanagari)
    exact = v3[v3["lyrics_devanagari"].map(nfc) == text]
    print(f"  src={str(row.source)[:22]:22s} stage={str(row.stage)[:12]:12s} lines={row.line_count:>3} chars={row.char_count:>5} "
          f"| {str(row.artist_clean)[:22]:22s} - {str(row.title_clean)[:34]:34s} | exact-lyrics rows={len(exact)}")

print("\nsource counts:", Counter(str(row.source)[:22] for row in missing).most_common(10))
