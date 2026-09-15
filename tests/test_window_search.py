"""Tests for window-level similarity search over chunked embeddings."""

from __future__ import annotations

import numpy as np

from music_rec.window_search import WindowIndex


def _basis(dim: int, index: int) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float32)
    vec[index] = 1.0
    return vec


def test_song_scores_use_best_window():
    vectors = np.vstack(
        [
            _basis(4, 0),
            _basis(4, 1),
            _basis(4, 1),
            _basis(4, 2),
        ]
    )
    owners = np.array([0, 1, 1, 2], dtype=np.int32)
    index = WindowIndex(vectors, owners, n_songs=3)

    scores = index.song_scores(_basis(4, 1))
    assert scores.shape == (3,)
    assert scores[1] == np.float32(1.0)
    assert scores[0] == np.float32(0.0)
    assert scores[2] == np.float32(0.0)


def test_search_ranks_songs_by_max_window_similarity():
    vectors = np.vstack([_basis(4, 0), _basis(4, 1), _basis(4, 1), _basis(4, 3)])
    owners = np.array([0, 1, 1, 2], dtype=np.int32)
    index = WindowIndex(vectors, owners, n_songs=3)

    results = index.search(_basis(4, 1), top_k=2)
    assert [sid for sid, _ in results] == [1, 0]
    assert results[0][1] == np.float32(1.0)


def test_normalizes_window_and_query_vectors():
    vectors = np.vstack(
        [
            np.array([3.0, 0.0], dtype=np.float32),
            np.array([0.5, 0.5], dtype=np.float32),
        ]
    )
    owners = np.array([0, 1], dtype=np.int32)
    index = WindowIndex(vectors, owners, n_songs=2)

    scores = index.song_scores(np.array([10.0, 0.0], dtype=np.float32))
    assert np.isclose(scores[0], 1.0)
    assert np.isclose(scores[1], np.float32(0.5) / np.sqrt(0.5))


def test_owner_length_mismatch_raises():
    vectors = np.vstack([_basis(4, 0), _basis(4, 0)])
    owners = np.array([0], dtype=np.int32)
    try:
        WindowIndex(vectors, owners, n_songs=1)
    except ValueError:
        return
    raise AssertionError("expected ValueError for mismatched lengths")
