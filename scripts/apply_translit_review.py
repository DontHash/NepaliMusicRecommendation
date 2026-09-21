"""Turn the reviewed quick-review sheet into the gold v2 sidecar.

Reads ``eval/translit_review_quick.csv`` (the human-reviewed file) and writes
``eval/translit_gold_v2.json``, which ``scripts/build_translit_gold.py`` merges
into the gold sets on the next build:

- ``new_heldout`` rows with ``user_devanagari`` become gold line additions
  (source ``corpus_review_v1``).
- ``legacy_consensus`` rows with ``user_devanagari`` become corrections to the
  legacy labels.

Rows with an empty ``user_devanagari`` keep whatever the gold already has.

Usage:
    python scripts/apply_translit_review.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUICK_CSV = PROJECT_ROOT / "eval" / "translit_review_quick.csv"
OUT_JSON = PROJECT_ROOT / "eval" / "translit_gold_v2.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, default=QUICK_CSV)
    parser.add_argument("--out", type=Path, default=OUT_JSON)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.review.exists():
        sys.exit(f"review sheet not found: {args.review}")

    with open(args.review, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    additions: list[list[str]] = []
    corrections: dict[str, str] = {}
    pending = 0
    for row in rows:
        accepted = (row.get("user_devanagari") or "").strip()
        if not accepted:
            if row.get("stratum") == "legacy_consensus":
                pending += 1
            continue
        roman = (row.get("roman") or "").strip()
        if not roman:
            continue
        if row.get("stratum") == "new_heldout":
            additions.append([roman, accepted])
        elif row.get("stratum") == "legacy_consensus":
            corrections[roman] = accepted

    payload = {
        "corpus_additions": additions,
        "line_corrections": corrections,
        "proposal_source": "pipeline",
        "source": args.review.name,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"new held-out lines accepted: {len(additions)}")
    print(f"legacy corrections accepted: {len(corrections)}")
    print(f"legacy rows left unchanged (empty user_devanagari): {pending}")
    print(f"-> {args.out}")
    print("rebuild with: python scripts/build_translit_gold.py && python scripts/check_transliteration.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
