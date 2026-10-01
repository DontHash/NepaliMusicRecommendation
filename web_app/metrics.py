"""Prometheus text metrics for the platform (served at ``GET /metrics``).

Reads the DE3 run store, the DE5 metrics stream, the data-health report, the
DE6 events database and the published-artifact pointer. Every section is
optional: missing or unreadable files are skipped, never fatal, so a scrape
always succeeds.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

HELP = {
    "projectr_build_info": "Static info about the metrics endpoint itself.",
    "projectr_pipeline_runs_total": "Pipeline runs by terminal status.",
    "projectr_pipeline_asset_duration_seconds": "Duration of the latest recorded run per asset.",
    "projectr_pipeline_asset_events_total": "Asset executions by status (from the metrics stream).",
    "projectr_dataset_rows": "Rows per dataset from the latest data-health report.",
    "projectr_dataset_age_seconds": "Age of the dataset file at the last health report.",
    "projectr_health_status": "Overall data-health status (1 for the current status).",
    "projectr_events_total": "User events by type.",
    "projectr_events_last_24h": "User events recorded in the last 24 hours.",
    "projectr_artifacts_published": "Published serving artifact version (1 per version label).",
}


def _escape(value) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _line(name: str, labels: dict | None = None, value=1) -> str:
    if labels:
        rendered = ",".join(f'{key}="{_escape(val)}"' for key, val in labels.items())
        return f"{name}{{{rendered}}} {value}"
    return f"{name} {value}"


def render_metrics(*, runs_db: Path | None = None, metrics_jsonl: Path | None = None,
                   health_report: Path | None = None, events_db: Path | None = None,
                   artifacts_pointer: Path | None = None) -> str:
    lines: list[str] = []
    families: set[str] = set()

    def family(name: str, kind: str) -> None:
        if name not in families:
            lines.append(f"# HELP {name} {HELP[name]}")
            lines.append(f"# TYPE {name} {kind}")
            families.add(name)

    def exists(path) -> bool:
        return path is not None and Path(path).exists()

    family("projectr_build_info", "gauge")
    lines.append(_line("projectr_build_info", {"component": "projectr"}))

    if exists(runs_db):
        try:
            connection = sqlite3.connect(str(runs_db))
            connection.row_factory = sqlite3.Row
            try:
                family("projectr_pipeline_runs_total", "counter")
                for row in connection.execute(
                        "SELECT status, COUNT(*) AS n FROM runs GROUP BY status"):
                    lines.append(_line("projectr_pipeline_runs_total", {"status": row["status"]},
                                       row["n"]))
                family("projectr_pipeline_asset_duration_seconds", "gauge")
                for row in connection.execute(
                        "SELECT a.asset, a.status, a.duration_s FROM asset_runs a "
                        "JOIN (SELECT asset, MAX(id) AS max_id FROM asset_runs GROUP BY asset) m "
                        "ON a.id = m.max_id"):
                    if row["duration_s"] is not None:
                        lines.append(_line(
                            "projectr_pipeline_asset_duration_seconds",
                            {"asset": row["asset"], "status": row["status"]},
                            row["duration_s"]))
            finally:
                connection.close()
        except sqlite3.Error:
            pass

    if exists(metrics_jsonl):
        counts: dict[str, int] = {}
        try:
            with Path(metrics_jsonl).open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if record.get("kind") == "asset":
                        status = str(record.get("status", "unknown"))
                        counts[status] = counts.get(status, 0) + 1
        except OSError:
            counts = {}
        if counts:
            family("projectr_pipeline_asset_events_total", "counter")
            for status, count in sorted(counts.items()):
                lines.append(_line("projectr_pipeline_asset_events_total",
                                   {"status": status}, count))

    if exists(health_report):
        try:
            report = json.loads(Path(health_report).read_text(encoding="utf-8"))
        except ValueError:
            report = {}
        if report:
            family("projectr_health_status", "gauge")
            lines.append(_line("projectr_health_status",
                               {"status": report.get("status", "unknown")}))
            family("projectr_dataset_rows", "gauge")
            for name, data in report.get("datasets", {}).items():
                if data.get("rows") is not None:
                    lines.append(_line("projectr_dataset_rows", {"dataset": name}, data["rows"]))
            family("projectr_dataset_age_seconds", "gauge")
            for name, data in report.get("datasets", {}).items():
                if data.get("age_days") is not None:
                    lines.append(_line("projectr_dataset_age_seconds", {"dataset": name},
                                       round(float(data["age_days"]) * 86400)))

    if exists(events_db):
        try:
            connection = sqlite3.connect(str(events_db))
            try:
                family("projectr_events_total", "counter")
                for row in connection.execute(
                        "SELECT event_type, COUNT(*) AS n FROM events GROUP BY event_type"):
                    lines.append(_line("projectr_events_total", {"event_type": row[0]}, row[1]))
                family("projectr_events_last_24h", "gauge")
                last_24h = connection.execute(
                    "SELECT COUNT(*) FROM events WHERE ts >= datetime('now', '-1 day')"
                ).fetchone()[0]
                lines.append(_line("projectr_events_last_24h", value=last_24h))
            finally:
                connection.close()
        except sqlite3.Error:
            pass

    if exists(artifacts_pointer):
        try:
            pointer = json.loads(Path(artifacts_pointer).read_text(encoding="utf-8"))
        except ValueError:
            pointer = {}
        version = pointer.get("version")
        if version:
            family("projectr_artifacts_published", "gauge")
            lines.append(_line("projectr_artifacts_published", {"version": version}))

    return "\n".join(lines) + "\n"
