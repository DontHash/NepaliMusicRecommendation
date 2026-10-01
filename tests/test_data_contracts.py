"""Hermetic tests for dataset contracts and the validator."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data_engineering.schemas import SCHEMAS, Column, Schema, get_schema
from data_engineering.validate import validate_file, validate_frame


def _valid_cleaned() -> pd.DataFrame:
    return pd.DataFrame({
        "song_id": [0, 1, 2],
        "title": ["A", "", "C"],
        "artist": ["X", "Y", ""],
        "category": ["nepali", "nepali", "romanized"],
        "lyrics": ["तिम्रो माया", "माया नै माया", "दुःखको कथा"],
        "token_count": [4, 5, 3],
    })


def test_valid_frame_passes():
    report = validate_frame(_valid_cleaned(), get_schema("cleaned_lyrics"))
    assert report["passed"], report["errors"]


def test_missing_column_fails():
    frame = _valid_cleaned().drop(columns=["lyrics"])
    report = validate_frame(frame, get_schema("cleaned_lyrics"))
    assert not report["passed"]
    assert any(error["check"] == "missing_columns" for error in report["errors"])


def test_null_in_required_column_fails():
    frame = _valid_cleaned()
    frame.loc[1, "lyrics"] = None
    report = validate_frame(frame, get_schema("cleaned_lyrics"))
    assert any(error["check"] == "not_null" and error["column"] == "lyrics" for error in report["errors"])


def test_whitespace_only_counts_as_null_when_strip():
    frame = _valid_cleaned()
    frame.loc[1, "lyrics"] = "   "
    report = validate_frame(frame, get_schema("cleaned_lyrics"))
    assert any(error["check"] == "not_null" and error["column"] == "lyrics" for error in report["errors"])


def test_range_and_allowed_fail():
    frame = pd.DataFrame({"song_id": [0], "joy": [1.2], "negative": [0], "positive": [0],
                          "sadness": [0], "anger": [0], "fear": [0], "depression": [0],
                          "sentiment_score": [2.0], "sentiment_label": ["happy"]})
    report = validate_frame(frame, get_schema("sentiment_scores"))
    checks = {error["check"] for error in report["errors"]}
    assert "max<=1.0" in checks
    assert "allowed" in checks


def test_primary_key_uniqueness():
    frame = _valid_cleaned()
    frame.loc[2, "song_id"] = 0
    report = validate_frame(frame, get_schema("cleaned_lyrics"))
    assert any(error["check"] == "pk_unique" for error in report["errors"])


def test_pattern_on_audio_song_id():
    frame = pd.DataFrame({
        "audio_song_id": ["A-0123456789", "A-zzz"],
        "track_key": ["a|b", "c|d"],
        "audio_artist": ["", ""], "audio_title": ["t", "t"], "duration_s": [10.0, 10.0],
        "n_files": [1, 1], "lyrics_source": ["lrclib_get", ""], "source_url": ["", ""],
        "category": ["nepali", "nepali"], "title_clean": ["t", "t"], "artist_clean": ["", ""],
        "lyrics_devanagari": ["क", "ख"], "line_count": [3, 3], "char_count": [10, 10],
        "script_style_original": ["devanagari", "devanagari"],
        "script_style_cleaned": ["devanagari", "devanagari"],
        "transliterated": [0, 1], "token_count": [10, 12],
    })
    report = validate_frame(frame, get_schema("audio_new_songs"))
    assert any(error["check"].startswith("pattern:") for error in report["errors"])


def test_extra_columns_warn_not_fail():
    frame = _valid_cleaned()
    frame["extra"] = "x"
    report = validate_frame(frame, get_schema("cleaned_lyrics"))
    assert report["passed"]
    assert any(warning["check"] == "extra_columns" for warning in report["warnings"])


def test_validate_file_roundtrip(tmp_path: Path):
    path = tmp_path / "cleaned.csv"
    _valid_cleaned().to_csv(path, index=False, encoding="utf-8")
    report = validate_file(path, get_schema("cleaned_lyrics"))
    assert report["passed"]
    assert report["rows"] == 3


def test_file_validation_keeps_string_columns_literal(tmp_path: Path):
    """A numeric-looking id column must stay '1746', not become '1746.0'."""
    frame = pd.DataFrame({
        "track_key": ["a|b", "c|d"],
        "artist": ["A", "B"],
        "title": ["T1", "T2"],
        "duration_s": [10.0, 20.0],
        "n_files": [1, 1],
        "files": ["a.mp3", "c.m4a"],
        "source_query": ["", ""],
        "cand_song_id": ["1746", ""],
        "cand_title": ["T", ""],
        "cand_artist": ["A", ""],
        "title_score": [99.0, 0.0],
        "artist_score": [99.0, 0.0],
        "metadata_match": ["strong", "none"],
    })
    path = tmp_path / "audio_tracks.csv"
    frame.to_csv(path, index=False, encoding="utf-8")
    report = validate_file(path, get_schema("audio_tracks"))
    assert report["passed"], report["errors"]


def test_missing_file_fails(tmp_path: Path):
    report = validate_file(tmp_path / "nope.csv", get_schema("cleaned_lyrics"))
    assert not report["passed"]
    assert report["errors"][0]["check"] == "file_missing"


def test_unknown_schema_raises():
    with pytest.raises(KeyError):
        get_schema("does_not_exist")


def test_all_schemas_are_well_formed():
    for name, schema in SCHEMAS.items():
        assert schema.name == name
        assert schema.version >= 1
        assert schema.columns, f"{name} has no columns"
        if schema.primary_key:
            assert schema.primary_key in schema.columns


@pytest.mark.parametrize("dataset", ["cleaned_lyrics", "corpus_rows", "sentiment_scores",
                                     "audio_tracks", "audio_manifest", "audio_track_matches",
                                     "audio_file_map", "audio_new_songs"])
def test_production_datasets_validate_when_present(dataset: str):
    """The CI gate: every committed production dataset must satisfy its contract."""
    from scripts.validate_datasets import production_datasets

    path = production_datasets().get(dataset)
    if path is None or not path.exists():
        pytest.skip(f"{dataset} not present in this checkout")
    report = validate_file(path, get_schema(dataset))
    assert report["passed"], report["errors"]
