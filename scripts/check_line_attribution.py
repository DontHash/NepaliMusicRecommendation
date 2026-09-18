"""Tune window-to-line mood attribution against the reviewed line gold.

Sweeps line aggregation modes and neutral floors over
``eval/line_mood_gold.csv`` (source ``user_v2``), reports per-cue and
per-difficulty breakdowns, and runs leave-one-song-out per-emotion bias
calibration. Candidate aggregators live here until one is adopted into
``music_rec.mood_attribution``; runtime behavior is unchanged.

Usage:
    python scripts/check_line_attribution.py
    python scripts/check_line_attribution.py --objective accuracy --no-calibration
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.mood_attribution import (
    EMOTIONS,
    MoodAttributor,
    _prob_matrix,
    _uniform_spans,
    aggregate_lines,
    dominant_label,
    line_spans,
)

GOLD = PROJECT_ROOT / "eval" / "line_mood_gold.csv"
OUT_JSON = PROJECT_ROOT / "music_rec_artifacts" / "line_attribution_tuning.json"
NEUTRAL = "neutral"
CLASSES = (*EMOTIONS, NEUTRAL)
MODES = ("mean", "overlap2", "hard", "max")
FLOORS = tuple(round(float(x), 2) for x in np.arange(0.30, 0.701, 0.05))


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def aggregate_mode(
    window_spans: list[tuple[int, int]],
    window_probs: np.ndarray,
    spans: list[tuple[int, int]],
    mode: str,
) -> np.ndarray:
    """Aggregate window probabilities per line under one of four modes.

    ``mean`` is the library's overlap-weighted average (runtime default);
    ``overlap2`` squares the overlap weight (sharper window focus); ``hard``
    votes each overlapping window's argmax weighted by overlap; ``max`` takes
    the elementwise max over overlapping windows.
    """
    if mode == "mean":
        return aggregate_lines(window_spans, window_probs, spans)
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")

    n_lines = len(spans)
    n_emo = int(window_probs.shape[1]) if len(window_probs) else len(EMOTIONS)
    if not n_lines:
        return np.zeros((0, n_emo), dtype=np.float32)
    if not len(window_spans):
        return np.zeros((n_lines, n_emo), dtype=np.float32)

    totals = np.zeros((n_lines, n_emo), dtype=np.float64)
    weights = np.zeros(n_lines, dtype=np.float64)
    votes = np.zeros(n_emo, dtype=np.float64)
    for probs in window_probs:
        votes[int(np.argmax(probs))] += 1.0
    vote_dist = votes / max(1.0, float(votes.sum()))
    fallback = window_probs.mean(axis=0)

    for (ws, we), probs in zip(window_spans, window_probs):
        for li, (ls, le) in enumerate(spans):
            overlap = _overlap((ws, we), (ls, le))
            if overlap <= 0:
                continue
            if mode == "overlap2":
                totals[li] += (overlap * overlap) * probs
                weights[li] += float(overlap * overlap)
            elif mode == "hard":
                hard = np.zeros(n_emo, dtype=np.float64)
                hard[int(np.argmax(probs))] = 1.0
                totals[li] += overlap * hard
                weights[li] += float(overlap)
            else:
                totals[li] = np.maximum(totals[li], probs)
                weights[li] = 1.0

    for li in range(n_lines):
        if weights[li] <= 0:
            totals[li] = vote_dist if mode == "hard" else fallback
            weights[li] = 1.0
    return (totals / weights[:, None]).astype(np.float32)


def gather(
    attributor: MoodAttributor, gold: pd.DataFrame
) -> tuple[list[dict], dict[str, dict[int, np.ndarray]]]:
    """Per-line gold records plus per-mode line probabilities keyed by song."""
    attributor._load_corpus_artifacts()
    emo_idx = attributor._emotion_indices()
    records: list[dict] = []
    probs_by_mode: dict[str, dict[int, np.ndarray]] = {mode: {} for mode in MODES}
    for song_id, group in gold.groupby("song_id", sort=True):
        song_id = int(song_id)
        row = attributor._row_of_song[song_id]
        rows = np.where(attributor._window_owners == row)[0]
        window_probs = _prob_matrix(
            attributor._window_vectors[rows], attributor._load_probe()
        )[:, emo_idx]
        text = str(attributor._cleaned.loc[song_id, "lyrics"])
        win_spans = attributor._window_spans(text)
        if len(win_spans) != len(rows):
            win_spans = _uniform_spans(text, len(rows))
        spans = line_spans(text)
        for mode in MODES:
            probs_by_mode[mode][song_id] = aggregate_mode(win_spans, window_probs, spans, mode)
        for rec in group.itertuples():
            records.append(
                {
                    "song_id": song_id,
                    "line_index": int(rec.line_index),
                    "emotion": str(rec.primary_emotion),
                    "cue": str(rec.cue_type),
                    "difficulty": str(rec.difficulty),
                    "occurrences": int(rec.occurrences),
                }
            )
    return records, probs_by_mode


def _predictions(
    records: list[dict], probs_by_mode: dict[str, dict[int, np.ndarray]], mode: str, floor: float
) -> list[str]:
    return [
        dominant_label(probs_by_mode[mode][rec["song_id"]][rec["line_index"]], floor)
        for rec in records
    ]


def _macro_f1(y_true: list[str], y_pred: list[str], classes: tuple[str, ...] = CLASSES) -> float:
    scores = []
    for label in classes:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        denom = 2 * tp + fp + fn
        scores.append(2 * tp / denom if denom else 0.0)
    return float(np.mean(scores))


def evaluate_config(
    records: list[dict], probs_by_mode: dict[str, dict[int, np.ndarray]], mode: str, floor: float
) -> dict:
    y_true = [rec["emotion"] for rec in records]
    y_pred = _predictions(records, probs_by_mode, mode, floor)
    correct = np.array([t == p for t, p in zip(y_true, y_pred)])
    result = {
        "mode": mode,
        "floor": floor,
        "accuracy": float(correct.mean()),
        "macro_f1": _macro_f1(y_true, y_pred),
        "per_cue_type": {},
        "per_difficulty": {},
    }
    for key, out_key in (("cue", "per_cue_type"), ("difficulty", "per_difficulty")):
        values = np.array([rec[key] for rec in records])
        for group in sorted(set(values.tolist())):
            mask = values == group
            result[out_key][group] = {
                "n": int(mask.sum()),
                "accuracy": float(correct[mask].mean()),
            }
    return result


def _encode(records: list[dict], probs_by_mode: dict[str, dict[int, np.ndarray]], mode: str):
    y = np.array([CLASSES.index(rec["emotion"]) for rec in records], dtype=np.int64)
    probs = np.stack(
        [probs_by_mode[mode][rec["song_id"]][rec["line_index"]] for rec in records]
    ).astype(np.float64)
    songs = np.array([rec["song_id"] for rec in records], dtype=np.int64)
    return y, probs, songs


def _bias_predict(probs: np.ndarray, bias: np.ndarray, floor: float) -> np.ndarray:
    biased = probs + np.asarray(bias, dtype=np.float64)
    idx = biased.argmax(axis=1)
    conf = biased[np.arange(len(biased)), idx]
    return np.where(conf < floor, len(EMOTIONS), idx)


def _macro_f1_matrix(pred: np.ndarray, y: np.ndarray) -> np.ndarray:
    scores = np.zeros(pred.shape[0], dtype=np.float64)
    for k in range(len(CLASSES)):
        tp = ((pred == k) & (y == k)).sum(axis=1)
        fp = ((pred == k) & (y != k)).sum(axis=1)
        fn = ((pred != k) & (y == k)).sum(axis=1)
        denom = 2 * tp + fp + fn
        scores += np.divide(2.0 * tp, denom, out=np.zeros_like(scores), where=denom > 0)
    return scores / len(CLASSES)


def _bias_scores(
    probs: np.ndarray,
    grid: np.ndarray,
    floor: float,
    y: np.ndarray,
    mask: np.ndarray,
    objective: str,
) -> np.ndarray:
    biased = probs[None, :, :] + grid[:, None, :]
    idx = biased.argmax(axis=2)
    conf = np.take_along_axis(biased, idx[:, :, None], axis=2)[:, :, 0]
    pred = np.where(conf < floor, len(EMOTIONS), idx)
    pred = pred[:, mask]
    truth = y[mask]
    if objective == "accuracy":
        return (pred == truth).mean(axis=1)
    return _macro_f1_matrix(pred, truth)


def calibrate(
    records: list[dict],
    probs_by_mode: dict[str, dict[int, np.ndarray]],
    mode: str,
    floor: float,
    objective: str,
    bias_max: float,
    bias_step: float,
) -> dict:
    y, probs, songs = _encode(records, probs_by_mode, mode)
    values = np.round(np.arange(-bias_max, bias_max + 1e-9, bias_step), 4)
    grid = np.array(list(product(values.tolist(), repeat=len(EMOTIONS))), dtype=np.float64)
    all_mask = np.ones(len(y), dtype=bool)

    scores = _bias_scores(probs, grid, floor, y, all_mask, objective)
    best = grid[int(np.argmax(scores))]
    in_pred = _bias_predict(probs, best, floor)

    loo_pred = np.zeros_like(y)
    loo_biases = []
    for song in sorted(set(songs.tolist())):
        mask = songs != song
        song_scores = _bias_scores(probs, grid, floor, y, mask, objective)
        song_best = grid[int(np.argmax(song_scores))]
        sel = songs == song
        loo_pred[sel] = _bias_predict(probs[sel], song_best, floor)
        loo_biases.append({"song_id": int(song), "bias": song_best.tolist()})

    y_named = [CLASSES[i] for i in y.tolist()]
    baseline_pred = [CLASSES[i] for i in _bias_predict(probs, np.zeros(len(EMOTIONS)), floor).tolist()]
    return {
        "mode": mode,
        "floor": floor,
        "objective": objective,
        "grid_values": values.tolist(),
        "biases_insample": best.tolist(),
        "accuracy_insample": float((in_pred == y).mean()),
        "macro_f1_insample": _macro_f1(y_named, [CLASSES[i] for i in in_pred.tolist()]),
        "accuracy_baseline": float((np.array(baseline_pred) == np.array(y_named)).mean()),
        "loocv_accuracy": float((loo_pred == y).mean()),
        "loocv_macro_f1": _macro_f1(y_named, [CLASSES[i] for i in loo_pred.tolist()]),
        "loocv_biases": loo_biases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, default=GOLD)
    parser.add_argument("--modes", default=",".join(MODES))
    parser.add_argument("--floors", default=",".join(str(f) for f in FLOORS))
    parser.add_argument("--objective", choices=("macro_f1", "accuracy"), default="macro_f1")
    parser.add_argument("--bias-max", type=float, default=0.12)
    parser.add_argument("--bias-step", type=float, default=0.04)
    parser.add_argument("--no-calibration", action="store_true")
    parser.add_argument("--json-out", type=Path, default=OUT_JSON)
    args = parser.parse_args()

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    floors = [float(f) for f in args.floors.split(",")]

    gold = pd.read_csv(args.gold, encoding="utf-8")
    attributor = MoodAttributor()
    records, probs_by_mode = gather(attributor, gold)

    sweep = [
        evaluate_config(records, probs_by_mode, mode, floor)
        for mode in modes
        for floor in floors
    ]
    sweep.sort(key=lambda row: row[args.objective], reverse=True)
    best = sweep[0]

    sanity = evaluate_config(records, probs_by_mode, "mean", 0.45)
    print(f"gold rows: {len(records)} lines / {gold['song_id'].nunique()} songs")
    print(
        f"sanity mean@0.45: {sanity['accuracy'] * len(records):.0f}/{len(records)} "
        f"= {sanity['accuracy']:.3f} (review kit reports 89/249)"
    )
    print(f"\ntop sweep by {args.objective}:")
    print(f"{'mode':9s} {'floor':5s} {'acc':7s} {'f1':7s}")
    for row in sweep[:8]:
        print(f"{row['mode']:9s} {row['floor']:<5.2f} {row['accuracy']:.4f}  {row['macro_f1']:.4f}")

    print(
        f"\nbest: {best['mode']}@{best['floor']:.2f} "
        f"acc={best['accuracy']:.4f} macro_f1={best['macro_f1']:.4f}"
    )
    print("per cue_type:")
    for cue, stats in sorted(best["per_cue_type"].items()):
        print(f"  {cue:14s} n={stats['n']:>3} acc={stats['accuracy']:.3f}")
    print("per difficulty:")
    for diff, stats in sorted(best["per_difficulty"].items()):
        print(f"  {diff:14s} n={stats['n']:>3} acc={stats['accuracy']:.3f}")

    report = {
        "objective": args.objective,
        "n_lines": len(records),
        "sweep": sweep,
        "best": best,
        "sanity_mean_045": sanity,
    }

    if not args.no_calibration:
        calibration = calibrate(
            records,
            probs_by_mode,
            best["mode"],
            best["floor"],
            args.objective,
            args.bias_max,
            args.bias_step,
        )
        print(
            f"\ncalibration ({best['mode']}@{best['floor']:.2f}): baseline={calibration['accuracy_baseline']:.4f} "
            f"insample={calibration['accuracy_insample']:.4f} loocv={calibration['loocv_accuracy']:.4f} "
            f"biases={calibration['biases_insample']}"
        )
        report["calibration"] = calibration

    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
