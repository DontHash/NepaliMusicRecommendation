"""Explainable mood attribution: per-line emotions from window-level probing.

The mood probe (``music_rec_artifacts/mood_probe.npz``) was trained on
48-token chunked lyric embeddings. This module probes a song's window vectors
(cached for the corpus, freshly encoded for arbitrary text), maps every window
back to the lyric lines it covers using fast-tokenizer offsets, and aggregates
per-line joy/sadness/anger probabilities plus a normalized song composition.

Corpus mode needs ``window_vectors.npy`` / ``window_owners.npy`` (rebuild via
``scripts/kaggle_embeddings.py``); text mode needs only the local embedding
model.

Line labels are floored at ``LINE_FLOOR`` and biased by ``LINE_BIAS``, the
per-emotion calibration selected by leave-one-song-out search over
``eval/line_mood_gold.csv`` in ``scripts/check_line_attribution.py``; the
returned probabilities stay uncalibrated.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config

EMOTIONS = ("joy", "sadness", "anger")
LINE_FLOOR = 0.55
LINE_BIAS = (-0.08, -0.12, 0.12)


def line_spans(text: str) -> list[tuple[int, int]]:
    """Character spans of non-empty (stripped) lines."""
    spans: list[tuple[int, int]] = []
    offset = 0
    for raw in text.split("\n"):
        stripped = raw.strip()
        if stripped:
            lead = len(raw) - len(raw.lstrip())
            start = offset + lead
            spans.append((start, start + len(stripped)))
        offset += len(raw) + 1
    return spans


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def aggregate_lines(
    window_spans: list[tuple[int, int]],
    window_probs: np.ndarray,
    spans: list[tuple[int, int]],
) -> np.ndarray:
    """Overlap-weighted average of window probabilities per line."""
    n_lines = len(spans)
    n_emo = int(window_probs.shape[1]) if len(window_probs) else len(EMOTIONS)
    if not n_lines:
        return np.zeros((0, n_emo), dtype=np.float32)
    if not len(window_spans):
        return np.zeros((n_lines, n_emo), dtype=np.float32)

    totals = np.zeros((n_lines, n_emo), dtype=np.float64)
    weights = np.zeros(n_lines, dtype=np.float64)
    for (ws, we), probs in zip(window_spans, window_probs):
        for li, (ls, le) in enumerate(spans):
            overlap = _overlap((ws, we), (ls, le))
            if overlap > 0:
                totals[li] += overlap * probs
                weights[li] += overlap

    fallback = window_probs.mean(axis=0)
    for li in range(n_lines):
        if weights[li] <= 0:
            totals[li] = fallback
            weights[li] = 1.0
    return (totals / weights[:, None]).astype(np.float32)


def composition_from_lines(line_probs: np.ndarray) -> dict[str, float]:
    """Normalized three-emotion share (sums to 1; equal split when empty)."""
    if not len(line_probs):
        share = round(1.0 / len(EMOTIONS), 4)
        return {emotion: share for emotion in EMOTIONS}
    mass = line_probs.sum(axis=0)
    total = float(mass.sum())
    if total < 1e-6:
        share = round(1.0 / len(EMOTIONS), 4)
        return {emotion: share for emotion in EMOTIONS}
    return {emotion: round(float(m) / total, 4) for emotion, m in zip(EMOTIONS, mass)}


def dominant_label(probs: np.ndarray, floor: float = LINE_FLOOR) -> str:
    best = int(np.argmax(probs)) if len(probs) else 0
    if not len(probs) or float(probs[best]) < floor:
        return "neutral"
    return EMOTIONS[best]


def probe_predict(embedding: np.ndarray, coef: np.ndarray, intercept: np.ndarray) -> np.ndarray:
    """Sigmoid of the linear mood probe; accepts one vector or a matrix."""
    emb = np.asarray(embedding, dtype=np.float32)
    single = emb.ndim == 1
    logits = (emb if not single else emb[None, :]) @ coef.T + intercept
    probs = 1.0 / (1.0 + np.exp(-logits))
    return probs[0] if single else probs


def _prob_matrix(vectors: np.ndarray, probe: dict) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return probe_predict((vectors / norms), probe["coef"], probe["intercept"])


class MoodAttributor:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self._probe: dict | None = None
        self._tokenizer = None
        self._sent_model = None
        self._cleaned = None
        self._phrase = None
        self._gold = None
        self._scores = None
        self._window_vectors = None
        self._window_owners = None
        self._ids: list[int] = []
        self._row_of_song: dict[int, int] = {}

    def _load_probe(self) -> dict:
        if self._probe is None:
            path = self.config.mood_probe_npz
            if not path.exists():
                raise FileNotFoundError(f"mood probe not found at {path}")
            data = np.load(path, allow_pickle=False)
            self._probe = {
                "coef": data["coef"].astype(np.float32),
                "intercept": data["intercept"].astype(np.float32),
                "labels": [str(x) for x in data["labels"]],
            }
        return self._probe

    def _load_tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.embedding_model, use_fast=True
            )
        return self._tokenizer

    def _load_sentence_model(self):
        if self._sent_model is None:
            from .embeddings import _load_model

            self._sent_model = _load_model(self.config.embedding_model)
        return self._sent_model

    def _load_corpus_artifacts(self) -> None:
        if self._window_vectors is not None:
            return
        for path in (
            self.config.window_vectors_npy,
            self.config.window_owners_npy,
            self.config.embedding_ids_json,
        ):
            if not path.exists():
                raise FileNotFoundError(
                    f"{path.name} missing — rebuild corpus embeddings (scripts/kaggle_embeddings.py)"
                )
        self._window_vectors = np.load(self.config.window_vectors_npy).astype(np.float32)
        self._window_owners = np.load(self.config.window_owners_npy)
        self._ids = [int(x) for x in json.loads(self.config.embedding_ids_json.read_text(encoding="utf-8"))]
        self._row_of_song = {song_id: i for i, song_id in enumerate(self._ids)}
        self._cleaned = pd.read_csv(self.config.cleaned_lyrics_csv, encoding="utf-8").fillna("")
        self._cleaned = self._cleaned.set_index("song_id")

        phrases_csv = self.config.artifacts_dir / "mood_phrases.csv"
        if phrases_csv.exists():
            self._phrase = pd.read_csv(phrases_csv, encoding="utf-8").set_index("song_id")
        gold_csv = Path(__file__).resolve().parents[1] / "eval" / "mood_gold.csv"
        self._gold = None
        if gold_csv.exists():
            self._gold = pd.read_csv(gold_csv, encoding="utf-8").set_index("song_id")
        if self.config.sentiment_scores_csv.exists():
            self._scores = pd.read_csv(self.config.sentiment_scores_csv, encoding="utf-8").set_index("song_id")

    def _window_spans(self, text: str, tokenizer=None) -> list[tuple[int, int]]:
        tok = tokenizer or self._load_tokenizer()
        max_len = self.config.embed_window_tokens
        stride = max(1, min(self.config.embed_window_stride, max_len - 1))
        encoded = tok(
            text,
            max_length=max_len,
            stride=stride,
            truncation=True,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding=False,
        )
        spans: list[tuple[int, int]] = []
        for offsets in encoded["offset_mapping"]:
            starts = [s for s, e in offsets if e > s]
            ends = [e for s, e in offsets if e > s]
            if starts:
                spans.append((min(starts), max(ends)))
        return spans

    def _emotion_indices(self) -> list[int]:
        labels = self._load_probe()["labels"]
        return [labels.index(emotion) for emotion in EMOTIONS]

    def _polarity_from_windows(self, probs: np.ndarray) -> dict:
        labels = self._load_probe()["labels"]
        pos = float(probs[:, labels.index("positive")].mean()) if len(probs) else 0.0
        neg = float(probs[:, labels.index("negative")].mean()) if len(probs) else 0.0
        score = pos - neg
        if score > self.config.probe_positive_threshold:
            label = "positive"
        elif score < -self.config.probe_negative_threshold:
            label = "negative"
        else:
            label = "neutral"
        return {"positive": round(pos, 4), "negative": round(neg, 4), "score": round(score, 4), "label": label}

    def _build_payload(
        self,
        text: str,
        probs_all: np.ndarray,
        window_spans: list[tuple[int, int]],
        meta: dict,
        polarity: dict,
    ) -> dict:
        emo_idx = self._emotion_indices()
        emo_probs = probs_all[:, emo_idx]
        spans = line_spans(text)
        line_probs = aggregate_lines(window_spans, emo_probs, spans)
        label_probs = line_probs + np.asarray(LINE_BIAS, dtype=np.float32)
        lines = []
        for index, ((start, end), probs, calibrated) in enumerate(
            zip(spans, line_probs, label_probs)
        ):
            lines.append(
                {
                    "index": index,
                    "text": text[start:end],
                    "probs": {e: round(float(p), 4) for e, p in zip(EMOTIONS, probs)},
                    "dominant": dominant_label(calibrated),
                }
            )
        payload = {
            "composition": composition_from_lines(line_probs),
            "polarity": polarity,
            "lines": lines,
        }
        payload.update(meta)
        return payload

    def attribute_song(self, song_id: int) -> dict:
        self._load_corpus_artifacts()
        song_id = int(song_id)
        if song_id not in self._row_of_song:
            raise KeyError(f"song {song_id} is not in the embedding set")
        row = self._row_of_song[song_id]
        rows = np.where(self._window_owners == row)[0]
        probs_all = _prob_matrix(self._window_vectors[rows], self._load_probe())

        text = str(self._cleaned.loc[song_id, "lyrics"])
        spans = self._window_spans(text)
        if len(spans) != len(rows):
            spans = _uniform_spans(text, len(rows))

        meta = {
            "song_id": song_id,
            "title": str(self._cleaned.loc[song_id, "title"]),
            "artist": str(self._cleaned.loc[song_id, "artist"]),
            "source": "corpus",
        }
        polarity = self._polarity_from_windows(probs_all)
        if self._scores is not None and song_id in self._scores.index:
            stored = self._scores.loc[song_id]
            polarity = {
                "positive": round(float(stored["positive"]), 4),
                "negative": round(float(stored["negative"]), 4),
                "score": round(float(stored["sentiment_score"]), 4),
                "label": str(stored["sentiment_label"]),
            }
        meta["polarity"] = polarity
        if self._phrase is not None and song_id in self._phrase.index:
            meta["mood_phrase"] = str(self._phrase.loc[song_id, "mood_phrase"])
            meta["confidence"] = str(self._phrase.loc[song_id, "confidence"])
        elif self._gold is not None and song_id in self._gold.index:
            note = str(self._gold.loc[song_id, "notes"])
            if note and note != "nan":
                meta["mood_phrase"] = note
            meta["confidence"] = str(self._gold.loc[song_id, "confidence"])
        return self._build_payload(text, probs_all, spans, meta, polarity)

    def attribute_text(self, text: str) -> dict:
        model = self._load_sentence_model()
        from .embeddings import _encode_chunked

        max_len = min(self.config.embed_window_tokens, model.max_seq_length)
        stride = max(1, min(self.config.embed_window_stride, max_len - 1))
        _, window_vectors, _ = _encode_chunked(
            model, [text], self.config.embed_batch_size, max_len, stride, 10**9, quiet=True
        )
        probs_all = _prob_matrix(window_vectors, self._load_probe())
        spans = self._window_spans(text, tokenizer=model.tokenizer)
        if len(spans) != len(window_vectors):
            spans = _uniform_spans(text, len(window_vectors))
        polarity = self._polarity_from_windows(probs_all)
        meta = {"source": "text"}
        return self._build_payload(text, probs_all, spans, meta, polarity)


def _uniform_spans(text: str, n: int) -> list[tuple[int, int]]:
    if n <= 0 or not text:
        return []
    width = max(1, len(text) // n)
    spans = []
    for i in range(n):
        start = i * width
        end = len(text) if i == n - 1 else min(len(text), start + width)
        spans.append((start, end))
    return spans


_default: MoodAttributor | None = None


def get_attributor() -> MoodAttributor:
    global _default
    if _default is None:
        _default = MoodAttributor()
    return _default
