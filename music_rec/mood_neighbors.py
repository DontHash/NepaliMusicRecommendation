"""Mood-space neighbours and per-emotion top charts.

Loads ``music_rec_artifacts/mood_vectors.csv`` (per-song joy/sadness/anger
probabilities from the mood probe) and offers nearest-neighbour songs in that
three-dimensional mood space plus ranked top lists per emotion. Neighbours are
ranked by Euclidean distance (closest profiles first, score = 1 / (1 + d)).
Titles and artists are joined from ``cleaned_lyrics.csv``; everything is pure
numpy over the ~4k-song corpus.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config
from .mood_attribution import EMOTIONS


class MoodNeighbors:
    def __init__(
        self,
        config: Config | None = None,
        vectors_path: Path | None = None,
        lyrics_path: Path | None = None,
    ):
        self.config = config or Config()
        self.vectors_path = vectors_path or self.config.artifacts_dir / "mood_vectors.csv"
        self.lyrics_path = lyrics_path or self.config.cleaned_lyrics_csv
        self._ids: list[int] = []
        self._vectors: np.ndarray | None = None
        self._meta: pd.DataFrame | None = None
        self._row_of_song: dict[int, int] = {}

    def _load(self) -> None:
        if self._vectors is not None:
            return
        if not self.vectors_path.exists():
            raise FileNotFoundError(
                f"mood vectors not found at {self.vectors_path}; run scripts/build_mood_vectors.py"
            )
        frame = pd.read_csv(self.vectors_path, encoding="utf-8")
        missing = [emotion for emotion in EMOTIONS if emotion not in frame.columns]
        if missing:
            raise ValueError(f"mood vectors missing columns: {missing}")
        lyrics = pd.read_csv(self.lyrics_path, encoding="utf-8").fillna("").set_index("song_id")

        self._ids = [int(x) for x in frame["song_id"]]
        self._row_of_song = {song_id: i for i, song_id in enumerate(self._ids)}
        self._vectors = frame[list(EMOTIONS)].to_numpy(dtype=np.float32)
        self._meta = lyrics

    def _entry(self, song_id: int, score: float) -> dict:
        row = self._row_of_song[song_id]
        vector = self._vectors[row]
        if song_id in self._meta.index:
            title = str(self._meta.loc[song_id, "title"])
            artist = str(self._meta.loc[song_id, "artist"])
        else:
            title = ""
            artist = ""
        return {
            "song_id": int(song_id),
            "title": title,
            "artist": artist,
            "score": round(float(score), 4),
            "mood": {e: round(float(v), 4) for e, v in zip(EMOTIONS, vector)},
        }

    def neighbors(self, song_id: int, k: int = 8) -> list[dict]:
        self._load()
        song_id = int(song_id)
        if song_id not in self._row_of_song:
            raise KeyError(song_id)
        row = self._row_of_song[song_id]
        distances = np.linalg.norm(self._vectors - self._vectors[row], axis=1)
        distances[row] = np.inf
        k = max(1, min(int(k), len(self._ids) - 1))
        order = np.argsort(distances)[:k]
        return [self._entry(self._ids[i], 1.0 / (1.0 + distances[i])) for i in order]

    def top(self, emotion: str, k: int = 10) -> list[dict]:
        self._load()
        if emotion not in EMOTIONS:
            raise ValueError(f"emotion must be one of {EMOTIONS}")
        column = EMOTIONS.index(emotion)
        scores = self._vectors[:, column]
        k = max(1, min(int(k), len(self._ids)))
        order = np.argsort(-scores)[:k]
        return [self._entry(self._ids[i], scores[i]) for i in order]


_default: MoodNeighbors | None = None


def get_mood_neighbors() -> MoodNeighbors:
    global _default
    if _default is None:
        _default = MoodNeighbors()
    return _default
