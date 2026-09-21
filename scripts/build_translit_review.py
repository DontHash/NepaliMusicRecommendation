"""Build the transliteration gold review kit (CSV + Markdown).

Runs the installed checkpoint over the committed gold sets and attaches its
prediction to every row, then samples fresh romanized corpus lines for the gold
v2 additions. The reviewer fills ``user_devanagari`` (only for ``new`` rows;
``gold`` rows are corrected in place when the legacy label is wrong) and
``user_note``.

- ``eval/translit_review.csv`` — gold lines, gold words, and new candidate lines
- ``eval/translit_review.md`` — the same content grouped for reading

Usage:
    python scripts/build_translit_review.py
    python scripts/build_translit_review.py --new-lines 200
"""

from __future__ import annotations

import argparse
import csv
import io
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.translit_metrics import levenshtein  # noqa: E402
from lyrics_pipeline.cleaner import clean_lyrics_body  # noqa: E402
from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

GOLD_LINES = PROJECT_ROOT / "eval" / "translit_gold_lines.csv"
GOLD_WORDS = PROJECT_ROOT / "eval" / "translit_gold_words.csv"
CORPUS_RAW = PROJECT_ROOT / "R_data" / "corpus" / "corpus_raw.csv"
OUT_CSV = PROJECT_ROOT / "eval" / "translit_review.csv"
OUT_MD = PROJECT_ROOT / "eval" / "translit_review.md"

ROMAN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
FIELDNAMES = [
    "kind",
    "ref_id",
    "roman",
    "devanagari",
    "model_pred",
    "model_cer",
    "difficulty",
    "source",
    "notes",
    "user_devanagari",
    "user_note",
]


def line_cer(prediction: str, reference: str) -> float:
    return round(levenshtein(prediction, reference) / max(len(reference), 1), 4)


def sample_corpus_lines(transliterator: NepaliTransliterator, count: int, seed: int = 42) -> list[dict]:
    """Fresh romanized lines from the corpus, deterministic and deduplicated."""
    if not CORPUS_RAW.exists():
        return []
    seen: set[str] = set()
    candidates: list[dict] = []
    with open(CORPUS_RAW, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("script") != "romanized":
                continue
            text, _ = clean_lyrics_body(
                row.get("Lyrics") or "", row.get("Title") or "", row.get("Artist") or ""
            )
            for line in text.splitlines():
                line = line.strip()
                if len(ROMAN_WORD_RE.findall(line)) < 2:
                    continue
                if line in seen:
                    continue
                seen.add(line)
                candidates.append(
                    {
                        "roman": line,
                        "song": f"{row.get('Title', '')} — {row.get('Artist', '')}".strip(" —"),
                        "source": row.get("source", ""),
                    }
                )
    rng = random.Random(seed)
    sample = rng.sample(candidates, min(count, len(candidates)))
    for row in sample:
        prediction = transliterator.transliterate_text(row["roman"])
        row["model_pred"] = prediction
        row["model_cer"] = ""
    return sample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-lines", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    transliterator = NepaliTransliterator()
    if not transliterator.available:
        sys.exit("transliterator checkpoint not available; cannot build the review kit")

    rows: list[dict] = []
    with open(GOLD_LINES, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            prediction = transliterator.transliterate_text(row["roman"])
            rows.append(
                {
                    "kind": "gold_line",
                    "ref_id": row["line_id"],
                    "roman": row["roman"],
                    "devanagari": row["devanagari"],
                    "model_pred": prediction,
                    "model_cer": line_cer(prediction, row["devanagari"]),
                    "difficulty": row["difficulty"],
                    "source": row["source"],
                    "notes": row["notes"],
                    "user_devanagari": "",
                    "user_note": "",
                }
            )

    with open(GOLD_WORDS, encoding="utf-8", newline="") as handle:
        word_rows = list(csv.DictReader(handle))
    predictions = transliterator.transliterate_tokens([row["roman"] for row in word_rows])
    for row, prediction in zip(word_rows, predictions):
        rows.append(
            {
                "kind": "gold_word",
                "ref_id": f"w_{row['roman']}",
                "roman": row["roman"],
                "devanagari": row["devanagari"],
                "model_pred": prediction,
                "model_cer": line_cer(prediction, row["devanagari"]),
                "difficulty": "",
                "source": row["source"],
                "notes": "",
                "user_devanagari": "",
                "user_note": "",
            }
        )

    for row in sample_corpus_lines(transliterator, args.new_lines, args.seed):
        rows.append(
            {
                "kind": "new_line",
                "ref_id": "",
                "roman": row["roman"],
                "devanagari": "",
                "model_pred": row["model_pred"],
                "model_cer": "",
                "difficulty": "",
                "source": row["source"],
                "notes": row["song"],
                "user_devanagari": "",
                "user_note": "",
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    gold_lines = [row for row in rows if row["kind"] == "gold_line"]
    gold_words = [row for row in rows if row["kind"] == "gold_word"]
    new_lines = [row for row in rows if row["kind"] == "new_line"]
    errors = sorted(gold_lines, key=lambda row: -float(row["model_cer"]))

    parts = [
        "# Transliteration gold review kit",
        "",
        f"- gold lines: {len(gold_lines)} (model errors: {sum(1 for r in gold_lines if r['model_cer'])})",
        f"- gold words: {len(gold_words)} (model errors: {sum(1 for r in gold_words if r['model_cer'])})",
        f"- new candidate lines for gold v2: {len(new_lines)}",
        "",
        "Fill `user_devanagari` on `new_line` rows; correct `devanagari` in place on",
        "`gold_line`/`gold_word` rows when the legacy label is wrong, and explain in",
        "`user_note`. Rubric: `eval/translit_policy.md`.",
        "",
        "## Gold lines with model errors (worst first)",
        "",
    ]
    for row in errors:
        if not row["model_cer"]:
            continue
        parts.extend(
            [
                f"### {row['ref_id']} · cer {row['model_cer']} · {row['difficulty']}",
                f"- roman: `{row['roman']}`",
                f"- gold:  {row['devanagari']}",
                f"- model: {row['model_pred']}",
                "",
            ]
        )
    parts.extend(["## New candidate lines for gold v2", ""])
    for index, row in enumerate(new_lines, start=1):
        parts.extend(
            [
                f"### new_{index:03d} · {row['notes']}",
                f"- roman: `{row['roman']}`",
                f"- model: {row['model_pred']}",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(parts), encoding="utf-8")

    print(f"gold lines: {len(gold_lines)} | gold words: {len(gold_words)} | new lines: {len(new_lines)}")
    print(f"csv -> {OUT_CSV}")
    print(f"md  -> {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
