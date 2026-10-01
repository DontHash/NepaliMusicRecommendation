"""Hermetic tests for the Prometheus metrics renderer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pipelines.state import RunStore
from web_app.metrics import render_metrics


def _runs_db(path: Path) -> None:
    store = RunStore(path)
    run_id = store.start_run(targets=["features"], options={})
    store.record_asset(run_id, asset="features", status="ok", duration_s=1.5,
                       metadata={"rows": 10})
    store.finish_run(run_id, "ok")
    store.close()


def _events_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, ts TEXT, event_type TEXT)")
    connection.execute("INSERT INTO events (ts, event_type) VALUES (datetime('now'), 'click')")
    connection.execute("INSERT INTO events (ts, event_type) VALUES (datetime('now'), 'click')")
    connection.execute("INSERT INTO events (ts, event_type) VALUES (datetime('now'), 'impression')")
    connection.commit()
    connection.close()


def test_render_metrics_from_fixtures(tmp_path: Path):
    runs_db = tmp_path / "runs.sqlite"
    _runs_db(runs_db)
    metrics_jsonl = tmp_path / "metrics.jsonl"
    metrics_jsonl.write_text(
        json.dumps({"kind": "asset", "asset": "features", "status": "ok"}) + "\n"
        + json.dumps({"kind": "asset", "asset": "mood.probe", "status": "failed"}) + "\n",
        encoding="utf-8")
    health = tmp_path / "health.json"
    health.write_text(json.dumps({
        "status": "green",
        "datasets": {"cleaned_lyrics": {"rows": 4211, "age_days": 0.5}},
    }), encoding="utf-8")
    events = tmp_path / "events.sqlite"
    _events_db(events)
    pointer = tmp_path / "current.json"
    pointer.write_text(json.dumps({"version": "vtest"}), encoding="utf-8")

    text = render_metrics(runs_db=runs_db, metrics_jsonl=metrics_jsonl, health_report=health,
                          events_db=events, artifacts_pointer=pointer)

    assert "projectr_build_info" in text
    assert 'projectr_pipeline_runs_total{status="ok"} 1' in text
    assert 'projectr_pipeline_asset_duration_seconds{asset="features",status="ok"} 1.5' in text
    assert 'projectr_pipeline_asset_events_total{status="failed"} 1' in text
    assert 'projectr_dataset_rows{dataset="cleaned_lyrics"} 4211' in text
    assert 'projectr_dataset_age_seconds{dataset="cleaned_lyrics"} 43200' in text
    assert 'projectr_health_status{status="green"} 1' in text
    assert 'projectr_events_total{event_type="click"} 2' in text
    assert "projectr_events_last_24h 3" in text
    assert 'projectr_artifacts_published{version="vtest"} 1' in text
    assert text.endswith("\n")


def test_render_metrics_tolerates_missing_files(tmp_path: Path):
    text = render_metrics(runs_db=tmp_path / "none.sqlite",
                          metrics_jsonl=tmp_path / "none.jsonl",
                          health_report=tmp_path / "none.json",
                          events_db=tmp_path / "none.sqlite",
                          artifacts_pointer=tmp_path / "none.json")
    assert "projectr_build_info" in text
    assert text.endswith("\n")


def test_render_metrics_escapes_labels(tmp_path: Path):
    pointer = tmp_path / "current.json"
    pointer.write_text(json.dumps({"version": 'v"1'}), encoding="utf-8")
    text = render_metrics(artifacts_pointer=pointer)
    assert 'version="v\\"1"' in text
