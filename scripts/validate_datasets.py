"""Validate every production dataset against its declared contract.

  python scripts/validate_datasets.py            # skips datasets not present
  python scripts/validate_datasets.py --strict   # missing dataset = failure

Writes music_rec_artifacts/data_contracts_report.json.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data_engineering.schemas import get_schema  # noqa: E402
from data_engineering.validate import format_report, validate_file  # noqa: E402

REPORT_PATH = PROJECT_ROOT / "music_rec_artifacts" / "data_contracts_report.json"


def production_datasets() -> dict[str, Path]:
    from music_rec.config import Config

    config = Config()
    corpus_v3 = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v3.csv"
    corpus_v2 = PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv"
    corpus = corpus_v3 if corpus_v3.exists() else corpus_v2

    label_candidates = sorted(
        Path(path) for path in glob.glob(str(PROJECT_ROOT / "R_data" / "raw" / "gemini" / "*" / "labels_merged.csv"))
    )
    datasets = {
        "cleaned_lyrics": config.cleaned_lyrics_csv,
        "corpus_rows": corpus,
        "sentiment_scores": config.sentiment_scores_csv,
        "audio_tracks": config.audio_dir / "audio_tracks.csv",
        "audio_manifest": config.audio_dir / "audio_manifest.csv",
        "audio_track_matches": config.audio_dir / "audio_track_matches.csv",
        "audio_file_map": config.audio_dir / "audio_file_map.csv",
        "audio_new_songs": config.audio_dir / "audio_new_songs_v2.csv",
    }
    if label_candidates:
        datasets["mood_labels"] = label_candidates[-1]
    return datasets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="missing dataset counts as failure")
    args = parser.parse_args()

    results = []
    for name, path in production_datasets().items():
        if not path.exists():
            results.append({"dataset": name, "schema_version": get_schema(name).version, "rows": 0,
                            "passed": not args.strict, "missing": True, "path": str(path),
                            "errors": [], "warnings": []})
            continue
        results.append(validate_file(path, get_schema(name)))

    for report in results:
        print(format_report(report) if not report.get("missing") else
              f"[SKIP] {report['dataset']} (missing: {report.get('path')})")

    failed = [report for report in results if not report["passed"]]
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strict": args.strict,
        "datasets": len(results),
        "failed": len(failed),
        "results": results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{len(results) - len(failed)}/{len(results)} datasets valid -> {REPORT_PATH}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
