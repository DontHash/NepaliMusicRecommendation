"""Compute multilingual lyric embeddings into embeddings.npy.

Long songs exceed the transformer's max sequence length (128 word pieces for
mpnet), so a full song cannot be represented by a single forward pass. The
chunked path (default) tokenizes each lyric into overlapping windows of
``embed_window_tokens`` pieces, encodes every window, and mean-pools the window
vectors into one vector per song. Without this, only the first ~128 pieces of
every song were embedded and lyric-snippet queries could not match.
"""

from __future__ import annotations

import json
import os
import threading

import numpy as np
import pandas as pd

from .config import Config

_SHARED_MODELS: dict[tuple[str, str], object] = {}
_SHARED_MODELS_LOCK = threading.Lock()


def resolve_device(preference: str | None = None) -> str:
    """Resolve the torch device for embedding models.

    ``preference`` wins over ``PROJECTR_EMBED_DEVICE``; ``auto`` (default)
    picks CUDA when available. The web app sets the env var to ``cpu`` so
    model inference does not compete with the browser's WebGL rendering on
    the same GPU.
    """
    choice = (preference or os.environ.get("PROJECTR_EMBED_DEVICE") or "auto").lower()
    if choice in {"cpu", "cuda"}:
        return choice
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_model(model_name: str, device: str | None = None):
    import torch
    from sentence_transformers import SentenceTransformer

    resolved = resolve_device(device)
    if resolved == "cuda" and not torch.cuda.is_available():
        resolved = "cpu"
    if resolved == "cuda":
        print(f"[embeddings] using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[embeddings] using CPU")
    return SentenceTransformer(model_name, device=resolved)


def get_shared_model(model_name: str, device: str | None = None):
    """Return a process-wide singleton SentenceTransformer.

    Query encoding, mood attribution and single-lyric analysis all need the
    same mpnet model; sharing one instance avoids duplicate ~1GB copies and
    repeated multi-second loads.
    """
    resolved = resolve_device(device)
    key = (model_name, resolved)
    cached = _SHARED_MODELS.get(key)
    if cached is not None:
        return cached
    with _SHARED_MODELS_LOCK:
        cached = _SHARED_MODELS.get(key)
        if cached is None:
            cached = _load_model(model_name, resolved)
            _SHARED_MODELS[key] = cached
    return cached


def shared_model_ready(model_name: str, device: str | None = None) -> bool:
    return (model_name, resolve_device(device)) in _SHARED_MODELS


def text_encoder_ready(config: Config) -> bool:
    """Whether the active query-text encoder is loaded and can encode now."""
    return shared_model_ready(config.embedding_model, config.embedding_device)


def reset_shared_models() -> None:
    with _SHARED_MODELS_LOCK:
        _SHARED_MODELS.clear()


def _encode_simple(
    model, texts: list[str], batch_size: int, log_every: int
) -> tuple[np.ndarray, np.ndarray]:
    embeddings: list[np.ndarray] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vecs = model.encode(
            batch,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=False,  # normalization happens at index build
            show_progress_bar=False,
        )
        embeddings.append(vecs.astype(np.float32))
        done = min(start + batch_size, len(texts))
        if done % log_every < batch_size or done == len(texts):
            print(f"[embeddings] {done}/{len(texts)} songs encoded")
    matrix = np.vstack(embeddings).astype(np.float32)
    return matrix, np.arange(len(texts), dtype=np.int32)


def _tokenize_windows(
    tokenizer, text: str, max_len: int, stride: int
) -> tuple[list[list[int]], list[list[int]]]:
    encoded = tokenizer(
        text,
        max_length=max_len,
        stride=stride,
        truncation=True,
        return_overflowing_tokens=True,
        padding=False,
    )
    return encoded["input_ids"], encoded["attention_mask"]


def _embedding_dim(model) -> int:
    getter = getattr(model, "get_embedding_dimension", None) or getattr(
        model, "get_sentence_embedding_dimension"
    )
    return int(getter())


def _encode_chunked(
    model,
    texts: list[str],
    batch_size: int,
    max_len: int,
    stride: int,
    log_every: int,
    quiet: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import torch

    tokenizer = model.tokenizer
    device = model.device
    pad_token_id = tokenizer.pad_token_id

    window_ids: list[list[int]] = []
    window_masks: list[list[int]] = []
    owners: list[int] = []
    for index, text in enumerate(texts):
        ids_list, mask_list = _tokenize_windows(tokenizer, text, max_len, stride)
        window_ids.extend(ids_list)
        window_masks.extend(mask_list)
        owners.extend([index] * len(ids_list))
        done = index + 1
        if not quiet and (done % log_every == 0 or done == len(texts)):
            print(f"[embeddings] tokenized {done}/{len(texts)} songs into {len(window_ids)} windows")

    hidden_size = _embedding_dim(model)
    sums = np.zeros((len(texts), hidden_size), dtype=np.float32)
    counts = np.zeros(len(texts), dtype=np.int32)
    all_vectors: list[np.ndarray] = []

    with torch.no_grad():
        for start in range(0, len(window_ids), batch_size):
            batch_ids = window_ids[start : start + batch_size]
            batch_masks = window_masks[start : start + batch_size]
            batch_owners = owners[start : start + batch_size]
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
            all_vectors.append(vectors)
            np.add.at(sums, batch_owners, vectors)
            np.add.at(counts, batch_owners, 1)
            done = min(start + batch_size, len(window_ids))
            if not quiet and (done % (log_every * batch_size) < batch_size or done == len(window_ids)):
                print(f"[embeddings] encoded {done}/{len(window_ids)} windows")

    counts[counts == 0] = 1
    matrix = (sums / counts[:, None]).astype(np.float32)
    window_vectors = np.vstack(all_vectors).astype(np.float32)
    window_owners = np.asarray(owners, dtype=np.int32)
    return matrix, window_vectors, window_owners


def compute_embeddings(config: Config | None = None, log_every: int = 500) -> np.ndarray:
    config = config or Config()
    df = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8")
    texts = df["lyrics"].fillna("").astype(str).tolist()
    song_ids = df["song_id"].tolist()

    model = _load_model(config.embedding_model)
    batch_size = (
        config.embed_batch_size_gpu if str(model.device).startswith("cuda") else config.embed_batch_size
    )
    if config.embed_chunking and getattr(model.tokenizer, "is_fast", False):
        max_len = min(config.embed_window_tokens, model.max_seq_length)
        stride = max(1, min(config.embed_window_stride, max_len - 1))
        print(f"[embeddings] chunked pooling: window={max_len} stride={stride} batch={batch_size}")
        matrix, window_vectors, window_owners = _encode_chunked(
            model, texts, batch_size, max_len, stride, log_every
        )
    else:
        if config.embed_chunking:
            print("[embeddings] tokenizer is not fast; falling back to single-pass encoding")
        matrix, window_owners = _encode_simple(model, texts, batch_size, log_every)
        window_vectors = matrix

    np.save(config.embeddings_npy, matrix)
    np.save(config.window_vectors_npy, window_vectors)
    np.save(config.window_owners_npy, window_owners)
    config.embedding_ids_json.write_text(json.dumps(song_ids), encoding="utf-8")
    print(f"[embeddings] saved {matrix.shape} -> {config.embeddings_npy.name}")
    print(f"[embeddings] saved {window_vectors.shape} windows -> {config.window_vectors_npy.name}")
    return matrix


if __name__ == "__main__":
    compute_embeddings()
