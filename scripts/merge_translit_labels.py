"""Merge teacher-label runs (or shards) into one canonical labels file.

Reads ``R_data/raw/gemini/<source>/labels.jsonl`` for every source, deduplicates
by ``line_id``, and writes the canonical ``labels.jsonl`` + ``labels.csv`` for
the output run. Also verifies that no merged line is reserved for evaluation
(the held-out review lines and gold v2 additions), which is the failure mode
that would silently turn the gold metric into a memorisation check.

Usage:
    python scripts/merge_translit_labels.py --out-run translit_corpus_v1 \
        --sources translit_corpus_v1 translit_corpus_v2_shard0 translit_corpus_v2_shard1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api_translit_label import held_out_romans, normalize  # noqa: E402

OUT_ROOT = PROJECT_ROOT / "R_data" / "raw" / "gemini"
FIELDNAMES = ["line_id", "roman", "devanagari", "confidence", "source"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-run", default="translit_corpus_v1")
    parser.add_argument("--sources", nargs="*", default=[])
    return parser.parse_args()


def read_jsonl(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if not path.exists():
        return records
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
                records[str(record["line_id"])] = record
            except (json.JSONDecodeError, KeyError):
                continue
    return records


def main() -> int:
    args = parse_args()
    sources = list(dict.fromkeys([args.out_run, *args.sources]))
    merged: dict[str, dict] = {}
    per_source: dict[str, dict] = {}
    for name in sources:
        records = read_jsonl(OUT_ROOT / name / "labels.jsonl")
        new = 0
        for line_id, record in records.items():
            if line_id not in merged:
                merged[line_id] = record
                new += 1
        per_source[name] = {"rows": len(records), "new": new}

    if not merged:
        sys.exit("no labels found in any source")

    reserved = held_out_romans()
    leaked = [
        record["line_id"]
        for record in merged.values()
        if normalize(record.get("roman") or "") in reserved
    ]

    out_dir = OUT_ROOT / args.out_run
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [merged[key] for key in sorted(merged)]
    with open(out_dir / "labels.jsonl", "w", encoding="utf-8") as handle:
        for record in rows:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    with open(out_dir / "labels.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "out_run": args.out_run,
        "sources": per_source,
        "merged_rows": len(merged),
        "reserved_lines": len(reserved),
        "reserved_leaks": leaked[:20],
        "leak_count": len(leaked),
    }
    (out_dir / "merge_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"sources: {json.dumps(per_source)}")
    print(f"merged rows: {len(merged)} -> {out_dir / 'labels.csv'}")
    print(f"evaluation-reserved lines: {len(reserved)} | leaks: {len(leaked)}")
    if leaked:
        print("  WARNING: reserved lines were labelled:")
        for record in rows:
            if record["line_id"] in leaked:
                print(f"    {record['line_id']} {record['roman'][:60]}")
    return 0 if not leaked else 1


if __name__ == "__main__":
    raise SystemExit(main())
