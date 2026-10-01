"""Encode free-text queries (optional Roman→Devanagari) into embedding vectors."""

from __future__ import annotations

import re
import threading
from collections import OrderedDict

import numpy as np

from .config import Config

_ROMAN_RE = re.compile(r"[A-Za-z]")


class QueryEncoder:
    def __init__(self, config: Config | None = None, use_transliterator: bool = True):
        self.config = config or Config()
        self._embed_model = None
        self._transliterator = None
        self._use_transliterator = use_transliterator
        self._cache_size = max(0, int(getattr(self.config, "query_cache_size", 0) or 0))
        self._vec_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._norm_cache: OrderedDict[str, str] = OrderedDict()
        self._cache_lock = threading.Lock()

    def _cache_get(self, cache: OrderedDict, key: str):
        if not self._cache_size:
            return None
        with self._cache_lock:
            value = cache.get(key)
            if value is not None:
                cache.move_to_end(key)
            return value

    def _cache_put(self, cache: OrderedDict, key: str, value) -> None:
        if not self._cache_size:
            return
        with self._cache_lock:
            cache[key] = value
            cache.move_to_end(key)
            while len(cache) > self._cache_size:
                cache.popitem(last=False)

    def _embedder(self):
        if self._embed_model is None:
            from .embeddings import get_text_encoder

            self._embed_model = get_text_encoder(self.config)
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
        cached = self._cache_get(self._norm_cache, text)
        if cached is not None:
            return cached
        translit = self._translit()
        if not translit.available:
            return text
        normalized = translit.transliterate_text(text)
        self._cache_put(self._norm_cache, text, normalized)
        return normalized

    def encode_text(self, text: str) -> np.ndarray:
        cached = self._cache_get(self._vec_cache, text)
        if cached is not None:
            return cached.copy()
        normalized = self.normalize_query(text)
        vec = self._embedder().encode([normalized], convert_to_numpy=True)[0]
        vec = vec.astype(np.float32)
        self._cache_put(self._vec_cache, text, vec.copy())
        return vec
