"""Integrity checks for the line-level mood gold set."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from music_rec.config import Config
from music_rec.mood_attribution import line_spans

GOLD = Path(__file__).resolve().parents[1] / "eval" / "line_mood_gold.csv"

EMOTIONS = {"joy", "sadness", "anger", "neutral"}
POLARITIES = {"positive", "negative", "mixed", "neutral"}
CUES = {
    "lexical",
    "metaphor",
    "negation",
    "address",
    "context_only",
    "repetition",
    "code_switch",
    "artifact",
    "filler",
    "none",
}
DIFFICULTIES = {"easy", "medium", "hard"}


@pytest.fixture(scope="module")
def gold() -> pd.DataFrame:
    return pd.read_csv(GOLD, encoding="utf-8")


@pytest.fixture(scope="module")
def corpus() -> pd.DataFrame:
    frame = pd.read_csv(Config().cleaned_lyrics_csv, encoding="utf-8").fillna("")
    return frame.set_index("song_id")


def test_columns_and_vocabulary(gold: pd.DataFrame):
    required = {
        "song_id",
        "title",
        "artist",
        "line_index",
        "text",
        "occurrences",
        "primary_emotion",
        "polarity",
        "cue_type",
        "difficulty",
        "notes",
        "source",
    }
    assert required <= set(gold.columns)
    assert set(gold["primary_emotion"]) <= EMOTIONS
    assert set(gold["polarity"]) <= POLARITIES
    assert set(gold["cue_type"]) <= CUES
    assert set(gold["difficulty"]) <= DIFFICULTIES
    assert set(gold["source"]) == {"agent_v1"}


def test_rows_unique_per_song_line(gold: pd.DataFrame):
    dupes = gold.duplicated(subset=["song_id", "line_index"]).sum()
    assert dupes == 0


def test_text_matches_corpus_and_occurrences(gold: pd.DataFrame, corpus: pd.DataFrame):
    for row in gold.itertuples():
        lyrics = str(corpus.loc[row.song_id, "lyrics"])
        spans = line_spans(lyrics)
        assert row.line_index < len(spans), f"{row.song_id}:{row.line_index} out of range"
        start, end = spans[row.line_index]
        assert lyrics[start:end] == row.text, f"{row.song_id}:{row.line_index} text drift"
        assert row.occurrences >= 1
        assert list(gold[gold["song_id"] == row.song_id]["text"]).count(row.text) == 1


def test_occurrence_counts(gold: pd.DataFrame, corpus: pd.DataFrame):
    for song_id, group in gold.groupby("song_id"):
        lyrics = str(corpus.loc[song_id, "lyrics"])
        spans = line_spans(lyrics)
        lines = [lyrics[s:e] for s, e in spans]
        for row in group.itertuples():
            assert sum(1 for line in lines if line == row.text) == row.occurrences


def test_song_coverage(gold: pd.DataFrame):
    assert gold["song_id"].nunique() == 18
    counts = gold.groupby("song_id").size()
    assert (counts >= 6).all()
    assert len(gold) >= 250
