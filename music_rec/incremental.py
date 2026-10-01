"""Incremental append of new corpus songs into the text artifacts (DE6).

Generalises the audio-pipeline prototype: only the new tail rows of
``cleaned_lyrics.csv`` are embedded and appended to embeddings/windows/ids/
sentiment scores; existing rows are never touched. Features and the song index
are rebuilt afterwards (cheap relative to embedding).

A watermark is recorded in ``R_data/state/watermarks.json`` so health/monitoring
can see when the corpus feed last advanced.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .config import Config

Encoder = Callable[[list[str]], tuple[np.ndarray, np.ndarray, np.ndarray]]
WATERMARKS_RELATIVE = Path("R_data") / "state" / "watermarks.json"


def _atomic_save(path: Path, save) -> None:
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    save(tmp)
    os.replace(tmp, path)


def default_encoder(config: Config, device: str = "auto") -> Encoder:
    from .embeddings import _encode_chunked, _load_model

    model = _load_model(config.embedding_model, device)
    batch = (config.embed_batch_size_gpu if str(model.device).startswith("cuda")
             else config.embed_batch_size)
    max_len = min(config.embed_window_tokens, model.max_seq_length)
    stride = max(1, min(config.embed_window_stride, max_len - 1))

    def encode(texts: list[str]):
        return _encode_chunked(model, texts, batch, max_len, stride, log_every=25)

    return encode


def score_with_probe(matrix: np.ndarray, probe) -> np.ndarray:
    """Label-order probabilities for ``matrix`` under the installed mood probe."""
    labels = [str(value) for value in probe["labels"]]
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    logits = (matrix / norms) @ probe["coef"].T + probe["intercept"]
    return 1.0 / (1.0 + np.exp(-logits))


def update_watermark(path: Path, name: str, payload: dict) -> dict:
    path = Path(path)
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
    entry = {"updated_at": datetime.now(timezone.utc).isoformat(), **payload}
    data[name] = entry
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / (path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return entry


def append_new_songs(config: Config | None = None, *, encoder: Encoder | None = None,
                     device: str = "auto", rebuild: bool = True,
                     report_path: Path | None = None,
                     watermark_path: Path | None = None) -> dict:
    """Append the corpus tail to the text artifacts; returns a report dict."""
    config = config or Config()
    frame = pd.read_csv(config.cleaned_lyrics_csv, encoding="utf-8").fillna("")
    embeddings = np.load(config.embeddings_npy)
    window_vectors = np.load(config.window_vectors_npy)
    window_owners = np.load(config.window_owners_npy)
    ids = [int(value) for value in
           json.loads(config.embedding_ids_json.read_text(encoding="utf-8"))]
    scores = pd.read_csv(config.sentiment_scores_csv, encoding="utf-8")

    n_old = len(ids)
    n_new = len(frame) - n_old
    report: dict = {"songs_before": n_old, "songs_after": int(len(frame)),
                    "new_songs": max(n_new, 0)}
    if n_new <= 0:
        return {**report, "status": "noop"}
    if ids != frame["song_id"].iloc[:n_old].astype(int).tolist():
        raise ValueError("embedding ids do not match the corpus prefix; refusing to append")
    if len(scores) != n_old:
        raise ValueError(f"sentiment rows ({len(scores)}) != embedded songs ({n_old})")
    if len(window_owners) != len(window_vectors):
        raise ValueError("window owners do not match window vectors")

    texts = frame["lyrics"].iloc[n_old:].astype(str).tolist()
    encoder = encoder or default_encoder(config, device)
    matrix, new_windows, new_owners_local = encoder(texts)
    if matrix.shape[0] != n_new:
        raise ValueError(f"encoded {matrix.shape[0]} songs, expected {n_new}")

    new_embeddings = np.vstack([embeddings, matrix.astype(np.float32)])
    new_window_vectors = np.vstack([window_vectors, new_windows.astype(np.float32)])
    new_window_owners = np.concatenate(
        [window_owners, new_owners_local.astype(np.int32) + n_old])
    new_ids = ids + frame["song_id"].iloc[n_old:].astype(int).tolist()

    probe = np.load(config.mood_probe_npz, allow_pickle=False)
    labels = [str(value) for value in probe["labels"]]
    probs = score_with_probe(matrix, probe)
    sentiment = probs[:, labels.index("positive")] - probs[:, labels.index("negative")]
    sentiment_label = np.where(
        sentiment > config.probe_positive_threshold,
        "positive",
        np.where(sentiment < -config.probe_negative_threshold, "negative", "neutral"),
    )
    new_scores = pd.DataFrame({
        "song_id": frame["song_id"].iloc[n_old:].astype(int).tolist(),
        **{label: probs[:, index] for index, label in enumerate(labels)},
        "sentiment_score": sentiment,
        "sentiment_label": sentiment_label,
    })[scores.columns.tolist()]
    merged_scores = pd.concat([scores, new_scores], ignore_index=True)

    _atomic_save(config.embeddings_npy, lambda path: np.save(path, new_embeddings))
    _atomic_save(config.window_vectors_npy, lambda path: np.save(path, new_window_vectors))
    _atomic_save(config.window_owners_npy, lambda path: np.save(path, new_window_owners))
    _atomic_save(config.embedding_ids_json,
                 lambda path: path.write_text(json.dumps(new_ids), encoding="utf-8"))
    _atomic_save(config.sentiment_scores_csv,
                 lambda path: merged_scores.to_csv(path, index=False, encoding="utf-8"))

    if rebuild:
        from .features import build_feature_matrix
        from .index import build_index

        build_feature_matrix(config)
        vectors_path = (config.feature_matrix_npy if config.feature_matrix_npy.exists()
                        else config.embeddings_npy)
        build_index(
            np.load(vectors_path),
            config.faiss_index_path,
            index_type=config.index_type,
            hnsw_m=config.index_hnsw_m,
            ef_construction=config.index_ef_construction,
            ef_search=config.index_ef_search,
        )

    digest = hashlib.sha256(",".join(str(value) for value in new_ids).encode()).hexdigest()[:12]
    report.update({
        "status": "appended",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "new_windows": int(len(new_owners_local)),
        "embedding_shape": list(new_embeddings.shape),
        "window_shape": list(new_window_vectors.shape),
        "sentiment_rows": int(len(merged_scores)),
        "ids_digest": digest,
        "rebuild": rebuild,
    })
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                               encoding="utf-8")
    report["watermark"] = update_watermark(
        Path(watermark_path) if watermark_path else config.project_root / WATERMARKS_RELATIVE,
        "corpus.append",
        {"rows": int(len(frame)), "new_songs": n_new, "ids_digest": digest},
    )
    return report
