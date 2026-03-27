from __future__ import annotations

from types import SimpleNamespace

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
