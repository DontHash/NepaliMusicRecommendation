"""Quick exploratory analysis for Lyrics_Dataset.csv noise patterns."""

import csv
import re
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).resolve().parents[1] / "CSVs Dataset" / "Lyrics_Dataset.csv"


def main():
    rows = list(csv.DictReader(open(DATASET, encoding="utf-8", newline="")))
    print("rows", len(rows))
    print("categories", Counter(r["Category"] for r in rows))

    noise = Counter()
    quotes = Counter()
    dev = re.compile(r"[\u0900-\u097F]")
    roman = re.compile(r"[A-Za-z]")

    for row in rows:
        lyrics = row["Lyrics"] or ""
        for ch in lyrics:
            if ch in "\"'`\u201c\u201d\u2018\u2019\u00ab\u00bb":
                quotes[ch] += 1

        for line in lyrics.splitlines():
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\d+\s+Contributors?$", s, re.I):
                noise["contributor"] += 1
            elif s == "Translations":
                noise["translations_header"] += 1
            elif re.search(r" Lyrics\s*$", s) and len(s) < 150:
                noise["title_lyrics_line"] += 1
            elif re.match(r"^\[[^\]]+\]\s*$", s):
                noise["section_bracket"] += 1
            elif re.match(
                r"^(Verse|Chorus|Bridge|Intro|Outro|Hook|Pre-Chorus|Interlude|Skit)\b",
                s,
                re.I,
            ):
                noise["section_word"] += 1
            elif "you might also like" in s.lower():
                noise["you_might_also_like"] += 1
            elif s.lower() in {"embed", "genius"}:
                noise["embed_genius"] += 1

        has_dev = bool(dev.search(lyrics))
        has_roman = bool(roman.search(lyrics))
        if has_dev and has_roman:
            noise["mixed_row"] += 1
        elif has_dev:
            noise["dev_row"] += 1
        elif has_roman:
            noise["roman_row"] += 1

    print("noise", dict(noise))
    print("quotes", dict(quotes))


if __name__ == "__main__":
    main()
