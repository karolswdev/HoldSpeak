"""HS-201 follow-up: doctor names the exact assigned summary route."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.db as hsdb
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.commands import doctor
from holdspeak.commands.doctor import _check_trust_destinations

from tests.unit.test_mesh_liveness_surfaces import _modern_mesh_summary_assignment


@pytest.fixture
def summary_db(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "summary-doctor.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    yield db
    reset_database()


def test_doctor_names_assigned_summary_route_and_ignores_legacy_pointer(summary_db) -> None:
    _modern_mesh_summary_assignment(summary_db)
    config = SimpleNamespace(
        meeting=SimpleNamespace(
            # This pointer is legacy state. The SERVICE assignment above is
            # the route that a Meeting summary actually uses.
            intel_enabled=True,
            intel_provider="cloud",
            intel_cloud_model="legacy-model",
            intel_cloud_api_key_env="LEGACY_KEY",
            intel_cloud_base_url="https://legacy.example.test/v1",
            intel_profile_id="legacyprofile",
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=False),
            runtime=SimpleNamespace(profile_id=None),
        ),
    )

    check = doctor._check_runtime_profiles(config)

    assert check.status == "PASS"
    assert "Meeting summary: profile 'Pocket 4B' (mesh node 'walk-edge')" in check.detail
    assert "Live analysis is off for Record." in check.detail
    assert "legacyprofile" not in check.detail


def test_doctor_quietly_names_unavailable_summary(summary_db) -> None:
    config = SimpleNamespace(
        meeting=SimpleNamespace(intel_profile_id="legacyprofile"),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=False),
            runtime=SimpleNamespace(profile_id=None),
        ),
    )

    check = doctor._check_runtime_profiles(config)

    assert check.status == "PASS"
    assert "Meeting summary: unavailable (no assignment)" in check.detail
    assert "Live analysis is off for Record." in check.detail
    assert "legacyprofile" not in check.detail


def test_doctor_trust_inventory_uses_the_assigned_summary_route(summary_db) -> None:
    _modern_mesh_summary_assignment(summary_db)
    config = Config()
    config.meeting.intel_profile_id = "legacyprofile"

    check = _check_trust_destinations(config)

    assert check.status == "WARN"
    assert "Meeting summary" in check.detail
