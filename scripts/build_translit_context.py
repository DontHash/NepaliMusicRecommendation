"""Generate lyrics_pipeline/translit_context.py: ambiguous readings + bigrams.

The lexicon deliberately leaves context-dependent tokens to the model, but the
model is exactly where the ``cha -> चा`` / ``ma -> मा`` errors come from. The
teacher labels already contain the contextual choices (6k lines), so this script
mines two tables from them:

- ``READINGS``: roman -> {Devanagari form: count} for tokens the lexicon does
  not cover because their reading is split.
- ``BIGRAM``: Devanagari form -> {preceding form: count} restricted to the
  candidate forms above, so the table stays small enough to commit.

``lyrics_pipeline/context_resolver.py`` runs a Viterbi pass over each line with
these tables to pick the reading that fits the neighbouring words.

Usage:
    python scripts/build_translit_context.py
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_corpus_v1" / "labels.csv"
CORPUS_CSV = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv"
OUT_PATH = PROJECT_ROOT / "lyrics_pipeline" / "translit_context.py"

ROMAN_TOKEN_RE = re.compile(r"[A-Za-z]+")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
WORD_EDGE_PUNCT = ",.;:!?\"'()[]{}।—–-"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()


def normalize_token(text: str) -> str:
    return normalize(text).strip(WORD_EDGE_PUNCT).strip()


def load_readings(labels_path: Path) -> tuple[dict[str, Counter], int]:
    readings: dict[str, Counter] = defaultdict(Counter)
    lines = 0
    with open(labels_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            lines += 1
            roman_tokens = ROMAN_TOKEN_RE.findall(row["roman"])
            dev_tokens = [normalize_token(token) for token in row["devanagari"].split()]
            dev_tokens = [token for token in dev_tokens if token]
            if len(roman_tokens) != len(dev_tokens):
                continue
            for roman, devanagari in zip(roman_tokens, dev_tokens):
                if len(roman) > 1 and DEVANAGARI_RE.search(devanagari):
                    readings[roman.lower()][devanagari] += 1
    return readings, lines


def load_transitions(csv_path: Path) -> tuple[dict[str, Counter], dict[str, Counter], int]:
    """Word bigrams from songs written in Devanagari originally.

    Independent of the transliterator's own output, and ~10x more tokens than
    the teacher labels, so the transition estimates are far less sparse.
    """
    bigram: dict[str, Counter] = defaultdict(Counter)
    forward: dict[str, Counter] = defaultdict(Counter)
    lines = 0
    if not csv_path.exists():
        return bigram, forward, lines
    with open(csv_path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script_style_original") not in {"devanagari", "mixed"}:
                continue
            for line in (row.get("lyrics_devanagari") or "").splitlines():
                tokens = [normalize_token(token) for token in line.split()]
                tokens = [token for token in tokens if token and DEVANAGARI_RE.search(token)]
                if not tokens:
                    continue
                lines += 1
                bigram[tokens[0]]["<s>"] += 1
                forward[tokens[-1]]["</s>"] += 1
                for previous, current in zip(tokens, tokens[1:]):
                    bigram[current][previous] += 1
                    forward[previous][current] += 1
    return bigram, forward, lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--corpus", type=Path, default=CORPUS_CSV)
    parser.add_argument("--min-readings", type=int, default=2, help="readings needed to treat a token as ambiguous")
    parser.add_argument("--min-reading-count", type=int, default=2, help="occurrences a reading needs to be a candidate")
    parser.add_argument("--max-prev", type=int, default=12, help="preceding-word entries kept per candidate")
    parser.add_argument("--max-next", type=int, default=12, help="following-word entries kept per candidate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.labels.exists():
        sys.exit(f"teacher labels not found: {args.labels}")

    readings, label_lines = load_readings(args.labels)
    bigram, forward, corpus_lines = load_transitions(args.corpus)

    ambiguous = {
        key: Counter(
            {
                form: count
                for form, count in counter.items()
                if count >= args.min_reading_count
            }
        )
        for key, counter in readings.items()
    }
    ambiguous = {
        key: counter
        for key, counter in ambiguous.items()
        if len(counter) >= args.min_readings
    }
    candidates = {form for counter in ambiguous.values() for form in counter}
    pruned_bigram = {
        form: Counter(dict(bigram[form].most_common(args.max_prev)))
        for form in sorted(candidates)
        if bigram.get(form)
    }
    pruned_forward = {
        form: Counter(dict(forward[form].most_common(args.max_next)))
        for form in sorted(candidates)
        if forward.get(form)
    }

    body = [
        '"""Ambiguous readings and context bigrams mined from teacher labels.',
        "",
        "Generated by ``scripts/build_translit_context.py``; do not edit by hand.",
        "",
        "``READINGS`` maps a roman token to its attested Devanagari readings and",
        "counts. ``BIGRAM`` maps a candidate form to the words seen before it and",
        "``FORWARD_BIGRAM`` to the words seen after it.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "READINGS: dict[str, dict[str, int]] = {",
    ]
    for key in sorted(ambiguous):
        entries = ", ".join(
            f'"{form}": {count}' for form, count in ambiguous[key].most_common()
        )
        body.append(f'    "{key}": {{{entries}}},')
    body.append("}")
    body.append("")
    body.append("BIGRAM: dict[str, dict[str, int]] = {")
    for form in sorted(pruned_bigram):
        entries = ", ".join(
            f'"{previous}": {count}' for previous, count in pruned_bigram[form].most_common()
        )
        body.append(f'    "{form}": {{{entries}}},')
    body.append("}")
    body.append("")
    body.append("FORWARD_BIGRAM: dict[str, dict[str, int]] = {")
    for form in sorted(pruned_forward):
        entries = ", ".join(
            f'"{following}": {count}' for following, count in pruned_forward[form].most_common()
        )
        body.append(f'    "{form}": {{{entries}}},')
    body.append("}")
    body.append("")
    body.append(
        f"STATS = {{'ambiguous_tokens': {len(ambiguous)}, 'candidate_forms': {len(candidates)}, "
        f"'bigram_forms': {len(pruned_bigram)}, 'forward_forms': {len(pruned_forward)}, "
        f"'label_lines': {label_lines}, 'corpus_lines': {corpus_lines}}}"
    )
    body.append("")
    OUT_PATH.write_text("\n".join(body), encoding="utf-8")

    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"teacher lines={label_lines}  corpus lines={corpus_lines}")
    print(
        f"ambiguous_tokens={len(ambiguous)} candidate_forms={len(candidates)} "
        f"bigram_forms={len(pruned_bigram)} forward_forms={len(pruned_forward)} "
        f"-> {OUT_PATH} ({size_kb:.0f} KB)"
    )
    print("examples:")
    for key in ["ma", "cha", "ra", "na", "ki", "hun"]:
        if key in ambiguous:
            top = ", ".join(f"{form} ({count})" for form, count in ambiguous[key].most_common(4))
            print(f"  {key:8s} {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
