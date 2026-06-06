"""HS-42-04: a successful real dictation sets the durable first-dictation
milestone (so `/setup` stops fronting the dashboard)."""
from __future__ import annotations

import threading
from types import SimpleNamespace

import numpy as np
import pytest

import holdspeak.db as db_module
import holdspeak.web_runtime as web_runtime
from holdspeak.db import FIRST_DICTATION_SUCCESS, Database


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        model=SimpleNamespace(name="base", warm_on_start=False, backend="auto"),
        hotkey=SimpleNamespace(key="alt_r", display="Right Option"),
        meeting=SimpleNamespace(
            mic_device=None, system_audio_device=None, mic_label="Me", remote_label="Remote",
            intel_enabled=False, intel_realtime_model="model.gguf", intel_provider="local",
            intel_cloud_model="gpt-5-mini", intel_cloud_api_key_env="OPENAI_API_KEY",
            intel_cloud_base_url=None, intel_cloud_reasoning_effort=None, intel_cloud_store=False,
            intel_deferred_enabled=True, diarization_enabled=False, diarize_mic=False,
            cross_meeting_recognition=True, web_auto_open=False, web_auth_token="t",
            mir_enabled=True, mir_profile="balanced",
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(
                enabled=False, stages=["project-rewriter"], max_total_latency_ms=600,
                target_profile_override="auto",
            ),
            runtime=SimpleNamespace(),
        ),
    )


class _FakeTranscriber:
    model_name = "base"

    def transcribe(self, _audio) -> str:
        return "hello world"


def _runtime(monkeypatch, tmp_path, typed: list):
    monkeypatch.setattr(web_runtime.Config, "load", lambda: _config())
    db = Database(tmp_path / "milestone.db")
    monkeypatch.setattr(db_module, "get_database", lambda *a, **k: db)

    class _FakeTyper:
        def type_text(self, text: str, **_kwargs) -> None:
            typed.append(text)

    monkeypatch.setattr(web_runtime, "TextTyper", _FakeTyper)
    rt = web_runtime.WebRuntime(
        no_open=True, stop_event=threading.Event(), register_signal_handlers=False
    )
    rt.transcriber = _FakeTranscriber()
    return rt, db


def test_successful_dictation_sets_the_first_dictation_milestone(monkeypatch, tmp_path):
    typed: list[str] = []
    rt, db = _runtime(monkeypatch, tmp_path, typed)

    assert db.milestones.is_set(FIRST_DICTATION_SUCCESS) is False  # fresh

    rt._transcribe_and_type(np.zeros(16000, dtype=np.float32))

    assert typed, "nothing reached the injection seam"
    assert "hello world" in typed[0].lower()
    assert db.milestones.is_set(FIRST_DICTATION_SUCCESS) is True


def test_no_speech_does_not_set_the_milestone(monkeypatch, tmp_path):
    typed: list[str] = []
    rt, db = _runtime(monkeypatch, tmp_path, typed)
    rt.transcriber = SimpleNamespace(model_name="base", transcribe=lambda _a: "")

    rt._transcribe_and_type(np.zeros(16000, dtype=np.float32))

    assert typed == []
    assert db.milestones.is_set(FIRST_DICTATION_SUCCESS) is False


def test_mark_first_dictation_is_idempotent_and_defensive(monkeypatch, tmp_path):
    typed: list[str] = []
    rt, db = _runtime(monkeypatch, tmp_path, typed)
    rt._mark_first_dictation()
    first = db.milestones.achieved_at(FIRST_DICTATION_SUCCESS)
    rt._mark_first_dictation()  # second call is a no-op (guarded)
    assert db.milestones.achieved_at(FIRST_DICTATION_SUCCESS) == first
