"""HS-201 follow-up: ordinary Web Record has no live meeting analysis.

The persisted ``intel_enabled`` field is legacy state on this path.  These
tests keep the reporting surfaces honest while leaving speech and later manual
summary routes available.
"""

from __future__ import annotations

from pathlib import Path
from urllib import request as urlrequest

import pytest

from holdspeak.commands import doctor
from holdspeak.config import Config
from holdspeak.services.settings_service import redacted_settings
from holdspeak.setup_status import _trust_block
from holdspeak.trust_destinations import destination_inventory


def _legacy_remote_config() -> Config:
    config = Config()
    config.meeting.intel_enabled = True
    config.meeting.intel_provider = "cloud"
    config.meeting.intel_cloud_base_url = "https://legacy.example.test/v1"
    config.meeting.intel_cloud_model = "legacy-model"
    # Dictation remains an independent route and must stay visible.
    config.dictation.pipeline.enabled = True
    config.dictation.runtime.backend = "openai_compatible"
    return config


def test_settings_wire_reports_live_analysis_off() -> None:
    config = _legacy_remote_config()

    wire = redacted_settings(config)
    assert wire["meeting"]["intel_enabled"] is False

@pytest.mark.parametrize(
    ("reader",),
    [
        ("runtime",),
        ("egress",),
        ("profiles",),
        ("preflight",),
    ],
)
def test_doctor_reports_live_analysis_off_for_record(
    reader: str,
) -> None:
    config = _legacy_remote_config()
    checks = {
        "runtime": lambda: doctor._check_meeting_intel_runtime(config),
        "egress": lambda: doctor._check_meeting_intel_egress(config),
        "profiles": lambda: doctor._check_runtime_profiles(config),
        "preflight": lambda: doctor._check_meeting_intel_cloud_preflight(config),
    }

    check = checks[reader]()

    assert check.status == "PASS"
    assert "live analysis is off for record" in check.detail.lower()
    if reader == "profiles":
        assert "dictation:" in check.detail
        assert "meeting intel: live analysis is off for Record" in check.detail


def test_setup_trust_and_inventory_scope_live_analysis_off() -> None:
    config = _legacy_remote_config()

    trust = _trust_block(config)
    assert trust["transcript_egress"] == "none"
    assert "no transcript leaves" not in trust["egress_detail"].lower()
    assert "live analysis is off for record" in trust["egress_detail"].lower()
    assert "https://legacy.example.test/v1" not in trust["configured_endpoints"]

    inventory = destination_inventory(config)
    meeting_destination = next(row for row in inventory if row["id"] == "meeting_intel")
    dictation_destination = next(
        row for row in inventory if row["id"] == "dictation_runtime"
    )
    assert meeting_destination["enabled"] is False
    assert meeting_destination["destination"] == "Live analysis is off for Record"
    assert dictation_destination["enabled"] is True




def test_legacy_intel_write_is_ignored_and_dictation_settings_stay_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from holdspeak import config as config_module
    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.settings_service import SettingsService

    config_path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_path)
    config = _legacy_remote_config()
    config.save()
    before = Config.load()

    service = SettingsService(Database(tmp_path / "settings.db"))
    result = service.update_settings(
        Principal(PrincipalKind.OWNER, "hs201-followup"),
        {"meeting": {"intel_enabled": False}},
    )

    assert result["success"] is True
    after = Config.load()
    assert after.meeting.intel_enabled is True
    assert after.dictation.pipeline.enabled is before.dictation.pipeline.enabled
    assert after.dictation.runtime.backend == before.dictation.runtime.backend


def test_cloud_preflight_does_not_probe_legacy_meeting_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _legacy_remote_config()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("legacy meeting cloud preflight must not run")

    monkeypatch.setattr(urlrequest, "urlopen", fail_network)

    check = doctor._check_meeting_intel_cloud_preflight(config, skip_network=False)

    assert check.status == "PASS"
    assert "live analysis is off for record" in check.detail.lower()
