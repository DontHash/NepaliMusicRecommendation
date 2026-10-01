"""Hermetic tests for the pipeline runner (fake assets, temp state)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipelines.core import Asset
from pipelines.runner import Pipeline


def _write(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("made by test", encoding="utf-8")


def make_asset(name: str, calls: dict, *, deps=(), outputs=(), fail_times: int = 0,
               retries: int = 0, external: bool = False) -> Asset:
    if external:
        return Asset(name, external=True, deps=deps, outputs=outputs)

    def action(context):
        calls[name] = calls.get(name, 0) + 1
        if calls[name] <= fail_times:
            raise RuntimeError(f"{name} boom")
        for output in outputs:
            _write(context.project_root, output)
        return {"asset": name}

    return Asset(name, action=action, deps=deps, outputs=outputs, retries=retries)


def build(tmp_path: Path, assets) -> Pipeline:
    return Pipeline(assets, project_root=tmp_path, state_dir=tmp_path / "state")


def statuses(result: dict) -> dict[str, str]:
    return {record["asset"]: record["status"] for record in result["assets"]}


def test_runs_in_dependency_order_and_records_history(tmp_path: Path):
    calls: dict = {}
    assets = [
        make_asset("c", calls, deps=("b",), outputs=("c.out",)),
        make_asset("a", calls, outputs=("a.out",)),
        make_asset("b", calls, deps=("a",), outputs=("b.out",)),
    ]
    pipeline = build(tmp_path, assets)
    assert pipeline.order == ["a", "b", "c"]

    result = pipeline.run()
    assert result["status"] == "ok"
    assert statuses(result) == {"a": "ok", "b": "ok", "c": "ok"}

    rows = pipeline.state.run_assets(result["run_id"])
    assert [row["asset"] for row in rows] == ["a", "b", "c"]
    assert all(row["status"] == "ok" and row["finished_at"] for row in rows)
    run = pipeline.state.history(1)[0]
    assert run["status"] == "ok" and run["finished_at"] and run["started_at"]


def test_resume_skips_materialized_and_force_reruns(tmp_path: Path):
    calls: dict = {}
    pipeline = build(tmp_path, [make_asset("a", calls, outputs=("a.out",))])
    pipeline.run()
    result = pipeline.run()
    assert statuses(result) == {"a": "skipped"}
    assert calls["a"] == 1

    result = pipeline.run(force=True)
    assert statuses(result) == {"a": "ok"}
    assert calls["a"] == 2


def test_select_pulls_in_only_missing_ancestors(tmp_path: Path):
    calls: dict = {}
    assets = [make_asset("a", calls, outputs=("a.out",)),
              make_asset("b", calls, deps=("a",), outputs=("b.out",))]
    pipeline = build(tmp_path, assets)
    pipeline.run()

    result = pipeline.run(select=["b"])
    assert [record["asset"] for record in result["assets"]] == ["b"]
    assert statuses(result) == {"b": "skipped"}

    (tmp_path / "a.out").unlink()
    result = pipeline.run(select=["b"], force=True)
    assert [record["asset"] for record in result["assets"]] == ["a", "b"]
    assert statuses(result) == {"a": "ok", "b": "ok"}
    assert calls["a"] == 2


def test_downstream_and_backfill_expand_and_force(tmp_path: Path):
    calls: dict = {}
    assets = [
        make_asset("a", calls, outputs=("a.out",)),
        make_asset("b", calls, deps=("a",), outputs=("b.out",)),
        make_asset("x", calls, outputs=("x.out",)),
    ]
    pipeline = build(tmp_path, assets)

    result = pipeline.run(select=["a"], downstream=True)
    assert [record["asset"] for record in result["assets"]] == ["a", "b"]

    before = dict(calls)
    result = pipeline.run(select=["a"], backfill=True)
    assert statuses(result) == {"a": "ok", "b": "ok"}
    assert calls["a"] == before["a"] + 1
    assert calls["b"] == before["b"] + 1
    assert calls.get("x", 0) == 0  # unrelated asset untouched


def test_failure_blocks_dependents_but_not_independent_branches(tmp_path: Path):
    calls: dict = {}
    assets = [
        make_asset("a", calls, outputs=("a.out",)),
        make_asset("b", calls, deps=("a",), outputs=("b.out",), fail_times=99),
        make_asset("c", calls, deps=("b",), outputs=("c.out",)),
        make_asset("x", calls, outputs=("x.out",)),
    ]
    result = build(tmp_path, assets).run()
    assert statuses(result) == {"a": "ok", "b": "failed", "c": "blocked", "x": "ok"}
    assert result["status"] == "failed"
    assert "boom" in result["assets"][1]["message"]


def test_retries_recover_flaky_asset(tmp_path: Path):
    calls: dict = {}
    pipeline = build(tmp_path, [make_asset("a", calls, outputs=("a.out",),
                                           fail_times=1, retries=1)])
    result = pipeline.run()
    assert statuses(result) == {"a": "ok"}
    assert result["assets"][0]["metadata"]["attempts"] == 2
    assert calls["a"] == 2


def test_global_retry_override(tmp_path: Path):
    calls: dict = {}
    pipeline = build(tmp_path, [make_asset("a", calls, outputs=("a.out",), fail_times=2)])
    result = pipeline.run(retries=2)
    assert statuses(result) == {"a": "ok"}
    assert calls["a"] == 3


def test_external_asset_recorded_not_executed(tmp_path: Path):
    calls: dict = {}
    assets = [make_asset("src", calls, external=True, outputs=("src.csv",)),
              make_asset("a", calls, deps=("src",), outputs=("a.out",))]
    result = build(tmp_path, assets).run()
    assert statuses(result) == {"src": "external", "a": "ok"}
    assert result["status"] == "ok"
    assert calls.get("src") is None


def test_dry_run_plans_without_running_or_recording(tmp_path: Path):
    calls: dict = {}
    pipeline = build(tmp_path, [make_asset("a", calls, outputs=("a.out",))])
    result = pipeline.run(dry_run=True)
    assert result["dry_run"] and result["plan"] == [{"asset": "a", "status": "run"}]
    assert calls == {}
    assert not (tmp_path / "a.out").exists()
    assert pipeline.state.history(5) == []


def test_asset_log_written_per_run(tmp_path: Path):
    calls: dict = {}
    pipeline = build(tmp_path, [make_asset("a", calls, outputs=("a.out",))])
    result = pipeline.run()
    log_path = tmp_path / "state" / "logs" / str(result["run_id"]) / "a.log"
    assert log_path.exists()


def test_unknown_dependency_cycle_and_unknown_selection_raise(tmp_path: Path):
    with pytest.raises(ValueError, match="unknown asset"):
        build(tmp_path, [make_asset("a", {}, deps=("ghost",))])

    with pytest.raises(ValueError, match="cycle"):
        build(tmp_path, [
            make_asset("a", {}, deps=("b",)),
            make_asset("b", {}, deps=("a",)),
        ])

    pipeline = build(tmp_path, [make_asset("a", {}, outputs=("a.out",))])
    with pytest.raises(KeyError, match="ghost"):
        pipeline.run(select=["ghost"])


def test_asset_definitions_are_validated():
    with pytest.raises(ValueError, match="external"):
        Asset("x", action=lambda context: None, external=True)
    with pytest.raises(ValueError, match="action"):
        Asset("x")
    with pytest.raises(ValueError, match="duplicate"):
        Pipeline([Asset("a", action=lambda context: None),
                  Asset("a", action=lambda context: None)],
                 project_root=Path("."), state_dir=Path("."))
