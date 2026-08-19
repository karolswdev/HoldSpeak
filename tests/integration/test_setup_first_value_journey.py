from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.db import FIRST_DICTATION_SUCCESS, get_database, reset_database
from holdspeak.services.errors import ValidationError
from holdspeak.services.setup_service import SetupService
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
    assert {item.name for item in isolated.directories.list()} >= {
        "Inbox", "Personal", "Work", "Meetings", "Decisions", "Reference",
    }


def test_disposition_never_persists_when_ordinary_seed_fails(
    isolated, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_seed(_database):
        raise RuntimeError("seed storage unavailable")

    monkeypatch.setattr("holdspeak.db.seed.apply_seed", broken_seed)
    with pytest.raises(RuntimeError, match="seed storage unavailable"):
        SetupService(isolated).set_onboarding_disposition(
            None, {"disposition": "dismissed"},
        )
    assert isolated.onboarding.disposition() is None


def test_invalid_disposition_has_no_seed_side_effect(isolated) -> None:
    with pytest.raises(ValidationError, match="invalid onboarding disposition"):
        SetupService(isolated).set_onboarding_disposition(None, {"disposition": "nope"})
    assert isolated.onboarding.disposition() is None
    assert isolated.directories.list() == []


def test_first_value_receipt_never_accepts_or_stores_phrase_content(isolated) -> None:
    client = _client()
    for content_key in ("text", "phrase", "transcript", "content", "audio", "clipboard", "note_body"):
        rejected = client.post(
            "/api/setup/first-value/start",
            json={"destination": "this_machine", content_key: "private phrase"},
        )
        assert rejected.status_code == 400

    started = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    )
    assert started.status_code == 201
    attempt = started.json()["attempt"]
    assert "text" not in attempt and "transcript" not in attempt

    with isolated._connection() as conn:
        attempt_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(first_value_attempts)")
        }
        event_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(first_value_events)")
        }
    forbidden = {"text", "phrase", "transcript", "content", "audio"}
    assert not forbidden.intersection(attempt_columns)
    assert not forbidden.intersection(event_columns)


def test_success_requires_transcript_receipt_and_leaves_handoff_to_story_05(isolated) -> None:
    client = _client()
    attempt_id = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    ).json()["attempt"]["id"]
    premature = client.post(
        f"/api/setup/first-value/{attempt_id}/finish",
        json={"outcome": "success", "destination": "this_machine"},
    )
    assert premature.status_code == 400
    recorded = client.post(
        f"/api/setup/first-value/{attempt_id}/event",
        json={
            "event_id": f"{attempt_id}:1:transcript_received",
            "kind": "transcript_received",
        },
    )
    assert recorded.status_code == 201
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
    assert isolated.milestones.is_set(FIRST_DICTATION_SUCCESS) is False
    assert isolated.onboarding.disposition() is None
    status = client.get("/api/setup/status").json()
    assert status["first_run"] is True
    assert status["arrival_required"] is True
    latest = status["onboarding"]["latest_first_value"]
    assert latest["steps"] == 1 and latest["decisions"] == 0
    assert latest["event_count"] == 2
    assert latest["elapsed_ms"] >= 0
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


def test_first_value_mechanics_derive_from_bounded_events_not_client_counts(
    isolated,
) -> None:
    client = _client()
    attempt_id = client.post(
        "/api/setup/first-value/start", json={"destination": "this_machine"}
    ).json()["attempt"]["id"]

    for content_key in ("text", "phrase", "transcript", "content", "audio", "clipboard", "note_body"):
        leaked = client.post(
            f"/api/setup/first-value/{attempt_id}/event",
            json={
                "event_id": f"{attempt_id}:1:capture_started",
                "kind": "capture_started",
                content_key: "this must never enter measurement",
            },
        )
        assert leaked.status_code == 400
    with pytest.raises(ValidationError, match="events accept only event_id and kind"):
        SetupService(isolated).record_event(
            None, attempt_id, {
                "event_id": f"{attempt_id}:1:capture_started",
                "kind": "capture_started",
                "clipboard": "private value",
            },
        )

    event = {
        "event_id": f"{attempt_id}:1:capture_started",
        "kind": "capture_started",
    }
    first = client.post(f"/api/setup/first-value/{attempt_id}/event", json=event)
    replay = client.post(f"/api/setup/first-value/{attempt_id}/event", json=event)
    assert first.status_code == replay.status_code == 201
    assert first.json()["event"] == replay.json()["event"]

    kept = client.post(
        f"/api/setup/first-value/{attempt_id}/event",
        json={
            "event_id": f"{attempt_id}:2:keep_selected",
            "kind": "keep_selected",
        },
    )
    assert kept.status_code == 201

    transcript = client.post(
        f"/api/setup/first-value/{attempt_id}/event",
        json={
            "event_id": f"{attempt_id}:3:transcript_received",
            "kind": "transcript_received",
        },
    )
    assert transcript.status_code == 201

    finished = client.post(
        f"/api/setup/first-value/{attempt_id}/finish",
        json={
            "outcome": "success",
            # Deliberately false client assertions: the event ledger wins.
            "steps": 20,
            "decisions": 20,
            "destination": "this_machine",
        },
    )
    assert finished.status_code == 200
    receipt = finished.json()["attempt"]
    assert receipt["event_count"] == 4
    assert receipt["steps"] == 2  # dictation requested + Keep as Note
    assert receipt["decisions"] == 1
    assert receipt["elapsed_ms"] >= 0
