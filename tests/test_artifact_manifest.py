"""Hermetic tests for the serving artifact manifest."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data_engineering.artifacts import (
    DEFAULT_MANIFEST_PATH,
    Artifact,
    build_manifest,
    sha256_file,
    verify_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FAKE_ARTIFACTS = (
    Artifact("cleaned_lyrics", "art/cleaned_lyrics.csv", "csv", text=True, schema="cleaned_lyrics"),
    Artifact("embedding_ids", "art/embedding_ids.json", "json", text=True),
    Artifact("embeddings", "art/embeddings.npy", "npy"),
    Artifact("feature_meta", "art/feature_meta.json", "json", text=True),
    Artifact("feature_matrix", "art/feature_matrix.npy", "npy"),
    Artifact("mood_probe", "art/mood_probe.npz", "npz"),
    Artifact("mood_vectors", "art/mood_vectors.csv", "csv", text=True),
    Artifact("sentiment_scores", "art/sentiment_scores.csv", "csv", text=True,
             schema="sentiment_scores"),
    Artifact("window_vectors", "art/window_vectors.npy", "npy", required=False),
    Artifact("window_owners", "art/window_owners.npy", "npy", required=False),
    Artifact("audio_embedding_keys", "art/audio_embedding_keys.csv", "csv", text=True),
    Artifact("audio_track_matches", "art/audio_track_matches.csv", "csv", text=True),
    Artifact("audio_embeddings", "art/audio_embeddings.npy", "npy", required=False),
)


def _fake_tree(root: Path, *, song_ids=(0, 1, 2), embed_dim: int = 4, feature_dim: int = 5,
               owners=(0, 0, 1, 1, 2, 2), probe_width: int = 4,
               embeddings_rows: int | None = None) -> None:
    art = root / "art"
    art.mkdir(parents=True, exist_ok=True)
    songs = list(song_ids)
    titles = ["A", "B", "C", "D"][: len(songs)]
    pd.DataFrame({
        "song_id": songs,
        "title": titles,
        "artist": ["X", "Y", "Z", "W"][: len(songs)],
        "category": ["nepali"] * len(songs),
        "lyrics": ["तिम्रो माया", "माया नै माया", "दुःखको कथा", "आँखै न हट्ने"][: len(songs)],
        "token_count": [4, 5, 3, 6][: len(songs)],
    }).to_csv(art / "cleaned_lyrics.csv", index=False, encoding="utf-8")
    (art / "embedding_ids.json").write_text(json.dumps(songs), encoding="utf-8")

    rows = len(songs) if embeddings_rows is None else embeddings_rows
    np.save(art / "embeddings.npy",
            np.arange(rows * embed_dim, dtype=np.float32).reshape(rows, embed_dim))
    (art / "feature_meta.json").write_text(
        json.dumps({"embedding_dim": embed_dim, "feature_dim": feature_dim}), encoding="utf-8")
    np.save(art / "feature_matrix.npy",
            np.zeros((len(songs), feature_dim), dtype=np.float32))
    np.savez(art / "mood_probe.npz",
             coef=np.zeros((7, probe_width), dtype=np.float32),
             intercept=np.zeros(7, dtype=np.float32))

    pd.DataFrame({"song_id": songs, "joy": [0.1] * len(songs)}) \
        .to_csv(art / "mood_vectors.csv", index=False, encoding="utf-8")
    pd.DataFrame({"song_id": songs, "sentiment_score": [0.0] * len(songs),
                  "sentiment_label": ["neutral"] * len(songs)}) \
        .to_csv(art / "sentiment_scores.csv", index=False, encoding="utf-8")

    owner_array = np.asarray(owners, dtype=np.int32)
    np.save(art / "window_vectors.npy", np.zeros((len(owner_array), embed_dim), dtype=np.float32))
    np.save(art / "window_owners.npy", owner_array)

    tracks = pd.DataFrame({"track_key": ["a|b", "c|d", "e|f"]})
    tracks.to_csv(art / "audio_embedding_keys.csv", index=False, encoding="utf-8")
    tracks.to_csv(art / "audio_track_matches.csv", index=False, encoding="utf-8")
    np.save(art / "audio_embeddings.npy", np.zeros((3, embed_dim), dtype=np.float32))


def _build(root: Path) -> dict:
    return build_manifest(root, FAKE_ARTIFACTS, inputs=())


def test_build_and_verify_fake_tree(tmp_path: Path):
    _fake_tree(tmp_path)
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
    _fake_tree(tmp_path)
    manifest = _build(tmp_path)
    np.save(tmp_path / "art" / "embeddings.npy",
            np.ones((3, 4), dtype=np.float32))
    report = verify_manifest(tmp_path, manifest)
    assert not report["passed"]
    assert any("embeddings.sha256" in error for error in report["errors"])


def test_missing_required_artifact_fails_build(tmp_path: Path):
    _fake_tree(tmp_path)
    (tmp_path / "art" / "cleaned_lyrics.csv").unlink()
    with pytest.raises(FileNotFoundError):
        _build(tmp_path)


def test_missing_optional_artifact_warns_not_fails(tmp_path: Path):
    _fake_tree(tmp_path)
    for name in ("window_vectors.npy", "window_owners.npy", "audio_embeddings.npy"):
        (tmp_path / "art" / name).unlink()
    manifest = _build(tmp_path)
    report = verify_manifest(tmp_path, manifest)
    assert report["passed"], report["errors"]
    assert len(report["warnings"]) == 3
    checks = {check["check"]: check["passed"] for check in report["checks"]}
    assert checks["window_rows_match"]  # skipped, not failed


def test_row_mismatch_fails_build(tmp_path: Path):
    _fake_tree(tmp_path, embeddings_rows=2)  # 3 songs but 2 vectors
    with pytest.raises(ValueError, match="song_rows_match"):
        _build(tmp_path)


def test_id_order_mismatch_fails_build(tmp_path: Path):
    _fake_tree(tmp_path)
    (tmp_path / "art" / "embedding_ids.json").write_text("[0, 1, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="corpus_embedding_id_order"):
        _build(tmp_path)


def test_window_owner_out_of_range_fails_build(tmp_path: Path):
    _fake_tree(tmp_path, owners=(0, 0, 1, 1, 2, 9))
    with pytest.raises(ValueError, match="window_owner_range"):
        _build(tmp_path)


def test_probe_width_mismatch_fails_build(tmp_path: Path):
    _fake_tree(tmp_path, embed_dim=4, probe_width=5)
    with pytest.raises(ValueError, match="probe_width_match"):
        _build(tmp_path)


def test_schema_version_drift_fails_verify(tmp_path: Path):
    _fake_tree(tmp_path)
    manifest = _build(tmp_path)
    for entry in manifest["artifacts"]:
        if entry["name"] == "sentiment_scores":
            entry["schema_version"] = 0
    report = verify_manifest(tmp_path, manifest)
    assert not report["passed"]
    assert any("sentiment_scores.schema_version" in error for error in report["errors"])


def test_skip_hashes_still_checks_metadata(tmp_path: Path):
    _fake_tree(tmp_path)
    manifest = _build(tmp_path)
    report = verify_manifest(tmp_path, manifest, check_hashes=False)
    assert report["passed"], report["errors"]


def test_unavailable_metadata_warns_not_fails(tmp_path: Path, monkeypatch):
    import data_engineering.artifacts as artifacts_module

    _fake_tree(tmp_path)
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

    _fake_tree(tmp_path)
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
