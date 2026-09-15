"""Kaggle kernel: chunked mean-pooled lyric embeddings.

Runs on Kaggle with ``cleaned_lyrics.csv`` attached as a dataset (mounted under
/kaggle/input). Long songs exceed the transformer max sequence length, so each
lyric is tokenized into overlapping windows, every window is encoded, and the
window vectors are mean-pooled into one vector per song. Writes
``embeddings.npy`` + ``embedding_ids.json`` + ``embed_report.json`` into
/kaggle/working, drop-in compatible with ``music_rec/embeddings.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
WINDOW_TOKENS = 128
WINDOW_STRIDE = 64
BATCH_SIZE = 256
INPUT_ROOT = Path("/kaggle/input")
OUT_DIR = Path("/kaggle/working")


def find_cleaned_csv() -> Path:
    named = sorted(INPUT_ROOT.rglob("cleaned_lyrics.csv"))
    if named:
        return max(named, key=lambda p: p.stat().st_size)
    candidates = sorted(INPUT_ROOT.rglob("*.csv"))
    if not candidates:
        raise SystemExit("no CSV found under /kaggle/input")
    return max(candidates, key=lambda p: p.stat().st_size)


def load_model():
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if device == "cuda" else ""
    print(f"[kaggle] device: {device} {gpu_name}".strip())
    return SentenceTransformer(MODEL_NAME, device=device), device, gpu_name


def embedding_dim(model) -> int:
    getter = getattr(model, "get_embedding_dimension", None) or getattr(
        model, "get_sentence_embedding_dimension"
    )
    return int(getter())


def encode_chunked(model, texts: list[str]) -> tuple[np.ndarray, int]:
    import torch

    tokenizer = model.tokenizer
    device = model.device
    pad_token_id = tokenizer.pad_token_id

    window_ids: list[list[int]] = []
    window_masks: list[list[int]] = []
    owners: list[int] = []
    for index, text in enumerate(texts):
        encoded = tokenizer(
            text,
            max_length=WINDOW_TOKENS,
            stride=WINDOW_STRIDE,
            truncation=True,
            return_overflowing_tokens=True,
            padding=False,
        )
        ids_list = encoded["input_ids"]
        mask_list = encoded["attention_mask"]
        window_ids.extend(ids_list)
        window_masks.extend(mask_list)
        owners.extend([index] * len(ids_list))
        done = index + 1
        if done % 500 == 0 or done == len(texts):
            print(f"[kaggle] tokenized {done}/{len(texts)} songs into {len(window_ids)} windows")

    hidden_size = embedding_dim(model)
    sums = np.zeros((len(texts), hidden_size), dtype=np.float32)
    counts = np.zeros(len(texts), dtype=np.int32)

    with torch.no_grad():
        for start in range(0, len(window_ids), BATCH_SIZE):
            batch_ids = window_ids[start : start + BATCH_SIZE]
            batch_masks = window_masks[start : start + BATCH_SIZE]
            batch_owners = owners[start : start + BATCH_SIZE]
            width = max(len(ids) for ids in batch_ids)
            padded_ids = np.full((len(batch_ids), width), pad_token_id, dtype=np.int64)
            padded_masks = np.zeros((len(batch_ids), width), dtype=np.int64)
            for row, (ids, mask) in enumerate(zip(batch_ids, batch_masks)):
                padded_ids[row, : len(ids)] = ids
                padded_masks[row, : len(mask)] = mask
            features = {
                "input_ids": torch.tensor(padded_ids, device=device),
                "attention_mask": torch.tensor(padded_masks, device=device),
            }
            output = model(features)
            vectors = output["sentence_embedding"].detach().cpu().numpy().astype(np.float32)
            np.add.at(sums, batch_owners, vectors)
            np.add.at(counts, batch_owners, 1)
            done = min(start + BATCH_SIZE, len(window_ids))
            if done % 5000 < BATCH_SIZE or done == len(window_ids):
                print(f"[kaggle] encoded {done}/{len(window_ids)} windows")

    counts[counts == 0] = 1
    return (sums / counts[:, None]).astype(np.float32), len(window_ids)


def encode_simple(model, texts: list[str]) -> tuple[np.ndarray, int]:
    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=False,
        show_progress_bar=False,
    )
    return vectors.astype(np.float32), len(texts)


def main() -> None:
    csv_path = find_cleaned_csv()
    print(f"[kaggle] input: {csv_path}")
    df = pd.read_csv(csv_path, encoding="utf-8")
    if "lyrics" not in df.columns or "song_id" not in df.columns:
        raise SystemExit(f"unexpected columns: {list(df.columns)}")
    texts = df["lyrics"].fillna("").astype(str).tolist()
    song_ids = [int(x) for x in df["song_id"].tolist()]

    model, device, gpu_name = load_model()
    if getattr(model.tokenizer, "is_fast", False):
        print(f"[kaggle] chunked pooling: window={WINDOW_TOKENS} stride={WINDOW_STRIDE} batch={BATCH_SIZE}")
        matrix, windows = encode_chunked(model, texts)
        mode = "chunked"
    else:
        print("[kaggle] tokenizer is not fast; using single-pass encoding")
        matrix, windows = encode_simple(model, texts)
        mode = "single-pass"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUT_DIR / "embeddings.npy", matrix)
    (OUT_DIR / "embedding_ids.json").write_text(json.dumps(song_ids), encoding="utf-8")
    report = {
        "model": MODEL_NAME,
        "mode": mode,
        "songs": len(song_ids),
        "windows": int(windows),
        "window_tokens": WINDOW_TOKENS,
        "window_stride": WINDOW_STRIDE,
        "batch_size": BATCH_SIZE,
        "embedding_dim": int(matrix.shape[1]),
        "device": device,
        "gpu": gpu_name,
        "norms_mean": round(float(np.linalg.norm(matrix, axis=1).mean()), 4),
        "finite": bool(np.isfinite(matrix).all()),
    }
    (OUT_DIR / "embed_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
