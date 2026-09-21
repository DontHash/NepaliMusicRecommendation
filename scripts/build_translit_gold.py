"""Build the transliteration eval gold sets from the legacy human-authored pairs.

The legacy GRU pipeline shipped hand-authored Roman -> Devanagari pairs that the
current Aksharantar-trained checkpoint has never seen, which makes them the only
in-domain gold available before the teacher pass (track A1):

- ``R_data/datasets/TransliterateLL.txt`` — line-level song lines
- ``R_data/datasets/Data1.csv`` .. ``Data4.csv`` — word-level pairs

Rows whose two sides do not correspond are dropped by the curated exclusion
lists below (gold-standard review, 2026-09). Word pairs whose gold is English
passthrough, a numeral, or a single character are out of scope. When one roman
key has several distinct golds the pair is context-dependent and is exported to
``eval/translit_ambiguous_words.csv`` for the context-rescoring work instead of
being scored context-free.

Outputs (committed):
- ``eval/translit_gold_lines.csv``
- ``eval/translit_gold_words.csv``
- ``eval/translit_ambiguous_words.csv``

Usage:
    python scripts/build_translit_gold.py
"""

from __future__ import annotations

import csv
import io
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LINE_SOURCE = PROJECT_ROOT / "R_data" / "datasets" / "TransliterateLL.txt"
WORD_SOURCES = [
    PROJECT_ROOT / "R_data" / "datasets" / "Data1.csv",
    PROJECT_ROOT / "R_data" / "datasets" / "Data2.csv",
    PROJECT_ROOT / "R_data" / "datasets" / "Data3.csv",
    PROJECT_ROOT / "R_data" / "datasets" / "Data4.csv",
]
OUT_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
OUT_WORDS = PROJECT_ROOT / "eval" / "translit_gold_words.csv"
OUT_AMBIGUOUS = PROJECT_ROOT / "eval" / "translit_ambiguous_words.csv"

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
ROMAN_RE = re.compile(r"[A-Za-z]")

HEADER_PAIRS = {
    ("roman", "devanagari"),
    ("romanized", "devanagari"),
    ("transliteration", "devanagari"),
}

LINE_EXCLUSIONS = {
    "Ti Sabale Chinchha": "misaligned: gold text is a different line",
    "Basilathe Bahnchan Malai": "misaligned: roman and gold do not correspond",
}

WORD_EXCLUSIONS = {
    ("duniya", "यो"): "misaligned",
    ("dharma", "यो"): "misaligned",
    ("odau", "न"): "misaligned",
    ("kati", "लाग्यो"): "misaligned",
    ("chaudha", "१४"): "numeral conversion, not transliteration",
    ("ramro", "राम्राे"): "gold typo (decomposed vowel sequence)",
    ("kasto", "कस्ता"): "grammatical variant, not a 1:1 transliteration",
    ("manko", "मन्को"): "gold typo (extra halanta)",
}

# Review corrections (eval/translit_policy.md): roman key -> corrected reference.
# Filled from the review kit; keeps the CSV a build artifact.
LINE_CORRECTIONS: dict[str, str] = {}
WORD_CORRECTIONS: dict[str, str] = {}

# Reviewed in-domain lines promoted from the review kit (roman, devanagari).
CORPUS_ADDITIONS: list[tuple[str, str]] = []


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


WORD_EDGE_PUNCT = ",.;:!?\"'()[]{}।—–-"


def normalize_word(text: str) -> str:
    return normalize(text).strip(WORD_EDGE_PUNCT).strip()


def read_pairs(path: Path) -> list[tuple[str, str]]:
    """Read ``roman,devanagari`` rows, splitting on the first comma only.

    The gold side contains commas (``अचानक बद्लियो, मानौँ, त्यो मेरो होइन``), so a
    CSV parser would truncate it.
    """
    pairs: list[tuple[str, str]] = []
    with io.open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.rstrip("\n").rstrip("\r")
            if "," not in line:
                continue
            roman, devanagari = line.split(",", 1)
            roman, devanagari = normalize(roman), normalize(devanagari)
            if not roman or not devanagari:
                continue
            if (roman.lower(), devanagari.lower()) in HEADER_PAIRS:
                continue
            pairs.append((roman, devanagari))
    return pairs


def difficulty(roman: str) -> str:
    words = len(roman.split())
    if words <= 3:
        return "short"
    if words <= 7:
        return "medium"
    return "long"


