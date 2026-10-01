"""For suspicious new lines: search corpus by Devanagari title tokens + BM25 score."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(r"D:\Code\ProjectR")
sys.path.insert(0, str(ROOT))

from scripts.audio import utils  # noqa: E402

corpus = utils.load_corpus()
new_rows = list(csv.DictReader(open(ROOT / "R_data" / "audio" / "audio_new_songs_v2.csv", encoding="utf-8")))

probes = ["नजर", "पिउँदा", "पिउदै", "जून हेरेँ", "विश्वासको दियो", "झलझल", "छयाम्मै"]
for probe in probes:
    hits = corpus[corpus["lyrics"].str.contains(probe, regex=False)]
    print(f"probe {probe!r}: {len(hits)}")
    for row in hits.head(3).itertuples():
        print(f"    #{row.song_id} {str(row.artist)[:25]} - {str(row.title)[:35]}")

print()
print("BM25 check for the two suspicious new lines:")
from music_rec.lexical import LexicalIndex  # noqa: E402

lexical = LexicalIndex(corpus["lyrics"].astype(str).tolist(), fuzzy_enabled=False)
for row in new_rows:
    text = row["lyrics_devanagari"]
    if not any(token in row["audio_title"] for token in ("Bhijeko", "Piunda", "Kandara", "Bishwasko")):
        continue
    scores = lexical.song_scores(text)
    import numpy as np

    for i in np.argsort(-scores)[:3]:
        corpus_row = corpus.iloc[i]
        sim = utils.lyrics_similarity(text, str(corpus_row["lyrics"]))
        print(f"  {row['audio_title'][:30]:30s} -> #{corpus_row['song_id']} {str(corpus_row['title'])[:30]:30s} bm25={scores[i]:6.2f} sim={sim}")
