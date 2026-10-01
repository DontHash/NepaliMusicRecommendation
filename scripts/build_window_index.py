"""Build and persist the window ANN side-index (window_index.faiss).

Usage:
  python scripts/build_window_index.py            # respects window_ann auto/threshold
  python scripts/build_window_index.py --force    # build regardless of threshold
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

from music_rec.config import Config  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    import numpy as np

    from music_rec.window_search import ann_enabled, build_window_index

    config = Config()
    if not (config.window_vectors_npy.exists() and config.window_owners_npy.exists()):
        raise SystemExit("window artifacts missing; run scripts/run_music_rec.py embed first")
    n_windows = int(np.load(config.window_owners_npy).shape[0])
    if not args.force and not ann_enabled(config.window_ann, n_windows, config.window_ann_threshold):
        print(f"window ANN skipped: {n_windows} windows < threshold {config.window_ann_threshold}")
        return
    build_window_index(
        config.window_vectors_npy,
        config.window_index_path,
        hnsw_m=config.index_hnsw_m,
        ef_construction=config.index_ef_construction,
        ef_search=config.index_ef_search,
    )
    report = {
        "windows": n_windows,
        "path": str(config.window_index_path),
        "hnsw_m": config.index_hnsw_m,
        "ef_construction": config.index_ef_construction,
        "ef_search": config.index_ef_search,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (config.artifacts_dir / "window_index_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
