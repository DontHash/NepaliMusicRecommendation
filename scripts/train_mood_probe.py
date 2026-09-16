"""Train a mood probe on lyric embeddings from LLM pseudo-labels.

The muRIL classification head collapsed onto label priors twice (see
Phase C3 notes), so mood is instead predicted by a linear probe over the
chunked mpnet embeddings (the same content-sensitive space used for
retrieval). Trains per-label logistic regressions, reports held-out F1,
saves ``music_rec_artifacts/mood_probe.npz``, writes
``music_rec_artifacts/sentiment_scores_probe.csv`` for every song, and
optionally scores the model on ``eval/mood_gold.csv``.

Usage:
    python scripts/train_mood_probe.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LABELS = ("joy", "sadness", "anger", "fear", "depression", "positive", "negative")
EMOTIONS = LABELS[:5]
POSITIVE_THRESHOLD = 0.0
NEGATIVE_THRESHOLD = 0.10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pseudo", type=Path,
        default=PROJECT_ROOT / "R_data" / "raw" / "kaggle" / "sentiment_distill" / "mood_pseudo_labels.csv",
    )
    parser.add_argument("--embeddings", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "embeddings.npy")
    parser.add_argument("--ids", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "embedding_ids.json")
    parser.add_argument("--cleaned", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv")
    parser.add_argument("--gold", type=Path, default=PROJECT_ROOT / "eval" / "mood_gold.csv")
    parser.add_argument("--probe-out", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "mood_probe.npz")
    parser.add_argument("--scores-out", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "sentiment_scores_probe.csv")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def multi_f1(y_true: np.ndarray, y_pred: np.ndarray, names: tuple[str, ...]) -> dict:
    return {name: round(f1_binary(y_true[:, i], y_pred[:, i]), 4) for i, name in enumerate(names)}


def macro_f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return round(float(np.mean([f1_binary(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])])), 4)


def sentiment_metrics(y_true: np.ndarray, labels: np.ndarray) -> dict:
    classes = ("positive", "negative", "neutral")
    per_class = {}
    for cls in classes:
        tp = int(((y_true == cls) & (labels == cls)).sum())
        fp = int(((y_true != cls) & (labels == cls)).sum())
        fn = int(((y_true == cls) & (labels != cls)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[cls] = {
            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
            "support": int((y_true == cls).sum()),
        }
    return {
        "accuracy": round(float((y_true == labels).mean()), 4),
        "macro_f1": round(float(np.mean([v["f1"] for v in per_class.values()])), 4),
        "per_class": per_class,
    }


def main() -> None:
    from sklearn.linear_model import LogisticRegression

    args = parse_args()
    cleaned = pd.read_csv(args.cleaned, encoding="utf-8")
    ids = [int(x) for x in json.loads(args.ids.read_text(encoding="utf-8"))]
    embeddings = np.load(args.embeddings).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    row_of_song = {song_id: row for row, song_id in enumerate(ids)}

    pseudo = pd.read_csv(args.pseudo, encoding="utf-8")
    pseudo = pseudo[pseudo["song_id"].isin(row_of_song)].reset_index(drop=True)
    x_train_all = embeddings[[row_of_song[s] for s in pseudo["song_id"]]]

    rng = np.random.default_rng(args.seed)
    order = rng.permutation(len(pseudo))
    n_test = int(len(pseudo) * args.test_size)
    test_idx, train_idx = order[:n_test], order[n_test:]

    report: dict = {"songs_in_train_pool": int(len(pseudo)), "labels": {}}
    coefs, intercepts = [], []
    test_probs = np.zeros((len(test_idx), len(LABELS)), dtype=np.float32)
    for li, label in enumerate(LABELS):
        y = pseudo[label].to_numpy().astype(int)
        model = LogisticRegression(max_iter=3000, C=1.0)
        model.fit(x_train_all[train_idx], y[train_idx])
        coefs.append(model.coef_[0].astype(np.float32))
        intercepts.append(float(model.intercept_[0]))
        probs = model.predict_proba(x_train_all)[:, 1]
        test_probs[:, li] = probs[test_idx]

    preds = (test_probs >= 0.5).astype(int)
    y_test = pseudo.iloc[test_idx][list(LABELS)].to_numpy().astype(int)
    report["holdout_emotion_f1"] = multi_f1(y_test[:, :5], preds[:, :5], EMOTIONS)
    report["holdout_f1"] = multi_f1(y_test, preds, LABELS)
    report["holdout_macro_f1"] = round(float(np.mean(list(report["holdout_f1"].values()))), 4)

    # full-corpus predictions
    all_probs = np.full((len(embeddings), len(LABELS)), np.nan, dtype=np.float32)
    for li, label in enumerate(LABELS):
        model = LogisticRegression(max_iter=3000, C=1.0)
        model.fit(x_train_all, pseudo[label].to_numpy().astype(int))
        all_probs[:, li] = model.predict_proba(embeddings)[:, 1]
        coefs[li] = model.coef_[0].astype(np.float32)
        intercepts[li] = float(model.intercept_[0])

    scores = pd.DataFrame({"song_id": ids})
    for li, label in enumerate(LABELS):
        scores[label] = all_probs[:, li]
    score = scores["positive"] - scores["negative"]
    scores["sentiment_score"] = score
    scores["sentiment_label"] = np.where(
        score > POSITIVE_THRESHOLD,
        "positive",
        np.where(score < -NEGATIVE_THRESHOLD, "negative", "neutral"),
    )
    scores.to_csv(args.scores_out, index=False, encoding="utf-8")
    report["sentiment_distribution"] = scores["sentiment_label"].value_counts().to_dict()

    np.savez(
        args.probe_out,
        coef=np.vstack(coefs),
        intercept=np.asarray(intercepts, dtype=np.float32),
        labels=np.array(LABELS),
    )

    if args.gold.exists():
        from eval.mood_gold_eval import f1_binary, relaxed_accuracy

        gold = pd.read_csv(args.gold, encoding="utf-8")
        renamed = scores.rename(
            columns={**{e: f"{e}_prob" for e in EMOTIONS}, "positive": "prob_positive", "negative": "prob_negative"}
        )
        merged = gold.merge(renamed, on="song_id", how="inner")
        gold_pos = merged["positive"].to_numpy()
        gold_neg = merged["negative"].to_numpy()
        model_pos = (merged["prob_positive"].to_numpy() >= 0.5).astype(int)
        model_neg = (merged["prob_negative"].to_numpy() >= 0.5).astype(int)
        report["gold"] = {
            "relaxed_accuracy": relaxed_accuracy(gold_pos, gold_neg, model_pos, model_neg),
            "positive": f1_binary(gold_pos, model_pos),
            "negative": f1_binary(gold_neg, model_neg),
        }
        gold_emotion = {}
        for emotion in EMOTIONS:
            truth = merged[emotion].to_numpy().astype(int)
            pred = (merged[f"{emotion}_prob"].to_numpy() >= 0.5).astype(int)
            gold_emotion[emotion] = {"f1": f1_binary(truth, pred)["f1"], "support": int(truth.sum())}
        report["gold_emotions"] = gold_emotion

    print(json.dumps(report, ensure_ascii=False, indent=2))
    out = PROJECT_ROOT / "music_rec_artifacts" / "mood_probe_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"probe -> {args.probe_out}")
    print(f"scores -> {args.scores_out}")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
