"""Unit tests for the analyzer's probe math and label thresholds."""

from __future__ import annotations

import numpy as np

from MusicAnalyzer import _mood, probe_predict, sentiment_label


def test_probe_predict_matches_sigmoid_of_linear_logits():
    coef = np.array([[2.0, 0.0], [-2.0, 0.0], [0.0, 2.0]], dtype=np.float32)
    intercept = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    probs = probe_predict(np.array([1.0, 0.0], dtype=np.float32), coef, intercept)
    expected = 1.0 / (1.0 + np.exp(-np.array([2.0, -2.0, -1.0])))
    assert np.allclose(probs, expected, atol=1e-6)
    assert probs[0] > 0.88
    assert probs[1] < 0.12


def test_sentiment_label_thresholds():
    assert sentiment_label(0.05, 0.0, 0.10) == "positive"
    assert sentiment_label(-0.11, 0.0, 0.10) == "negative"
    assert sentiment_label(-0.05, 0.0, 0.10) == "neutral"
    assert sentiment_label(0.0, 0.0, 0.10) == "neutral"


def test_mood_bands():
    assert "Joyful" in _mood("positive", 0.5)
    assert "Sad" in _mood("negative", -0.5)
    assert _mood("positive", 0.1) == "Warm / Hopeful"
    assert _mood("negative", -0.1) == "Reflective / Bittersweet"
    assert _mood("neutral", 0.0) == "Neutral / Calm"
