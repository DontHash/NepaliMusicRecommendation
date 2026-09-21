"""Generate lyrics_pipeline/translit_lexicon.py from teacher-labeled corpus lines.

Mines roman -> Devanagari token pairs from the Gemini teacher labels by
positional alignment (lines whose token counts match after edge-punctuation
normalization) and keeps entries that are attested at least twice with a
dominant reading. Tokens whose readings are split (``ma`` -> म / मा) are not
lookups at all: they go to ``AMBIGUOUS`` and stay with the model (context
rescoring is track A3).

The committed word gold is deliberately NOT used here, so it stays a clean
evaluation set.

Usage:
    python scripts/build_translit_lexicon.py
    python scripts/build_translit_lexicon.py --min-count 3 --min-share 0.9
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_corpus_v1" / "labels.csv"
ATTESTED_CSV = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv"
GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
OUT_PATH = PROJECT_ROOT / "lyrics_pipeline" / "translit_lexicon.py"

ROMAN_TOKEN_RE = re.compile(r"[A-Za-z]+")
DEVANAGARI_WORD_RE = re.compile(r"[\u0900-\u097F]+")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
WORD_EDGE_PUNCT = ",.;:!?\"'()[]{}।—–-"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def normalize_token(text: str) -> str:
    return normalize(text).strip(WORD_EDGE_PUNCT).strip()


def mine_pairs(labels_path: Path) -> tuple[dict[str, Counter], int, int]:
    counts: dict[str, Counter] = defaultdict(Counter)
    lines = aligned = 0
    with open(labels_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            lines += 1
            roman_tokens = ROMAN_TOKEN_RE.findall(row["roman"])
            dev_tokens = [normalize_token(token) for token in row["devanagari"].split()]
            dev_tokens = [token for token in dev_tokens if token]
            if len(roman_tokens) != len(dev_tokens):
                continue
            aligned += 1
            for roman, devanagari in zip(roman_tokens, dev_tokens):
                key = roman.lower()
                if len(key) <= 1 or not DEVANAGARI_RE.search(devanagari):
                    continue
                counts[key][devanagari] += 1
    return counts, lines, aligned


def load_attested(csv_path: Path) -> set[str]:
    """Devanagari word forms attested in natively-Devanagari songs.

    Independent of the transliterator's own output, so it acts as a precision
    filter: entries whose form is not a real corpus word (``barsha`` -> बर्ष)
    are dropped and left to the model.
    """
    forms: set[str] = set()
    if not csv_path.exists():
        return forms
    with open(csv_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script_style_original") != "devanagari":
                continue
            forms.update(DEVANAGARI_WORD_RE.findall(row.get("lyrics_devanagari") or ""))
    return forms


def load_line_gold_readings(path: Path) -> dict[str, Counter]:
    """Aligned roman -> Devanagari readings from the human line gold."""
    readings: dict[str, Counter] = defaultdict(Counter)
    if not path.exists():
        return readings
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            roman_tokens = ROMAN_TOKEN_RE.findall(row["roman"])
            dev_tokens = [normalize_token(token) for token in row["devanagari"].split()]
            dev_tokens = [token for token in dev_tokens if token]
            if len(roman_tokens) != len(dev_tokens):
                continue
            for roman, devanagari in zip(roman_tokens, dev_tokens):
                readings[roman.lower()][devanagari] += 1
    return readings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--attested-csv", type=Path, default=ATTESTED_CSV)
    parser.add_argument("--gold-lines", type=Path, default=GOLD_LINES)
    parser.add_argument("--min-count", type=int, default=2)
    parser.add_argument("--min-share", type=float, default=0.8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.labels.exists():
        sys.exit(f"teacher labels not found: {args.labels}")

    counts, lines, aligned = mine_pairs(args.labels)
    attested = load_attested(args.attested_csv)
    line_gold = load_line_gold_readings(args.gold_lines)
    entries: dict[str, str] = {}
    ambiguous: list[tuple[str, str, int]] = []
    unattested: list[tuple[str, str]] = []
    contradictions: list[tuple[str, str, str]] = []
    for key in sorted(counts):
        readings = counts[key]
        total = sum(readings.values())
        best, best_count = readings.most_common(1)[0]
        share = best_count / total
        if total < args.min_count:
            continue
        if share < args.min_share:
            summary = " | ".join(f"{value} ({count})" for value, count in readings.most_common(4))
            ambiguous.append((key, summary, total))
            continue
        if attested and best not in attested:
            unattested.append((key, best))
            continue
        gold_readings = line_gold.get(key)
        if gold_readings:
            dominant = gold_readings.most_common(1)[0][0]
            if dominant != best:
                contradictions.append((key, best, dominant))
                continue
        entries[key] = best

    if not entries:
        sys.exit("no lexicon entries mined; check the teacher labels")

    body = [
        '"""Roman -> Devanagari lookup mined from teacher-labeled corpus lines.',
        "",
        "Generated by ``scripts/build_translit_lexicon.py``; do not edit by hand.",
        "Regenerate after retraining or relabeling the teacher data.",
        "",
        "``LEXICON`` holds readings attested at least "
        f"{args.min_count} times with a dominant share >= {args.min_share:.0%}.",
        "``AMBIGUOUS`` lists roman tokens whose readings are context-dependent",
        "(``ma`` -> म / मा); they are deliberately left to the model.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "LEXICON = {",
    ]
    for key in sorted(entries):
        body.append(f'    "{key}": "{entries[key]}",')
    body.append("}")
    body.append("")
    body.append("AMBIGUOUS = frozenset(")
    body.append("{")
    for key, _, _ in ambiguous:
        body.append(f'    "{key}",')
    body.append("}")
    body.append(")")
    body.append("")
    body.append(
        f"STATS = {{'entries': {len(entries)}, 'ambiguous': {len(ambiguous)}, "
        f"'unattested': {len(unattested)}, 'contradictions': {len(contradictions)}, "
        f"'mined_types': {len(counts)}, 'lines': {lines}, 'aligned_lines': {aligned}}}"
    )
    body.append("")
    OUT_PATH.write_text("\n".join(body), encoding="utf-8")

    print(f"labels: {args.labels}")
    print(f"lines={lines} aligned={aligned} ({aligned / max(lines, 1):.1%}) mined_types={len(counts)}")
    print(
        f"entries={len(entries)} ambiguous={len(ambiguous)} "
        f"dropped_unattested={len(unattested)} dropped_contradiction={len(contradictions)} "
        f"-> {OUT_PATH}"
    )
    if unattested:
        print("dropped (form not attested in the Devanagari corpus):")
        for key, form in unattested[:10]:
            print(f"  {key:12s} {form}")
    if contradictions:
        print("dropped (contradicts the human line gold):")
        for key, form, gold_form in contradictions[:10]:
            print(f"  {key:12s} teacher={form:14s} line-gold={gold_form}")
    print("ambiguous examples:")
    for key, summary, total in ambiguous[:10]:
        print(f"  {key:12s} n={total:<4d} {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
