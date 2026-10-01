"""Audio (CLAP) similarity index over the local audio collection.

Built by ``scripts/audio/embed_audio.py`` and ``build_dataset_lines.py``:

  R_data/audio/audio_embeddings.npy      (N x 512, L2-normalised)
  R_data/audio/audio_embedding_keys.csv  (row order == embedding rows)
  R_data/audio/audio_track_matches.csv   (track_key -> existing song_id or A-id)

``AudioIndex.load(config)`` returns ``None`` when the artifacts are absent, so
the recommender degrades to text-only behaviour on a machine that has never run
the audio pipeline.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .config import Config


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-8, None)


class AudioIndex:
    def __init__(self, vectors, track_keys, song_of_track):
        self.vectors = normalize_rows(np.asarray(vectors, dtype=np.float32))
        self.track_keys = [str(key) for key in track_keys]
        self.song_of_track = list(song_of_track)
        self._track_row = {key: row for row, key in enumerate(self.track_keys)}

        sums: dict[int, np.ndarray] = {}
        counts: dict[int, int] = {}
        for row, song_id in enumerate(self.song_of_track):
            if song_id is None:
                continue
            sums.setdefault(song_id, np.zeros(self.vectors.shape[1], dtype=np.float32))
            sums[song_id] += self.vectors[row]
            counts[song_id] = counts.get(song_id, 0) + 1
        self.song_ids = sorted(sums)
        if self.song_ids:
            self.song_matrix = normalize_rows(np.stack([sums[sid] / counts[sid] for sid in self.song_ids]))
        else:
            self.song_matrix = np.zeros((0, self.vectors.shape[1]), dtype=np.float32)
        self._song_row = {song_id: row for row, song_id in enumerate(self.song_ids)}

    # --- construction ---------------------------------------------------------

    @classmethod
    def from_files(cls, embeddings_path, keys_path, matches_path) -> "AudioIndex | None":
        paths = [Path(embeddings_path), Path(keys_path), Path(matches_path)]
        if not all(path.exists() for path in paths):
            return None
        vectors = np.load(paths[0])
        with open(paths[1], encoding="utf-8") as handle:
            keys = [row["track_key"] for row in csv.DictReader(handle)]
        with open(paths[2], encoding="utf-8") as handle:
            matches = {row["track_key"]: row for row in csv.DictReader(handle)}
        if not keys or vectors.shape[0] != len(keys):
            return None
        song_of_track: list[int | None] = []
        for key in keys:
            raw = (matches.get(key, {}).get("match_song_id") or "").strip()
            song_of_track.append(int(raw) if raw else None)
        return cls(vectors, keys, song_of_track)

    @classmethod
    def load(cls, config: Config | None = None) -> "AudioIndex | None":
        config = config or Config()
        return cls.from_files(
            config.audio_embeddings_npy,
            config.audio_embedding_keys_csv,
            config.audio_track_matches_csv,
        )

    # --- queries --------------------------------------------------------------

    def has_audio(self, song_id: int) -> bool:
        return int(song_id) in self._song_row

    def song_vector(self, song_id: int) -> np.ndarray | None:
        row = self._song_row.get(int(song_id))
        return None if row is None else self.song_matrix[row]

    def song_for_track(self, track_key: str) -> int | None:
        row = self._track_row.get(track_key)
        return None if row is None else self.song_of_track[row]

    def scores_for_vector(self, vector) -> tuple[list[int], np.ndarray]:
        if not self.song_ids:
            return [], np.zeros(0, dtype=np.float32)
        vector = np.asarray(vector, dtype=np.float32)
        vector = vector / max(float(np.linalg.norm(vector)), 1e-8)
        return self.song_ids, (self.song_matrix @ vector).astype(np.float32)

    def scores_for_song(self, song_id: int) -> tuple[list[int], np.ndarray]:
        vector = self.song_vector(song_id)
        if vector is None:
            return [], np.zeros(0, dtype=np.float32)
        return self.scores_for_vector(vector)

    def scores_for_track(self, track_key: str) -> tuple[list[int], np.ndarray]:
        row = self._track_row.get(track_key)
        if row is None:
            return [], np.zeros(0, dtype=np.float32)
        return self.scores_for_vector(self.vectors[row])

    @staticmethod
    def blend_rows(
        text_scores: np.ndarray,
        row_song_ids,
        audio_scores_by_song: dict[int, float],
        weight: float,
    ) -> np.ndarray:
        """Blend audio similarity into a corpus-row score array.

        Rows whose song has no audio keep their text score unchanged, so the
        fusion never penalises songs outside the audio collection.
        """
        blended = np.asarray(text_scores, dtype=np.float32).copy()
        if weight <= 0.0 or not audio_scores_by_song:
            return blended
        for row, song_id in enumerate(row_song_ids):
            audio_score = audio_scores_by_song.get(int(song_id))
            if audio_score is not None:
                blended[row] = (1.0 - weight) * blended[row] + weight * float(audio_score)
        return blended
