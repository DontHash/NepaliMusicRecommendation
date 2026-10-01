"""Structure tests for the ProjectR asset graph (no actions executed)."""

from __future__ import annotations

from pathlib import Path

from pipelines.definitions import build_pipeline


def test_project_graph_is_valid_and_complete(tmp_path: Path):
    pipeline = build_pipeline(state_dir=tmp_path / "state")
    names = set(pipeline.assets_by_name)
    assert {"corpus.clean", "corpus.embed", "mood.probe", "mood.vectors", "features",
            "index.songs", "index.windows", "audio.manifest", "audio.dataset_lines",
            "corpus.v3", "corpus.refresh", "publish.artifacts"} <= names

    externals = {asset.name for asset in pipeline.assets if asset.external}
    assert externals == {"corpus.source", "labels.gemini", "audio.collection"}

    position = {name: index for index, name in enumerate(pipeline.order)}
    for asset in pipeline.assets:
        for dependency in asset.deps:
            assert position[dependency] < position[asset.name]

    assert pipeline.order[-1] == "publish.artifacts"  # serving set publishes last


def test_project_graph_downstream_selection(tmp_path: Path):
    pipeline = build_pipeline(state_dir=tmp_path / "state")
    scope, forced = pipeline.resolve(["features"], downstream=True)
    assert "features" in scope
    assert "index.songs" in scope
    assert "publish.artifacts" in scope
    assert forced == set()
    backfill_scope, backfill_forced = pipeline.resolve(["features"], backfill=True)
    assert backfill_forced == {"features", "index.songs", "publish.artifacts"}
    assert set(backfill_scope) >= backfill_forced
