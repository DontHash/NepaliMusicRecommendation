"""Hermetic tests for the persisted lexical (BM25) index cache."""

from __future__ import annotations

import numpy as np

from music_rec.lexical import LexicalIndex, corpus_digest

DOCS = [
    "तिम्रो माया मलाई छोयो",
    "माया नै माया यो जिन्दगीको कथा",
    "तिम्रो माया मेरो ज्यान",
]


def test_save_load_roundtrip_matches_scores(tmp_path):
    index = LexicalIndex(DOCS, fuzzy_enabled=True)
    path = tmp_path / "lexical_cache.pkl"
    digest = corpus_digest(DOCS)
    index.save(path, digest=digest)

    loaded = LexicalIndex.load(path, digest=digest)
    assert loaded is not None
    query = "तिम्रो माया"
    assert np.allclose(index.song_scores(query), loaded.song_scores(query))
    assert loaded.n_songs == 3


def test_stale_digest_rejected(tmp_path):
    index = LexicalIndex(DOCS, fuzzy_enabled=False)
    path = tmp_path / "cache.pkl"
    index.save(path, digest=corpus_digest(DOCS))
    assert LexicalIndex.load(path, digest=corpus_digest(DOCS + ["new song"])) is None


def test_corrupt_cache_returns_none(tmp_path):
    path = tmp_path / "cache.pkl"
    path.write_bytes(b"not a pickle")
    assert LexicalIndex.load(path, digest="irrelevant") is None


def test_missing_cache_returns_none(tmp_path):
    assert LexicalIndex.load(tmp_path / "missing.pkl", digest="x") is None


def test_cache_without_fuzzy_rebuilds_cleanly(tmp_path):
    index = LexicalIndex(DOCS, fuzzy_enabled=False)
    path = tmp_path / "cache.pkl"
    digest = corpus_digest(DOCS)
    index.save(path, digest=digest)
    loaded = LexicalIndex.load(path, digest=digest)
    assert loaded is not None
    assert loaded.fuzzy_enabled is False
    assert loaded._fuzzy_ngrams == {}
