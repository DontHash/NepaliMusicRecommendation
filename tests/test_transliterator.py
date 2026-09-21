"""Gold-set integrity and transliteration harness behavior."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest

from eval.translit_metrics import error_rows, evaluate_pairs, levenshtein

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
GOLD_WORDS = PROJECT_ROOT / "eval" / "translit_gold_words.csv"
AMBIGUOUS = PROJECT_ROOT / "eval" / "translit_ambiguous_words.csv"

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
ROMAN_RE = re.compile(r"[A-Za-z]")
REPLACEMENT_CHAR = "\ufffd"


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_levenshtein_basics() -> None:
    assert levenshtein("", "") == 0
    assert levenshtein("abc", "abc") == 0
    assert levenshtein("abc", "abd") == 1
    assert levenshtein("abc", "ab") == 1
    assert levenshtein("abc", "abcd") == 1
    assert levenshtein("kitten", "sitting") == 3


def test_evaluate_pairs_micro_average() -> None:
    report = evaluate_pairs([("ab", "ab"), ("ab", "ac")])
    assert report["n"] == 2
    assert report["distance"] == 1
    assert report["exact"] == 1
    assert report["cer"] == 0.25
    assert report["exact_match"] == 0.5
    assert evaluate_pairs([])["cer"] == 0.0


def test_error_rows_ranked_by_cer() -> None:
    rows = error_rows([("abc", "abc"), ("axc", "abc"), ("x", "abc")], limit=2)
    assert len(rows) == 2
    assert rows[0]["cer"] >= rows[1]["cer"]
    assert all(row["prediction"] != row["reference"] for row in rows)


def test_gold_lines_integrity() -> None:
    rows = read_csv(GOLD_LINES)
    assert len(rows) >= 200
    romans = [row["roman"] for row in rows]
    assert len(set(romans)) == len(romans)
    for row in rows:
        assert ROMAN_RE.search(row["roman"]), row
        assert DEVANAGARI_RE.search(row["devanagari"]), row
        assert REPLACEMENT_CHAR not in row["roman"] + row["devanagari"], row
        assert row["roman"] == row["roman"].strip()
        assert row["devanagari"] == row["devanagari"].strip()
        assert row["difficulty"] in {"short", "medium", "long"}, row
        assert row["line_id"], row


def test_gold_words_integrity() -> None:
    rows = read_csv(GOLD_WORDS)
    assert len(rows) >= 500
    romans = [row["roman"] for row in rows]
    assert len(set(romans)) == len(romans)
    for row in rows:
        assert ROMAN_RE.search(row["roman"]), row
        assert DEVANAGARI_RE.search(row["devanagari"]), row
        assert REPLACEMENT_CHAR not in row["roman"] + row["devanagari"], row


def test_ambiguous_words_are_not_scored() -> None:
    ambiguous = {row["roman"] for row in read_csv(AMBIGUOUS)}
    scored = {row["roman"] for row in read_csv(GOLD_WORDS)}
    assert ambiguous
    assert not (ambiguous & scored)


def test_denoise_drops_junk_lines_and_minority_readings(tmp_path) -> None:
    from scripts.finetune_transliterator import in_domain_pairs

    labels = tmp_path / "labels.csv"
    labels.write_text(
        "\n".join(
            [
                "line_id,roman,devanagari,confidence,source",
                # kept: clean line, repeated token with a dominant reading
                "a1,ma timilai maya garchu,म तिमीलाई माया गर्छु,high,t",
                "a2,ma timilai maya garchu,म तिमीलाई माया गर्छु,high,t",
                "a3,ma timilai maya garchu,मा तिमीलाई माया गर्छु,medium,t",
                # skipped: no Devanagari at all (English/credits)
                "b1,You know I like it,You know I like it,high,t",
                # skipped: unexpected script (Cyrillic lookalike)
                "c1,mero man ma,मेरो मन \u043c\u0430,high,t",
                # skipped: token counts do not align
                "d1,timi ra ma,तिमी र,high,t",
                # kept: single-occurrence long tail
                "e1,ghamailo,घमाइलो,high,t",
            ]
        ),
        encoding="utf-8",
    )
    pairs, stats = in_domain_pairs(labels)

    assert stats["lines_total"] == 7
    assert stats["lines_skipped_no_devanagari"] == 1
    assert stats["lines_skipped_unexpected_script"] == 1
    assert stats["lines_skipped_unaligned"] == 1
    assert pairs[("ma", "म")] == 2
    assert ("ma", "मा") not in pairs
    assert stats["occurrences_dropped_minority"] == 1
    assert pairs[("ghamailo", "घमाइलो")] == 1


def test_denoise_min_dominant_share_drops_split_tokens(tmp_path) -> None:
    from scripts.finetune_transliterator import in_domain_pairs

    labels = tmp_path / "labels.csv"
    labels.write_text(
        "\n".join(
            [
                "line_id,roman,devanagari,confidence,source",
                "a1,ko ghar,को घर,high,t",
                "a2,ko ghar,का घर,high,t",
            ]
        ),
        encoding="utf-8",
    )
    pairs, stats = in_domain_pairs(labels, min_dominant_share=0.9)
    assert ("ko", "को") not in pairs
    assert ("ko", "का") not in pairs
    assert pairs[("ghar", "घर")] == 2
    assert stats["tokens_dropped_low_share"] >= 1


@pytest.fixture(scope="module")
def transliterator():
    from lyrics_pipeline.transliterator import NepaliTransliterator

    engine = NepaliTransliterator()
    if not engine.available:
        pytest.skip("transliterator checkpoint not available")
    return engine


def test_transliterator_scores_gold_lines(transliterator) -> None:
    rows = read_csv(GOLD_LINES)[:10]
    pairs = [
        (transliterator.transliterate_text(row["roman"]), row["devanagari"]) for row in rows
    ]
    report = evaluate_pairs(pairs)
    assert report["n"] == 10
    assert 0.0 <= report["cer"] <= 2.0
    assert all(prediction.strip() for prediction, _ in pairs)
