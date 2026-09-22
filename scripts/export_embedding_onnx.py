"""Export the mpnet query encoder to ONNX for fast CPU inference.

One-time, dev-machine step (needs torch + transformers, not the runtime):

    python scripts/export_embedding_onnx.py

Writes ``model.onnx`` + ``tokenizer.json`` into
``music_rec_artifacts/embedding_onnx/`` (gitignored, ~440MB). The web app then
loads this artifact through ``music_rec/onnx_encoder.py``, which avoids the
~9s transformers import on first query. Validate with
``scripts/check_onnx_parity.py`` before relying on it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config  # noqa: E402


def export(out_dir: Path, *, max_seq_length: int = 128, force: bool = False) -> dict:
    import torch
    from transformers import AutoModel, AutoTokenizer

    model_path = out_dir / "model.onnx"
    tokenizer_path = out_dir / "tokenizer.json"
    if model_path.exists() and tokenizer_path.exists() and not force:
        return {"skipped": True, "model": str(model_path), "tokenizer": str(tokenizer_path)}

    out_dir.mkdir(parents=True, exist_ok=True)
    name = Config().embedding_model

    tokenizer = AutoTokenizer.from_pretrained(name, use_fast=True)
    tokenizer.save_pretrained(out_dir)

    model = AutoModel.from_pretrained(name)
    model.eval()

    class _LastHiddenState(torch.nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, input_ids, attention_mask):
            output = self.inner(
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=False,
            )
            return output[0]

    sample = tokenizer(
        "warmup",
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_seq_length,
    )
    with torch.no_grad():
        torch.onnx.export(
            _LastHiddenState(model),
            (sample["input_ids"], sample["attention_mask"]),
            str(model_path),
            input_names=["input_ids", "attention_mask"],
            output_names=["last_hidden_state"],
            dynamic_axes={
                "input_ids": {0: "batch", 1: "sequence"},
                "attention_mask": {0: "batch", 1: "sequence"},
                "last_hidden_state": {0: "batch", 1: "sequence"},
            },
            opset_version=14,
        )

    return {
        "skipped": False,
        "model": str(model_path),
        "model_mb": round(model_path.stat().st_size / 1e6, 1),
        "tokenizer": str(tokenizer_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Config().embedding_onnx_dir)
    parser.add_argument("--max-seq-length", type=int, default=128)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export(args.out, max_seq_length=args.max_seq_length, force=args.force)
    print(result)


if __name__ == "__main__":
    main()
