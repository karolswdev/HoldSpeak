from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = get_database(temp_dir / "first-value.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client() -> TestClient:
    return TestClient(
        MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(), on_stop=MagicMock(),
                get_state=MagicMock(return_value={}),
            )
        ).app
    )


def test_continue_later_is_durable_without_faking_first_success(isolated) -> None:
    client = _client()
    before = client.get("/api/setup/status").json()
    assert before["first_run"] is True
    assert before["arrival_required"] is True

    saved = client.put(
        "/api/setup/onboarding", json={"disposition": "dismissed"}
    )
    assert saved.status_code == 200

    after = client.get("/api/setup/status").json()
    assert after["first_run"] is True
    assert after["arrival_required"] is False
    assert after["onboarding"]["disposition"] == "dismissed"
    assert isolated.milestones.is_set(FIRST_DICTATION_SUCCESS) is False


def test_first_value_receipt_never_accepts_or_stores_phrase_content(isolated) -> None:
    client = _client()
    rejected = client.post(
        "/api/setup/first-value/start",
        json={"destination": "this_machine", "transcript": "private phrase"},
    )
    assert rejected.status_code == 400

    started = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    )
    assert started.status_code == 201
    attempt = started.json()["attempt"]
    assert "text" not in attempt and "transcript" not in attempt

    with isolated._connection() as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(first_value_attempts)")
        }
    assert not {"text", "phrase", "transcript", "content", "audio"}.intersection(columns)


def test_success_records_mechanics_and_closes_arrival_exactly_once(isolated) -> None:
    client = _client()
    attempt_id = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    ).json()["attempt"]["id"]
    payload = {
        "outcome": "success", "steps": 1, "decisions": 0,
        "destination": "this_machine",
    }
    first = client.post(
        f"/api/setup/first-value/{attempt_id}/finish", json=payload
    )
    second = client.post(
        f"/api/setup/first-value/{attempt_id}/finish", json=payload
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["attempt"] == second.json()["attempt"]
    assert isolated.milestones.is_set(FIRST_DICTATION_SUCCESS) is True
    assert isolated.onboarding.disposition()["disposition"] == "completed"
    status = client.get("/api/setup/status").json()
    assert status["first_run"] is False
    assert status["arrival_required"] is False
    latest = status["onboarding"]["latest_first_value"]
    assert latest["steps"] == 1 and latest["decisions"] == 0
    assert latest["destination"] == "this_machine"
    assert latest["failure_category"] is None


def test_failure_category_is_bounded_and_retained_without_content(isolated) -> None:
    client = _client()
    attempt_id = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    ).json()["attempt"]["id"]
    failed = client.post(
        f"/api/setup/first-value/{attempt_id}/finish",
        json={
            "outcome": "failure", "steps": 1, "decisions": 0,
            "destination": "this_machine", "failure_category": "permission_denied",
        },
    )
    assert failed.status_code == 200
    assert failed.json()["attempt"]["failure_category"] == "permission_denied"
    assert isolated.onboarding.latest_attempt()["succeeded_at"] is None

    # A delayed/replayed success for the same terminal attempt must not turn a
    # failed journey into a success milestone.
    replay = client.post(
        f"/api/setup/first-value/{attempt_id}/finish",
        json={
            "outcome": "success", "steps": 1, "decisions": 0,
            "destination": "this_machine",
        },
    )
    assert replay.status_code == 200
    assert replay.json()["attempt"] == failed.json()["attempt"]
    assert isolated.milestones.is_set(FIRST_DICTATION_SUCCESS) is False
    assert isolated.onboarding.disposition() is None
