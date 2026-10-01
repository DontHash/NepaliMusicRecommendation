"""Hermetic tests for the serving artifact manifest."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from _artifact_fixtures import FAKE_ARTIFACTS, fake_tree
from data_engineering.artifacts import (
    DEFAULT_MANIFEST_PATH,
    build_manifest,
    sha256_file,
    verify_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build(root: Path) -> dict:
    return build_manifest(root, FAKE_ARTIFACTS, inputs=())


def test_build_and_verify_fake_tree(tmp_path: Path):
    fake_tree(tmp_path)
    manifest = _build(tmp_path)
    assert manifest["format_version"] == 1
    assert manifest["config_hash"]
    report = verify_manifest(tmp_path, manifest)
    assert report["passed"], report["errors"]
    assert report["artifacts_verified"] == len(FAKE_ARTIFACTS)
    checks = {check["check"]: check["passed"] for check in report["checks"]}
    assert checks["song_rows_match"]
    assert checks["corpus_embedding_id_order"]
    assert checks["window_owner_range"]
    assert checks["feature_layout_match"]
    assert checks["probe_width_match"]


def test_tampered_artifact_fails(tmp_path: Path):
    fake_tree(tmp_path)
    manifest = _build(tmp_path)
    np.save(tmp_path / "art" / "embeddings.npy",
            np.ones((3, 4), dtype=np.float32))
    report = verify_manifest(tmp_path, manifest)
    assert not report["passed"]
    assert any("embeddings.sha256" in error for error in report["errors"])


def test_missing_required_artifact_fails_build(tmp_path: Path):
    fake_tree(tmp_path)
    (tmp_path / "art" / "cleaned_lyrics.csv").unlink()
    with pytest.raises(FileNotFoundError):
        _build(tmp_path)


def test_missing_optional_artifact_warns_not_fails(tmp_path: Path):
    fake_tree(tmp_path)
    for name in ("window_vectors.npy", "window_owners.npy", "audio_embeddings.npy"):
        (tmp_path / "art" / name).unlink()
    manifest = _build(tmp_path)
    report = verify_manifest(tmp_path, manifest)
    assert report["passed"], report["errors"]
    assert len(report["warnings"]) == 3
    checks = {check["check"]: check["passed"] for check in report["checks"]}
    assert checks["window_rows_match"]  # skipped, not failed


def test_row_mismatch_fails_build(tmp_path: Path):
    fake_tree(tmp_path, embeddings_rows=2)  # 3 songs but 2 vectors
    with pytest.raises(ValueError, match="song_rows_match"):
        _build(tmp_path)


def test_id_order_mismatch_fails_build(tmp_path: Path):
    fake_tree(tmp_path)
    (tmp_path / "art" / "embedding_ids.json").write_text("[0, 1, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="corpus_embedding_id_order"):
        _build(tmp_path)


def test_window_owner_out_of_range_fails_build(tmp_path: Path):
    fake_tree(tmp_path, owners=(0, 0, 1, 1, 2, 9))
    with pytest.raises(ValueError, match="window_owner_range"):
        _build(tmp_path)


def test_probe_width_mismatch_fails_build(tmp_path: Path):
    fake_tree(tmp_path, embed_dim=4, probe_width=5)
    with pytest.raises(ValueError, match="probe_width_match"):
        _build(tmp_path)


def test_schema_version_drift_fails_verify(tmp_path: Path):
    fake_tree(tmp_path)
    manifest = _build(tmp_path)
    for entry in manifest["artifacts"]:
        if entry["name"] == "sentiment_scores":
            entry["schema_version"] = 0
    report = verify_manifest(tmp_path, manifest)
    assert not report["passed"]
    assert any("sentiment_scores.schema_version" in error for error in report["errors"])


def test_skip_hashes_still_checks_metadata(tmp_path: Path):
    fake_tree(tmp_path)
    manifest = _build(tmp_path)
    report = verify_manifest(tmp_path, manifest, check_hashes=False)
    assert report["passed"], report["errors"]


def test_unavailable_metadata_warns_not_fails(tmp_path: Path, monkeypatch):
    import data_engineering.artifacts as artifacts_module

    fake_tree(tmp_path)
    manifest = _build(tmp_path)
    real_describe = artifacts_module.describe

    def fake_describe(path, artifact, *, compute_hash: bool = True):
        entry = real_describe(path, artifact, compute_hash=compute_hash)
        if artifact.name == "embeddings":
            entry.pop("shape", None)
            entry["note"] = "simulated unavailable metadata"
        return entry

    monkeypatch.setattr(artifacts_module, "describe", fake_describe)
    report = verify_manifest(tmp_path, manifest)
    assert report["passed"], report["errors"]
    assert any("embeddings.shape not re-measured" in warning for warning in report["warnings"])


def test_text_hash_is_line_ending_independent(tmp_path: Path):
    lf = tmp_path / "lf.csv"
    crlf = tmp_path / "crlf.csv"
    lf.write_bytes(b"song_id,lyrics\n0,a\n1,b\n")
    crlf.write_bytes(b"song_id,lyrics\r\n0,a\r\n1,b\r\n")
    assert sha256_file(lf, text=True) == sha256_file(crlf, text=True)
    assert sha256_file(lf, text=False) != sha256_file(crlf, text=False)


def test_input_drift_fails_verify(tmp_path: Path):
    from data_engineering.artifacts import InputArtifact

    fake_tree(tmp_path)
    source = tmp_path / "source.csv"
    source.write_text("song_id,lyrics\n0,a\n", encoding="utf-8")
    inputs = (InputArtifact("source", "source.csv"),)
    manifest = build_manifest(tmp_path, FAKE_ARTIFACTS, inputs=inputs)
    assert verify_manifest(tmp_path, manifest)["passed"]
    source.write_text("song_id,lyrics\n0,changed\n", encoding="utf-8")
    report = verify_manifest(tmp_path, manifest)
    assert not report["passed"]
    assert any("input source" in error for error in report["errors"])


PROD_MANIFEST = PROJECT_ROOT / DEFAULT_MANIFEST_PATH


@pytest.mark.skipif(not PROD_MANIFEST.exists(), reason="no committed artifact manifest")
def test_committed_manifest_is_consistent():
    manifest = json.loads(PROD_MANIFEST.read_text(encoding="utf-8"))
    report = verify_manifest(PROJECT_ROOT, manifest, check_hashes=False)
    assert report["passed"], report["errors"]


@pytest.mark.skipif(os.environ.get("PROJECTR_VERIFY_ARTIFACTS") != "1",
                    reason="full hash verification is opt-in (CI runs scripts/verify_artifacts.py)")
def test_committed_manifest_hashes():
    manifest = json.loads(PROD_MANIFEST.read_text(encoding="utf-8"))
    report = verify_manifest(PROJECT_ROOT, manifest)
    assert report["passed"], report["errors"]
