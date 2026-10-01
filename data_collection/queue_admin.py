"""Operate the collection work queue: status, sweeps, DLQ, requeue, orphans.

  python -m data_collection.queue_admin status
  python -m data_collection.queue_admin sweep --max-attempts 3
  python -m data_collection.queue_admin dlq --out R_data/corpus/dead_letters_candidates.csv
  python -m data_collection.queue_admin requeue --status dead --reset-attempts
  python -m data_collection.queue_admin reset-orphans [--all]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config as cfg
from . import state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command",
                        choices=["status", "sweep", "dlq", "requeue", "reset-orphans"])
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--out", type=Path,
                        default=cfg.DEFAULT_PATHS.corpus / "dead_letters_candidates.csv")
    parser.add_argument("--status", default="dead", help="requeue source status")
    parser.add_argument("--reset-attempts", action="store_true")
    parser.add_argument("--all", action="store_true",
                        help="reset-orphans: also recover live leases")
    args = parser.parse_args()

    conn = state.open_db(args.db)
    state.init_db(conn)

    if args.command == "status":
        print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))
        print(f"dead_letters: {len(state.dead_letters(conn))}")
        return 0
    if args.command == "sweep":
        candidates = state.sweep_exhausted(conn, max_attempts=args.max_attempts)
        pages = state.sweep_exhausted_pages(conn, max_attempts=args.max_attempts)
        print(f"candidates swept to dead: {candidates}")
        print(f"pages swept to dead: {pages}")
        return 0
    if args.command == "dlq":
        count = state.export_dead_letters(conn, args.out)
        print(f"exported {count} dead candidates -> {args.out}")
        return 0
    if args.command == "requeue":
        count = state.requeue(conn, status=args.status, reset_attempts=args.reset_attempts)
        print(f"requeued {count} candidates from status={args.status}")
        return 0
    if args.command == "reset-orphans":
        candidates = state.reset_orphaned(conn, force=args.all)
        pages = state.reset_orphaned_pages(conn, force=args.all)
        scope = "all" if args.all else "expired"
        print(f"reset {candidates} candidates and {pages} pages ({scope} leases)")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
