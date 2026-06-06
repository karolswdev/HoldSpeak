"""HS-42-01: the first-run setup-state contract + the `first_run` milestone.

Covers the composition (sections from doctor checks, overall derivation,
single primary action), the trust/presence blocks, the durable first-success
milestone (set → persists across a restart), and the cheapness guarantee
(no network call by default).
"""
from __future__ import annotations

from pathlib import Path

import pytest

import holdspeak.config as config_module
import holdspeak.setup_status as setup_status
from holdspeak.commands.doctor import DoctorCheck
from holdspeak.config import Config
from holdspeak.db import FIRST_DICTATION_SUCCESS, Database


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")


def _checks(*specs: tuple[str, str]) -> list[DoctorCheck]:
    return [DoctorCheck(name=n, status=s, detail=f"{n} detail", fix=f"fix {n}") for n, s in specs]


def _stub_checks(monkeypatch: pytest.MonkeyPatch, checks: list[DoctorCheck]) -> None:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks", lambda **_: checks
    )


# ── overall + sections ────────────────────────────────────────────────


def test_sections_mirror_doctor_checks_one_to_one(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Microphone", "PASS"), ("Hotkey", "WARN")))
    status = setup_status.build_setup_status(config=Config())
    assert [s["label"] for s in status["sections"]] == ["Microphone", "Hotkey"]
    assert status["sections"][0]["status"] == "pass"
    assert status["sections"][1]["status"] == "warn"
    assert status["sections"][0]["id"] == "microphone"


def test_overall_blocked_on_any_fail(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS"), ("Transcription", "FAIL")))
    assert setup_status.build_setup_status(config=Config())["overall"] == "blocked"


def test_overall_needs_attention_on_warn_only(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS"), ("Hotkey", "WARN")))
    assert setup_status.build_setup_status(config=Config())["overall"] == "needs_attention"


def test_overall_ready_when_all_pass(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS"), ("Hotkey", "PASS")))
    assert setup_status.build_setup_status(config=Config())["overall"] == "ready"


def test_unknown_status_is_normalized(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, [DoctorCheck(name="X", status="SKIPPED", detail="d")])
    status = setup_status.build_setup_status(config=Config())
    assert status["sections"][0]["status"] == "unknown"


# ── primary action: the single next step ──────────────────────────────


def test_primary_action_points_at_the_fail(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "WARN"), ("Transcription", "FAIL")))
    action = setup_status.build_setup_status(config=Config())["primary_action"]
    assert action["id"] == "transcription"  # FAIL outranks WARN
    assert action["route"] == "/setup#transcription"
    assert action["label"] == "fix Transcription"


def test_primary_action_is_first_dictation_when_ready_and_first_run(
    isolated_config, monkeypatch, tmp_path
) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    db = Database(tmp_path / "s.db")
    action = setup_status.build_setup_status(config=Config(), database=db)["primary_action"]
    assert action["id"] == "first_dictation"
    assert action["route"] == "/setup#first-dictation"


def test_no_primary_action_when_ready_and_already_succeeded(
    isolated_config, monkeypatch, tmp_path
) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    db = Database(tmp_path / "s.db")
    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    status = setup_status.build_setup_status(config=Config(), database=db)
    assert status["first_run"] is False
    assert status["primary_action"] is None


# ── the first_run milestone (durable) ─────────────────────────────────


def test_first_run_true_with_no_database(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    assert setup_status.build_setup_status(config=Config())["first_run"] is True


def test_first_run_flips_after_milestone_and_survives_restart(
    isolated_config, monkeypatch, tmp_path
) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    db_path = tmp_path / "s.db"
    db = Database(db_path)
    assert setup_status.build_setup_status(config=Config(), database=db)["first_run"] is True

    db.milestones.mark(FIRST_DICTATION_SUCCESS)
    assert setup_status.build_setup_status(config=Config(), database=db)["first_run"] is False

    # A fresh container over the same file (a simulated restart) still sees it.
    reopened = Database(db_path)
    assert reopened.milestones.is_set(FIRST_DICTATION_SUCCESS) is True
    assert setup_status.build_setup_status(config=Config(), database=reopened)["first_run"] is False


def test_milestone_mark_is_idempotent(tmp_path) -> None:
    db = Database(tmp_path / "s.db")
    first = db.milestones.mark(FIRST_DICTATION_SUCCESS)
    second = db.milestones.mark(FIRST_DICTATION_SUCCESS)
    assert first == second  # the original achieved_at is kept
    assert db.milestones.clear(FIRST_DICTATION_SUCCESS) is True
    assert db.milestones.is_set(FIRST_DICTATION_SUCCESS) is False


# ── trust block ───────────────────────────────────────────────────────


def test_trust_default_is_local_only(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    trust = setup_status.build_setup_status(config=Config())["trust"]
    assert trust["web_bind"] == "127.0.0.1"
    assert trust["auth_token_set"] is False
    assert trust["transcript_egress"] == "none"
    assert trust["configured_endpoints"] == []
    assert trust["actuators_enabled"] is False


def test_trust_reflects_cloud_endpoint_and_actuators(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    cfg = Config()
    cfg.meeting.intel_enabled = True
    cfg.meeting.intel_provider = "cloud"
    cfg.meeting.intel_cloud_base_url = "http://homelab.local:8000/v1"
    cfg.meeting.allow_actuators = True
    trust = setup_status.build_setup_status(config=cfg)["trust"]
    assert trust["transcript_egress"] == "configured"
    assert "http://homelab.local:8000/v1" in trust["configured_endpoints"]
    assert trust["actuators_enabled"] is True


# ── presence block ────────────────────────────────────────────────────


def test_presence_tier_macos_is_hud(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    monkeypatch.setattr(
        "holdspeak.desktop_presence.detect_presence_platform",
        lambda env=None: {"os": "macos", "wayland": False, "compositor": None, "overlay_capable": True},
    )
    presence = setup_status.build_setup_status(config=Config(), env={})["presence"]
    assert presence == {"enabled": False, "available": True, "tier": "hud", "os": "macos", "wayland": False}


def test_presence_tier_wayland_gnome_is_notification(isolated_config, monkeypatch) -> None:
    _stub_checks(monkeypatch, _checks(("Mic", "PASS")))
    monkeypatch.setattr(
        "holdspeak.desktop_presence.detect_presence_platform",
        lambda env=None: {"os": "linux", "wayland": True, "compositor": "gnome", "overlay_capable": False},
    )
    presence = setup_status.build_setup_status(config=Config(), env={})["presence"]
    assert presence["tier"] == "notification"
    assert presence["available"] is True


# ── cheapness: no network by default ──────────────────────────────────


def test_status_read_skips_network_by_default(isolated_config, monkeypatch) -> None:
    seen = {}

    def _spy(*, skip_network: bool = False):
        seen["skip_network"] = skip_network
        return _checks(("Mic", "PASS"))

    monkeypatch.setattr("holdspeak.commands.doctor.collect_doctor_checks", _spy)
    setup_status.build_setup_status(config=Config())
    assert seen["skip_network"] is True
