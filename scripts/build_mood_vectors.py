"""Build per-song mood vectors (joy/sadness/anger) for mood-aware browsing.

Reads the probe's per-song scores (``music_rec_artifacts/sentiment_scores.csv``)
and writes the slim ``music_rec_artifacts/mood_vectors.csv`` contract consumed
by ``music_rec.mood_neighbors``.

Usage:
    python scripts/build_mood_vectors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config
from music_rec.mood_attribution import EMOTIONS


def main() -> int:
    config = Config()
    scores = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8")
    missing = [emotion for emotion in EMOTIONS if emotion not in scores.columns]
    if missing:
        raise SystemExit(f"sentiment scores missing columns: {missing}")

    vectors = scores[["song_id", *EMOTIONS]].copy()
    for emotion in EMOTIONS:
        vectors[emotion] = vectors[emotion].astype(float).round(6)

    out = config.artifacts_dir / "mood_vectors.csv"
    vectors.to_csv(out, index=False, encoding="utf-8")
    print(f"wrote {len(vectors)} mood vectors -> {out}")
    print(vectors[list(EMOTIONS)].describe().loc[["mean", "std", "min", "max"]].round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
