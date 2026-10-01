"""Run, inspect or backfill the ProjectR asset graph.

  python scripts/pipeline.py graph
  python scripts/pipeline.py run --select features --force
  python scripts/pipeline.py run --select publish.artifacts
  python scripts/pipeline.py run --select corpus.v3 --downstream --dry-run
  python scripts/pipeline.py history --limit 5

Assets materialize from their declared outputs: re-running a command skips
steps whose outputs already exist (`--force` re-runs them, `--backfill` forces
the selection and everything downstream). See docs/DE3_ORCHESTRATION_PLAN.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.core import PROJECT_ROOT as ROOT  # noqa: E402
from pipelines.definitions import build_pipeline  # noqa: E402


def _print_graph(pipeline) -> None:
    entries = pipeline.graph()
    external = sum(1 for entry in entries if entry["external"])
    print(f"{len(entries)} assets ({external} external sources)")
    for entry in entries:
        kind = "external" if entry["external"] else "internal"
        deps = ", ".join(entry["deps"]) or "-"
        print(f"  {entry['asset']:<22} [{kind:<8}] deps: {deps}")
        if entry["description"]:
            print(f"  {'':<22}  {entry['description']}")


def _print_history(pipeline, limit: int) -> None:
    runs = pipeline.state.history(limit)
    if not runs:
        print("no runs recorded")
        return
    for run in runs:
        print(f"#{run['id']:<4} {run['status']:<8} {run['started_at']} "
              f"targets={run['targets']}")
    print(f"\nrun #{runs[0]['id']} assets:")
    for row in pipeline.state.run_assets(runs[0]["id"]):
        print(f"  {row['status']:<8} {row['asset']:<22} "
              f"{row['duration_s'] or 0:7.2f}s {row['message'] or ''}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "graph", "history"])
    parser.add_argument("--select", default=None,
                        help="comma-separated asset names (default: all)")
    parser.add_argument("--downstream", action="store_true",
                        help="also run everything downstream of the selection")
    parser.add_argument("--backfill", action="store_true",
                        help="downstream + force the selection (re-run despite outputs)")
    parser.add_argument("--force", action="store_true",
                        help="re-run every asset in scope, even if materialized")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the execution plan without running anything")
    parser.add_argument("--retries", type=int, default=None,
                        help="retry override for every asset")
    parser.add_argument("--limit", type=int, default=5, help="history rows to show")
    parser.add_argument("--state-dir", type=Path, default=ROOT / "R_data" / "state")
    args = parser.parse_args()

    pipeline = build_pipeline(state_dir=args.state_dir)

    if args.command == "graph":
        _print_graph(pipeline)
        return 0
    if args.command == "history":
        _print_history(pipeline, args.limit)
        return 0

    select = [name.strip() for name in args.select.split(",")] if args.select else None
    try:
        result = pipeline.run(select=select, downstream=args.downstream,
                              backfill=args.backfill, force=args.force,
                              dry_run=args.dry_run, retries=args.retries)
    except (KeyError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if result["dry_run"]:
        print("plan (dry run):")
        for step in result["plan"]:
            print(f"  {step['status']:<8} {step['asset']}")
        return 0

    print(f"run #{result['run_id']} {result['status']} in {result['duration_s']:.1f}s")
    for record in result["assets"]:
        metadata = record["metadata"] or {}
        detail = record["message"] or ", ".join(f"{key}={value}" for key, value
                                                in list(metadata.items())[:4])
        print(f"  {record['status']:<8} {record['asset']:<22} "
              f"{record['duration_s']:7.2f}s {detail}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
