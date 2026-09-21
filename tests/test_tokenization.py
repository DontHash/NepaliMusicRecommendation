"""Regression tests for Devanagari tokenization."""

from __future__ import annotations

from music_rec.tokenization import normalize_nfc, tokenize


def test_tokenize_strips_whitespace_and_drops_empties():
    tokens = tokenize("तुक तुक\n४ चिरबिर")
    assert "४" in tokens
    assert all(tok == tok.strip() and tok for tok in tokens)


def test_tokenize_removes_newline_glued_to_line_final_token():
    tokens = tokenize("पहिलो लाइन\nदोस्रो लाइन")
    assert "लाइन" in tokens
    assert not any("\n" in tok for tok in tokens)


def test_tokenize_empty_text_returns_no_tokens():
    assert tokenize("") == []
    assert tokenize("   \n  ") == []


def test_normalize_composes_legacy_two_part_vowels():
    assert normalize_nfc("हाे") == "हो"
    assert normalize_nfc("काै") == "कौ"


def test_tokenize_matches_legacy_and_atomic_vowel_spellings():
    assert tokenize("हाे") == tokenize("हो") == ["हो"]
