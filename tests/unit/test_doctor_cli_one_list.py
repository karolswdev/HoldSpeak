"""PHILO-15 02: `holdspeak doctor` runs the list Setup status runs.

The CLI ran only the 10 running-hub checks (holdspeak/doctor.py) and ignored
`--strict` and `--connectors`, while `/api/setup/status` ran
`collect_doctor_checks` (Coding agents, microphone, hotkey, connectors...).
These fences hold the two on ONE list and hold the flags.
"""

from __future__ import annotations

import sys

import pytest

import holdspeak.commands.doctor as local_doctor
import holdspeak.doctor as hub_doctor
import holdspeak.main as main_module
from holdspeak.commands.doctor import DoctorCheck

SENTINEL = DoctorCheck(name="Sentinel one-list", status="PASS", detail="from the one list")


def _one_list(monkeypatch: pytest.MonkeyPatch, *checks: DoctorCheck) -> list[bool]:
    seen: list[bool] = []

    def collect(*, skip_network: bool = False) -> list[DoctorCheck]:
        seen.append(skip_network)
        return list(checks)

    monkeypatch.setattr(local_doctor, "collect_doctor_checks", collect)
    return seen


def _hub(monkeypatch: pytest.MonkeyPatch, *results: hub_doctor.DoctorResult) -> list[int]:
    calls: list[int] = []

    def run_checks(url=None, token=None):
        calls.append(1)
        return list(results)

    monkeypatch.setattr(hub_doctor, "run_checks", run_checks)
    return calls


def _cli(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["holdspeak", "doctor", *argv])
    monkeypatch.setattr(main_module, "setup_logging", lambda *a, **k: None, raising=False)
    with pytest.raises(SystemExit) as exc:
        main_module.main()
    return int(exc.value.code or 0)


def test_cli_and_setup_status_read_the_same_list(monkeypatch, capsys) -> None:
    """The CLI and Setup status both call the one `collect_doctor_checks`."""
    seen = _one_list(monkeypatch, SENTINEL)
    _hub(monkeypatch, hub_doctor.DoctorResult("PASS", "hub-health", "ok"))

    assert _cli(monkeypatch) == 0
    out = capsys.readouterr().out
    assert "[PASS] Sentinel one-list: from the one list" in out

    from holdspeak.setup_status import build_setup_status

    status = build_setup_status(database=None, skip_network=True)
    assert "Sentinel one-list" in [section["label"] for section in status["sections"]]
    # The CLI runs the live preflight; Setup keeps its page load cheap.
    assert seen == [False, True]


def test_the_real_list_carries_coding_agents_mic_hotkey_and_connectors() -> None:
    import inspect

    source = inspect.getsource(local_doctor.collect_doctor_checks)
    for check in ("_check_coding_agents", "_check_microphone", "_check_hotkey", "_check_connector_packs"):
        assert check in source


def test_cli_runs_the_hub_checks_after_the_list(monkeypatch, capsys) -> None:
    _one_list(monkeypatch, SENTINEL)
    calls = _hub(monkeypatch, hub_doctor.DoctorResult("PASS", "hub-health", "ok"))

    assert _cli(monkeypatch) == 0
    out = capsys.readouterr().out
    assert calls == [1]
    assert out.index("Sentinel one-list") < out.index("Running hub") < out.index("PASS  Hub ")


def test_cli_strict_fails_on_a_warning_and_plain_does_not(monkeypatch, capsys) -> None:
    _one_list(monkeypatch, DoctorCheck(name="Clipboard backend", status="WARN", detail="missing", fix="install"))
    _hub(monkeypatch, hub_doctor.DoctorResult("PASS", "hub-health", "ok"))

    assert _cli(monkeypatch) == 0
    assert _cli(monkeypatch, "--strict") == 1
    assert "Clipboard backend: install" in capsys.readouterr().out


def test_cli_fails_when_the_hub_fails(monkeypatch) -> None:
    _one_list(monkeypatch, SENTINEL)
    _hub(monkeypatch, hub_doctor.DoctorResult("FAIL", "hub-health", "unreachable"))

    assert _cli(monkeypatch) == 1


def test_cli_connectors_lists_packs_and_skips_every_other_check(monkeypatch, capsys) -> None:
    seen = _one_list(monkeypatch, SENTINEL)
    calls = _hub(monkeypatch)
    monkeypatch.setattr(local_doctor, "run_connector_packs_listing", lambda: print("PACKS") or 0)

    assert _cli(monkeypatch, "--connectors") == 0
    out = capsys.readouterr().out
    assert "PACKS" in out
    assert seen == [] and calls == []
    assert "Running hub" not in out
