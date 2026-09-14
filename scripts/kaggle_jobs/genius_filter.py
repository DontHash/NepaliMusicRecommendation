"""Kaggle kernel: filter the language-labeled Genius lyrics dump to Nepali rows.

Runs on Kaggle with the dataset
``carlosgdcj/genius-song-lyrics-with-language-information`` mounted at
/kaggle/input. Writes ``genius_ne.csv`` + ``filter_report.json`` to /kaggle/working.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

INPUT_DIR = Path("/kaggle/input/genius-song-lyrics-with-language-information")
OUT_DIR = Path("/kaggle/working")
TARGET_CODES = {"ne", "nep"}
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
CHUNK_SIZE = 200_000


def find_csv() -> Path:
    roots = [INPUT_DIR, Path("/kaggle/input")]
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates = sorted(root.rglob("*.csv"))
            if candidates:
                break
    if not candidates:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        listing = []
        input_root = Path("/kaggle/input")
        if input_root.exists():
            listing = [str(p) for p in list(input_root.rglob("*"))[:300]]
        (OUT_DIR / "input_listing.json").write_text(json.dumps(listing, indent=2), encoding="utf-8")
        print("\n".join(listing[:50]))
        raise SystemExit(f"no CSV found under /kaggle/input ({len(listing)} entries listed)")
    return max(candidates, key=lambda p: p.stat().st_size)


def pick_col(columns: list[str], names: tuple[str, ...]) -> str | None:
    lower = {c.lower(): c for c in columns}
    for name in names:
        if name in lower:
            return lower[name]
    for col in columns:
        lowered = col.lower()
        if any(name in lowered for name in names):
            return col
    return None


def devanagari_ratio(text: str) -> float:
    text = str(text)
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if DEVANAGARI_RE.match(c)) / len(letters)


def main() -> None:
    csv_path = find_csv()
    header = pd.read_csv(csv_path, nrows=0)
    columns = list(header.columns)
    language_cols = [c for c in columns if "language" in c.lower()]
    id_col = pick_col(columns, ("id",))
    if not language_cols:
        raise SystemExit(f"no language columns found in {columns}")

    matches: list[pd.DataFrame] = []
    total = 0
    code_counts: Counter = Counter()
    for chunk in pd.read_csv(csv_path, chunksize=CHUNK_SIZE, low_memory=False):
        total += len(chunk)
        for col in language_cols:
            code_counts.update(chunk[col].astype(str).str.lower().str.strip().value_counts().to_dict())
        mask = pd.Series(False, index=chunk.index)
        for col in language_cols:
            mask |= chunk[col].astype(str).str.lower().str.strip().isin(TARGET_CODES)
        if mask.any():
            part = chunk[mask].copy()
            part["devanagari_ratio"] = part["lyrics"].map(devanagari_ratio) if "lyrics" in part.columns else 0.0
            matches.append(part)

    if matches:
        result = pd.concat(matches, ignore_index=True)
        if id_col:
            result = result.drop_duplicates(subset=[id_col])
    else:
        result = pd.DataFrame(columns=columns + ["devanagari_ratio"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_DIR / "genius_ne.csv", index=False)
    report = {
        "input_csv": str(csv_path),
        "rows_scanned": total,
        "rows_matched": len(result),
        "language_top": dict(code_counts.most_common(25)),
        "devanagari_ratio_mean": float(result["devanagari_ratio"].mean()) if len(result) else 0.0,
        "devanagari_ratio_below_0_5": int((result["devanagari_ratio"] < 0.5).sum()) if len(result) else 0,
    }
    (OUT_DIR / "filter_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
