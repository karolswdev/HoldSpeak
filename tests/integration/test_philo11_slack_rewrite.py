"""PHILO-11-02 fences for retiring the legacy Slack aftercare path.

These checks exercise the real Config, settings serializers, settings writer,
aftercare route, and desk actuator route.  Slack channel delivery belongs to the
channel worker; this file only proves that the old Settings webhook path cannot
still publish or expose its retained config value.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient

import holdspeak.config as config_module
import holdspeak.plugins.builtin.webhook_post_actuator as webhook_module
from holdspeak.config import Config
from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.principals import UNAUTHENTICATED
from holdspeak.services import credential_service, settings_service
from holdspeak.services.settings_service import SettingsService
from holdspeak.slack_export import document_markdown_for
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]

SENTINEL = "https://hooks.slack.com/services/SENTINEL/DO-NOT-RETURN"


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", path)
    return path


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = get_database(tmp_path / "rewrite.db")
    yield database
    reset_database()


@pytest.fixture
def seeded(db: Database) -> Database:
    db.meetings.save_meeting(
        MeetingState(
            id="m-rewrite",
            started_at=datetime(2026, 9, 30, 10, 0, 0),
            title="Rewrite boundary",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    {
                        "id": "a1",
                        "task": "Keep the channel boundary",
                        "owner": "Astra",
                        "due": "Friday",
                        "status": "pending",
                        "review_state": "accepted",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 9, 30, 10, 0, 0).isoformat(),
                    }
                ],
            ),
        )
    )
    return db


@pytest.fixture
def client(db: Database, settings_path: Path) -> TestClient:
    _ = db
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def _save_legacy_config(path: Path, *, mode: str = "yolo") -> None:
    config = Config()
    config.control_mode = mode
    config.meeting.slack_webhook_url = SENTINEL
    config.save(path=path)


def test_old_config_loads_but_aftercare_does_not_advertise_slack(
    client: TestClient, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path)

    response = client.get("/api/meetings/m-rewrite/aftercare")

    assert response.status_code == 200
    assert "slack_configured" not in response.json()
    assert SENTINEL not in response.text
    assert Config.load(settings_path).meeting.slack_webhook_url == SENTINEL


def test_settings_read_and_write_keep_the_retained_field_private(
    db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    config = Config.load(settings_path)

    # Reproduce the charter red case: removing only the credential registrations
    # leaves the retained Config field exposed by both serializers and writable.
    monkeypatch.delitem(settings_service.SECRET_PATHS, "slack_webhook_url", raising=False)
    monkeypatch.delitem(credential_service.SECRET_PATHS, "slack_webhook_url", raising=False)

    settings_payload = settings_service.redacted_settings(config)
    credential_payload = credential_service.redacted_settings(config)
    assert SENTINEL not in repr(settings_payload)
    assert SENTINEL not in repr(credential_payload)

    assert Config.load(settings_path).meeting.slack_webhook_url == SENTINEL


def test_settings_write_ignores_the_retained_field(
    db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    monkeypatch.delitem(settings_service.SECRET_PATHS, "slack_webhook_url", raising=False)
    monkeypatch.delitem(credential_service.SECRET_PATHS, "slack_webhook_url", raising=False)

    before = Config.load(settings_path).meeting.slack_webhook_url
    SettingsService(db).update_settings(
        UNAUTHENTICATED,
        {"meeting": {"slack_webhook_url": "https://hooks.slack.com/services/ATTACKER"}},
    )
    assert Config.load(settings_path).meeting.slack_webhook_url == before


def test_posture_aftercare_route_is_parked_and_never_posts(
    client: TestClient,
    settings_path: Path,
    seeded: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_legacy_config(settings_path)
    calls: list[tuple[str, object]] = []

    def fake_post(url: str, body: object, *, timeout: float):
        calls.append((url, body))
        return webhook_module.WebhookResponse(status=200, body="ok")

    monkeypatch.setattr(webhook_module, "_default_post", fake_post)
    response = client.post(
        "/api/meetings/m-rewrite/export/slack", json={"what": "digest"}
    )

    assert response.status_code == 400
    assert response.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert calls == []


def test_meeting_slack_proposal_approval_is_parked_but_rejection_works(
    client: TestClient, db: Database, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    proposal = db.actuators.record_proposal(
        meeting_id="m-rewrite",
        window_id="m-rewrite:aftercare",
        plugin_id="webhook_post",
        plugin_version="1",
        idempotency_key="legacy-slack-approval-1",
        target="slack",
        action="post_message",
        preview="historical Slack proposal",
        payload={"body": {"text": "historical Slack proposal"}},
        required_capabilities=["actuator"],
        fixed_destination=True,
    )

    approved = client.post(
        f"/api/meetings/m-rewrite/proposals/{proposal.id}/decision",
        json={"decision": "approved", "decided_by": "owner"},
    )
    assert approved.status_code == 400
    assert approved.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert db.actuators.get_proposal(proposal.id).status == "proposed"

    rejected = client.post(
        f"/api/meetings/m-rewrite/proposals/{proposal.id}/decision",
        json={"decision": "rejected", "decided_by": "owner"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["success"] is True
    assert rejected.json()["proposal"]["status"] == "rejected"


def test_desk_slack_target_is_parked(
    client: TestClient, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path)

    response = client.post(
        "/api/desk/actuators/slack/propose", json={"text": "free text"}
    )

    assert response.status_code == 400
    assert response.json()["error"] == "slack_moved_to_channel"


def test_historical_slack_proposals_remain_readable(
    client: TestClient, db: Database, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    proposal = db.actuators.record_proposal(
        meeting_id="m-rewrite",
        window_id="m-rewrite:aftercare",
        plugin_id="webhook_post",
        plugin_version="1",
        idempotency_key="legacy-slack-receipt-1",
        target="slack",
        action="post_message",
        preview="historical proposal",
        payload={"body": {"text": "historical proposal"}},
        required_capabilities=["actuator"],
        fixed_destination=True,
    )

    response = client.get("/api/meetings/m-rewrite/proposals")

    assert response.status_code == 200
    rows = response.json()["proposals"]
    assert any(row["id"] == proposal.id for row in rows)
    assert SENTINEL not in response.text

    # Mint the retained historical receipt through its real database lifecycle.
    # This records a past outcome; it invokes no connector or network edge.
    db.actuators.transition_proposal(proposal.id, to_status="approved", actor="historical-owner")
    receipt = db.actuators.transition_proposal(
        proposal.id, to_status="executed", actor="historical-owner",
        result={"status": 200, "body": "ok"},
    )
    history = client.get("/api/meetings/m-rewrite/proposals").json()["proposals"]
    retained = next(row for row in history if row["id"] == proposal.id)
    assert retained["status"] == "executed" and retained["result"] == receipt.result
    assert retained["executed_at"] == receipt.executed_at
    assert db.actuators.last_execution_receipt("slack") == receipt.executed_at


def test_legacy_slack_connector_is_removed() -> None:
    import holdspeak.slack_export as slack_export

    assert not hasattr(slack_export, "build_slack_connector")
    assert document_markdown_for(
        {"meeting_title": "A meeting", "meeting_date": "2026-09-30", "is_empty": False},
        "digest",
    ).startswith("# A meeting")
