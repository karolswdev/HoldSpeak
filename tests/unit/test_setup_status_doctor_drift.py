"""HS-42-01: the no-duplicate-doctor invariant.

`/api/setup/status` must be an *adapter* over `collect_doctor_checks()`, not a
second implementation. These tests lock that: every real doctor check surfaces as
a setup section (1:1, none dropped), and a `FAIL` can never be silently filtered
out of the setup view.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import holdspeak.config as config_module
import holdspeak.setup_status as setup_status
from holdspeak.commands.doctor import DoctorCheck, collect_doctor_checks
from holdspeak.config import Config
from holdspeak.setup_status import _slug


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")


def test_every_real_doctor_check_becomes_a_section(isolated_config) -> None:
    checks = collect_doctor_checks(skip_network=True)
    status = setup_status.build_setup_status(config=Config())

    # 1:1 — nothing dropped, so a FAIL on any check can't be hidden.
    assert len(status["sections"]) == len(checks)
    assert {s["id"] for s in status["sections"]} == {_slug(c.name) for c in checks}


def test_a_failing_check_surfaces_as_a_blocking_section(isolated_config, monkeypatch) -> None:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks",
        lambda **_: [
            DoctorCheck(name="Microphone", status="PASS", detail="ok"),
            DoctorCheck(name="Text insertion", status="FAIL", detail="blocked", fix="Grant accessibility"),
        ],
    )
    status = setup_status.build_setup_status(config=Config())

    failing = [s for s in status["sections"] if s["status"] == "fail"]
    assert [s["id"] for s in failing] == ["text-insertion"]
    assert status["overall"] == "blocked"
    assert status["primary_action"]["id"] == "text-insertion"


def test_skip_network_returns_cloud_preflight_as_not_run(monkeypatch) -> None:
    """The cheap path returns the cloud-preflight check as a neutral 'not run'
    instead of probing the endpoint (so a page load never blocks on HTTP)."""
    from holdspeak.commands.doctor import _check_meeting_intel_cloud_preflight

    cfg = Config()
    cfg.meeting.intel_enabled = True
    cfg.meeting.intel_provider = "cloud"
    cfg.meeting.intel_cloud_base_url = "http://10.255.255.1:9/v1"  # would hang if probed
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    check = _check_meeting_intel_cloud_preflight(cfg, skip_network=True)
    assert check.status == "PASS"
    assert "Not run" in check.detail
