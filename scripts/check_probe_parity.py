"""Parity check: analyzer probe inference vs stored corpus artifacts.

Samples corpus songs, re-encodes their lyrics with the analyzer's chunked
recipe, applies the probe, and verifies agreement with the stored artifacts:
embedding cosine vs ``embeddings.npy``, probability deltas vs
``sentiment_scores.csv``, and label agreement through the analyzer path.

Usage:
    python scripts/check_probe_parity.py [--n 25]
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

from MusicAnalyzer import MusicAnalyzer, probe_predict, sentiment_label
from music_rec.config import Config
from music_rec.embeddings import _encode_chunked

LABELS = ("joy", "sadness", "anger", "fear", "depression", "positive", "negative")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    config = Config()
    cleaned = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8").fillna("")
    ids = [int(x) for x in json.loads(config.embedding_ids_json.read_text(encoding="utf-8"))]
    stored = np.load(config.embeddings_npy).astype(np.float32)
    stored_n = stored / np.maximum(np.linalg.norm(stored, axis=1, keepdims=True), 1e-12)
    scores = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8").set_index("song_id")

    analyzer = MusicAnalyzer(config=config, use_transliterator=False)
    probe = analyzer._load_probe()
    model = analyzer._load_embedder()
    max_len = min(config.embed_window_tokens, model.max_seq_length)
    stride = max(1, min(config.embed_window_stride, max_len - 1))

    rng = np.random.default_rng(args.seed)
    sample = [int(x) for x in rng.choice(ids, size=min(args.n, len(ids)), replace=False)]
    row_of = {song_id: i for i, song_id in enumerate(ids)}
    by_song = cleaned.set_index("song_id")["lyrics"]

    texts = [str(by_song.loc[sid]) for sid in sample]
    matrix, _, _ = _encode_chunked(
        model, texts, config.embed_batch_size, max_len, stride, 10**9, quiet=True
    )
    matrix = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)

    cos_min, diff_max, label_ok = 1.0, 0.0, 0
    for i, song_id in enumerate(sample):
        cos = float(matrix[i] @ stored_n[row_of[song_id]])
        probs = probe_predict(matrix[i], probe["coef"], probe["intercept"])
        by_label = dict(zip(probe["labels"], (float(p) for p in probs)))
        stored_row = scores.loc[song_id]
        dmax = max(abs(by_label[label] - float(stored_row[label])) for label in LABELS)
        score = by_label["positive"] - by_label["negative"]
        label = sentiment_label(
            score, config.probe_positive_threshold, config.probe_negative_threshold
        )
        stored_label = str(stored_row["sentiment_label"])
        ok = label == stored_label
        cos_min = min(cos_min, cos)
        diff_max = max(diff_max, dmax)
        label_ok += int(ok)
        print(
            f"  [{song_id}] cos={cos:.5f} max_delta={dmax:.4f} "
            f"label={label:8s} stored={stored_label:8s} {'OK' if ok else 'MISMATCH'}"
        )

    for song_id in sample[:2]:
        result = analyzer.analyze_sentiment(str(by_song.loc[song_id]))
        print(
            f"  analyzer[{song_id}] label={result['label']} "
            f"score={result['score']:+.3f} stored={scores.loc[song_id, 'sentiment_label']}"
        )

    passed = cos_min > 0.99 and diff_max < 0.05 and label_ok == len(sample)
    print(
        f"sampled={len(sample)} min_cosine={cos_min:.5f} max_prob_delta={diff_max:.5f} "
        f"label_agreement={label_ok}/{len(sample)} -> {'PASS' if passed else 'FAIL'}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
