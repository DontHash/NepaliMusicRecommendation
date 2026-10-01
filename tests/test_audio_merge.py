"""Hermetic tests for the audio -> corpus merge helpers."""

from __future__ import annotations

import pandas as pd

from scripts.audio.merge_into_corpus import prepare_new_rows, resolve_target


def _corpus():
    return pd.DataFrame([
        {"song_id": 0, "title": "Resham Firiri", "artist": "Folk", "lyrics": "one two three four five"},
        {"song_id": 1, "title": "Tal Ko Pani", "artist": "Nepathya", "lyrics": "six seven eight nine ten"},
    ])


def test_prepare_new_rows_maps_duplicates_to_survivors():
    new_rows = [
        {"audio_song_id": "A-1", "title_clean": "Resham", "artist_clean": "Folk",
         "lyrics_devanagari": "one two three four five"},                      # exact lyrics dup
        {"audio_song_id": "A-2", "title_clean": "Tal Ko Pani", "artist_clean": "Nepathya",
         "lyrics_devanagari": "unrelated new words here"},                     # same title+artist
        {"audio_song_id": "A-3", "title_clean": "Naya Geet", "artist_clean": "Singer",
         "lyrics_devanagari": "brand new lyrics line two"},                    # kept
        {"audio_song_id": "A-4", "title_clean": "Naya Geet 2", "artist_clean": "Singer",
         "lyrics_devanagari": "brand new lyrics line two"},                    # dup of kept A-3
    ]
    kept, skipped = prepare_new_rows(new_rows, _corpus())
    assert [row["audio_song_id"] for row in kept] == ["A-3"]
    reasons = {row["audio_song_id"]: (row["reason"], row["maps_to"]) for row in skipped}
    assert reasons["A-1"] == ("exact lyrics duplicate", 0)
    assert reasons["A-2"] == ("same title+artist", 1)
    assert reasons["A-4"] == ("exact lyrics duplicate", "A-3")


def test_resolve_target_follows_aliases():
    alias = {"A-2": "A-1", "A-3": "7"}
    kept_final = {"A-1": 99}
    assert resolve_target("A-1", alias, kept_final) == 99
    assert resolve_target("A-2", alias, kept_final) == 99
    assert resolve_target("A-3", alias, kept_final) == 7
    assert resolve_target("A-9", alias, kept_final) is None
    assert resolve_target("12", alias, kept_final) == 12
