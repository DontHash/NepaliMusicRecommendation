"""Tests for embedding device resolution (GPU vs CPU policy)."""

from __future__ import annotations

from music_rec.config import Config
from music_rec.embeddings import resolve_device


def test_resolve_device_honours_explicit_preference():
    assert resolve_device("cpu") == "cpu"
    assert resolve_device("CPU") == "cpu"


def test_resolve_device_reads_environment(monkeypatch):
    monkeypatch.setenv("PROJECTR_EMBED_DEVICE", "cpu")
    assert resolve_device() == "cpu"
    assert resolve_device("cuda") == "cuda"


def test_resolve_device_auto_returns_known_device(monkeypatch):
    monkeypatch.delenv("PROJECTR_EMBED_DEVICE", raising=False)
    assert resolve_device("auto") in {"cpu", "cuda"}


def test_config_reads_device_from_environment(monkeypatch):
    monkeypatch.setenv("PROJECTR_EMBED_DEVICE", "cpu")
    assert Config().embedding_device == "cpu"


def test_config_device_defaults_to_auto(monkeypatch):
    monkeypatch.delenv("PROJECTR_EMBED_DEVICE", raising=False)
    assert Config().embedding_device == "auto"
