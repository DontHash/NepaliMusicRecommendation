"""Tests for the curated corpus typo map (index-time canonicalization)."""

from __future__ import annotations

import pandas as pd

from music_rec.typo_map import TypoMap, load_typo_map


def _write_map(tmp_path, rows):
    path = tmp_path / "typo_map.csv"
    pd.DataFrame(rows, columns=["kind", "typo", "canonical", "note", "source", "confidence"]).to_csv(
        path, index=False, encoding="utf-8"
    )
    return path


def test_token_map_applies_to_tokens(tmp_path):
    path = _write_map(
        tmp_path,
        [{"kind": "token", "typo": "अखै", "canonical": "आँखै", "note": "", "source": "test", "confidence": "high"}],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_tokens(["अखै", "मुहार"]) == ["आँखै", "मुहार"]


def test_phrase_map_wins_over_token_map(tmp_path):
    path = _write_map(
        tmp_path,
        [
            {"kind": "token", "typo": "हात्ने", "canonical": "हट्ने", "note": "", "source": "test", "confidence": "high"},
            {"kind": "phrase", "typo": "ना हात्ने", "canonical": "न हट्ने", "note": "", "source": "test", "confidence": "high"},
        ],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_tokens(["ना", "हात्ने", "कस्तो"]) == ["न", "हट्ने", "कस्तो"]


def test_longest_phrase_wins(tmp_path):
    path = _write_map(
        tmp_path,
        [
            {"kind": "phrase", "typo": "अ ब", "canonical": "X", "note": "", "source": "test", "confidence": "high"},
            {"kind": "phrase", "typo": "अ ब स", "canonical": "Y", "note": "", "source": "test", "confidence": "high"},
        ],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_tokens(["अ", "ब", "स"]) == ["Y"]


def test_apply_text_preserves_punctuation(tmp_path):
    path = _write_map(
        tmp_path,
        [{"kind": "token", "typo": "अखै", "canonical": "आँखै", "note": "", "source": "test", "confidence": "high"}],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_text("अखै, मुहार!") == "आँखै, मुहार!"


def test_apply_text_does_not_replace_inside_longer_words(tmp_path):
    path = _write_map(
        tmp_path,
        [{"kind": "token", "typo": "अखै", "canonical": "आँखै", "note": "", "source": "test", "confidence": "high"}],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_text("अखैमा") == "अखैमा"


def test_apply_text_phrase(tmp_path):
    path = _write_map(
        tmp_path,
        [
            {
                "kind": "phrase",
                "typo": "अखै ना हात्ने कस्तो मुहार",
                "canonical": "आँखै न हट्ने तिम्रो मुहार",
                "note": "",
                "source": "test",
                "confidence": "high",
            }
        ],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_text("अखै ना हात्ने कस्तो मुहार सुन") == "आँखै न हट्ने तिम्रो मुहार सुन"


def test_missing_file_is_empty_map(tmp_path):
    typo_map = load_typo_map(tmp_path / "missing.csv")
    assert typo_map.enabled is False
    assert typo_map.apply_tokens(["अखै"]) == ["अखै"]


def test_disabled_map_is_noop(tmp_path):
    path = _write_map(
        tmp_path,
        [{"kind": "token", "typo": "अखै", "canonical": "आँखै", "note": "", "source": "test", "confidence": "high"}],
    )
    typo_map = load_typo_map(path, enabled=False)
    assert typo_map.enabled is False
    assert typo_map.apply_tokens(["अखै"]) == ["अखै"]


def test_invalid_rows_are_skipped(tmp_path):
    path = _write_map(
        tmp_path,
        [
            {"kind": "token", "typo": "अखै", "canonical": "आँखै", "note": "", "source": "test", "confidence": "high"},
            {"kind": "token", "typo": "साथी", "canonical": "साथी", "note": "identical", "source": "test", "confidence": "low"},
            {"kind": "weird", "typo": "x", "canonical": "y", "note": "", "source": "test", "confidence": "low"},
            {"kind": "token", "typo": "", "canonical": "z", "note": "", "source": "test", "confidence": "low"},
        ],
    )
    typo_map = load_typo_map(path)
    assert typo_map.apply_tokens(["अखै", "साथी"]) == ["आँखै", "साथी"]


def test_empty_map_is_disabled():
    typo_map = TypoMap(tokens={}, phrases=())
    assert typo_map.enabled is False
