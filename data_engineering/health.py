"""Data health: freshness, quality budgets and row deltas per dataset.

Complements the DE1 schema contracts with *quality* gates: row-count floors,
duplication/coverage ceilings, freshness and row deltas against the previous
snapshot. The CLI is ``scripts/data_health.py``; CI runs it after dataset
validation so a budget breach fails the build.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from data_engineering.artifacts import DEFAULT_MANIFEST_PATH, verify_manifest
from data_engineering.schemas import get_schema
from data_engineering.validate import validate_file

DEFAULT_MAX_AGE_DAYS = 30.0
FRESHNESS_OVERRIDES: dict[str, float] = {
    "mood_labels": 90.0,
    "audio_tracks": 90.0,
    "audio_track_matches": 90.0,
    "audio_file_map": 90.0,
}
EVENTS_DB_RELATIVE = Path("R_data") / "state" / "events.sqlite"


@dataclass(frozen=True)
class Budget:
    metric: str
    minimum: float | None = None
    maximum: float | None = None
    derive: Callable[[dict, dict], float] | None = None


# --- metric extractors -------------------------------------------------------


def _generic_metrics(path: Path) -> dict:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        rows = sum(1 for row in reader if row)
    return {"rows": rows}


def _cleaned_metrics(path: Path) -> dict:
    frame = pd.read_csv(path, encoding="utf-8").fillna("")
    text = (frame["lyrics"].astype(str)
            .str.replace(r"\s+", " ", regex=True).str.strip().str.casefold())
    tokens = pd.to_numeric(frame["token_count"], errors="coerce")
    has_tokens = bool(tokens.notna().any())
    return {
        "rows": int(len(frame)),
        "duplicate_lyrics_share": float(text.duplicated().mean()) if len(frame) else 1.0,
        "empty_artist_share": (float((frame["artist"].astype(str).str.strip() == "").mean())
                               if len(frame) else 1.0),
        "empty_title_share": (float((frame["title"].astype(str).str.strip() == "").mean())
                              if len(frame) else 1.0),
        "avg_tokens": float(tokens.mean()) if len(frame) and has_tokens else 0.0,
        "min_tokens": int(tokens.min()) if len(frame) and has_tokens else 0,
    }


def _corpus_metrics(path: Path) -> dict:
    frame = pd.read_csv(path, encoding="utf-8")
    sources = int(frame["source"].astype(str).nunique()) if "source" in frame else 0
    return {"rows": int(len(frame)), "sources": sources}


def _audio_match_metrics(path: Path) -> dict:
    frame = pd.read_csv(path, encoding="utf-8", dtype=str).fillna("")
    matched = ((frame["match_song_id"].str.strip() != "")
               | (frame["new_id"].str.strip() != ""))
    return {"rows": int(len(frame)),
            "matched_share": float(matched.mean()) if len(frame) else 0.0}


METRICS: dict[str, Callable[[Path], dict]] = {
    "cleaned_lyrics": _cleaned_metrics,
    "corpus_rows": _corpus_metrics,
    "audio_track_matches": _audio_match_metrics,
}

BUDGETS: dict[str, list[Budget]] = {
    "cleaned_lyrics": [
        Budget("rows", minimum=4000),
        Budget("duplicate_lyrics_share", maximum=0.02),
        Budget("empty_artist_share", maximum=0.02),
        Budget("empty_title_share", maximum=0.005),
        Budget("avg_tokens", minimum=50.0),
        Budget("min_tokens", minimum=10),
    ],
    "corpus_rows": [
        Budget("rows", minimum=4000),
        Budget("sources", minimum=5),
    ],
    "sentiment_scores": [
        Budget("rows", minimum=4000),
        Budget("coverage", minimum=0.999,
               derive=lambda metrics, context: metrics["rows"]
               / max(context.get("cleaned_lyrics", {}).get("rows", metrics["rows"]), 1)),
    ],
    "mood_labels": [Budget("rows", minimum=3000)],
    "audio_tracks": [Budget("rows", minimum=3000)],
    "audio_track_matches": [
        Budget("rows", minimum=3000),
        Budget("matched_share", minimum=0.20),
    ],
    "audio_file_map": [Budget("rows", minimum=3000)],
    "audio_new_songs": [Budget("rows", minimum=10)],
}


# --- report construction -----------------------------------------------------


def events_health(path: Path) -> dict:
    """Freshness/size of the user-event feed (DE6), informational."""
    path = Path(path)
    if not path.exists():
        return {"status": "absent", "path": str(path)}
    try:
        connection = sqlite3.connect(str(path))
        try:
            total = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            last = connection.execute("SELECT MAX(ts) FROM events").fetchone()[0]
            last_24h = connection.execute(
                "SELECT COUNT(*) FROM events WHERE ts >= datetime('now', '-1 day')"
            ).fetchone()[0]
        finally:
            connection.close()
    except sqlite3.Error as error:
        return {"status": "error", "path": str(path), "error": str(error)}

    age_hours = None
    if last:
        try:
            parsed = datetime.fromisoformat(str(last))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age_hours = round((datetime.now(timezone.utc) - parsed).total_seconds() / 3600, 2)
        except ValueError:
            pass
    return {"status": "present", "path": str(path), "rows": int(total),
            "last_24h": int(last_24h), "last_ts": last, "age_hours": age_hours}


def artifact_health(root: Path) -> dict:
    manifest_path = Path(root) / DEFAULT_MANIFEST_PATH
    if not manifest_path.exists():
        return {"status": "missing", "path": str(manifest_path)}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError as error:
        return {"status": "fail", "path": str(manifest_path), "errors": [str(error)]}
    report = verify_manifest(Path(root), manifest, check_hashes=False)
    return {
        "status": "pass" if report["passed"] else "fail",
        "path": str(manifest_path),
        "version": manifest.get("version"),
        "git_sha": manifest.get("git_sha"),
        "errors": report["errors"][:5],
        "warnings": len(report.get("warnings", [])),
        "checks_passed": sum(1 for check in report["checks"] if check["passed"]),
        "checks": len(report["checks"]),
    }


def _read_last_history(history_path: Path | None) -> dict:
    if history_path is None or not Path(history_path).exists():
        return {}
    last = None
    with Path(history_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line)
                except ValueError:
                    continue
    return last or {}


def _append_history(history_path: Path, report: dict) -> None:
    history_path = Path(history_path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {"generated_at": report["generated_at"], "status": report["status"],
                "rows": {name: data.get("rows") for name, data in report["datasets"].items()}}
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def dataset_health(name: str, path: Path, *, max_age_days: float,
                   previous_rows: int | None = None) -> dict:
    path = Path(path)
    entry: dict = {"dataset": name, "path": str(path), "exists": path.exists()}
    if not path.exists():
        entry.update({"status": "missing", "rows": None, "contract": None,
                      "metrics": {}, "budgets": []})
        return entry

    stat = path.stat()
    entry["bytes"] = stat.st_size
    entry["age_days"] = round((time.time() - stat.st_mtime) / 86400, 2)
    entry["stale"] = entry["age_days"] > max_age_days

    metrics = METRICS.get(name, _generic_metrics)(path)
    entry["metrics"] = metrics
    entry["rows"] = metrics.get("rows")
    if previous_rows is not None and entry["rows"] is not None:
        entry["delta_rows"] = int(entry["rows"]) - int(previous_rows)

    contract = validate_file(path, get_schema(name))
    entry["contract"] = "pass" if contract["passed"] else "fail"
    if contract["passed"] is False:
        entry["contract_errors"] = contract["errors"][:3]
    entry["budgets"] = []
    entry["status"] = "green" if contract["passed"] else "red"
    return entry


def evaluate_budgets(metrics: dict, budgets: list[Budget],
                     context: dict | None = None) -> list[dict]:
    context = context or {}
    checks: list[dict] = []
    for budget in budgets:
        if budget.metric in metrics and metrics[budget.metric] is not None:
            value = metrics[budget.metric]
        elif budget.derive is not None:
            value = budget.derive(metrics, context)
        else:
            value = None
        passed = value is not None and (
            (budget.minimum is None or value >= budget.minimum)
            and (budget.maximum is None or value <= budget.maximum))
        checks.append({"metric": budget.metric,
                       "value": None if value is None else round(float(value), 4),
                       "min": budget.minimum, "max": budget.maximum, "passed": bool(passed)})
    return checks


def build_health_report(root: Path, datasets: dict[str, Path], *,
                        budgets: dict[str, list[Budget]] | None = None,
                        max_age_days: float = DEFAULT_MAX_AGE_DAYS,
                        freshness_overrides: dict[str, float] | None = None,
                        strict: bool = False, fail_on_stale: bool = False,
                        check_artifacts: bool = True,
                        history_path: Path | None = None,
                        events_db: Path | None = None) -> dict:
    root = Path(root)
    budgets = BUDGETS if budgets is None else budgets
    freshness_overrides = FRESHNESS_OVERRIDES if freshness_overrides is None else freshness_overrides
    previous = _read_last_history(history_path).get("rows", {})

    entries: dict[str, dict] = {}
    for name, path in datasets.items():
        entries[name] = dataset_health(
            name, path,
            max_age_days=freshness_overrides.get(name, max_age_days),
            previous_rows=previous.get(name),
        )
    context = {name: data.get("metrics", {}) for name, data in entries.items()}
    for name, data in entries.items():
        if data["status"] == "missing":
            continue
        checks = evaluate_budgets(data.get("metrics", {}), budgets.get(name, []), context)
        data["budgets"] = checks
        data["status"] = ("green" if data["contract"] == "pass"
                          and all(check["passed"] for check in checks) else "red")

    failed = [name for name, data in entries.items()
              if data["status"] == "red" or (strict and data["status"] == "missing")]
    stale = [name for name, data in entries.items() if data.get("stale")]
    if fail_on_stale:
        failed.extend(name for name in stale if name not in failed)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "red" if failed else "green",
        "failed": failed,
        "stale": stale,
        "strict": strict,
        "fail_on_stale": fail_on_stale,
        "datasets": entries,
        "artifacts": artifact_health(root) if check_artifacts else {"status": "skipped"},
        "events": events_health(events_db) if events_db else {"status": "absent"},
    }
    if history_path is not None:
        _append_history(Path(history_path), report)
        report["history_path"] = str(history_path)
    return report


def format_health_report(report: dict) -> str:
    status = report["status"].upper()
    lines = [f"[{status}] data health at {report['generated_at']}"]
    for name, data in report["datasets"].items():
        if data["status"] == "missing":
            lines.append(f"  {name:<22} missing   {data['path']}")
            continue
        row_bits = f"rows={data.get('rows')}"
        if data.get("delta_rows") is not None:
            row_bits += f" delta={data['delta_rows']:+d}"
        row_bits += f" age={data.get('age_days')}d"
        budget_summary = ", ".join(
            f"{check['metric']}={'ok' if check['passed'] else 'BREACH'}"
            for check in data.get("budgets", []))
        flag = " (stale)" if data.get("stale") else ""
        lines.append(f"  {name:<22} {data['status']:<8} {row_bits}{flag}")
        if budget_summary:
            lines.append(f"  {'':<22} budgets: {budget_summary}")
        if data["contract"] == "fail":
            lines.append(f"  {'':<22} contract: FAIL {data.get('contract_errors')}")
    artifacts = report["artifacts"]
    lines.append(f"  artifacts              {artifacts['status']:<8} "
                 f"{artifacts.get('checks_passed', '-')}/{artifacts.get('checks', '-')} checks")
    events = report["events"]
    if events.get("status") == "present":
        lines.append(f"  events                 present  rows={events['rows']} "
                     f"last_24h={events['last_24h']} age={events.get('age_hours')}h")
    else:
        lines.append(f"  events                 {events.get('status')}")
    if report["failed"]:
        lines.append(f"  failed: {', '.join(report['failed'])}")
    if report["stale"]:
        lines.append(f"  stale : {', '.join(report['stale'])}")
    return "\n".join(lines)
