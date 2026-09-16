"""Score the LLM teacher against the mood gold set (the labeling diagnostic).

Compares the two teacher prompt variants from
``scripts/kaggle_jobs/mood_teacher_check.py`` with the installed probe and
trivial baselines, using the multi-label gold schema (positive/negative
binaries; both = mixed).

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


def f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "support": int((y_true == 1).sum()),
    }


def gold_class(pos: int, neg: int) -> str:
    if pos and neg:
        return "mixed"
    if pos:
        return "positive"
    if neg:
        return "negative"
    return "neutral"


def relaxed_accuracy(gold_pos, gold_neg, model_pos, model_neg) -> float:
    correct = 0
    for gp, gn, mp, mn in zip(gold_pos, gold_neg, model_pos, model_neg):
        cls = gold_class(int(gp), int(gn))
        if cls == "mixed":
            ok = mp == 1 or mn == 1
        elif cls == "positive":
            ok = mp == 1
        elif cls == "negative":
            ok = mn == 1
        else:
            ok = mp == 0 and mn == 0
        correct += int(ok)
    return round(correct / len(gold_pos), 4) if len(gold_pos) else 0.0


def main() -> None:
    gold = pd.read_csv(GOLD, encoding="utf-8")
    teacher = pd.read_csv(TEACHER, encoding="utf-8")
    merged = gold.merge(teacher, on="song_id", how="inner")
    report: dict = {"gold_size": len(gold), "matched": len(merged)}

    for tag, label in (("a", "teacher_production_prompt"), ("b", "teacher_strict_prompt")):
        parsed = merged[merged[f"parsed_{tag}"] == 1]
        teacher_pos = (parsed[f"{tag}_sentiment"] == "positive").astype(int).to_numpy()
        teacher_neg = (parsed[f"{tag}_sentiment"] == "negative").astype(int).to_numpy()
        entry = {
            "evaluated": int(len(parsed)),
            "positive": f1_binary(parsed["positive"].to_numpy(), teacher_pos),
            "negative": f1_binary(parsed["negative"].to_numpy(), teacher_neg),
            "relaxed_accuracy": relaxed_accuracy(
                parsed["positive"].to_numpy(), parsed["negative"].to_numpy(), teacher_pos, teacher_neg
            ),
            "emotion_f1": {
                e: f1_binary(parsed[e].to_numpy().astype(int), parsed[f"{tag}_{e}"].to_numpy().astype(int))["f1"]
                for e in EMOTIONS
            },
        }
        report[label] = entry

    baseline = {
        "relaxed_accuracy": relaxed_accuracy(
            merged["positive"].to_numpy(),
            merged["negative"].to_numpy(),
            np.zeros(len(merged), dtype=int),
            np.ones(len(merged), dtype=int),
        ),
        "positive": f1_binary(merged["positive"].to_numpy(), np.zeros(len(merged), dtype=int)),
        "negative": f1_binary(merged["negative"].to_numpy(), np.ones(len(merged), dtype=int)),
    }
    report["always_negative"] = baseline

    if PROBE.exists():
        probe = pd.read_csv(PROBE, encoding="utf-8")
        probe_merged = merged.merge(probe[["song_id", "positive", "negative"]], on="song_id", suffixes=("", "_pred"))
        report["probe_installed"] = {
            "relaxed_accuracy": relaxed_accuracy(
                probe_merged["positive"].to_numpy(),
                probe_merged["negative"].to_numpy(),
                (probe_merged["positive_pred"].to_numpy() >= 0.5).astype(int),
                (probe_merged["negative_pred"].to_numpy() >= 0.5).astype(int),
            ),
            "positive": f1_binary(
                probe_merged["positive"].to_numpy(), (probe_merged["positive_pred"].to_numpy() >= 0.5).astype(int)
            ),
            "negative": f1_binary(
                probe_merged["negative"].to_numpy(), (probe_merged["negative_pred"].to_numpy() >= 0.5).astype(int)
            ),
        }

    for name, entry in report.items():
        if isinstance(entry, dict) and "relaxed_accuracy" in entry:
            print(
                f"{name:26s} relaxed_acc={entry['relaxed_accuracy']:.3f} "
                f"F1(pos)={entry['positive']['f1']:.3f} F1(neg)={entry['negative']['f1']:.3f}"
            )
    for tag, label in (("a", "teacher_production_prompt"), ("b", "teacher_strict_prompt")):
        print(f"{label} emotion F1:", report[label]["emotion_f1"])

    out = PROJECT_ROOT / "music_rec_artifacts" / "mood_teacher_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
