"""Tests for the mood/free-text retrieval evaluation helpers."""

from __future__ import annotations

import pandas as pd

from eval.mood_retrieval_eval import (
    hit_at_k,
    load_gold_sets,
    load_weak_sets,
    map_theme,
    precision_at_k,
)


def test_map_theme_maps_emotions_and_positive_themes():
    assert map_theme("sadness") == "sadness"
    assert map_theme("joy") == "joy"
    assert map_theme("party") == "joy"
    assert map_theme("romance") == "positive"
    assert map_theme("romance-dev") == "positive"
    assert map_theme("patriotic") == "positive"
    assert map_theme("life") is None
    assert map_theme("dream") is None
    assert map_theme("unknown-theme") is None


def test_precision_at_k_counts_relevant_in_top_k():
    assert precision_at_k([1, 2, 3], {2, 3}, k=3) == 2 / 3
    assert precision_at_k([1, 2, 3], {4}, k=3) == 0.0
    assert precision_at_k([], {1}, k=10) == 0.0


def test_hit_at_k_is_binary_presence():
    assert hit_at_k([1, 2], {2}, k=2) == 1.0
    assert hit_at_k([1, 2], {3}, k=2) == 0.0
    assert hit_at_k([1, 2, 3], {3}, k=2) == 0.0


def test_load_weak_sets_uses_label_flags():
    frame = pd.DataFrame(
        {
            "song_id": [1, 2, 3],
            "joy": [1, 0, 0],
            "sadness": [0, 1, 1],
            "positive": [1, 1, 0],
        }
    )
    sets = load_weak_sets(frame)
    assert sets["joy"] == {1}
    assert sets["sadness"] == {2, 3}
    assert sets["positive"] == {1, 2}


def test_load_gold_sets_reads_human_flags():
    frame = pd.DataFrame(
        {
            "song_id": [10, 11, 12],
            "joy": [1, 0, 0],
            "sadness": [0, 1, 0],
            "anger": [0, 0, 1],
        }
    )
    sets = load_gold_sets(frame)
    assert sets["joy"] == {10}
    assert sets["sadness"] == {11}
    assert sets["anger"] == {12}
