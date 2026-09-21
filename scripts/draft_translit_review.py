"""Draft the transliteration review kit with a second model.

Fills ``draft_devanagari`` / ``draft_cer`` in ``eval/translit_review.csv`` so the
reviewer can accept or correct instead of translating from scratch. The draft is
produced by a different model than the one that labeled the training corpus
(``--model``, default ``gemini-3.8-flash``), and it never sees the legacy label
when drafting a gold row, so the disagreement is a genuine second opinion.

Only the human ``user_devanagari`` column feeds gold v2; the draft is an aid,
never a label.

Usage:
    python scripts/draft_translit_review.py
    python scripts/draft_translit_review.py --kinds new_line --limit 40
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eval.translit_metrics import levenshtein  # noqa: E402
from scripts.api_translit_label import SYSTEM, load_key, label_batch  # noqa: E402

REVIEW_CSV = PROJECT_ROOT / "eval" / "translit_review.csv"
DRAFT_CACHE = PROJECT_ROOT / "R_data" / "raw" / "gemini" / "translit_draft_v1" / "drafts.jsonl"

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "line_id": {"type": "string"},
            "devanagari": {"type": "string"},
        },
        "required": ["line_id", "devanagari"],
    },
}

FEW_SHOT = [
    ("huncha ki nai hunna", "हुन्छ कि नै हुन्न"),
    ("ma timilai maya garchu", "म तिमीलाई माया गर्छु"),
    ("yo katha aaja prastut gardai", "यो कथा आज प्रस्तुत गर्दै"),
    ("I love you bhanne geet", "I love you भन्ने गीत"),
    ("sanga bina kahile", "सँग बिना कहिले"),
]


def build_prompt(block: str, batch: list[dict]) -> str:
    lines = [block, "", "### Lines to transliterate"]
    for row in batch:
        lines.append(f"<line id={row['row_id']}>{row['roman']}</line>")
    lines.append("")
    lines.append(f"Transliterate all {len(batch)} lines above. Reply with ONLY the JSON array.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--kinds", nargs="*", default=["gold_line", "new_line"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--attempts", type=int, default=2)
    parser.add_argument("--sleep-between", type=int, default=3)
    parser.add_argument("--key-var", default="GEMINI_API_KEY")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with open(REVIEW_CSV, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    done: dict[str, str] = {}
    if DRAFT_CACHE.exists():
        for line in DRAFT_CACHE.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                done[record["row_id"]] = record["devanagari"]
            except (json.JSONDecodeError, KeyError):
                continue

    targets = []
    for index, row in enumerate(rows):
        if row["kind"] not in args.kinds:
            continue
        row_id = f"r{index:04d}"
        row["row_id"] = row_id
        if row_id not in done:
            targets.append(row)
    if args.limit:
        targets = targets[: args.limit]

    print(f"rows={len(rows)} kinds={args.kinds} already drafted={len(done)} todo={len(targets)}")
    if targets:
        key = load_key(args.key_var)
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=180_000))
        block = "### Examples (policy-consistent)\n" + "\n".join(
            f"<line id=x>{roman}</line>\noutput: {json.dumps({'line_id': 'x', 'devanagari': devanagari}, ensure_ascii=False)}"
            for roman, devanagari in FEW_SHOT
        )
        DRAFT_CACHE.parent.mkdir(parents=True, exist_ok=True)
        batches = math.ceil(len(targets) / args.batch_size)
        with DRAFT_CACHE.open("a", encoding="utf-8") as handle:
            for index in range(batches):
                batch = targets[index * args.batch_size : (index + 1) * args.batch_size]
                expected = {row["row_id"] for row in batch}
                items, _, error = label_batch(
                    client,
                    args.model,
                    build_prompt(block, batch),
                    expected,
                    attempts=args.attempts,
                )
                if not items and error:
                    print(f"batch {index + 1}/{batches}: FAILED ({error})", flush=True)
                    break
                for item in items:
                    handle.write(
                        json.dumps(
                            {"row_id": item["line_id"], "devanagari": item["devanagari"]},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    done[item["line_id"]] = item["devanagari"]
                handle.flush()
                print(f"batch {index + 1}/{batches}: drafted {len(items)}", flush=True)
                if args.sleep_between:
                    time.sleep(args.sleep_between)

    drafted = updated = 0
    for index, row in enumerate(rows):
        row_id = f"r{index:04d}"
        draft = done.get(row_id)
        if not draft:
            continue
        row["draft_devanagari"] = draft
        drafted += 1
        if row["kind"] == "gold_line" and row["devanagari"]:
            distance = levenshtein(draft, row["devanagari"])
            row["draft_cer"] = round(distance / max(len(row["devanagari"]), 1), 4)
            updated += int(draft != row["devanagari"])
        row.pop("row_id", None)

    fieldnames = [name for name in rows[0] if name != "row_id"]
    with open(REVIEW_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"drafts written: {drafted} (gold rows where the draft disagrees: {updated})")
    print(f"cache -> {DRAFT_CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
