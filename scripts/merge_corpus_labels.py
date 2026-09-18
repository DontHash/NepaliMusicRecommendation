"""Merge relabeled songs into the corpus mood-label set.

The corpus labels live per relabel run under ``R_data/raw/gemini/<run>/labels.csv``.
This script folds a newer run into the base set (song-level overwrite), writes
the merged file for probe training, and refreshes
``music_rec_artifacts/mood_phrases.csv`` for the attribution phrase fallback.

Usage:
    python scripts/merge_corpus_labels.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config  # noqa: E402

LABEL_COLUMNS = [
    "song_id",
    "positive",
    "negative",
    "joy",
    "sadness",
    "anger",
    "fear",
    "depression",
    "mood_phrase",
    "confidence",
]


def merge(base: pd.DataFrame, update: pd.DataFrame) -> pd.DataFrame:
    base = base.copy()
    update = update.copy()
    for frame in (base, update):
        missing = set(LABEL_COLUMNS) - set(frame.columns)
        if missing:
            sys.exit(f"missing columns {sorted(missing)}")
    base = base.set_index("song_id")
    update = update.set_index("song_id")
    merged = update.combine_first(base)
    merged = merged.reset_index()
    return merged[LABEL_COLUMNS].sort_values("song_id").reset_index(drop=True)


def main() -> None:
    config = Config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        type=Path,
        default=PROJECT_ROOT / "R_data" / "raw" / "gemini" / "corpus_v2" / "labels.csv",
    )
    parser.add_argument(
        "--update",
        type=Path,
        default=PROJECT_ROOT / "R_data" / "raw" / "gemini" / "corpus_v3" / "labels.csv",
    )
    parser.add_argument(
        "--merged",
        type=Path,
        default=PROJECT_ROOT / "R_data" / "raw" / "gemini" / "corpus_v3" / "labels_merged.csv",
    )
    parser.add_argument(
        "--phrases-out",
        type=Path,
        default=config.artifacts_dir / "mood_phrases.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "R_data" / "raw" / "gemini" / "corpus_v3" / "merge_report.json",
    )
    args = parser.parse_args()

    base = pd.read_csv(args.base, encoding="utf-8")
    update = pd.read_csv(args.update, encoding="utf-8")
    merged = merge(base, update)

    args.merged.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.merged, index=False, encoding="utf-8")

    phrases = merged[["song_id", "mood_phrase", "confidence"]].dropna(subset=["mood_phrase"])
    phrases.to_csv(args.phrases_out, index=False, encoding="utf-8")

    report = {
        "base": str(args.base),
        "base_rows": int(len(base)),
        "update": str(args.update),
        "update_rows": int(len(update)),
        "merged_rows": int(len(merged)),
        "replaced_ids": sorted(int(x) for x in set(update["song_id"])),
        "merged": str(args.merged),
        "phrases": str(args.phrases_out),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"base {len(base)} + update {len(update)} -> merged {len(merged)}")
    print(f"merged labels -> {args.merged}")
    print(f"mood phrases ({len(phrases)}) -> {args.phrases_out}")


if __name__ == "__main__":
    main()
