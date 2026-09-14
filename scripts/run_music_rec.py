"""Build pipeline runner for the music recommender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config


def main():
    parser = argparse.ArgumentParser(description="Build the Nepali music recommender.")
    parser.add_argument(
        "phase",
        choices=["audit", "embed", "sentiment", "features", "index", "eval", "all"],
    )
    parser.add_argument("--with-sentiment", action="store_true", help="Include sentiment in 'all'")
    parser.add_argument("--input", type=Path, default=None, help="Override raw lyrics CSV for this run")
    args = parser.parse_args()
    cfg = Config()
    if args.input is not None:
        cfg.raw_lyrics_csv = Path(args.input)

    def do_audit():
        from music_rec.data_audit import run_audit
        from dataclasses import asdict

        print(json.dumps(asdict(run_audit(cfg)), ensure_ascii=False, indent=2))

    def do_embed():
        from music_rec.embeddings import compute_embeddings

        compute_embeddings(cfg)

    def do_sentiment():
        from music_rec.sentiment import train_classifier, infer_sentiment

        train_classifier(cfg)
        infer_sentiment(cfg)

    def do_features():
        from music_rec.features import build_feature_matrix

        build_feature_matrix(cfg)

    def do_index():
        import numpy as np
        from music_rec.index import build_index

        vecs_path = cfg.feature_matrix_npy if cfg.feature_matrix_npy.exists() else cfg.embeddings_npy
        build_index(np.load(vecs_path), cfg.faiss_index_path)
        print(f"[index] built from {Path(vecs_path).name} -> {cfg.faiss_index_path.name}")

    def do_eval():
        from music_rec.evaluate import evaluate

        print(json.dumps(evaluate(cfg), ensure_ascii=False, indent=2))

    if args.phase == "all":
        do_audit()
        do_embed()
        if args.with_sentiment:
            do_sentiment()
        do_features()
        do_index()
        do_eval()
    else:
        {
            "audit": do_audit,
            "embed": do_embed,
            "sentiment": do_sentiment,
            "features": do_features,
            "index": do_index,
            "eval": do_eval,
        }[args.phase]()


if __name__ == "__main__":
    main()
