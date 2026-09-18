"""Unit checks for the line-attribution tuning harness."""

from __future__ import annotations

import numpy as np

from music_rec.mood_attribution import aggregate_lines
from scripts.check_line_attribution import (
    CLASSES,
    EMOTIONS,
    _bias_predict,
    _macro_f1,
    aggregate_mode,
    evaluate_config,
)

LINES = [(0, 10), (11, 21)]
WINDOWS = [(0, 10), (5, 15), (11, 21)]
PROBS = np.array(
    [
        [0.9, 0.1, 0.0],
        [0.2, 0.8, 0.0],
        [0.1, 0.1, 0.8],
    ],
    dtype=np.float32,
)


def test_mean_mode_matches_library():
    got = aggregate_mode(WINDOWS, PROBS, LINES, "mean")
    want = aggregate_lines(WINDOWS, PROBS, LINES)
    assert np.allclose(got, want)


def test_overlap2_sharpens_window_focus():
    mean = aggregate_mode(WINDOWS, PROBS, LINES, "mean")
    sharp = aggregate_mode(WINDOWS, PROBS, LINES, "overlap2")
    assert sharp[0, 0] > mean[0, 0]
    assert sharp[1, 2] > mean[1, 2]
    assert np.isclose(sharp.sum(axis=1), 1.0, atol=1e-5).all()


def test_hard_mode_is_overlap_weighted_argmax_vote():
    windows = [(0, 10), (0, 10)]
    probs = np.array([[0.6, 0.4, 0.0], [0.3, 0.7, 0.0]], dtype=np.float32)
    hard = aggregate_mode(windows, probs, [(0, 10)], "hard")
    assert np.allclose(hard, [[0.5, 0.5, 0.0]])


def test_max_mode_takes_elementwise_max():
    windows = [(0, 10), (0, 10)]
    probs = np.array([[0.6, 0.4, 0.0], [0.3, 0.7, 0.0]], dtype=np.float32)
    got = aggregate_mode(windows, probs, [(0, 10)], "max")
    assert np.allclose(got, [[0.6, 0.7, 0.0]])


def test_fallback_when_no_window_overlaps():
    windows = [(100, 110)]
    probs = np.array([[0.2, 0.3, 0.5]], dtype=np.float32)
    mean = aggregate_mode(windows, probs, [(0, 5)], "mean")
    hard = aggregate_mode(windows, probs, [(0, 5)], "hard")
    assert np.allclose(mean, probs)
    assert np.allclose(hard, [[0.0, 0.0, 1.0]])


def test_macro_f1_perfect_and_mixed():
    perfect = _macro_f1(["joy", "anger"], ["joy", "anger"], classes=("joy", "anger"))
    assert np.isclose(perfect, 1.0)
    mixed = _macro_f1(
        ["joy", "joy", "sadness", "neutral"],
        ["joy", "sadness", "sadness", "neutral"],
    )
    assert np.isclose(mixed, (2 / 3 + 2 / 3 + 0.0 + 1.0) / 4)


def test_evaluate_config_breakdowns():
    probs_by_mode = {"mean": {1: np.array([[0.9, 0.05, 0.05], [0.1, 0.1, 0.8]])}}
    records = [
        {"song_id": 1, "line_index": 0, "emotion": "joy", "cue": "lexical", "difficulty": "easy", "occurrences": 1},
        {"song_id": 1, "line_index": 1, "emotion": "anger", "cue": "metaphor", "difficulty": "hard", "occurrences": 1},
    ]
    result = evaluate_config(records, probs_by_mode, "mean", 0.5)
    assert result["accuracy"] == 1.0
    assert result["per_cue_type"]["lexical"]["n"] == 1
    assert result["per_difficulty"]["hard"]["accuracy"] == 1.0


def test_bias_predict_floor_and_bias():
    probs = np.array([[0.5, 0.3, 0.2]])
    assert _bias_predict(probs, np.zeros(len(EMOTIONS)), 0.6).tolist() == [CLASSES.index("neutral")]
    biased = _bias_predict(probs, np.array([0.2, -0.1, -0.1]), 0.6).tolist()
    assert biased == [CLASSES.index("joy")]
