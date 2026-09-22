"""Unit tests for window-to-line mood attribution helpers."""

from __future__ import annotations

import pandas as pd
import numpy as np

from music_rec.config import Config
from music_rec.mood_attribution import (
    LINE_BIAS,
    MoodAttributor,
    aggregate_lines,
    composition_from_lines,
    dominant_label,
    line_spans,
)


def test_line_spans_skip_blank_lines_and_track_offsets():
    text = "first line\n\n   indented  \nlast"
    spans = line_spans(text)
    assert spans == [(0, 10), (15, 23), (26, 30)]
    assert text[spans[0][0] : spans[0][1]] == "first line"
    assert text[spans[1][0] : spans[1][1]] == "indented"
    assert text[spans[2][0] : spans[2][1]] == "last"


def test_aggregate_lines_weights_by_overlap():
    spans = [(0, 10), (11, 20)]
    windows = [(0, 6), (5, 20)]
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    result = aggregate_lines(windows, probs, spans)
    assert result.shape == (2, 3)
    # line 0: overlap 6 chars with window 0, 5 chars with window 1
    expected_line0 = (6 * 1.0 + 5 * 0.0) / 11
    assert np.isclose(result[0, 0], expected_line0, atol=1e-6)
    assert result[1].argmax() == 1
    assert np.isclose(result[1, 1], 1.0, atol=1e-6)


def test_aggregate_lines_falls_back_to_window_mean():
    spans = [(0, 5)]
    windows = [(100, 110)]
    probs = np.array([[0.2, 0.6, 0.1]], dtype=np.float32)
    result = aggregate_lines(windows, probs, spans)
    assert np.allclose(result[0], probs[0], atol=1e-6)


def test_composition_normalizes_and_handles_empty():
    line_probs = np.array([[0.8, 0.2, 0.0], [0.4, 0.6, 0.0]], dtype=np.float32)
    comp = composition_from_lines(line_probs)
    assert abs(sum(comp.values()) - 1.0) < 1e-6
    assert comp["anger"] == 0.0
    empty = composition_from_lines(np.zeros((0, 3), dtype=np.float32))
    assert all(abs(v - 1 / 3) < 1e-3 for v in empty.values())


def test_dominant_label_respects_floor():
    assert dominant_label(np.array([0.1, 0.8, 0.1], dtype=np.float32)) == "sadness"
    assert dominant_label(np.array([0.3, 0.3, 0.2], dtype=np.float32)) == "neutral"


def test_line_bias_calibration_shifts_labels():
    bias = np.asarray(LINE_BIAS, dtype=np.float32)
    promoted = np.array([0.30, 0.30, 0.44], dtype=np.float32)
    assert dominant_label(promoted) == "neutral"
    assert dominant_label(promoted + bias) == "anger"
    demoted = np.array([0.10, 0.60, 0.05], dtype=np.float32)
    assert dominant_label(demoted) == "sadness"
    assert dominant_label(demoted + bias) == "neutral"


def test_display_text_applies_typo_map(tmp_path):
    map_path = tmp_path / "typo_map.csv"
    pd.DataFrame(
        [
            {
                "kind": "phrase",
                "typo": "अखै ना हात्ने कस्तो मुहार",
                "canonical": "आँखै न हट्ने तिम्रो मुहार",
                "note": "",
                "source": "test",
                "confidence": "high",
            }
        ]
    ).to_csv(map_path, index=False, encoding="utf-8")
    config = Config()
    config.corpus_typo_map_csv = map_path
    attributor = MoodAttributor(config)
    assert attributor.display_text("अखै ना हात्ने कस्तो मुहार सुन") == "आँखै न हट्ने तिम्रो मुहार सुन"


def test_display_text_without_map_is_passthrough(tmp_path):
    config = Config()
    config.corpus_typo_map_csv = tmp_path / "missing.csv"
    attributor = MoodAttributor(config)
    assert attributor.display_text("अखै ना हात्ने") == "अखै ना हात्ने"
