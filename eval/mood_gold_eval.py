"""Benchmark song-mood models against the hand-reviewed gold set.

Compares the distilled song-domain model (predictions in
``music_rec_artifacts/sentiment_scores.csv``) with the original tweet-trained
muRIL model (inferred locally on the gold lyrics) on sentiment accuracy/F1,
plus per-emotion F1 for the distilled model.

Usage:
    python eval/mood_gold_eval.py
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
CLEANED = PROJECT_ROOT / "music_rec_artifacts" / "cleaned_lyrics.csv"
SCORES = PROJECT_ROOT / "music_rec_artifacts" / "sentiment_scores.csv"
SENTIMENT_MODEL_DIR = PROJECT_ROOT / "music_rec_artifacts" / "sentiment_model"
EMOTIONS = ("joy", "sadness", "anger", "fear", "depression")
SENTIMENTS = ("positive", "negative", "neutral")


def f1_scores(y_true: np.ndarray, y_pred: np.ndarray, labels: tuple[str, ...]) -> dict:
    out = {}
    for label in labels:
        tp = int(((y_true == label) & (y_pred == label)).sum())
        fp = int(((y_true != label) & (y_pred == label)).sum())
        fn = int(((y_true == label) & (y_pred != label)).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        out[label] = {
            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "support": int((y_true == label).sum()),
        }
    return out


def infer_existing_model(texts: list[str], max_len: int = 256) -> pd.DataFrame:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(SENTIMENT_MODEL_DIR)
    model = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_MODEL_DIR)
    model.eval()

    labels: list[str] = []
    scores: list[float] = []
    with torch.no_grad():
        for text in texts:
            ids = tokenizer.encode(text, add_special_tokens=True)
            if len(ids) > max_len:
                ids = [ids[0]] + ids[-(max_len - 1) :]
            input_ids = torch.tensor([ids])
            attn = torch.ones_like(input_ids)
            logits = model(input_ids=input_ids, attention_mask=attn).logits
            probs = torch.softmax(logits, dim=-1).numpy()[0]
            id2label = model.config.id2label
            pos = sum(float(probs[i]) for i in range(len(probs)) if "pos" in id2label[i].lower())
            neg = sum(float(probs[i]) for i in range(len(probs)) if "neg" in id2label[i].lower())
            scores.append(pos - neg)
            labels.append(id2label[int(np.argmax(probs))].lower())
    return pd.DataFrame({"sentiment_label": labels, "sentiment_score": scores})


def classify(score: float, threshold: float = 0.15) -> str:
    if score > threshold:
        return "positive"
    if score < -threshold:
        return "negative"
    return "neutral"


def main() -> None:
    gold = pd.read_csv(GOLD, encoding="utf-8")
    cleaned = pd.read_csv(CLEANED, encoding="utf-8")
    report: dict = {"gold_size": len(gold)}

    gold = gold.merge(cleaned[["song_id", "lyrics"]], on="song_id", how="left")
    y_true = gold["sentiment"].to_numpy()

    if SCORES.exists():
        distilled = pd.read_csv(SCORES, encoding="utf-8")
        distilled = distilled.rename(columns={e: f"{e}_prob" for e in EMOTIONS})
        merged = gold.merge(distilled, on="song_id", how="inner")
        y_pred = merged["sentiment_label"].str.lower().to_numpy()
        acc = float((y_true == y_pred).mean())
        report["distilled"] = {
            "accuracy": round(acc, 4),
            "macro_f1": round(float(np.mean([v["f1"] for v in f1_scores(y_true, y_pred, SENTIMENTS).values()])), 4),
            "per_class": f1_scores(y_true, y_pred, SENTIMENTS),
        }
        emotion_scores = {}
        for emotion in EMOTIONS:
            prob_col = f"{emotion}_prob"
            if prob_col in merged.columns:
                pred = (merged[prob_col].to_numpy() >= 0.5).astype(int)
                truth = gold[emotion].to_numpy()
                tp = int(((truth == 1) & (pred == 1)).sum())
                fp = int(((truth == 0) & (pred == 1)).sum())
                fn = int(((truth == 1) & (pred == 0)).sum())
                precision = tp / (tp + fp) if tp + fp else 0.0
                recall = tp / (tp + fn) if tp + fn else 0.0
                emotion_scores[emotion] = {
                    "f1": round(2 * precision * recall / (precision + recall), 4)
                    if precision + recall
                    else 0.0,
                    "support": int(truth.sum()),
                }
        report["distilled"]["emotions"] = emotion_scores

    if SENTIMENT_MODEL_DIR.exists():
        existing = infer_existing_model(gold["lyrics"].fillna("").astype(str).tolist())
        y_pred_existing = np.array([classify(s) for s in existing["sentiment_score"]])
        acc = float((y_true == y_pred_existing).mean())
        report["existing_muril"] = {
            "accuracy": round(acc, 4),
            "macro_f1": round(float(np.mean([v["f1"] for v in f1_scores(y_true, y_pred_existing, SENTIMENTS).values()])), 4),
            "per_class": f1_scores(y_true, y_pred_existing, SENTIMENTS),
        }

    out_path = PROJECT_ROOT / "music_rec_artifacts" / "mood_gold_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report -> {out_path}")


if __name__ == "__main__":
    main()
