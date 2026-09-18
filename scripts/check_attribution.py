"""Validate window-to-line mood attribution against gold labels.

For a set of gold songs with confident labels, compares the attributed
composition (joy/sadness/anger shares) and per-line dominance with the gold
primary emotion, verifies that recomputed window spans match cached window
counts (the main technical risk), and spot-checks text-mode attribution
against corpus mode.

Usage:
    python scripts/check_attribution.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config
from music_rec.mood_attribution import EMOTIONS, MoodAttributor

GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"

CASES = [3235, 3396, 182, 4024, 3980, 1511, 757, 2252]


def main() -> int:
    config = Config()
    attributor = MoodAttributor(config)
    gold = pd.read_csv(GOLD, encoding="utf-8").set_index("song_id")
    attributor._load_corpus_artifacts()

    mismatches = 0
    matches = 0
    scored = 0
    print(f"{'id':>5} {'title':32s} {'gold':10s} {'top':10s} {'shares':26s} {'lines':12s} {'match'}")
    for song_id in CASES:
        payload = attributor.attribute_song(song_id)
        g = gold.loc[song_id]
        comp = payload["composition"]
        top = max(comp, key=comp.get)
        primary = str(g["primary_emotion"])

        row = attributor._row_of_song[song_id]
        n_cached = int((attributor._window_owners == row).sum())
        text = str(attributor._cleaned.loc[song_id, "lyrics"])
        n_computed = len(attributor._window_spans(text))
        if n_cached != n_computed:
            mismatches += 1

        lines = payload["lines"]
        dominant_counts = {e: 0 for e in (*EMOTIONS, "neutral")}
        for line in lines:
            dominant_counts[line["dominant"]] += 1
        gold_lines = dominant_counts.get(primary, 0)
        ratio = gold_lines / max(1, len(lines))

        if primary in EMOTIONS:
            scored += 1
            ok = top == primary
            matches += int(ok)
        else:
            ok = None
        shares = " ".join(f"{e[:3]}={comp[e]:.2f}" for e in EMOTIONS)
        print(
            f"{song_id:>5} {payload['title'][:32]:32s} {primary:10s} {top:10s} "
            f"{shares:26s} {gold_lines:>3}/{len(lines):<3} ({ratio:.0%}) "
            f"{'OK' if ok else '-' if ok is None else 'MISS'} "
            f"[windows cached={n_cached} computed={n_computed}]"
        )

    print(f"\nwindow-count mismatches: {mismatches}/{len(CASES)}")
    print(f"composition argmax matches gold primary: {matches}/{scored}")

    sample = CASES[2]
    text = str(attributor._cleaned.loc[sample, "lyrics"])
    corpus_comp = attributor.attribute_song(sample)["composition"]
    text_comp = attributor.attribute_text(text)["composition"]
    delta = max(abs(corpus_comp[e] - text_comp[e]) for e in EMOTIONS)
    print(
        f"text-vs-corpus composition ({sample}): max_delta={delta:.4f} "
        f"corpus={' '.join(f'{e[:3]}={corpus_comp[e]:.2f}' for e in EMOTIONS)} "
        f"text={' '.join(f'{e[:3]}={text_comp[e]:.2f}' for e in EMOTIONS)}"
    )

    passed = mismatches == 0 and matches >= scored * 0.7 and delta < 0.05
    print("PASS" if passed else "REVIEW")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
