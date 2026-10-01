"""Build the serving artifact manifest.

  python scripts/build_artifact_manifest.py [--out music_rec_artifacts/artifact_manifest.json]

Refuses to write a manifest when the artifact set is internally inconsistent
(row/shape/id mismatches), so the committed manifest always describes a coherent
set. See data_engineering/artifacts.py for the registry and checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.artifacts import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    build_manifest,
    format_manifest_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=PROJECT_ROOT / DEFAULT_MANIFEST_PATH,
                        help="manifest output path")
    args = parser.parse_args()

    from music_rec.config import Config

    manifest = build_manifest(PROJECT_ROOT, config=Config())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(format_manifest_summary(manifest))
    print(f"written {args.out} at {datetime.now(timezone.utc).isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
