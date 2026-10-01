"""Dataset validation against the contracts in ``data_engineering.schemas``.

Usage:
  python -m data_engineering.validate --schema cleaned_lyrics music_rec_artifacts/cleaned_lyrics.csv
  python scripts/validate_datasets.py            # all production datasets
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:  # allow `python data_engineering/validate.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_engineering.schemas import SCHEMAS, Column, Schema, get_schema  # noqa: E402

MAX_EXAMPLES = 5


def _examples(mask) -> list[int]:
    return [int(i) for i in mask[mask].index[:MAX_EXAMPLES]]


def _is_numeric(series: pd.Series) -> bool:
    if pd.api.types.is_numeric_dtype(series):
        return True
    try:
        pd.to_numeric(series)
        return True
    except (ValueError, TypeError):
        return False


def _coerce_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series.astype("float64")
    return pd.to_numeric(series, errors="coerce")


def _null_mask(series: pd.Series, spec: Column) -> pd.Series:
    mask = series.isna()
    if spec.strip:
        mask = mask | series.astype(str).str.strip().eq("")
    return mask


def _check_column(df: pd.DataFrame, name: str, spec: Column, errors: list[dict]) -> None:
    series = df[name]
    null_mask = _null_mask(series, spec)
    if int(null_mask.sum()) and not spec.nullable:
        errors.append({
            "column": name, "check": "not_null", "count": int(null_mask.sum()),
            "examples": _examples(null_mask),
        })
    valid = series[~null_mask]
    if valid.empty:
        return

    if spec.dtype in {"int", "float"}:
        if not _is_numeric(valid):
            errors.append({"column": name, "check": "dtype_numeric", "count": int(valid.shape[0]),
                           "examples": _examples(pd.Series(True, index=valid.index))})
            return
        numeric = _coerce_numeric(valid)
        if spec.dtype == "int":
            non_integral = numeric % 1 != 0
            if int(non_integral.sum()):
                errors.append({"column": name, "check": "dtype_int", "count": int(non_integral.sum()),
                               "examples": _examples(non_integral)})
        if spec.minimum is not None:
            below = numeric < spec.minimum
            if int(below.sum()):
                errors.append({"column": name, "check": f"min>={spec.minimum}", "count": int(below.sum()),
                               "examples": _examples(below)})
        if spec.maximum is not None:
            above = numeric > spec.maximum
            if int(above.sum()):
                errors.append({"column": name, "check": f"max<={spec.maximum}", "count": int(above.sum()),
                               "examples": _examples(above)})

    if spec.allowed is not None:
        allowed_str = {str(value) for value in spec.allowed}
        bad = valid.map(lambda value: value not in spec.allowed and str(value) not in allowed_str)
        if int(bad.sum()):
            errors.append({"column": name, "check": "allowed", "count": int(bad.sum()),
                           "examples": _examples(bad)})

    if spec.pattern is not None:
        bad = ~valid.astype(str).str.fullmatch(spec.pattern)
        if int(bad.sum()):
            errors.append({"column": name, "check": f"pattern:{spec.pattern}", "count": int(bad.sum()),
                           "examples": _examples(bad)})


def validate_frame(frame: pd.DataFrame, schema: Schema) -> dict:
    report: dict = {
        "dataset": schema.name,
        "schema_version": schema.version,
        "rows": int(len(frame)),
        "passed": True,
        "errors": [],
        "warnings": [],
    }
    missing = [name for name in schema.columns if name not in frame.columns]
    if missing:
        report["errors"].append({"column": None, "check": "missing_columns",
                                 "count": len(missing), "examples": missing})
    extra = [name for name in frame.columns if name not in schema.columns]
    if extra:
        report["warnings"].append({"column": None, "check": "extra_columns",
                                   "count": len(extra), "examples": extra})

    for name, spec in schema.columns.items():
        if name in frame.columns:
            _check_column(frame, name, spec, report["errors"])

    primary_key = schema.primary_key
    if primary_key and primary_key in frame.columns:
        nulls = _null_mask(frame[primary_key], schema.columns[primary_key])
        if int(nulls.sum()):
            report["errors"].append({"column": primary_key, "check": "pk_not_null",
                                     "count": int(nulls.sum()), "examples": _examples(nulls)})
        duplicated = frame[primary_key].duplicated(keep=False) & ~nulls
        if int(duplicated.sum()):
            report["errors"].append({"column": primary_key, "check": "pk_unique",
                                     "count": int(duplicated.sum()), "examples": _examples(duplicated)})

    report["passed"] = not report["errors"]
    return report


def validate_file(path: Path, schema: Schema, *, encoding: str = "utf-8") -> dict:
    try:
        string_columns = {name: "string" for name, spec in schema.columns.items() if spec.dtype == "str"}
        frame = pd.read_csv(path, encoding=encoding, dtype=string_columns, low_memory=False)
    except FileNotFoundError:
        return {"dataset": schema.name, "schema_version": schema.version, "rows": 0,
                "passed": False, "errors": [{"column": None, "check": "file_missing",
                                              "count": 1, "examples": [str(path)]}],
                "warnings": []}
    report = validate_frame(frame, schema)
    report["path"] = str(path)
    return report


def format_report(report: dict) -> str:
    status = "PASS" if report["passed"] else "FAIL"
    lines = [f"[{status}] {report['dataset']} v{report['schema_version']} "
             f"({report.get('path', '')}) rows={report['rows']}"]
    for error in report["errors"]:
        lines.append(f"    error {error['check']} column={error['column']} "
                     f"count={error['count']} examples={error['examples']}")
    for warning in report["warnings"]:
        lines.append(f"    warn  {warning['check']} column={warning['column']} "
                     f"count={warning['count']} examples={warning['examples']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one dataset against its contract.")
    parser.add_argument("--schema", required=True, choices=sorted(SCHEMAS))
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", help="print the machine-readable report")
    args = parser.parse_args()
    report = validate_file(args.path, get_schema(args.schema))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
