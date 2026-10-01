"""CLI: append new corpus songs to the text artifacts (incremental, DE6).

Thin wrapper over ``music_rec.incremental.append_new_songs``; see
docs/DE6_INCREMENTAL_PLAN.md.

Run:
  python scripts/audio/update_text_artifacts.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audio import utils  # noqa: E402
from music_rec.config import force_staging  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    args = parser.parse_args()

    from music_rec.incremental import append_new_songs

    force_staging()  # incremental updater always reads/writes the staging layout
    report = append_new_songs(
        device=args.device,
        report_path=utils.AUDIO_DATA_DIR / "text_artifacts_update_report.json",
    )
    print(json.dumps(report, indent=2))
    if report["status"] == "appended":
        print("next: re-run evals and scripts/build_mood_vectors.py")


if __name__ == "__main__":
    main()
