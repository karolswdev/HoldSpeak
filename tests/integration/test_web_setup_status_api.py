"""HS-42-01: GET /api/setup/status route shape (ready + blocked fixtures)."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.commands.doctor import DoctorCheck
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")


@pytest.fixture
def db_singleton():
    """Point the get_database() singleton at a temp DB for the duration."""
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = get_database(temp_dir / "setup.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def _stub_checks(monkeypatch, checks: list[DoctorCheck]) -> None:
    monkeypatch.setattr(
        "holdspeak.commands.doctor.collect_doctor_checks", lambda **_: checks
    )


def test_setup_status_shape_ready(isolated_config, db_singleton, monkeypatch) -> None:
    _stub_checks(monkeypatch, [DoctorCheck(name="Microphone", status="PASS", detail="ok")])
    resp = _client().get("/api/setup/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall"] == "ready"
    assert body["first_run"] is True
    # ready + first-run → the next step is the first-dictation test itself.
    assert body["primary_action"]["id"] == "first_dictation"
    assert {"web_bind", "auth_token_set", "transcript_egress"} <= set(body["trust"])
    assert body["trust"]["destinations"]
    assert {
        "operation", "enabled", "destination", "boundary", "data_class", "authority_basis",
        "background_ability", "revoke_action", "last_receipt",
    } <= set(body["trust"]["destinations"][0])
    assert {"enabled", "available", "tier"} <= set(body["presence"])
    assert isinstance(body["sections"], list) and body["sections"]


def test_setup_status_shape_blocked(isolated_config, db_singleton, monkeypatch) -> None:
    _stub_checks(
        monkeypatch,
        [
            DoctorCheck(name="Microphone", status="PASS", detail="ok"),
            DoctorCheck(name="Transcription backend", status="FAIL", detail="none", fix="Install a backend"),
        ],
    )
    body = _client().get("/api/setup/status").json()
    assert body["overall"] == "blocked"
    assert body["primary_action"]["id"] == "transcription-backend"
    assert body["primary_action"]["route"] == "/setup#transcription-backend"


def test_setup_status_first_run_false_after_milestone(
    isolated_config, db_singleton, monkeypatch
) -> None:
    _stub_checks(monkeypatch, [DoctorCheck(name="Microphone", status="PASS", detail="ok")])
    db_singleton.milestones.mark(FIRST_DICTATION_SUCCESS)
    body = _client().get("/api/setup/status").json()
    assert body["first_run"] is False
    assert body["primary_action"] is None
