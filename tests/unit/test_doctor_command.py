from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from urllib import error as urlerror

import pytest

import holdspeak.commands.doctor as doctor
from holdspeak.config import Config


def test_check_hotkey_wayland_failure_is_warn(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingHotkey:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no compositor support")

    monkeypatch.setattr(doctor, "HotkeyListener", FailingHotkey)
    result = doctor._check_hotkey("alt_r", is_wayland=True)
    assert result.status == "WARN"
    assert "focused and hold `v`" in (result.fix or "")


def test_check_hotkey_non_wayland_failure_is_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingHotkey:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no display")

    monkeypatch.setattr(doctor, "HotkeyListener", FailingHotkey)
    result = doctor._check_hotkey("alt_r", is_wayland=False)
    assert result.status == "FAIL"


def test_transcription_backend_failure_surfaces_fix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.sys, "platform", "linux")

    def fail_backend(_backend: str) -> str:
        raise doctor.TranscriberError("backend missing")

    monkeypatch.setattr(doctor, "_resolve_backend", fail_backend)
    result = doctor._check_transcription_backend()
    assert result.status == "FAIL"
    assert "holdspeak[linux]" in (result.fix or "")


def test_run_doctor_command_strict_treats_warnings_as_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    checks = [
        doctor.DoctorCheck(name="Runtime", status="PASS", detail="ok"),
        doctor.DoctorCheck(name="Clipboard backend", status="WARN", detail="missing", fix="install"),
    ]
    monkeypatch.setattr(doctor, "collect_doctor_checks", lambda: checks)

    rc_non_strict = doctor.run_doctor_command(SimpleNamespace(strict=False))
    rc_strict = doctor.run_doctor_command(SimpleNamespace(strict=True))

    assert rc_non_strict == 0
    assert rc_strict == 1


def _cloud_config(*, provider: str = "cloud", model: str = "qwen2.5-32b-instruct") -> SimpleNamespace:
    return SimpleNamespace(
        meeting=SimpleNamespace(
            intel_enabled=True,
            intel_provider=provider,
            intel_cloud_model=model,
            intel_cloud_api_key_env="HOMELAB_INTEL_API_KEY",
            intel_cloud_base_url="http://homelab.local:8000/v1",
        )
    )


def test_cloud_preflight_warns_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOMELAB_INTEL_API_KEY", raising=False)

    result = doctor._check_meeting_intel_cloud_preflight(_cloud_config())

    assert result.status == "WARN"
    assert "Missing API key" in result.detail


def test_cloud_preflight_warns_on_dns_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMELAB_INTEL_API_KEY", "test-key")

    def _fail_urlopen(_request, timeout):
        _ = timeout
        raise urlerror.URLError(OSError("temporary failure in name resolution"))

    monkeypatch.setattr(doctor.urlrequest, "urlopen", _fail_urlopen)

    result = doctor._check_meeting_intel_cloud_preflight(_cloud_config())

    assert result.status == "WARN"
    assert "Unable to reach" in result.detail or "DNS lookup failed" in result.detail


def test_cloud_preflight_warns_when_model_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMELAB_INTEL_API_KEY", "test-key")

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return json.dumps({"data": [{"id": "mixtral-8x7b"}, {"id": "llama-3.1-8b"}]}).encode("utf-8")

    monkeypatch.setattr(doctor.urlrequest, "urlopen", lambda _request, timeout: _FakeResponse())

    result = doctor._check_meeting_intel_cloud_preflight(_cloud_config(model="qwen2.5-32b-instruct"))

    assert result.status == "WARN"
    assert "unavailable" in result.detail


def test_cloud_preflight_passes_when_model_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMELAB_INTEL_API_KEY", "test-key")

    class _FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = exc_type, exc, tb
            return False

        def read(self):
            return json.dumps({"data": [{"id": "qwen2.5-32b-instruct"}]}).encode("utf-8")

    monkeypatch.setattr(doctor.urlrequest, "urlopen", lambda _request, timeout: _FakeResponse())

    result = doctor._check_meeting_intel_cloud_preflight(_cloud_config())

    assert result.status == "PASS"
    assert "reachable" in result.detail


