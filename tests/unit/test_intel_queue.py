"""Unit tests for deferred-intel queue worker lifecycle."""

from __future__ import annotations

import time

import holdspeak.intel_queue as intel_queue_module


def test_worker_start_and_stop(monkeypatch) -> None:
    calls = []

    def fake_drain(
        model_path=None,
        *,
        provider="local",
        cloud_model="gpt-5-mini",
        cloud_api_key_env="OPENAI_API_KEY",
        cloud_base_url=None,
        cloud_reasoning_effort=None,
        cloud_store=False,
        max_jobs=None,
    ):
        _ = provider, cloud_model, cloud_api_key_env, cloud_base_url, cloud_reasoning_effort, cloud_store
        _ = max_jobs
        calls.append(model_path)
        return 0

    monkeypatch.setattr(intel_queue_module, "drain_intel_queue", fake_drain)

    worker = intel_queue_module.start_intel_queue_worker(model_path="model.gguf", poll_seconds=1.0)
    time.sleep(0.02)
    worker.stop(timeout=1.0)

    assert calls
    assert worker.model_path == "model.gguf"
    assert worker.poll_seconds == 5.0
    assert worker.is_alive() is False
