"""Hermetic tests for versioned artifact publishing and pointer resolution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _artifact_fixtures import FAKE_ARTIFACTS, fake_tree
from data_engineering.artifacts import verify_manifest
from data_engineering.publish import (
    list_versions,
    publish_artifacts,
    read_pointer,
    version_dir_for,
)


def _pointer_path(root: Path) -> Path:
    return root / "music_rec_artifacts" / "current.json"


def _publish(root: Path, version: str, **kwargs):
    return publish_artifacts(root, _pointer_path(root), artifacts=FAKE_ARTIFACTS,
                             inputs=(), version=version, **kwargs)


def test_publish_copies_verifies_and_swaps_pointer(tmp_path: Path):
    fake_tree(tmp_path)
    pointer = _pointer_path(tmp_path)
    result = _publish(tmp_path, "v1")

    assert pointer.exists()
    document = read_pointer(pointer)
    assert document["version"] == "v1"
    assert document["artifacts"] == len(FAKE_ARTIFACTS)
    assert result["bytes"] > 0

    destination = version_dir_for(pointer, "v1")
    assert (destination / "art" / "cleaned_lyrics.csv").exists()
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "v1"
    report = verify_manifest(destination, {**manifest, "inputs": []})
    assert report["passed"], report["errors"]


def test_pointer_swap_prunes_old_versions_but_keeps_predecessor(tmp_path: Path):
    fake_tree(tmp_path)
    pointer = _pointer_path(tmp_path)
    _publish(tmp_path, "v1", keep=2)
    _publish(tmp_path, "v2", keep=2)
    _publish(tmp_path, "v3", keep=2)

    versions = [item["version"] for item in list_versions(pointer)]
    assert versions == ["v3", "v2"]  # newest first, v1 pruned
    assert read_pointer(pointer)["version"] == "v3"
    assert not version_dir_for(pointer, "v1").exists()
    assert version_dir_for(pointer, "v2").exists()


def test_publish_refuses_inconsistent_set(tmp_path: Path):
    fake_tree(tmp_path, embeddings_rows=2)  # 3 songs, 2 vectors
    with pytest.raises(ValueError, match="song_rows_match"):
        _publish(tmp_path, "bad")


def test_publish_refuses_existing_version(tmp_path: Path):
    fake_tree(tmp_path)
    _publish(tmp_path, "v1")
    with pytest.raises(FileExistsError, match="v1"):
        _publish(tmp_path, "v1")


def test_dry_run_writes_nothing(tmp_path: Path):
    fake_tree(tmp_path)
    pointer = _pointer_path(tmp_path)
    result = _publish(tmp_path, "dry", dry_run=True)
    assert result["dry_run"]
    assert not pointer.exists()
    assert not version_dir_for(pointer, "dry").exists()


def test_config_resolves_published_version(tmp_path: Path, monkeypatch):
    pointer = _pointer_path(tmp_path)
    version_dir = version_dir_for(pointer, "v9")
    (version_dir / "music_rec_artifacts").mkdir(parents=True)
    (version_dir / "R_data" / "audio").mkdir(parents=True)
    (version_dir / "music_rec_artifacts" / "cleaned_lyrics.csv").write_text(
        "song_id,lyrics\n0,a\n", encoding="utf-8")
    (version_dir / "music_rec_artifacts" / "embeddings.npy").write_bytes(b"npy")
    (version_dir / "R_data" / "audio" / "audio_track_matches.csv").write_text(
        "track_key\n", encoding="utf-8")
    (version_dir / "manifest.json").write_text(json.dumps({
        "version": "v9",
        "artifacts": [
            {"name": "cleaned_lyrics", "path": "music_rec_artifacts/cleaned_lyrics.csv"},
            {"name": "embeddings", "path": "music_rec_artifacts/embeddings.npy"},
            {"name": "audio_track_matches", "path": "R_data/audio/audio_track_matches.csv"},
            {"name": "window_vectors", "path": "music_rec_artifacts/window_vectors.npy",
             "missing": True},
        ],
    }), encoding="utf-8")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps({"version": "v9"}), encoding="utf-8")

    monkeypatch.delenv("PROJECTR_ARTIFACTS_DISABLE", raising=False)
    monkeypatch.setenv("PROJECTR_ARTIFACTS_POINTER", str(pointer))
    from music_rec.config import Config

    config = Config()
    assert config.artifact_source == "published:v9"
    assert config.artifact_version == "v9"
    assert config.cleaned_lyrics_csv == version_dir / "music_rec_artifacts" / "cleaned_lyrics.csv"
    assert config.embeddings_npy == version_dir / "music_rec_artifacts" / "embeddings.npy"
    assert config.audio_track_matches_csv == \
        version_dir / "R_data" / "audio" / "audio_track_matches.csv"
    # missing entries and caches stay on the staging layout
    assert config.window_vectors_npy == config.artifacts_dir / "window_vectors.npy"
    assert config.lexical_cache_path == config.artifacts_dir / "lexical_cache.pkl"


def test_invalid_pointer_falls_back_to_staging(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("PROJECTR_ARTIFACTS_DISABLE", raising=False)
    monkeypatch.setenv("PROJECTR_ARTIFACTS_POINTER", str(tmp_path / "missing.json"))
    from music_rec.config import Config

    config = Config()
    assert config.artifact_source == "staging"
    assert config.artifact_version is None
    assert config.cleaned_lyrics_csv == config.artifacts_dir / "cleaned_lyrics.csv"


def test_force_staging_disables_pointer(tmp_path: Path, monkeypatch):
    pointer = _pointer_path(tmp_path)
    version_dir = version_dir_for(pointer, "v9")
    version_dir.mkdir(parents=True)
    (version_dir / "manifest.json").write_text(json.dumps({"artifacts": []}), encoding="utf-8")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(json.dumps({"version": "v9"}), encoding="utf-8")

    monkeypatch.delenv("PROJECTR_ARTIFACTS_DISABLE", raising=False)
    monkeypatch.setenv("PROJECTR_ARTIFACTS_POINTER", str(pointer))
    from music_rec.config import Config, force_staging

    force_staging()
    config = Config()
    assert config.artifact_source == "staging"
