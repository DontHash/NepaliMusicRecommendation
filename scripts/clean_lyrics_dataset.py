"""CLI for cleaning Lyrics_Dataset.csv."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.pipeline import LyricsCleaningPipeline
from lyrics_pipeline.transliterator import NepaliTransliterator


def parse_args() -> argparse.Namespace:
    project_root = PROJECT_ROOT
    default_input = project_root / "CSVs Dataset" / "Lyrics_Dataset.csv"
    default_output = project_root / "CSVs Dataset" / "Lyrics_Dataset_cleaned.csv"
    default_report = project_root / "CSVs Dataset" / "Lyrics_Dataset_cleaning_report.json"

    parser = argparse.ArgumentParser(description="Clean and transliterate Nepali lyrics CSV data.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input Genius lyrics CSV")
    parser.add_argument("--output", type=Path, default=default_output, help="Output cleaned CSV")
    parser.add_argument("--report", type=Path, default=default_report, help="JSON cleaning report")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Char-transformer checkpoint .pt")
    parser.add_argument("--vocab", type=Path, default=None, help="Vocabulary .pkl file")
    parser.add_argument(
        "--skip-transliteration",
        action="store_true",
        help="Only clean metadata/noise; do not romanize to Devanagari",
    )
    parser.add_argument("--beam-size", type=int, default=5, help="Beam size for transliteration")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transliterator = NepaliTransliterator(
        checkpoint_path=args.checkpoint,
        vocab_path=args.vocab,
        beam_size=args.beam_size,
    )

    pipeline = LyricsCleaningPipeline(
        transliterator=transliterator,
        transliterate=not args.skip_transliteration,
    )
    summary = pipeline.process_file(args.input, args.output, args.report)

    print(f"Wrote cleaned dataset: {args.output}")
    print(f"Wrote report: {args.report}")
    print(f"Rows processed: {summary['total_rows']}")
    print(f"Rows still containing roman letters: {summary['rows_still_with_roman_letters']}")
    print(f"Rows transliterated: {summary['transliterated_rows']}")
    if summary["rows_still_with_roman_letters"] and not transliterator.available:
        print(
            "Note: transliteration model not found. Re-run with checkpoint/vocab from Kaggle "
            "or pass --checkpoint and --vocab explicitly."
        )


if __name__ == "__main__":
    main()
