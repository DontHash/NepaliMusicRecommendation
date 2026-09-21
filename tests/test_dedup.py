"""Behavior tests for duplicate-upload collapsing in ranked results."""

from __future__ import annotations

import pandas as pd

from music_rec.dedup import DuplicateCollapser


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _lyrics(seed: str, n: int = 40) -> str:
    return " ".join(f"{seed}{i}" for i in range(n))


def test_exact_duplicate_lyrics_are_collapsed():
    songs = _frame(
        [
            {"song_id": 0, "title": "A", "artist": "X", "lyrics": "माया गर्छु तिमीलाई माया"},
            {"song_id": 1, "title": "B", "artist": "Y", "lyrics": "माया गर्छु तिमीलाई माया"},
            {"song_id": 2, "title": "C", "artist": "Z", "lyrics": "पार्टी गीत नाच्ने रमाइलो"},
        ]
    )
    collapser = DuplicateCollapser(songs)
    assert collapser.keep_mask([0, 1, 2]).tolist() == [True, False, True]


def test_near_duplicate_versions_are_kept():
    body = _lyrics("शब्द")
    songs = _frame(
        [
            {"song_id": 0, "title": "Ek Sarvanaam", "artist": "Sajjan Raj Vaidya", "lyrics": body},
            {
                "song_id": 1,
                "title": "Sajjan Raj Vaidya - Ek Sarvanaam",
                "artist": "Genius Romanizations",
                "lyrics": body + " एक थप शब्द",
            },
        ]
    )
    collapser = DuplicateCollapser(songs)
    assert collapser.keep_mask([0, 1]).tolist() == [True, True]


def test_same_title_with_different_lyrics_is_kept():
    songs = _frame(
        [
            {"song_id": 0, "title": "Samaya", "artist": "A", "lyrics": _lyrics("क")},
            {"song_id": 1, "title": "samaya", "artist": "B", "lyrics": _lyrics("ख")},
        ]
    )
    collapser = DuplicateCollapser(songs)
    assert collapser.keep_mask([0, 1]).tolist() == [True, True]


def test_collapse_keeps_first_ranked_representative():
    songs = _frame(
        [
            {"song_id": 0, "title": "A", "artist": "X", "lyrics": "माया गर्छु तिमीलाई माया"},
            {"song_id": 1, "title": "B", "artist": "Y", "lyrics": "माया गर्छु तिमीलाई माया"},
        ]
    )
    collapser = DuplicateCollapser(songs)
    assert collapser.keep_mask([1, 0]).tolist() == [True, False]
