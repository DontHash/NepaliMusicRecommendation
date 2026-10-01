"""Roll serving back to a retained artifact version.

  python scripts/rollback_artifacts.py --list
  python scripts/rollback_artifacts.py --previous [--verify]
  python scripts/rollback_artifacts.py --to <version-id> [--verify]

Rollback is a pointer swap: the target version directory already exists and is
untouched, so the operation is instant. ``--verify`` hash-checks the target
version before switching; the default only checks that the version directory
and its manifest exist.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.publish import (  # noqa: E402
    default_pointer_path,
    list_versions,
    previous_version,
    rollback_artifacts,
)


def _print_versions(pointer_path: Path) -> None:
    versions = list_versions(pointer_path)
    if not versions:
        print(f"no published versions under {pointer_path.parent}")
        return
    print(f"versions under {pointer_path.parent}:")
    for item in versions:
        marker = "*" if item["current"] else " "
        print(f"  {marker} {item['version']:<28} artifacts={item['artifacts']:<3} "
              f"published={item['published_at']} git={item['git_sha']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--pointer", type=Path, default=None,
                        help="pointer path (default <root>/music_rec_artifacts/current.json)")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--to", metavar="VERSION", help="version id to roll back to")
    target.add_argument("--previous", action="store_true",
                        help="roll back to the newest version before the current one")
    parser.add_argument("--verify", action="store_true",
                        help="hash-verify the target version before switching")
    parser.add_argument("--list", action="store_true", help="list versions and exit")
    args = parser.parse_args()

    pointer_path = args.pointer or default_pointer_path(args.root)
    if args.list:
        _print_versions(pointer_path)
        return 0

    version = args.to
    if args.previous:
        version = previous_version(pointer_path)
        if version is None:
            print("no earlier version to roll back to", file=sys.stderr)
            return 1
    if not version:
        parser.error("one of --to/--previous/--list is required")

    try:
        result = rollback_artifacts(pointer_path, version, verify=args.verify)
    except (FileNotFoundError, ValueError) as error:
        print(f"rollback failed: {error}", file=sys.stderr)
        return 1

    print(f"rolled back {result['previous']} -> {result['version']}")
    print(f"  version dir : {result['destination']}")
    print(f"  pointer     : {result['pointer']}")
    _print_versions(pointer_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
