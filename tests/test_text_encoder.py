"""Tests for query-text encoder backend selection (torch vs ONNX)."""

from __future__ import annotations

import pytest

import music_rec.embeddings as embeddings
from music_rec.config import Config


@pytest.fixture(autouse=True)
def _clean_encoder_cache():
    embeddings.reset_shared_models()
    yield
    embeddings.reset_shared_models()


def test_torch_backend_uses_shared_model(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(embeddings, "get_shared_model", lambda *args, **kwargs: sentinel)
    config = Config()
    config.embedding_backend = "torch"
    assert embeddings.get_text_encoder(config) is sentinel


def test_auto_backend_prefers_onnx_when_available(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(embeddings, "_onnx_artifact_available", lambda config: True)
    monkeypatch.setattr(embeddings, "_load_onnx_encoder", lambda config: sentinel)
    config = Config()
    config.embedding_backend = "auto"
    assert embeddings.get_text_encoder(config) is sentinel
    assert embeddings.text_encoder_ready(config) is True


def test_onnx_encoder_is_cached(monkeypatch):
    calls: list = []
    monkeypatch.setattr(embeddings, "_onnx_artifact_available", lambda config: True)

    def fake_load(config):
        calls.append(config.embedding_onnx_dir)
        return object()

    monkeypatch.setattr(embeddings, "_load_onnx_encoder", fake_load)
    config = Config()
    config.embedding_backend = "auto"
    first = embeddings.get_text_encoder(config)
    second = embeddings.get_text_encoder(config)
    assert first is second
    assert len(calls) == 1


def test_onnx_backend_falls_back_when_artifact_missing(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(embeddings, "_onnx_artifact_available", lambda config: False)
    monkeypatch.setattr(embeddings, "get_shared_model", lambda *args, **kwargs: sentinel)
    config = Config()
    config.embedding_backend = "onnx"
    assert embeddings.get_text_encoder(config) is sentinel


def test_text_encoder_ready_false_before_load(monkeypatch):
    monkeypatch.setattr(embeddings, "_onnx_artifact_available", lambda config: True)
    config = Config()
    config.embedding_backend = "auto"
    assert embeddings.text_encoder_ready(config) is False
