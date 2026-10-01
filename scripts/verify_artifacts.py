"""Verify the serving artifact set against its manifest.

  python scripts/verify_artifacts.py [--manifest PATH] [--skip-hashes] [--json]

Re-measures every artifact (SHA-256, size, rows, shapes, index metadata) and
every provenance input, then re-runs the cross-artifact consistency checks.
Missing optional artifacts (window/audio vectors are not committed) warn;
missing required artifacts, hash drift, schema-version drift and inconsistent
row/shape counts fail with a nonzero exit code. This is the gate CI runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.artifacts import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    format_verify_report,
    verify_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path,
                        default=PROJECT_ROOT / DEFAULT_MANIFEST_PATH)
    parser.add_argument("--skip-hashes", action="store_true",
                        help="re-check metadata/consistency without re-hashing files")
    parser.add_argument("--json", action="store_true", help="print the machine-readable report")
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"manifest not found: {args.manifest}\n"
              f"run python scripts/build_artifact_manifest.py first", file=sys.stderr)
        return 1

    report = verify_manifest(PROJECT_ROOT, manifest, check_hashes=not args.skip_hashes)
    report["manifest_path"] = str(args.manifest)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_verify_report(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