# ---------------------------------------------------------------------------
# DIR-01 (HS-1-09) — `LLM runtime` + `Structured-output compilation` checks.
# ---------------------------------------------------------------------------


_VALID_BLOCKS_YAML = """\
version: 1
default_match_confidence: 0.6
blocks:
  - id: ai_prompt_buildout
    description: User is building out a prompt for an AI assistant.
    match:
      examples:
        - "Claude, please build me a function that..."
    inject:
      mode: append
      template: "{raw_text}"
"""


def _enabled_dictation_config(model_path: Path) -> Config:
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.runtime.backend = "llama_cpp"
    cfg.dictation.runtime.llama_cpp_model_path = str(model_path)
    return cfg


def test_dictation_runtime_check_pass_when_pipeline_disabled() -> None:
    cfg = Config()  # default: pipeline.enabled = False
    result = doctor._check_dictation_runtime(cfg)
    assert result.status == "PASS"
    assert "disabled" in result.detail


def test_dictation_runtime_check_warn_when_backend_unresolvable(monkeypatch, tmp_path) -> None:
    cfg = _enabled_dictation_config(tmp_path / "model.gguf")
    from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

    def _refuse(requested, **_kw):
        raise RuntimeUnavailableError("no backend installed")

    monkeypatch.setattr("holdspeak.plugins.dictation.runtime.resolve_backend", _refuse)
    result = doctor._check_dictation_runtime(cfg)
    assert result.status == "WARN"
    assert "resolution failed" in result.detail
    assert result.fix and "holdspeak[dictation-" in result.fix


def test_dictation_runtime_check_warn_when_model_missing(monkeypatch, tmp_path) -> None:
    cfg = _enabled_dictation_config(tmp_path / "missing.gguf")
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed"),
    )
    result = doctor._check_dictation_runtime(cfg)
    assert result.status == "WARN"
    assert "model missing" in result.detail
    assert result.fix and "Download" in result.fix


def test_dictation_runtime_check_pass_when_model_available(monkeypatch, tmp_path) -> None:
    model_path = tmp_path / "model.gguf"
    model_path.write_bytes(b"weights")
    cfg = _enabled_dictation_config(model_path)
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed"),
    )
    result = doctor._check_dictation_runtime(cfg)
    assert result.status == "PASS"
    assert "model available" in result.detail
    assert "llama_cpp" in result.detail


def test_project_context_check_pass_when_pipeline_disabled() -> None:
    cfg = Config()  # default: dictation pipeline disabled
    result = doctor._check_dictation_project_context(cfg)
    assert result.status == "PASS"
    assert "disabled" in result.detail


def test_project_context_check_pass_when_project_detected(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    root = tmp_path / "proj"
    (root / ".holdspeak").mkdir(parents=True)
    monkeypatch.chdir(root)

    cfg = Config()
    cfg.dictation.pipeline.enabled = True

    result = doctor._check_dictation_project_context(cfg)
    assert result.status == "PASS"
    assert "proj" in result.detail
    assert "anchor=holdspeak" in result.detail


def test_project_context_check_warn_when_no_project_detected(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    bare = tmp_path / "no_project"
    bare.mkdir()
    monkeypatch.chdir(bare)

    cfg = Config()
    cfg.dictation.pipeline.enabled = True

    result = doctor._check_dictation_project_context(cfg)
    assert result.status == "WARN"
    assert "no project root detected" in result.detail
    assert result.fix and ".holdspeak" in result.fix


def test_dictation_compile_check_pass_when_pipeline_disabled() -> None:
    cfg = Config()
    result = doctor._check_dictation_constraint_compile(cfg)
    assert result.status == "PASS"
    assert "disabled" in result.detail


def test_dictation_compile_check_pass_when_no_blocks_file(monkeypatch, tmp_path) -> None:
    cfg = _enabled_dictation_config(tmp_path / "model.gguf")
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.assembly.DEFAULT_GLOBAL_BLOCKS_PATH",
        tmp_path / "no-blocks-here.yaml",
    )
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed"),
    )
    result = doctor._check_dictation_constraint_compile(cfg)
    assert result.status == "PASS"
    assert "nothing to compile" in result.detail


