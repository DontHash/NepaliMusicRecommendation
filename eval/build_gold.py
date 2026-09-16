"""Sample the gold-set v2 batch for mood labeling.

Keeps the 60 reviewed v1 songs untouched and selects ~90 additions:
60 random songs + 30 targeted at rare emotions (teacher pseudo-labels pick
anger/fear/depression candidates). Writes an excerpt file for drafting labels;
the drafted labels then get merged into ``eval/mood_gold.csv`` for review.

Usage:
    python eval/build_gold.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
CLEANED = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
PSEUDO = PROJECT_ROOT / "R_data" / "raw" / "kaggle" / "sentiment_distill" / "mood_pseudo_labels.csv"
OUT = PROJECT_ROOT / "R_data" / "corpus" / "eval" / "gold_v2_excerpts.csv"

N_RANDOM = 60
N_ANGER = 15
N_FEAR = 8
N_DEPRESSION = 7


def excerpt(lyrics: str, head: int = 6, tail: int = 2) -> str:
    lines = [line.strip() for line in str(lyrics).splitlines() if line.strip()]
    parts = lines[:head]
    if len(lines) > head + tail:
        parts = parts + ["..."] + lines[-tail:]
    return " / ".join(parts)[:600]


def main() -> None:
    gold = pd.read_csv(GOLD, encoding="utf-8")
    cleaned = pd.read_csv(CLEANED, encoding="utf-8").fillna("")
    pseudo = pd.read_csv(PSEUDO, encoding="utf-8")
    existing = set(gold["song_id"].astype(int))
    all_ids = cleaned["song_id"].astype(int).to_numpy()

    pool = np.array(sorted(set(all_ids) - existing))
    rng = np.random.default_rng(123)
    random_ids = rng.choice(pool, size=N_RANDOM, replace=False)
    chosen = set(int(x) for x in random_ids)

    teacher = pseudo[pseudo["song_id"].isin(pool) & ~pseudo["song_id"].isin(chosen)]

    def pick(mask: pd.Series, count: int, seed: int) -> list[int]:
        candidates = np.array(sorted(teacher.loc[mask, "song_id"].astype(int)))
        candidates = [c for c in candidates if c not in chosen]
        if not candidates:
            return []
        rng2 = np.random.default_rng(seed)
        take = min(count, len(candidates))
        selection = rng2.choice(candidates, size=take, replace=False)
        return [int(x) for x in selection]

    anger_ids = pick(teacher["anger"] == 1, N_ANGER, 124)
    chosen.update(anger_ids)
    fear_ids = pick(
        (teacher["fear"] == 1) & (teacher["sadness"] == 0) & (teacher["depression"] == 0),
        N_FEAR,
        125,
    )
    chosen.update(fear_ids)
    depression_ids = pick(
        (teacher["depression"] == 1) & (teacher["joy"] == 0) & (teacher["fear"] == 0) & (teacher["anger"] == 0),
        N_DEPRESSION,
        126,
    )

    rows = []
    for song_id, stratum in (
        [(int(x), "v2_random") for x in random_ids]
        + [(x, "v2_anger") for x in anger_ids]
        + [(x, "v2_fear") for x in fear_ids]
        + [(x, "v2_depression") for x in depression_ids]
    ):
        row = cleaned.loc[cleaned["song_id"] == song_id].iloc[0]
        rows.append(
            {
                "song_id": song_id,
                "stratum": stratum,
                "title": str(row["title"])[:60],
                "artist": str(row["artist"])[:40],
                "excerpt": excerpt(row["lyrics"]),
            }
        )

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"new songs: {len(out)} (random {len(random_ids)}, anger {len(anger_ids)}, fear {len(fear_ids)}, depression {len(depression_ids)})")
    print(f"excerpts -> {OUT}")
    for row in rows:
        print(f"[{row['song_id']}] ({row['stratum']}) {row['title']} — {row['artist']}")
        print(f"    {row['excerpt'][:260]}")


if __name__ == "__main__":
    main()
