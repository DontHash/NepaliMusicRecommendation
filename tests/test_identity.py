"""Hermetic tests for MinHash/LSH duplicate review."""

from __future__ import annotations

import csv
from pathlib import Path

from data_collection.identity import (
    SongRecord,
    load_corpus_records,
    near_duplicate_pairs,
    review_file,
    review_songs,
    suggest_action,
)

RECORDS = [
    SongRecord(key="a", artist="Kali Prasad Baskota", title="Khusi",
               source="deezer", script="devanagari", isrc="NPX1"),
    SongRecord(key="b", artist="kali prasad baskota", title="Khusi (Official Video)",
               source="site_paankopat.com", script="devanagari"),
    SongRecord(key="c", artist="Nepathya", title="Bhedako Oon Jasto",
               source="deezer", script="devanagari"),
]


def test_variant_pairs_found_and_unrelated_not():
    pairs = near_duplicate_pairs(RECORDS)
    indices = [(left, right) for left, right, _ in pairs]
    assert (0, 1) in indices
    assert (0, 2) not in indices and (1, 2) not in indices
    assert near_duplicate_pairs(RECORDS) == pairs  # deterministic


def test_review_rows_carry_suggestions_and_pending_decisions():
    rows = review_songs(RECORDS)
    assert rows
    row = next(row for row in rows if {row["left_key"], row["right_key"]} == {"a", "b"})
    assert 0.6 <= row["similarity"] <= 1.0
    assert row["decision"] == "pending"
    assert row["suggested_action"] in {"merge_candidate", "review_title_variant", "review"}
    assert row["suggested_keep"] in {"left", "right"}


def test_merge_candidate_and_keep_side_by_source_priority():
    left = SongRecord(key="x", artist="A", title="T", source="itunes")      # priority 6
    right = SongRecord(key="y", artist="A", title="T", source="deezer")     # priority 5
    action, keep_side = suggest_action(left, right)
    assert action == "merge_candidate"
    assert keep_side == "right"  # deezer is the better source

    variant_action, _ = suggest_action(
        SongRecord(key="x", artist="A", title="T"),
        SongRecord(key="y", artist="A", title="T (Live)"),
    )
    assert variant_action == "review_title_variant"

    unrelated_action, _ = suggest_action(
        SongRecord(key="x", artist="A", title="T"),
        SongRecord(key="y", artist="B", title="T"),
    )
    assert unrelated_action == "review"


FIELDS = ["Category", "Title", "Artist", "Lyrics", "source", "source_url", "stage",
          "script", "sha256", "duration_s", "album", "preview_url", "isrc", "fetched_at"]

ROWS = [
    ["nepali", "Khusi", "Kali Prasad Baskota", "माया लाग्छ तिम्रो मन", "deezer",
     "", "", "devanagari", "aa11", "", "", "", "NPX1", ""],
    ["nepali", "Khusi (Official Video)", "kali prasad baskota", "माया लाग्छ तिम्रो मन फेरि",
     "site_paankopat.com", "", "", "devanagari", "bb22", "", "", "", "", ""],
    ["nepali", "Bhedako Oon Jasto", "Nepathya", "अर्कै गीत", "deezer",
     "", "", "devanagari", "cc33", "", "", "", "", ""],
]


def _write_corpus(path: Path) -> None:
    import csv as _csv

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = _csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(ROWS)


def test_review_file_writes_csv_and_report(tmp_path: Path):
    inp = tmp_path / "corpus_raw.csv"
    out = tmp_path / "duplicate_review.csv"
    _write_corpus(inp)

    from data_collection.identity import write_report

    report = review_file(inp, out)
    assert report["records"] == 3
    assert report["pairs"] >= 1
    assert report["pending_decisions"] == report["pairs"]
    assert report["input_sha256"]

    lines = out.read_text(encoding="utf-8").splitlines()
    assert "decision" in lines[0] and "suggested_action" in lines[0]
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert any(row["decision"] == "pending" for row in rows)

    report_path = tmp_path / "report.json"
    write_report(report, report_path)
    assert "input_sha256" in report_path.read_text(encoding="utf-8")


def test_load_corpus_records_reads_compact_columns(tmp_path: Path):
    inp = tmp_path / "corpus_raw.csv"
    _write_corpus(inp)
    records = load_corpus_records(inp)
    assert [record.key for record in records] == ["aa11", "bb22", "cc33"]
    assert records[0].isrc == "NPX1"
    assert records[1].source == "site_paankopat.com"