def test_dictation_compile_check_pass_for_valid_blocks(monkeypatch, tmp_path) -> None:
    blocks_path = tmp_path / "blocks.yaml"
    blocks_path.write_text(_VALID_BLOCKS_YAML, encoding="utf-8")
    cfg = _enabled_dictation_config(tmp_path / "model.gguf")
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.assembly.DEFAULT_GLOBAL_BLOCKS_PATH",
        blocks_path,
    )
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed"),
    )
    result = doctor._check_dictation_constraint_compile(cfg)
    assert result.status == "PASS"
    assert "1 block(s) compiled cleanly" in result.detail


def test_dictation_compile_check_warn_when_compiler_raises(monkeypatch, tmp_path) -> None:
    blocks_path = tmp_path / "blocks.yaml"
    blocks_path.write_text(_VALID_BLOCKS_YAML, encoding="utf-8")
    cfg = _enabled_dictation_config(tmp_path / "model.gguf")
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.assembly.DEFAULT_GLOBAL_BLOCKS_PATH",
        blocks_path,
    )
    monkeypatch.setattr(
        "holdspeak.plugins.dictation.runtime.resolve_backend",
        lambda requested, **_kw: ("llama_cpp", "stubbed"),
    )

    def _explode(_schema):
        raise RuntimeError("schema not acceptable")

    monkeypatch.setattr("holdspeak.commands.doctor.to_gbnf", _explode, raising=False)
    # to_gbnf is imported inside the function — patch at the source module instead.
    monkeypatch.setattr("holdspeak.plugins.dictation.grammars.to_gbnf", _explode)

    result = doctor._check_dictation_constraint_compile(cfg)
    assert result.status == "WARN"
    assert "compile failed" in result.detail
    assert result.fix and "holdspeak dictation blocks validate" in result.fix


# ============================================================
# HS-2-10 / spec §9.10 — MIR-01 doctor checks
# ============================================================


def test_mir_routing_check_pass_when_router_disabled() -> None:
    config = Config()  # MeetingConfig.intent_router_enabled defaults to False
    result = doctor._check_mir_routing(config)
    assert result.status == "PASS"
    assert "disabled" in result.detail.lower()


def test_mir_routing_check_pass_when_enabled_with_valid_profile() -> None:
    config = Config()
    config.meeting.intent_router_enabled = True
    config.meeting.plugin_profile = "architect"
    result = doctor._check_mir_routing(config)
    assert result.status == "PASS"
    assert "enabled" in result.detail
    assert "profile=architect" in result.detail


def test_mir_routing_check_warn_for_unknown_profile() -> None:
    config = Config()
    config.meeting.intent_router_enabled = True
    config.meeting.plugin_profile = "no-such-profile"
    result = doctor._check_mir_routing(config)
    assert result.status == "WARN"
    assert "no-such-profile" in result.detail
    assert result.fix and "plugin_profile" in result.fix


def test_mir_routing_check_never_returns_fail() -> None:
    """MIR-01 mirrors DIR-DOC-003: opt-in, so doctor never escalates to FAIL."""
    for enabled, profile in [(False, "balanced"), (True, "balanced"), (True, "garbage")]:
        config = Config()
        config.meeting.intent_router_enabled = enabled
        config.meeting.plugin_profile = profile
        result = doctor._check_mir_routing(config)
        assert result.status in {"PASS", "WARN"}


def test_mir_telemetry_check_smoke_passes() -> None:
    result = doctor._check_mir_telemetry()
    assert result.status == "PASS"
    # Smoke detail contains both telemetry surfaces.
    assert "router_counters=" in result.detail
    assert "host_metrics=" in result.detail
    # The router counter API exposes routed/dropped windows.
    assert "routed_windows" in result.detail
    assert "dropped_windows" in result.detail
