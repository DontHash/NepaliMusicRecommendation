"""ANN parity + latency gate vs exact search (songs and windows).

Builds flat and HNSW indexes in memory, compares rankings and latency, and
exits nonzero when recall drops below the gates. Run after any index change:

  python scripts/check_ann_parity.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from music_rec.config import Config  # noqa: E402

SONG_RECALL_GATE = 0.98
WINDOW_OVERLAP_GATE = 0.90


def _recall(exact_ids, approx_ids) -> float:
    return len(set(exact_ids) & set(approx_ids)) / max(len(exact_ids), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--song-queries", type=int, default=200)
    parser.add_argument("--window-queries", type=int, default=20)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()

    import numpy as np

    from music_rec.index import build_index, search
    from music_rec.window_search import WindowIndex, build_window_index

    config = Config()
    report: dict = {}
    failed = False

    # --- song index -----------------------------------------------------------
    vectors_path = config.feature_matrix_npy if config.feature_matrix_npy.exists() else config.embeddings_npy
    vectors = np.load(vectors_path).astype(np.float32)
    rng = np.random.default_rng(0)
    query_rows = rng.choice(len(vectors), size=min(args.song_queries, len(vectors)), replace=False)
    queries = vectors[query_rows]

    flat = build_index(vectors, config.artifacts_dir / "_parity_flat.faiss", index_type="flat")
    hnsw = build_index(
        vectors, config.artifacts_dir / "_parity_hnsw.faiss", index_type="hnsw",
        hnsw_m=config.index_hnsw_m, ef_construction=config.index_ef_construction,
        ef_search=config.index_ef_search,
    )
    exact_ids = flat.search(np.ascontiguousarray(queries), args.top_k)[1]
    start = time.perf_counter()
    approx_ids = hnsw.search(np.ascontiguousarray(queries), args.top_k)[1]
    hnsw_batch_ms = (time.perf_counter() - start) * 1000
    recalls = [_recall(exact, approx) for exact, approx in zip(exact_ids, approx_ids)]
    song_recall = float(np.mean(recalls))

    start = time.perf_counter()
    for query in queries[:50]:
        search(hnsw, query, args.top_k, ef_search=config.index_ef_search)
    hnsw_single_ms = (time.perf_counter() - start) * 1000 / min(50, len(queries))
    start = time.perf_counter()
    for query in queries[:50]:
        search(flat, query, args.top_k)
    flat_single_ms = (time.perf_counter() - start) * 1000 / min(50, len(queries))

    report["songs"] = {
        "vectors": int(vectors.shape[0]),
        "dim": int(vectors.shape[1]),
        f"recall@{args.top_k}": round(song_recall, 4),
        "flat_ms_per_query": round(flat_single_ms, 3),
        "hnsw_ms_per_query": round(hnsw_single_ms, 3),
        "hnsw_batch_ms": round(hnsw_batch_ms, 3),
        "gate": SONG_RECALL_GATE,
    }
    failed |= song_recall < SONG_RECALL_GATE

    # --- window index ---------------------------------------------------------
    if config.window_vectors_npy.exists() and config.window_owners_npy.exists():
        window_vectors = np.load(config.window_vectors_npy).astype(np.float32)
        owners = np.load(config.window_owners_npy)
        index_path = config.artifacts_dir / "_parity_window.faiss"
        build_window_index(
            config.window_vectors_npy, index_path,
            hnsw_m=config.index_hnsw_m, ef_construction=config.index_ef_construction,
            ef_search=config.index_ef_search,
        )
        exact = WindowIndex(window_vectors, owners, int(owners.max()) + 1)
        approx = WindowIndex.load(
            config.window_vectors_npy, config.window_owners_npy, int(owners.max()) + 1,
            index_path=index_path, ann_top_k=config.window_ann_top_k,
            ann_mode="on", ann_threshold=0,
        )
        rows = rng.choice(len(window_vectors), size=min(args.window_queries, len(window_vectors)), replace=False)
        overlaps = []
        timings_exact, timings_ann = [], []
        for row in rows:
            query = window_vectors[row]
            start = time.perf_counter()
            exact_ids = [song for song, _ in exact.search(query, args.top_k)]
            timings_exact.append((time.perf_counter() - start) * 1000)
            start = time.perf_counter()
            ann_ids = [song for song, _ in approx.search(query, args.top_k)]
            timings_ann.append((time.perf_counter() - start) * 1000)
            overlaps.append(_recall(exact_ids, ann_ids))
        window_overlap = float(np.mean(overlaps))
        report["windows"] = {
            "windows": int(window_vectors.shape[0]),
            f"top{args.top_k}_song_overlap": round(window_overlap, 4),
            "exact_ms_per_query": round(float(np.mean(timings_exact)), 3),
            "ann_ms_per_query": round(float(np.mean(timings_ann)), 3),
            "gate": WINDOW_OVERLAP_GATE,
        }
        failed |= window_overlap < WINDOW_OVERLAP_GATE
        for path in (index_path,):
            path.unlink(missing_ok=True)
    for path in (config.artifacts_dir / "_parity_flat.faiss", config.artifacts_dir / "_parity_hnsw.faiss"):
        path.unlink(missing_ok=True)

    report["passed"] = not failed
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
