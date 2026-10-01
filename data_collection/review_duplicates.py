"""Generate the near-duplicate identity review for a compacted corpus.

  python -m data_collection.review_duplicates
  python -m data_collection.review_duplicates --input R_data/corpus/corpus_raw.csv \\
      --output R_data/corpus/duplicate_review.csv --threshold 0.6

Writes the review CSV (one row per candidate pair with a suggested action and
an empty decision to be filled during review) plus a JSON report under
R_data/corpus/reports/.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from .identity import DEFAULT_THRESHOLD, review_file, write_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=cfg.DEFAULT_PATHS.corpus / "corpus_raw.csv")
    parser.add_argument("--output", type=Path,
                        default=cfg.DEFAULT_PATHS.corpus / "duplicate_review.csv")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"input corpus not found: {args.input}")
        return 1
    report = review_file(args.input, args.output, threshold=args.threshold)
    paths = cfg.DEFAULT_PATHS.ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = paths.reports / f"review_duplicates_{stamp}.json"
    write_report(report, report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report -> {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
