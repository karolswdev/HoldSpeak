from __future__ import annotations

import json
from types import SimpleNamespace
from urllib import error as urlerror

import pytest

import holdspeak.commands.doctor as doctor


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
