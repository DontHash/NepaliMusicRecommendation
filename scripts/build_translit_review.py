"""Build the transliteration gold review kit (CSV + Markdown).

Runs the installed checkpoint over the committed gold sets and attaches its
prediction to every row, then samples fresh romanized corpus lines for the gold
v2 additions. The sampled lines are **held out** from the teacher training set
(``R_data/raw/gemini/translit_corpus_v1/labels.jsonl``), so gold v2 measures the
system on lines it was never distilled from.

- ``eval/translit_review.csv`` — gold lines, gold words, and new candidate lines
- ``eval/translit_review.md`` — the same content grouped for reading

``scripts/draft_translit_review.py`` fills the ``draft_*`` columns with a second
model's opinion so the reviewer can accept/correct instead of translating from
scratch. Only the human ``user_devanagari`` column feeds gold v2.

Usage:
    python scripts/build_translit_review.py
    python scripts/build_translit_review.py --new-lines 200
"""

from __future__ import annotations

import argparse
import csv
import io
import json
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
TEACHER_LABELS = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_corpus_v1" / "labels.jsonl"
OUT_CSV = PROJECT_ROOT / "eval" / "translit_review.csv"
OUT_MD = PROJECT_ROOT / "eval" / "translit_review.md"
QUICK_CSV = PROJECT_ROOT / "eval" / "translit_review_quick.csv"
QUICK_MD = PROJECT_ROOT / "eval" / "translit_review_quick.md"

ROMAN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
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
    "draft_devanagari",
    "draft_cer",
    "draft_issue",
    "user_devanagari",
    "user_note",
]


def line_cer(prediction: str, reference: str) -> float:
    return round(levenshtein(prediction, reference) / max(len(reference), 1), 4)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def teacher_romans(path: Path) -> set[str]:
    romans: set[str] = set()
    if not path.exists():
        return romans
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                romans.add(normalize(json.loads(line)["roman"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return romans


def is_credit_like(line: str) -> bool:
    """All-caps short lines are credit/name rows, not lyric lines."""
    return line.isupper() and len(line.split()) <= 4


def sample_corpus_lines(
    transliterator: NepaliTransliterator, count: int, seed: int = 42
) -> list[dict]:
    """Fresh romanized lines held out from the teacher training set.

    Candidates that are not lyric transliterations are skipped: English-only
    lines (the gate leaves them Latin, so there is nothing to score) and
    credit-like all-caps rows.
    """
    gold_romans = {
        normalize(row["roman"])
        for row in csv.DictReader(io.open(GOLD_LINES, encoding="utf-8"))
    }
    excluded = teacher_romans(TEACHER_LABELS) | gold_romans
    seen: set[str] = set()
    candidates: list[dict] = []
    if not CORPUS_RAW.exists():
        return []
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
                if line in seen or line in excluded or is_credit_like(line):
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
    rng.shuffle(candidates)
    sample: list[dict] = []
    for row in candidates:
        prediction = transliterator.transliterate_text(row["roman"])
        if not DEVANAGARI_RE.search(prediction):
            continue
        row["model_pred"] = prediction
        row["model_cer"] = ""
        sample.append(row)
        if len(sample) >= count:
            break
    return sample


def preserve_review(rows: list[dict]) -> int:
    """Carry draft/user columns over from an existing review CSV.

    Keyed by ``(kind, ref_id, roman)`` so a rebuild never loses drafting or
    human review work.
    """
    if not OUT_CSV.exists():
        return 0
    with open(OUT_CSV, encoding="utf-8", newline="") as handle:
        existing = list(csv.DictReader(handle))
    by_key = {
        (row.get("kind", ""), row.get("ref_id", ""), row.get("roman", "")): row
        for row in existing
    }
    carried = 0
    for row in rows:
        previous = by_key.get((row["kind"], row["ref_id"], row["roman"]))
        if not previous:
            continue
        for column in ("draft_devanagari", "draft_cer", "draft_issue", "user_devanagari", "user_note"):
            value = previous.get(column, "")
            if value:
                row[column] = value
                carried += 1
    return carried


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
                    "draft_devanagari": "",
                    "draft_cer": "",
                    "draft_issue": "",
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
                "draft_devanagari": "",
                "draft_cer": "",
                    "draft_issue": "",
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
                "draft_devanagari": "",
                "draft_cer": "",
                    "draft_issue": "",
                "user_devanagari": "",
                "user_note": "",
            }
        )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    carried = preserve_review(rows)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    gold_lines = [row for row in rows if row["kind"] == "gold_line"]
    gold_words = [row for row in rows if row["kind"] == "gold_word"]
    new_lines = [row for row in rows if row["kind"] == "new_line"]
    errors = sorted(gold_lines, key=lambda row: -float(row["model_cer"] or 0))
    draft_disagreements = sorted(
        (row for row in gold_lines if row["draft_devanagari"] and row["draft_devanagari"] != row["devanagari"]),
        key=lambda row: -float(row["draft_cer"] or 0),
    )

    parts = [
        "# Transliteration gold review kit",
        "",
        f"- gold lines: {len(gold_lines)} (model errors: {sum(1 for r in gold_lines if r['model_cer'])})",
        f"- gold words: {len(gold_words)} (model errors: {sum(1 for r in gold_words if r['model_cer'])})",
        f"- new candidate lines for gold v2: {len(new_lines)} (held out from teacher training)",
        "",
        "`draft_devanagari` is a second model's opinion (see",
        "`scripts/draft_translit_review.py`) so you can accept or correct rather",
        "than translate from scratch. Only `user_devanagari` feeds gold v2.",
        "Rubric: `eval/translit_policy.md`.",
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
                f"- draft: {row['draft_devanagari'] or '(pending)'}",
                "",
            ]
        )
    parts.extend(
        [
            f"## Draft disagrees with the legacy gold ({len(draft_disagreements)} rows)",
            "",
            "These are the rows worth a human decision: either the legacy label is",
            "wrong (we already confirmed several) or the draft is. Set",
            "`user_devanagari` to the accepted form and explain in `user_note`.",
            "",
        ]
    )
    for row in draft_disagreements[:80]:
        parts.extend(
            [
                f"### {row['ref_id']} · draft cer {row['draft_cer']}",
                f"- roman: `{row['roman']}`",
                f"- gold:  {row['devanagari']}",
                f"- draft: {row['draft_devanagari']}",
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
                f"- draft: {row['draft_devanagari'] or '(pending)'}",
                "",
            ]
        )
    OUT_MD.write_text("\n".join(parts), encoding="utf-8")

    print(f"gold lines: {len(gold_lines)} | gold words: {len(gold_words)} | new lines: {len(new_lines)}")
    print(f"draft disagreements on gold lines: {len(draft_disagreements)}")
    print(f"review work carried over: {carried} cells")
    print(f"csv -> {OUT_CSV}")
    print(f"md  -> {OUT_MD}")

    write_quick_review(new_lines, draft_disagreements)
    return 0


