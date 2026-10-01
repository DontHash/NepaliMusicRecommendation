"""Extend text artifacts after a corpus merge (new tail rows only).

Appends to: embeddings.npy, window_vectors.npy, window_owners.npy,
embedding_ids.json and sentiment_scores.csv, then rebuilds feature_matrix.npy
and lyrics.faiss. Existing rows are never touched.

Run:
  python scripts/audio/update_text_artifacts.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import config, utils  # noqa: E402


def atomic_save(path: Path, save) -> None:
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    save(tmp)
    os.replace(tmp, path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    args = parser.parse_args()

    import numpy as np
    import pandas as pd

    from music_rec.config import Config, force_staging
    from music_rec.embeddings import _encode_chunked, _load_model
    from music_rec.index import build_index

    force_staging()  # incremental updater always reads/writes the staging layout
    music = Config()
    df = pd.read_csv(music.cleaned_lyrics_csv, encoding="utf-8").fillna("")
    embeddings = np.load(music.embeddings_npy)
    window_vectors = np.load(music.window_vectors_npy)
    window_owners = np.load(music.window_owners_npy)
    ids = json.loads(music.embedding_ids_json.read_text(encoding="utf-8"))
    scores = pd.read_csv(music.sentiment_scores_csv, encoding="utf-8")

    n_old = len(ids)
    n_new = len(df) - n_old
    if n_new <= 0:
        print(f"nothing to do: {len(df)} corpus rows, {n_old} embedded")
        return
    if [int(x) for x in ids] != df["song_id"].iloc[:n_old].astype(int).tolist():
        sys.exit("embedding ids do not match the corpus prefix; refusing to append")
    if len(scores) != n_old:
        sys.exit(f"sentiment rows ({len(scores)}) != embedded songs ({n_old})")
    print(f"appending {n_new} new songs to {n_old} existing (corpus {len(df)})")

    texts = df["lyrics"].iloc[n_old:].astype(str).tolist()
    model = _load_model(music.embedding_model, args.device)
    batch = music.embed_batch_size_gpu if str(model.device).startswith("cuda") else music.embed_batch_size
    max_len = min(music.embed_window_tokens, model.max_seq_length)
    stride = max(1, min(music.embed_window_stride, max_len - 1))
    matrix, new_windows, new_owners_local = _encode_chunked(model, texts, batch, max_len, stride, log_every=25)
    if matrix.shape[0] != n_new:
        sys.exit(f"encoded {matrix.shape[0]} songs, expected {n_new}")

    new_embeddings = np.vstack([embeddings, matrix.astype(np.float32)])
    new_window_vectors = np.vstack([window_vectors, new_windows.astype(np.float32)])
    new_window_owners = np.concatenate([window_owners, new_owners_local.astype(np.int32) + n_old])
    new_ids = [int(x) for x in ids] + df["song_id"].iloc[n_old:].astype(int).tolist()

    # Mood probe scores for the new songs (same recipe as the installed scores).
    probe = np.load(music.mood_probe_npz, allow_pickle=False)
    labels = [str(x) for x in probe["labels"]]
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    probs = 1.0 / (1.0 + np.exp(-((matrix / norms) @ probe["coef"].T + probe["intercept"])))
    pos = probs[:, labels.index("positive")]
    neg = probs[:, labels.index("negative")]
    sent_score = pos - neg
    sent_label = np.where(
        sent_score > music.probe_positive_threshold,
        "positive",
        np.where(sent_score < -music.probe_negative_threshold, "negative", "neutral"),
    )
    new_scores = pd.DataFrame({
        "song_id": df["song_id"].iloc[n_old:].astype(int).tolist(),
        **{label: probs[:, index] for index, label in enumerate(labels)},
        "sentiment_score": sent_score,
        "sentiment_label": sent_label,
    })[scores.columns.tolist()]
    merged_scores = pd.concat([scores, new_scores], ignore_index=True)

    atomic_save(music.embeddings_npy, lambda p: np.save(p, new_embeddings))
    atomic_save(music.window_vectors_npy, lambda p: np.save(p, new_window_vectors))
    atomic_save(music.window_owners_npy, lambda p: np.save(p, new_window_owners))
    atomic_save(music.embedding_ids_json, lambda p: p.write_text(json.dumps(new_ids), encoding="utf-8"))
    atomic_save(music.sentiment_scores_csv, lambda p: merged_scores.to_csv(p, index=False, encoding="utf-8"))

    from music_rec.features import build_feature_matrix

    build_feature_matrix(music)
    vectors_path = music.feature_matrix_npy if music.feature_matrix_npy.exists() else music.embeddings_npy
    build_index(
        np.load(vectors_path),
        music.faiss_index_path,
        index_type=music.index_type,
        hnsw_m=music.index_hnsw_m,
        ef_construction=music.index_ef_construction,
        ef_search=music.index_ef_search,
    )
    print(f"[index] rebuilt from {vectors_path.name} -> {music.faiss_index_path.name}")

    report = {
        "schema_version": config.SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": utils.git_sha(),
        "songs_before": n_old,
        "songs_after": len(df),
        "new_songs_embedded": n_new,
        "new_windows": int(len(new_owners_local)),
        "embedding_shape": list(new_embeddings.shape),
        "window_shape": list(new_window_vectors.shape),
        "sentiment_rows": len(merged_scores),
    }
    (utils.AUDIO_DATA_DIR / "text_artifacts_update_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    print("next: re-run evals and scripts/build_mood_vectors.py")


if __name__ == "__main__":
    main()
