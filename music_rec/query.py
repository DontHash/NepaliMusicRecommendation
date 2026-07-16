"""Encode free-text queries (optional Roman→Devanagari) into embedding vectors."""

from __future__ import annotations

import re

import numpy as np

from .config import Config

_ROMAN_RE = re.compile(r"[A-Za-z]")


class QueryEncoder:
    def __init__(self, config: Config | None = None, use_transliterator: bool = True):
        self.config = config or Config()
        self._embed_model = None
        self._transliterator = None
        self._use_transliterator = use_transliterator

    def _embedder(self):
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer

            self._embed_model = SentenceTransformer(self.config.embedding_model)
        return self._embed_model

    def _translit(self):
        if self._transliterator is None:
            import sys

            root = str(self.config.project_root)
            if root not in sys.path:
                sys.path.insert(0, root)
            from lyrics_pipeline.transliterator import NepaliTransliterator

            self._transliterator = NepaliTransliterator(
                checkpoint_path=self.config.transliterator_checkpoint,
                vocab_path=self.config.transliterator_vocab,
            )
        return self._transliterator

    def normalize_query(self, text: str) -> str:
        """Transliterate Romanized Nepali to Devanagari when applicable."""
        if not self._use_transliterator or not _ROMAN_RE.search(text):
            return text
        translit = self._translit()
        if not translit.available:
            return text
        return translit.transliterate_text(text)

    def encode_text(self, text: str) -> np.ndarray:
        normalized = self.normalize_query(text)
        vec = self._embedder().encode([normalized], convert_to_numpy=True)[0]
        return vec.astype(np.float32)
