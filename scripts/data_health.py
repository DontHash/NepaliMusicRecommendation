"""Data health: freshness, quality budgets and row deltas (DE5).

  python scripts/data_health.py
  python scripts/data_health.py --strict --fail-on-stale
  python scripts/data_health.py --json --datasets cleaned_lyrics,sentiment_scores

Green/red per dataset; the JSON report is written to
music_rec_artifacts/data_health_report.json and a red report exits nonzero.
CI runs this after dataset validation so a budget breach fails the build.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.health import (  # noqa: E402
    DEFAULT_MAX_AGE_DAYS,
    EVENTS_DB_RELATIVE,
    build_health_report,
    format_health_report,
)
from scripts.validate_datasets import production_datasets  # noqa: E402

REPORT_PATH = PROJECT_ROOT / "music_rec_artifacts" / "data_health_report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true",
                        help="a missing dataset fails the report")
    parser.add_argument("--fail-on-stale", action="store_true",
                        help="freshness breaches fail the report")
    parser.add_argument("--no-history", action="store_true",
                        help="do not read/append the row-count history")
    parser.add_argument("--json", action="store_true", help="print the JSON report")
    parser.add_argument("--max-age-days", type=float, default=DEFAULT_MAX_AGE_DAYS)
    parser.add_argument("--datasets", default=None,
                        help="comma-separated subset of dataset names")
    args = parser.parse_args()

    datasets = production_datasets()
    if args.datasets:
        wanted = {name.strip() for name in args.datasets.split(",") if name.strip()}
        unknown = wanted - set(datasets)
        if unknown:
            print(f"unknown dataset(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        datasets = {name: path for name, path in datasets.items() if name in wanted}

    history_path = None if args.no_history else PROJECT_ROOT / "R_data" / "state" / "health_history.jsonl"
    report = build_health_report(
        PROJECT_ROOT, datasets,
        max_age_days=args.max_age_days,
        strict=args.strict,
        fail_on_stale=args.fail_on_stale,
        history_path=history_path,
        events_db=PROJECT_ROOT / EVENTS_DB_RELATIVE,
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_health_report(report))
        print(f"\nreport -> {REPORT_PATH}")
    return 0 if report["status"] == "green" else 1


if __name__ == "__main__":
    raise SystemExit(main())
