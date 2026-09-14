"""Regression-diff two transliterator checkpoints on the full corpus.

Run after training ``new_char_transformer_best.pt`` on Kaggle to see exactly
what changed vs the old ``char_transformer_442.pt``: which songs, which words,
and how long each model took.

Usage:
    python scripts/compare_transliterators.py
    python scripts/compare_transliterators.py --limit 50
    python scripts/compare_transliterators.py --new-checkpoint /path/to/new.pt
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.cleaner import clean_lyrics_body  # noqa: E402
from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402

DEVANAGARI_WORD_RE = re.compile(r"[\u0900-\u097F]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two transliterator checkpoints.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "CSVs Dataset" / "Lyrics_Dataset.csv",
        help="Raw lyrics CSV (same schema as Lyrics_Dataset.csv)",
    )
    parser.add_argument(
        "--old-checkpoint",
        type=Path,
        default=PROJECT_ROOT / "char_transformer_442.pt",
    )
    parser.add_argument("--old-vocab", type=Path, default=PROJECT_ROOT / "char_vocab.pkl")
    parser.add_argument(
        "--new-checkpoint",
        type=Path,
        default=PROJECT_ROOT / "new_char_transformer_best.pt",
    )
    parser.add_argument(
        "--new-vocab", type=Path, default=PROJECT_ROOT / "new_char_vocab.pkl"
    )
    parser.add_argument(
        "--lexicon-csv",
        type=Path,
        default=PROJECT_ROOT / "CSVs Dataset" / "Lyrics_Dataset_final.csv",
        help="All-Devanagari corpus used for the word-coverage proxy",
    )
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "compare_report.json")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only process the first N songs (0 = all)",
    )
    parser.add_argument("--sample-diffs", type=int, default=10, help="Diff samples printed")
    return parser.parse_args()


def build_lexicon(csv_path: Path) -> Counter:
    if not csv_path.exists():
        return Counter()
    words: Counter = Counter()
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            words.update(DEVANAGARI_WORD_RE.findall(row.get("lyrics_devanagari", "")))
    return words


def coverage(unique_words: set[str], lexicon: Counter) -> float:
    if not unique_words:
        return 0.0
    hits = sum(1 for word in unique_words if word in lexicon)
    return hits / len(unique_words)


def main() -> None:
    args = parse_args()

    if not args.new_checkpoint.exists():
        print(
            f"New checkpoint not found: {args.new_checkpoint}\n"
            "Train it first (NewTransliterate.ipynb on Kaggle) or pass "
            "--new-checkpoint/--new-vocab explicitly."
        )
        sys.exit(1)

    old = NepaliTransliterator(
        checkpoint_path=args.old_checkpoint, vocab_path=args.old_vocab
    )
    new = NepaliTransliterator(
        checkpoint_path=args.new_checkpoint, vocab_path=args.new_vocab
    )
    if not old.available or not new.available:
        print("One of the two models failed to load; check checkpoint/vocab paths.")
        sys.exit(2)

    with open(args.input, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]
    print(
        f"Comparing {len(rows)} songs | old={args.old_checkpoint.name} "
        f"new={args.new_checkpoint.name}"
    )

    lexicon = build_lexicon(args.lexicon_csv)
    changed_words: Counter = Counter()
    diffs: list[dict] = []
    old_unique: set[str] = set()
    new_unique: set[str] = set()
    total_old = total_new = 0.0

    for index, row in enumerate(rows, start=1):
        cleaned, _ = clean_lyrics_body(row.get("Lyrics") or "", row.get("Title") or "", row.get("Artist") or "")
        if not cleaned:
            continue

        start = time.perf_counter()
        old_out = old.transliterate_text(cleaned)
        total_old += time.perf_counter() - start
        start = time.perf_counter()
        new_out = new.transliterate_text(cleaned)
        total_new += time.perf_counter() - start

        old_words = set(DEVANAGARI_WORD_RE.findall(old_out))
        new_words = set(DEVANAGARI_WORD_RE.findall(new_out))
        old_unique |= old_words
        new_unique |= new_words

        if old_out != new_out:
            added = new_words - old_words
            removed = old_words - new_words
            for word in added | removed:
                changed_words[word] += 1
            diffs.append(
                {
                    "row": index,
                    "title": row.get("Title", ""),
                    "artist": row.get("Artist", ""),
                    "old": old_out,
                    "new": new_out,
                    "added_words": sorted(added),
                    "removed_words": sorted(removed),
                }
            )

    print(f"\nRows processed: {len(rows)}")
    print(f"Rows with different output: {len(diffs)}")
    print(f"Time: old={total_old:.1f}s  new={total_new:.1f}s")
    print(
        f"Unique Devanagari words: old={len(old_unique)}  new={len(new_unique)}"
    )
    if lexicon:
        print(
            f"Corpus coverage (higher = better): "
            f"old={coverage(old_unique, lexicon):.3f}  "
            f"new={coverage(new_unique, lexicon):.3f}"
        )

    print(f"\nWords that changed most often between models:")
    for word, count in changed_words.most_common(25):
        print(f"  {word:10s} {count}")

    if diffs:
        print(f"\nFirst {min(args.sample_diffs, len(diffs))} differing rows:")
        for diff in diffs[: args.sample_diffs]:
            print(f"  [{diff['row']}] {diff['title']} — {diff['artist']}")
            old_first = " / ".join(diff["old"].splitlines()[:2])
            new_first = " / ".join(diff["new"].splitlines()[:2])
            print(f"    old: {old_first}")
            print(f"    new: {new_first}")

    report = {
        "rows_processed": len(rows),
        "rows_differ": len(diffs),
        "time_seconds": {"old": total_old, "new": total_new},
        "unique_words": {"old": len(old_unique), "new": len(new_unique)},
        "coverage": (
            {"old": coverage(old_unique, lexicon), "new": coverage(new_unique, lexicon)}
            if lexicon
            else None
        ),
        "changed_words_top": changed_words.most_common(50),
        "samples": diffs[:20],
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport written to {args.output}")


if __name__ == "__main__":
    main()
