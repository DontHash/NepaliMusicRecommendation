"""Collapse duplicate uploads of the same song in ranked results.

The corpus contains exact-duplicate lyric sets (the same text uploaded twice
under different titles or artists). Showing both wastes result slots, so
candidates are grouped by normalized lyrics at ranking time and only the
best-ranked member of each group is kept.

Near-duplicate heuristics (versions, covers, shared refrains) are deliberately
not applied: on this corpus they merged distinct songs and versions.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

from .tokenization import tokenize


def _normalized_lyrics(text: str) -> str:
    return " ".join(tokenize(text or ""))


class DuplicateCollapser:
    def __init__(self, songs: pd.DataFrame):
        song_ids = [int(sid) for sid in songs["song_id"].tolist()]
        lyrics = [_normalized_lyrics(text) for text in songs["lyrics"].fillna("").astype(str)]

        parent = list(range(len(song_ids)))

        def find(row: int) -> int:
            while parent[row] != row:
                parent[row] = parent[parent[row]]
                row = parent[row]
            return row

        by_lyrics: dict[str, int] = {}
        for row, text in enumerate(lyrics):
            if not text:
                continue
            if text in by_lyrics:
                parent[find(row)] = find(by_lyrics[text])
            else:
                by_lyrics[text] = row

        self._group_of_song = {song_id: find(row) for row, song_id in enumerate(song_ids)}

    def keep_mask(self, song_ids: Sequence[int] | np.ndarray) -> np.ndarray:
        mask = np.zeros(len(song_ids), dtype=bool)
        seen_groups: set[int] = set()
        for position, song_id in enumerate(song_ids):
            group = self._group_of_song.get(int(song_id))
            if group is None or group not in seen_groups:
                mask[position] = True
                if group is not None:
                    seen_groups.add(group)
        return mask
