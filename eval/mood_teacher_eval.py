"""Score the LLM teacher against the mood gold set (the labeling diagnostic).

Compares the two teacher prompt variants from
``scripts/kaggle_jobs/mood_teacher_check.py`` with the installed probe and
trivial baselines, on the 60 hand-reviewed songs.

Usage:
    python eval/mood_teacher_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
TEACHER = PROJECT_ROOT / "R_data" / "raw" / "kaggle" / "mood_teacher_check" / "teacher_gold_labels.csv"
PROBE = PROJECT_ROOT / "music_rec_artifacts" / "sentiment_scores.csv"
EMOTIONS = ("joy", "sadness", "anger", "fear", "depression")
SENTIMENTS = ("positive", "negative", "neutral")


def f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0


def sentiment_scores(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    per_class = {}
    for cls in SENTIMENTS:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[cls] = round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0
    return {
        "accuracy": round(float((y_true == y_pred).mean()), 4),
        "macro_f1": round(float(np.mean(list(per_class.values()))), 4),
        "per_class_f1": per_class,
    }


def main() -> None:
    gold = pd.read_csv(GOLD, encoding="utf-8")
    teacher = pd.read_csv(TEACHER, encoding="utf-8")
    merged = gold.merge(teacher, on="song_id", how="inner")
    report: dict = {"gold_size": len(gold), "matched": len(merged)}

    y_true_sent = merged["sentiment"].to_numpy()

    for tag, label in (("a", "teacher_production_prompt"), ("b", "teacher_strict_prompt")):
        parsed = merged[merged[f"parsed_{tag}"] == 1]
        y_pred = parsed[f"{tag}_sentiment"].to_numpy()
        entry = sentiment_scores(parsed["sentiment"].to_numpy(), y_pred)
        entry["evaluated"] = int(len(parsed))
        entry["emotion_f1"] = {
            e: f1_binary(parsed[e].to_numpy().astype(int), parsed[f"{tag}_{e}"].to_numpy().astype(int))
            for e in EMOTIONS
        }
        entry["emotion_supports"] = {e: int(parsed[e].sum()) for e in EMOTIONS}
        report[label] = entry

    baseline = np.full(len(merged), "negative")
    report["always_negative"] = sentiment_scores(y_true_sent, baseline)

    if PROBE.exists():
        probe = pd.read_csv(PROBE, encoding="utf-8")
        probe_merged = merged.merge(probe[["song_id", "sentiment_label"]], on="song_id", how="inner")
        report["probe_installed"] = sentiment_scores(
            probe_merged["sentiment"].to_numpy(), probe_merged["sentiment_label"].to_numpy()
        )

    for name, entry in report.items():
        if isinstance(entry, dict) and "accuracy" in entry:
            print(f"{name:26s} acc={entry['accuracy']:.3f} macro_f1={entry['macro_f1']:.3f}")
    print()
    for tag, label in (("a", "teacher_production_prompt"), ("b", "teacher_strict_prompt")):
        print(f"{label} emotion F1:", report[label]["emotion_f1"])

    out = PROJECT_ROOT / "music_rec_artifacts" / "mood_teacher_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
