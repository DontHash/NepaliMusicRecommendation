"""Hermetic tests for the ANN-capable FAISS index layer."""

from __future__ import annotations

import numpy as np
import pytest

from music_rec.index import (
    AUTO_HNSW_THRESHOLD,
    build_index,
    index_kind,
    load_index,
    resolve_index_type,
    search,
)

faiss = pytest.importorskip("faiss")


def _random(n, dim, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(size=(n, dim)).astype(np.float32)


def test_resolve_index_type_auto_threshold():
    assert resolve_index_type("auto", 100) == "flat"
    assert resolve_index_type("auto", AUTO_HNSW_THRESHOLD + 1) == "hnsw"
    assert resolve_index_type("hnsw", 10) == "hnsw"
    assert resolve_index_type("flat", 10**7) == "flat"
    with pytest.raises(ValueError):
        resolve_index_type("ivf", 10)


def test_build_and_load_flat(tmp_path):
    vectors = _random(100, 16)
    path = tmp_path / "idx.faiss"
    index = build_index(vectors, path, index_type="flat")
    assert index_kind(index) == "flat"
    loaded = load_index(path)
    assert loaded.ntotal == 100
    scores, ids = search(loaded, vectors[3], 5)
    assert ids[0] == 3 and scores[0] > 0.999


def test_hnsw_recall_matches_flat(tmp_path):
    vectors = _random(2000, 32, seed=1)
    queries = vectors[:25]
    flat = build_index(vectors, tmp_path / "flat.faiss", index_type="flat")
    hnsw = build_index(vectors, tmp_path / "hnsw.faiss", index_type="hnsw", ef_search=128)

    overlaps = []
    for query in queries:
        _, flat_ids = search(flat, query, 10)
        _, hnsw_ids = search(hnsw, query, 10, ef_search=128)
        overlaps.append(len(set(flat_ids.tolist()) & set(hnsw_ids.tolist())) / 10)
    mean_overlap = float(np.mean(overlaps))
    assert mean_overlap >= 0.9, f"HNSW recall overlap {mean_overlap:.2f} below gate"
    assert index_kind(hnsw) == "hnsw"


def test_hnsw_persists(tmp_path):
    vectors = _random(500, 32, seed=2)
    path = tmp_path / "idx.faiss"
    build_index(vectors, path, index_type="hnsw")
    loaded = load_index(path, ef_search=64)
    assert index_kind(loaded) == "hnsw"
    _, ids = search(loaded, vectors[7], 3)
    assert ids[0] == 7
