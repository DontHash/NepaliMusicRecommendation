"""Tests for the shared embedding-model cache."""

from __future__ import annotations

import threading

import music_rec.embeddings as embeddings


class _FakeModel:
    def __init__(self, name: str, device: str):
        self.name = name
        self.device = device


def _patch_loader(monkeypatch, calls: list, delay: float = 0.0):
    def fake_load(model_name, device=None):
        if delay:
            import time

            time.sleep(delay)
        calls.append((model_name, device))
        return _FakeModel(model_name, device)

    monkeypatch.setattr(embeddings, "_load_model", fake_load)


def test_get_shared_model_loads_once_and_returns_same_object(monkeypatch):
    calls: list = []
    _patch_loader(monkeypatch, calls)
    monkeypatch.setattr(embeddings, "resolve_device", lambda device=None: "cpu")
    embeddings.reset_shared_models()

    first = embeddings.get_shared_model("model-x")
    second = embeddings.get_shared_model("model-x")
    assert first is second
    assert calls == [("model-x", "cpu")]


def test_shared_model_ready_tracks_cache(monkeypatch):
    calls: list = []
    _patch_loader(monkeypatch, calls)
    monkeypatch.setattr(embeddings, "resolve_device", lambda device=None: "cpu")
    embeddings.reset_shared_models()

    assert embeddings.shared_model_ready("model-x") is False
    embeddings.get_shared_model("model-x")
    assert embeddings.shared_model_ready("model-x") is True


def test_get_shared_model_is_thread_safe(monkeypatch):
    calls: list = []
    _patch_loader(monkeypatch, calls, delay=0.1)
    monkeypatch.setattr(embeddings, "resolve_device", lambda device=None: "cpu")
    embeddings.reset_shared_models()

    results = []
    barrier = threading.Barrier(4)

    def worker():
        barrier.wait()
        results.append(embeddings.get_shared_model("model-x"))

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(calls) == 1
    assert all(model is results[0] for model in results)


def test_reset_shared_models_forces_reload(monkeypatch):
    calls: list = []
    _patch_loader(monkeypatch, calls)
    monkeypatch.setattr(embeddings, "resolve_device", lambda device=None: "cpu")
    embeddings.reset_shared_models()

    embeddings.get_shared_model("model-x")
    embeddings.reset_shared_models()
    embeddings.get_shared_model("model-x")
    assert len(calls) == 2
