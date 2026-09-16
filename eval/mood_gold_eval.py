"""Benchmark song-mood models against the hand-reviewed gold set.

Gold sentiment is two binaries (``positive``, ``negative``; both = mixed, neither
= neutral). Models are scored with per-class binary F1 plus a relaxed accuracy:
mixed gold songs accept a positive OR negative prediction, and neutral gold
songs require a neutral prediction. Emotion metrics use the five binary emotion
columns.

Usage:
    python eval/mood_gold_eval.py [--scores PATH] [--report PATH]
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

GOLD = PROJECT_ROOT / "eval" / "mood_gold.csv"
CLEANED = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
SCORES = PROJECT_ROOT / "music_rec_artifacts" / "sentiment_scores.csv"
SENTIMENT_MODEL_DIR = PROJECT_ROOT / "music_rec_artifacts" / "sentiment_model"
EMOTIONS = ("joy", "sadness", "anger", "fear", "depression")


def f1_binary(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
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


def score_model(name: str, gold: pd.DataFrame, model_pos: np.ndarray, model_neg: np.ndarray) -> dict:
    return {
        "model": name,
        "positive": f1_binary(gold["positive"].to_numpy(), model_pos),
        "negative": f1_binary(gold["negative"].to_numpy(), model_neg),
        "relaxed_accuracy": relaxed_accuracy(
            gold["positive"].to_numpy(), gold["negative"].to_numpy(), model_pos, model_neg
        ),
    }


def infer_existing_model(texts: list[str], max_len: int = 256) -> tuple[np.ndarray, np.ndarray]:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_DIR)
    model.eval()

    pos_flags, neg_flags = [], []
    with torch.no_grad():
        for text in texts:
            ids = tokenizer.encode(text, add_special_tokens=True)
            if len(ids) > max_len:
                ids = [ids[0]] + ids[-(max_len - 1) :]
            input_ids = torch.tensor([ids])
            logits = model(input_ids=input_ids, attention_mask=torch.ones_like(input_ids)).logits
            probs = torch.softmax(logits, dim=-1).numpy()[0]
            id2label = model.config.id2label
            pos = sum(float(probs[i]) for i in range(len(probs)) if "pos" in id2label[i].lower())
            neg = sum(float(probs[i]) for i in range(len(probs)) if "neg" in id2label[i].lower())
            pos_flags.append(int(pos >= 0.5))
            neg_flags.append(int(neg >= 0.5))
    return np.array(pos_flags), np.array(neg_flags)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=SCORES)
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "music_rec_artifacts" / "mood_gold_report.json")
    args = parser.parse_args()

    gold = pd.read_csv(GOLD, encoding="utf-8")
    cleaned = pd.read_csv(CLEANED, encoding="utf-8")
    report: dict = {"gold_size": len(gold), "scores_path": str(args.scores)}
    results = []

    results.append(
        score_model(
            "always_negative",
            gold,
            np.zeros(len(gold), dtype=int),
            np.ones(len(gold), dtype=int),
        )
    )

    if args.scores.exists():
        scores = pd.read_csv(args.scores, encoding="utf-8")
        merged = gold.merge(scores, on="song_id", how="inner", suffixes=("", "_pred"))
        if "positive_pred" in merged.columns:
            model_pos = (merged["positive_pred"].to_numpy() >= 0.5).astype(int)
            model_neg = (merged["negative_pred"].to_numpy() >= 0.5).astype(int)
        else:
            labels = merged["sentiment_label"].str.lower()
            model_pos = (labels == "positive").astype(int).to_numpy()
            model_neg = (labels == "negative").astype(int).to_numpy()
        entry = score_model(str(args.scores.name), merged, model_pos, model_neg)
        emotion_scores = {}
        for emotion in EMOTIONS:
            prob_col = f"{emotion}_pred"
            if prob_col in merged.columns:
                truth = merged[emotion].to_numpy().astype(int)
                pred = (merged[prob_col].to_numpy() >= 0.5).astype(int)
                emotion_scores[emotion] = f1_binary(truth, pred)
        if emotion_scores:
            entry["emotions"] = emotion_scores
        results.append(entry)

    if SENTIMENT_MODEL_DIR.exists():
        gold_lyrics = gold.merge(cleaned[["song_id", "lyrics"]], on="song_id", how="left")
        pos_flags, neg_flags = infer_existing_model(gold_lyrics["lyrics"].fillna("").astype(str).tolist())
        results.append(score_model("existing_muril_tweet", gold_lyrics, pos_flags, neg_flags))

    report["models"] = results
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    for entry in results:
        print(
            f"{entry['model'][:36]:36s} relaxed_acc={entry['relaxed_accuracy']:.3f} "
            f"F1(pos)={entry['positive']['f1']:.3f} F1(neg)={entry['negative']['f1']:.3f}"
        )
    print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
