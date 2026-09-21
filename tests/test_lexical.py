"""Behavior tests for the BM25 lexical index."""

from __future__ import annotations

import numpy as np

from music_rec.lexical import LexicalIndex, fuse_scores

SONGS = [
    "माया गर्छु तिमीलाई माया",
    "तिमी मेरो साथ नहुँदा दुख्छ मन",
    "पार्टी गीत नाच्ने रमाइलो",
]


def test_query_matching_document_ranks_it_first():
    index = LexicalIndex(SONGS)
    scores = index.song_scores("तिमी मेरो साथ नहुँदा")
    assert scores.shape == (len(SONGS),)
    assert scores[1] > 0
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]


def test_unknown_query_scores_all_zero():
    index = LexicalIndex(SONGS)
    scores = index.song_scores("असम्बन्धित अज्ञात शब्दहरू")
    assert not scores.any()


def test_empty_query_scores_all_zero():
    index = LexicalIndex(SONGS)
    assert not index.song_scores("").any()


def test_legacy_two_part_vowel_spelling_still_matches():
    index = LexicalIndex(["हो"])
    assert index.song_scores("हाे")[0] > 0


def test_contiguous_phrase_outranks_scattered_tokens():
    index = LexicalIndex(["हो के यो माया", "के यो माया हो"])
    scores = index.song_scores("के यो माया हो")
    assert scores[1] > scores[0]


def _specificity_index() -> LexicalIndex:
    docs = ["माया लाग्छ"] * 30 + ["बतास भनी", "sad song", "तिमीलाई माया लाग्छ"]
    return LexicalIndex(docs)


def test_should_fuse_gates_common_two_token_keywords():
    index = _specificity_index()
    assert index.should_fuse("माया लाग्छ") is False
    assert index.should_fuse("माया") is False


def test_should_fuse_allows_rare_devanagari_pairs():
    index = _specificity_index()
    assert index.should_fuse("बतास भनी") is True


def test_should_fuse_rejects_short_english_keywords():
    index = _specificity_index()
    assert index.should_fuse("sad song") is False


def test_should_fuse_allows_three_token_queries():
    index = _specificity_index()
    assert index.should_fuse("तिमीलाई माया लाग्छ") is True


def test_fusion_prefers_lexical_winner_when_weight_is_high():
    dense = np.array([1.0, 0.0, 0.0])
    lexical = np.array([0.0, 2.0, 0.0])
    fused = fuse_scores(dense, lexical, lexical_weight=0.8)
    assert fused[1] > fused[0]


def test_fusion_preserves_dense_order_when_lexical_is_silent():
    dense = np.array([0.3, 0.9, 0.1])
    lexical = np.zeros(3)
    fused = fuse_scores(dense, lexical, lexical_weight=0.65)
    assert list(np.argsort(-fused)) == [1, 0, 2]


def test_fusion_rejects_invalid_weight():
    with np.testing.assert_raises(ValueError):
        fuse_scores(np.zeros(2), np.zeros(2), lexical_weight=1.5)
