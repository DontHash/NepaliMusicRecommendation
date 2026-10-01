"""Publish the staging artifact set as a version and point serving at it.

  python scripts/publish_artifacts.py [--version ID] [--keep 3] [--dry-run] [--list]

Builds the manifest for the staging files, copies them into
music_rec_artifacts/versions/<version-id>/ (verified after copy), then swaps
music_rec_artifacts/current.json atomically. Readers resolve artifact paths
through the pointer; roll back with scripts/rollback_artifacts.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.publish import (  # noqa: E402
    DEFAULT_KEEP,
    default_pointer_path,
    list_versions,
    publish_artifacts,
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
    parser.add_argument("--version", default=None, help="explicit version id")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP,
                        help="number of version directories to retain")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and check the manifest without copying or swapping")
    parser.add_argument("--list", action="store_true", help="list versions and exit")
    args = parser.parse_args()

    pointer_path = args.pointer or default_pointer_path(args.root)
    if args.list:
        _print_versions(pointer_path)
        return 0

    from music_rec.config import Config

    result = publish_artifacts(
        args.root, pointer_path, version=args.version, keep=args.keep,
        dry_run=args.dry_run, config=Config(),
    )
    verb = "would publish" if result["dry_run"] else "published"
    print(f"{verb} {result['version']} -> {result['destination']}")
    print(f"  artifacts copied : {len(result['copied'])} "
          f"({result['bytes'] / 1e6:.1f} MB)")
    if result["missing_optional"]:
        print(f"  optional missing : {', '.join(result['missing_optional'])}")
    if result["pruned"]:
        print(f"  pruned           : {', '.join(result['pruned'])}")
    print(f"  pointer          : {result['pointer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
