"""Numerical parity check: ONNX query encoder vs the torch SentenceTransformer.

    python scripts/check_onnx_parity.py [--n 24]

Exits non-zero when the minimum per-text cosine similarity drops below the
gate, so the ONNX backend is never adopted on faith.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config  # noqa: E402
from music_rec.embeddings import get_shared_model  # noqa: E402
from music_rec.onnx_encoder import OnnxEncoder  # noqa: E402

MIN_COSINE = 0.9999

SAMPLE_TEXTS = [
    "ke yo maya ho",
    "तिमी मेरो साथ नहुँदा",
    "जुदाइयाँ चल के आ रही हैं",
    "dukha",
    "maya lagcha",
    "तिमी बिना कसरी बिताउने होला जिन्दगी",
    "sad song",
    "party song",
    "Narayan Gopal",
    "रातको तारा जस्तै टाढा",
    "himal rahechu",
    "बतास भनी",
    "cause you trying to but you",
    "आमा को माया",
    "फूल फुल्यो बगैंचामा",
    "khusi",
]


def check(n: int = 24, min_cosine: float = MIN_COSINE) -> dict:
    config = Config()
    onnx_dir = config.embedding_onnx_dir
    model_path = onnx_dir / "model.onnx"
    tokenizer_path = onnx_dir / "tokenizer.json"
    if not model_path.exists() or not tokenizer_path.exists():
        raise SystemExit(f"ONNX artifact missing under {onnx_dir}; run scripts/export_embedding_onnx.py")

    texts = (SAMPLE_TEXTS * ((n // len(SAMPLE_TEXTS)) + 1))[:n]
    torch_model = get_shared_model(config.embedding_model, config.embedding_device)
    onnx_model = OnnxEncoder(model_path, tokenizer_path)

    rows = []
    for text in texts:
        reference = np.asarray(
            torch_model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0],
            dtype=np.float64,
        )
        candidate = np.asarray(onnx_model.encode([text])[0], dtype=np.float64)
        cosine = float(
            reference @ candidate / (np.linalg.norm(reference) * np.linalg.norm(candidate) + 1e-12)
        )
        rows.append((text, cosine))

    cosines = [cosine for _, cosine in rows]
    result = {
        "texts": len(rows),
        "min_cosine": round(float(min(cosines)), 6),
        "mean_cosine": round(float(np.mean(cosines)), 6),
        "gate": min_cosine,
        "passed": bool(min(cosines) >= min_cosine),
    }
    worst = sorted(rows, key=lambda row: row[1])[:3]
    result["worst"] = [{"text": text, "cosine": round(cosine, 6)} for text, cosine in worst]
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=24)
    parser.add_argument("--min-cosine", type=float, default=MIN_COSINE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = check(args.n, args.min_cosine)
    print(result)
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