def build_lines() -> tuple[list[dict], list[tuple[str, str]]]:
    if not LINE_SOURCE.exists():
        sys.exit(f"missing line source: {LINE_SOURCE}")
    rows: list[dict] = []
    dropped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for roman, devanagari in read_pairs(LINE_SOURCE):
        if roman in seen:
            continue
        seen.add(roman)
        if roman in LINE_EXCLUSIONS:
            dropped.append((roman, LINE_EXCLUSIONS[roman]))
            continue
        if not ROMAN_RE.search(roman) or not DEVANAGARI_RE.search(devanagari):
            dropped.append((roman, "not a Roman -> Devanagari pair"))
            continue
        notes = ""
        if roman in LINE_CORRECTIONS:
            devanagari = LINE_CORRECTIONS[roman]
            notes = "review correction"
        rows.append(
            {
                "line_id": f"tl_{len(rows) + 1:04d}",
                "roman": roman,
                "devanagari": devanagari,
                "difficulty": difficulty(roman),
                "source": "legacy_user_v1",
                "notes": notes,
            }
        )
    for roman, devanagari in CORPUS_ADDITIONS:
        if roman in seen:
            continue
        seen.add(roman)
        if not ROMAN_RE.search(roman) or not DEVANAGARI_RE.search(devanagari):
            dropped.append((roman, "not a Roman -> Devanagari pair"))
            continue
        rows.append(
            {
                "line_id": f"tl_{len(rows) + 1:04d}",
                "roman": roman,
                "devanagari": devanagari,
                "difficulty": difficulty(roman),
                "source": "corpus_review_v1",
                "notes": "",
            }
        )
    return rows, dropped


def build_words() -> tuple[list[dict], list[dict], list[tuple[str, str]]]:
    by_roman: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    dropped: list[tuple[str, str]] = []
    for path in WORD_SOURCES:
        if not path.exists():
            sys.exit(f"missing word source: {path}")
        for roman, devanagari in read_pairs(path):
            roman, devanagari = normalize_word(roman), normalize_word(devanagari)
            key = roman.lower()
            if len(roman) <= 1:
                dropped.append((roman, "single-character token"))
                continue
            if not ROMAN_RE.search(roman):
                dropped.append((roman, "no Roman characters"))
                continue
            if not DEVANAGARI_RE.search(devanagari):
                dropped.append((f"{roman} -> {devanagari}", "English passthrough"))
                continue
            if (key, devanagari) in WORD_EXCLUSIONS:
                dropped.append((f"{roman} -> {devanagari}", WORD_EXCLUSIONS[(key, devanagari)]))
                continue
            if key in WORD_CORRECTIONS:
                devanagari = WORD_CORRECTIONS[key]
            by_roman[key][devanagari].add(path.name)

    rows: list[dict] = []
    ambiguous: list[dict] = []
    for key in sorted(by_roman):
        golds = by_roman[key]
        if len(golds) > 1:
            ambiguous.append(
                {
                    "roman": key,
                    "golds": " | ".join(sorted(golds)),
                    "n_golds": len(golds),
                    "sources": " ".join(sorted({name for names in golds.values() for name in names})),
                }
            )
            continue
        devanagari, sources = next(iter(golds.items()))
        rows.append(
            {
                "roman": key,
                "devanagari": devanagari,
                "source": " ".join(sorted(sources)),
            }
        )
    return rows, ambiguous, dropped


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    lines, line_drops = build_lines()
    words, ambiguous, word_drops = build_words()

    if len(lines) < 150:
        sys.exit(f"line gold too small: {len(lines)} rows")
    if len(words) < 500:
        sys.exit(f"word gold too small: {len(words)} rows")

    write_csv(
        OUT_LINES,
        lines,
        ["line_id", "roman", "devanagari", "difficulty", "source", "notes"],
    )
    write_csv(OUT_WORDS, words, ["roman", "devanagari", "source"])
    write_csv(OUT_AMBIGUOUS, ambiguous, ["roman", "golds", "n_golds", "sources"])

    by_difficulty: dict[str, int] = defaultdict(int)
    for row in lines:
        by_difficulty[row["difficulty"]] += 1

    print(f"lines: {len(lines)} -> {OUT_LINES}")
    print(f"  by difficulty: {dict(by_difficulty)}")
    print(f"  dropped: {len(line_drops)}")
    for roman, reason in line_drops:
        print(f"    - {roman!r}: {reason}")
    print(f"words: {len(words)} -> {OUT_WORDS}")
    print(f"  dropped: {len(word_drops)}")
    print(f"ambiguous (context-dependent, unscored): {len(ambiguous)} -> {OUT_AMBIGUOUS}")
    for row in ambiguous[:10]:
        print(f"    - {row['roman']}: {row['golds']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