def write_quick_review(new_lines: list[dict], disagreements: list[dict]) -> None:
    """A short list where the human decision actually changes the gold.

    Two strata: the held-out new lines (no legacy baggage) and the legacy rows
    where the draft and the pipeline agree against the gold (likely legacy
    errors). The pipeline's own output is the proposal because a review pass
    showed it beating the draft on exactly these lines; the draft is kept as a
    cross-check column.
    """
    consensus = [
        row
        for row in disagreements
        if row["draft_devanagari"] == row["model_pred"] and row["draft_devanagari"]
    ]
    quick: list[dict] = []
    for row in new_lines:
        quick.append(
            {
                "stratum": "new_heldout",
                "ref_id": "",
                "roman": row["roman"],
                "gold": "",
                "model": row["model_pred"],
                "draft": row["draft_devanagari"],
                "draft_agrees": int(row["draft_devanagari"] == row["model_pred"]),
                "proposal": row["model_pred"],
                "user_devanagari": row["model_pred"],
                "user_note": "",
            }
        )
    for row in consensus:
        quick.append(
            {
                "stratum": "legacy_consensus",
                "ref_id": row["ref_id"],
                "roman": row["roman"],
                "gold": row["devanagari"],
                "model": row["model_pred"],
                "draft": row["draft_devanagari"],
                "draft_agrees": 1,
                "proposal": row["model_pred"],
                "user_devanagari": "",
                "user_note": "",
            }
        )
    fieldnames = [
        "stratum",
        "ref_id",
        "roman",
        "gold",
        "model",
        "draft",
        "draft_agrees",
        "proposal",
        "user_devanagari",
        "user_note",
    ]
    with open(QUICK_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(quick)

    parts = [
        "# Quick transliteration review",
        "",
        f"- `new_heldout`: {len(new_lines)} lines held out from teacher training. The",
        "  **pipeline** output is pre-filled in `user_devanagari` (a review pass showed",
        "  it beats the draft here); `draft` is a second opinion and `draft_agrees`",
        "  marks where the two agree. Edit or delete what you disagree with.",
        f"- `legacy_consensus`: {len(consensus)} legacy rows where the draft and the pipeline",
        "  agree against the recorded gold (likely legacy errors). Set `user_devanagari` to",
        "  the accepted form, or leave empty to keep the legacy label.",
        "",
        "Non-lyric candidates (English-only lines, credit rows) are filtered out of the",
        "sample. Full kit with all draft disagreements: `eval/translit_review.md`.",
        "",
        "## new_heldout",
        "",
    ]
    for index, row in enumerate(quick, start=1):
        if row["stratum"] != "new_heldout":
            continue
        parts.extend(
            [
                f"### {index:03d}",
                f"- roman: `{row['roman']}`",
                f"- model: {row['model']}",
                f"- draft: {row['draft']} ({'agrees' if row['draft_agrees'] else 'differs'})",
                "",
            ]
        )
    parts.extend(["## legacy_consensus", ""])
    for row in quick:
        if row["stratum"] != "legacy_consensus":
            continue
        parts.extend(
            [
                f"### {row['ref_id']}",
                f"- roman: `{row['roman']}`",
                f"- gold:  {row['gold']}",
                f"- model: {row['model']}",
                "",
            ]
        )
    QUICK_MD.write_text("\n".join(parts), encoding="utf-8")
    print(f"quick -> {QUICK_CSV} ({len(quick)} rows: {len(new_lines)} new + {len(consensus)} consensus)")


if __name__ == "__main__":
    raise SystemExit(main())
