"""Hermetic tests for exact vs HNSW window retrieval parity."""

from __future__ import annotations

import numpy as np
import pytest

from music_rec.window_search import WindowIndex, ann_enabled, build_window_index

faiss = pytest.importorskip("faiss")

N_SONGS = 40
N_WINDOWS = 4000
DIM = 24


def _data(seed=3):
    rng = np.random.default_rng(seed)
    vectors = rng.normal(size=(N_WINDOWS, DIM)).astype(np.float32)
    owners = rng.integers(0, N_SONGS, N_WINDOWS).astype(np.int64)
    return vectors, owners


def _write(tmp_path, vectors, owners):
    vectors_path = tmp_path / "window_vectors.npy"
    owners_path = tmp_path / "window_owners.npy"
    np.save(vectors_path, vectors)
    np.save(owners_path, owners)
    return vectors_path, owners_path


def test_ann_modes():
    assert ann_enabled("auto", 100, 1000) is False
    assert ann_enabled("auto", 2000, 1000) is True
    assert ann_enabled("off", 10**9, 1) is False
    assert ann_enabled("on", 0, 10**9) is True


def test_window_ann_matches_exact_ranking(tmp_path):
    vectors, owners = _data()
    vectors_path, owners_path = _write(tmp_path, vectors, owners)
    index_path = tmp_path / "window_index.faiss"
    build_window_index(vectors_path, index_path, ef_search=128)

    exact = WindowIndex(vectors, owners, N_SONGS)
    approx = WindowIndex.load(
        vectors_path, owners_path, N_SONGS,
        index_path=index_path, ann_top_k=500, ann_mode="on", ann_threshold=0,
    )
    assert approx.mode == "hnsw"

    overlaps = []
    for query in vectors[::200][:20]:
        exact_ids = [song for song, _ in exact.search(query, 10)]
        ann_ids = [song for song, _ in approx.search(query, 10)]
        overlaps.append(len(set(exact_ids) & set(ann_ids)) / 10)
    assert float(np.mean(overlaps)) >= 0.9


def test_window_ann_threshold_keeps_exact(tmp_path):
    vectors, owners = _data()
    vectors_path, owners_path = _write(tmp_path, vectors, owners)
    index_path = tmp_path / "window_index.faiss"
    build_window_index(vectors_path, index_path)
    index = WindowIndex.load(
        vectors_path, owners_path, N_SONGS,
        index_path=index_path, ann_mode="auto", ann_threshold=10**9,
    )
    assert index.mode == "exact"
