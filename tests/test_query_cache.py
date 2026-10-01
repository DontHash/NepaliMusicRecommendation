"""Hermetic tests for the bounded query-embedding cache."""

from __future__ import annotations

import numpy as np

from music_rec.config import Config
from music_rec.query import QueryEncoder


class _CountingEmbedder:
    def __init__(self):
        self.calls = 0

    def encode(self, texts, **kwargs):
        self.calls += 1
        return np.tile(np.array([[1.0, 0.0, 0.0]], dtype=np.float32), (len(texts), 1))


def _encoder(size: int = 2) -> tuple[QueryEncoder, _CountingEmbedder]:
    config = Config()
    config.query_cache_size = size
    encoder = QueryEncoder(config, use_transliterator=False)
    embedder = _CountingEmbedder()
    encoder._embed_model = embedder
    return encoder, embedder


def test_repeat_query_uses_cache():
    encoder, embedder = _encoder()
    first = encoder.encode_text("maya")
    second = encoder.encode_text("maya")
    assert embedder.calls == 1
    assert np.allclose(first, second)
    first[0] = 99.0  # callers must not be able to mutate the cached vector
    assert encoder.encode_text("maya")[0] == 1.0


def test_cache_is_bounded():
    encoder, embedder = _encoder(size=2)
    for text in ("maya", "timi", "mann"):
        encoder.encode_text(text)
    assert embedder.calls == 3
    encoder.encode_text("mann")  # still cached
    assert embedder.calls == 3
    encoder.encode_text("maya")  # evicted by "mann"
    assert embedder.calls == 4


def test_caching_disabled():
    encoder, embedder = _encoder(size=0)
    encoder.encode_text("maya")
    encoder.encode_text("maya")
    assert embedder.calls == 2
