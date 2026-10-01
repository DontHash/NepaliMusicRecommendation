"""Rebuild the corpus with the fixed cleaner and English-preserving gate.

Re-runs ``lyrics_pipeline`` over ``R_data/corpus/corpus_raw.csv`` (the
pre-pipeline collection, positional 1:1 with ``CSVs Dataset/corpus_final.csv``),
writes ``CSVs Dataset/corpus_final_v2.csv``, then refreshes
``music_rec_artifacts/cleaned_lyrics.csv`` in place while preserving existing
``song_id`` values so eval sets, labels, and embeddings stay addressable.

Songs are dropped only when the source text is unrecoverable (known-bad legacy
rows) or the fixed cleaner leaves too little content (``Config.min_tokens``).

Usage:
    python scripts/rebuild_corpus.py --dry-run --limit 50
    python scripts/rebuild_corpus.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lyrics_pipeline.pipeline import LyricsCleaningPipeline  # noqa: E402
from lyrics_pipeline.transliterator import NepaliTransliterator  # noqa: E402
from music_rec.config import Config, force_staging  # noqa: E402
from music_rec.tokenization import normalize_nfc, token_count  # noqa: E402

force_staging()  # corpus rebuild always reads/writes the staging layout
from scripts.audit_corpus_quality import KNOWN_BAD  # noqa: E402

V2_COLUMNS = [
    "category",
    "title_clean",
    "artist_clean",
    "lyrics_devanagari",
    "line_count",
    "char_count",
    "script_style_original",
    "script_style_cleaned",
    "transliterated",
    "source",
    "stage",
    "source_url",
]


def reconstruct_v1_mapping(v1_final: pd.DataFrame, min_tokens: int) -> list[int]:
    """Return the v1 corpus_final row index behind each existing song_id."""
    kept: list[int] = []
    seen_lyrics: set[str] = set()
    seen_keys: set[tuple[str, str]] = set()
    for index, row in v1_final.iterrows():
        lyrics = normalize_nfc(str(row["lyrics_devanagari"]))
        if not lyrics.strip():
            continue
        if lyrics in seen_lyrics:
            continue
        seen_lyrics.add(lyrics)
        key = (str(row["title_clean"]), str(row["artist_clean"]))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if token_count(lyrics) < min_tokens:
            continue
        kept.append(int(index))
    return kept


def build_v2(
    raw: pd.DataFrame,
    pipeline: LyricsCleaningPipeline,
) -> list:
    results = []
    for row in raw.itertuples():
        row_dict = {
            "Category": getattr(row, "Category", ""),
            "Title": getattr(row, "Title", ""),
            "Artist": getattr(row, "Artist", ""),
            "Lyrics": getattr(row, "Lyrics", ""),
        }
        extras = {
            "source": getattr(row, "source", ""),
            "stage": getattr(row, "stage", ""),
            "source_url": getattr(row, "source_url", ""),
        }
        results.append(pipeline.process_row(row_dict, extras))
    return results


def rebuild(
    config: Config,
    raw_path: Path,
    v1_final_path: Path,
    v1_cleaned_path: Path,
    limit: int | None,
    dry_run: bool,
    v2_final_out: Path,
    quarantine_out: Path,
    report_out: Path,
    cleaned_out: Path,
    assemble_only: bool = False,
) -> dict:
    v1_final = pd.read_csv(v1_final_path, encoding="utf-8").fillna("")
    v1_cleaned = pd.read_csv(v1_cleaned_path, encoding="utf-8").fillna("")
    kept_indices = reconstruct_v1_mapping(v1_final, config.min_tokens)
    if len(kept_indices) != len(v1_cleaned):
        sys.exit(
            f"v1 mapping mismatch: reconstructed {len(kept_indices)} rows but "
            f"cleaned_lyrics.csv has {len(v1_cleaned)}"
        )

    if assemble_only:
        if not v2_final_out.exists():
            sys.exit(f"assemble-only needs an existing {v2_final_out}")
        v2_final = pd.read_csv(v2_final_out, encoding="utf-8").fillna("")
        results = [
            SimpleNamespace(
                lyrics_devanagari=row.lyrics_devanagari,
                extras={
                    "source": row.source,
                    "stage": row.stage,
                    "source_url": row.source_url,
                },
                transliterated=bool(int(row.transliterated)),
                line_count=int(row.line_count),
            )
            for row in v2_final.itertuples()
        ]
        print(f"assembling from {v2_final_out} ({len(results)} rows)")
    else:
        raw = pd.read_csv(raw_path, encoding="utf-8").fillna("")
        if limit:
            raw = raw.head(limit)
        print(f"processing {len(raw)} raw rows with the fixed pipeline")
        pipeline = LyricsCleaningPipeline(transliterator=NepaliTransliterator())
        results = build_v2(raw, pipeline)

    rows_out: list[dict] = []
    drops: list[dict] = []
    changed: list[int] = []
    unchanged = 0
    line_delta = 0
    processed = 0
    for song_id, final_index in enumerate(kept_indices):
        if final_index >= len(results):
            break
        processed += 1
        result = results[final_index]
        v1_row = v1_cleaned.iloc[song_id]
        text = result.lyrics_devanagari
        tokens = token_count(text)
        old_lines = len([line for line in str(v1_row["lyrics"]).splitlines() if line.strip()])
        new_lines = len([line for line in text.splitlines() if line.strip()])
        line_delta += new_lines - old_lines
        reason = KNOWN_BAD.get(int(v1_row["song_id"]), "")
        if not reason and (not text.strip() or tokens < config.min_tokens or new_lines < 3):
            reason = (
                f"cleaned_short: {new_lines} lines, {tokens} tokens after cleaning"
            )
        if reason:
            drops.append(
                {
                    "song_id": int(v1_row["song_id"]),
                    "title": v1_row["title"],
                    "artist": v1_row["artist"],
                    "source": result.extras.get("source", ""),
                    "reason": reason,
                    "v1_lines": old_lines,
                    "v2_lines": new_lines,
                    "v2_tokens": tokens,
                }
            )
            continue
        if str(v1_row["lyrics"]) != text:
            changed.append(int(v1_row["song_id"]))
        else:
            unchanged += 1
        rows_out.append(
            {
                "song_id": int(v1_row["song_id"]),
                "title": v1_row["title"],
                "artist": v1_row["artist"],
                "category": v1_row["category"],
                "lyrics": text,
                "token_count": tokens,
            }
        )

    v2_frame = pd.DataFrame(rows_out)
    report = {
        "raw_rows": int(len(v2_final)) if assemble_only else int(len(raw)),
        "mapped_songs": int(processed),
        "kept": int(len(v2_frame)),
        "dropped": int(len(drops)),
        "text_changed": int(len(changed)),
        "text_unchanged": int(unchanged),
        "line_delta": int(line_delta),
        "transliterated_rows": int(sum(1 for result in results if result.transliterated)),
        "drops": drops,
        "processed_song_ids": [int(value) for value in v2_frame.get("song_id", [])],
    }

    if not dry_run:
        v2_rows = []
        for result in results if not assemble_only else []:
            extras = result.extras
            v2_rows.append(
                {
                    "category": result.category,
                    "title_clean": result.title_clean,
                    "artist_clean": result.artist_clean,
                    "lyrics_devanagari": result.lyrics_devanagari,
                    "line_count": result.line_count,
                    "char_count": result.char_count,
                    "script_style_original": result.script_style_original,
                    "script_style_cleaned": result.script_style_cleaned,
                    "transliterated": int(result.transliterated),
                    "source": extras.get("source", ""),
                    "stage": extras.get("stage", ""),
                    "source_url": extras.get("source_url", ""),
                }
            )
        v2_final_out.parent.mkdir(parents=True, exist_ok=True)
        if assemble_only:
            print(f"kept existing {v2_final_out}")
        else:
            pd.DataFrame(v2_rows, columns=V2_COLUMNS).to_csv(
                v2_final_out, index=False, encoding="utf-8"
            )

        tmp = cleaned_out.with_suffix(".csv.tmp")
        cleaned_out.parent.mkdir(parents=True, exist_ok=True)
        v2_frame.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, cleaned_out)

        pd.DataFrame(drops).to_csv(quarantine_out, index=False, encoding="utf-8")
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if assemble_only:
            print("kept existing corpus_final_v2.csv")
        else:
            print(f"wrote {v2_final_out}")
        print(f"wrote {cleaned_out}")
        print(f"wrote {quarantine_out}")
        print(f"wrote {report_out}")

    print(f"mapped songs       {report['mapped_songs']}")
    print(f"kept               {report['kept']}")
    print(f"dropped            {report['dropped']}")
    print(f"text changed       {report['text_changed']}")
    print(f"text unchanged     {report['text_unchanged']}")
    print(f"line delta         {report['line_delta']}")
    for drop in drops[:20]:
        print(
            f"  drop {drop['song_id']:5d} {drop['title'][:40]:40s} "
            f"{drop['reason'][:60]}"
        )
    return report


def main() -> None:
    config = Config()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=PROJECT_ROOT / "R_data" / "corpus" / "corpus_raw.csv",
    )
    parser.add_argument(
        "--v1-final",
        type=Path,
        default=PROJECT_ROOT / "CSVs Dataset" / "corpus_final.csv",
    )
    parser.add_argument(
        "--cleaned-v1",
        type=Path,
        default=config.cleaned_lyrics_csv,
        help="Baseline cleaned_lyrics used for song_id mapping and diffing",
    )
    parser.add_argument(
        "--cleaned-out",
        type=Path,
        default=config.cleaned_lyrics_csv,
        help="Where the rebuilt cleaned_lyrics.csv is written",
    )
    parser.add_argument(
        "--v2-final-out",
        type=Path,
        default=PROJECT_ROOT / "CSVs Dataset" / "corpus_final_v2.csv",
    )
    parser.add_argument(
        "--quarantine-out",
        type=Path,
        default=config.artifacts_dir / "corpus_quarantine.csv",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=config.artifacts_dir / "corpus_rebuild_report.json",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--assemble-only",
        action="store_true",
        help="Skip the pipeline and rebuild cleaned_lyrics from corpus_final_v2.csv",
    )
    args = parser.parse_args()

    rebuild(
        config,
        args.raw,
        args.v1_final,
        args.cleaned_v1,
        args.limit,
        args.dry_run,
        args.v2_final_out,
        args.quarantine_out,
        args.report,
        args.cleaned_out,
        assemble_only=args.assemble_only,
    )


if __name__ == "__main__":
    main()
