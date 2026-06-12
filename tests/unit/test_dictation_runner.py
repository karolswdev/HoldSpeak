"""HS-52-01: the dictation-execution seam carved out of ``web_runtime``.

These tests drive ``holdspeak.dictation_runner.run_dictation_pipeline`` directly (it
could not be unit-tested while it lived inline on the ``WebRuntime`` god-object) and
pin the byte-identical defaults the carve must preserve: disabled or missing config
returns the text unchanged, any error falls back to the text, and the ``WebRuntime``
method still delegates to the extracted function.

(Distinct from ``test_dictation_runtime.py``, which covers the DIR-01 LLM backend.)
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import holdspeak.web_runtime as web_runtime
from holdspeak.dictation_runner import run_dictation_pipeline

_NOW = datetime(2026, 6, 8, 12, 0, 0)


def _enabled_config() -> SimpleNamespace:
    pipeline = SimpleNamespace(
        enabled=True,
        corrections_enabled=False,
        target_profile_override="auto",
        target_detect_llm_enabled=False,
        target_detect_llm_below=0.8,
        journal_enabled=True,
        journal_retention=500,
    )
    return SimpleNamespace(dictation=SimpleNamespace(pipeline=pipeline))


def _bare_server() -> SimpleNamespace:
    return SimpleNamespace(
        dictation_corrections=None,
        dictation_telemetry=None,
        dictation_journal=None,
    )


def test_disabled_pipeline_returns_text_unchanged() -> None:
    cfg = _enabled_config()
    cfg.dictation.pipeline.enabled = False
    out = run_dictation_pipeline(
        "hello world",
        config=cfg,
        server=_bare_server(),
        audio_duration_s=1.0,
        transcribed_at=_NOW,
    )
    assert out == "hello world"


def test_missing_dictation_config_returns_text_unchanged() -> None:
    out = run_dictation_pipeline(
        "hello world",
        config=SimpleNamespace(),  # no `.dictation`
        server=_bare_server(),
        audio_duration_s=1.0,
        transcribed_at=_NOW,
    )
    assert out == "hello world"


def test_build_pipeline_error_falls_back_to_text(monkeypatch) -> None:
    def _boom(*_a, **_k):
        raise RuntimeError("pipeline construction failed")

    monkeypatch.setattr("holdspeak.plugins.dictation.assembly.build_pipeline", _boom)
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.project_root.detect_project_for_cwd",
        lambda *_a, **_k: None,
    )
    out = run_dictation_pipeline(
        "keep me",
        config=_enabled_config(),
        server=_bare_server(),
        audio_duration_s=1.0,
        transcribed_at=_NOW,
    )
    assert out == "keep me"


def test_pipeline_not_loaded_returns_text(monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.project_root.detect_project_for_cwd",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.assembly.build_pipeline",
        lambda *_a, **_k: SimpleNamespace(runtime_status="error", runtime=None, pipeline=None),
    )
    out = run_dictation_pipeline(
        "unchanged",
        config=_enabled_config(),
        server=_bare_server(),
        audio_duration_s=1.0,
        transcribed_at=_NOW,
    )
    assert out == "unchanged"


def test_enabled_pipeline_returns_final_text(monkeypatch) -> None:
    """The happy path: an enabled, loaded pipeline returns ``run.final_text``."""
    _tp = SimpleNamespace(to_dict=lambda: {})
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.project_root.detect_project_for_cwd",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr("holdspeak.agent_device.target_profile_override_for_agent", lambda _s: None)
    monkeypatch.setattr("holdspeak.agent_context.get_recent_agent_session", lambda **_k: None)
    monkeypatch.setattr(
        "holdspeak.activity_context.build_activity_context",
        lambda **_k: SimpleNamespace(to_dict=lambda: {}),
    )
    monkeypatch.setattr("holdspeak.target_profile.collect_active_target_hints", lambda: [])
    monkeypatch.setattr(
        "holdspeak.target_profile.detect_target_profile_with_override",
        lambda _hints, _override: _tp,
    )
    monkeypatch.setattr("holdspeak.target_profile.apply_target_correction", lambda tp, **_k: tp)
    monkeypatch.setattr("holdspeak.target_profile.apply_model_assisted_target", lambda tp, **_k: tp)
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.assembly.build_pipeline",
        lambda *_a, **_k: SimpleNamespace(
            runtime_status="loaded",
            runtime=None,
            pipeline=SimpleNamespace(run=lambda _utt: SimpleNamespace(final_text="REWRITTEN")),
        ),
    )

    out = run_dictation_pipeline(
        "draft text",
        config=_enabled_config(),
        server=_bare_server(),
        audio_duration_s=2.0,
        transcribed_at=_NOW,
    )
    assert out == "REWRITTEN"


def test_web_runtime_method_delegates(monkeypatch) -> None:
    """``WebRuntime._maybe_run_dictation_pipeline`` is now a thin delegate that passes
    ``self.config`` / ``self.server`` through to the carved function."""
    captured: dict = {}

    def _spy(text, *, config, server, audio_duration_s, transcribed_at, agent_reply_session=None, journal_source="dictation"):
        captured.update(
            text=text,
            config=config,
            server=server,
            audio_duration_s=audio_duration_s,
            transcribed_at=transcribed_at,
            agent_reply_session=agent_reply_session,
        )
        return "SENTINEL"

    monkeypatch.setattr(web_runtime, "run_dictation_pipeline", _spy)
    fake_self = SimpleNamespace(config="CFG", server="SRV")
    out = web_runtime.WebRuntime._maybe_run_dictation_pipeline(
        fake_self,
        "hi",
        audio_duration_s=2.0,
        transcribed_at=_NOW,
        agent_reply_session=None,
    )
    assert out == "SENTINEL"
    assert captured["text"] == "hi"
    assert captured["config"] == "CFG"
    assert captured["server"] == "SRV"
    assert captured["audio_duration_s"] == 2.0
    assert captured["transcribed_at"] is _NOW
