"""Integration tests for local activity intelligence web APIs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak import db as db_module
from holdspeak.db import MeetingDatabase, reset_database
from holdspeak.web_server import MeetingWebServer

pytestmark = [pytest.mark.requires_meeting]


@pytest.fixture
def activity_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MeetingDatabase:
    reset_database()
    db_path = tmp_path / "holdspeak.db"
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_path)
    database = MeetingDatabase(db_path)
    yield database
    reset_database()


@pytest.fixture
def test_client(activity_db: MeetingDatabase) -> TestClient:
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        get_state=MagicMock(return_value={}),
    )
    return TestClient(server.app)


def test_activity_page_serves_browser_surface(test_client: TestClient) -> None:
    response = test_client.get("/activity")

    assert response.status_code == 200
    assert "Local Activity" in response.text
    assert "/api/activity/status" in response.text
    assert "/api/activity/meeting-candidates/preview" in response.text
    assert "candidate-status-filter" in response.text
    assert "No preview loaded" in response.text
    assert "candidates-message" in response.text


def test_activity_status_reports_default_enabled_state(test_client: TestClient) -> None:
    response = test_client.get("/api/activity/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["enabled"] is True
    assert payload["settings"]["paused"] is False
    assert payload["settings"]["retention_days"] == 30
    assert payload["domain_rules"] == []


def test_activity_records_endpoint_returns_serialized_records(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/99",
        title="PR 99",
        domain="github.com",
        visit_count=2,
        last_seen_at=datetime(2026, 4, 26, 12, 0),
        entity_type="github_pull_request",
        entity_id="openai/codex#99",
    )

    response = test_client.get("/api/activity/records")

    assert response.status_code == 200
    payload = response.json()
    assert payload["records"][0]["entity_id"] == "openai/codex#99"
    assert payload["entity_counts"] == {"github_pull_request": 1}


def test_activity_settings_can_pause_ingestion(test_client: TestClient) -> None:
    response = test_client.put("/api/activity/settings", json={"enabled": False, "retention_days": 10})

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["enabled"] is False
    assert payload["settings"]["paused"] is True
    assert payload["settings"]["retention_days"] == 10
    assert payload["status"]["settings"]["enabled"] is False


def test_activity_domain_exclusion_and_clear_controls(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    activity_db.upsert_activity_record(
        source_browser="firefox",
        url="https://miro.com/app/board/uXjVTest/",
        domain="miro.com",
        entity_type="miro_board",
        entity_id="uXjVTest",
    )

    rule_response = test_client.post(
        "/api/activity/domains",
        json={"domain": "miro.com", "action": "exclude"},
    )
    assert rule_response.status_code == 200
    assert rule_response.json()["rule"]["domain"] == "miro.com"

    clear_response = test_client.delete("/api/activity/records?domain=miro.com")
    assert clear_response.status_code == 200
    assert clear_response.json()["deleted"] == 1
    assert activity_db.list_activity_records() == []

    delete_rule_response = test_client.delete("/api/activity/domains/miro.com")
    assert delete_rule_response.status_code == 200
    assert delete_rule_response.json()["deleted"] is True


def test_activity_project_rule_api_previews_and_applies_mappings(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    activity_db.create_project(project_id="holdspeak", name="HoldSpeak")
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 mapping",
        domain="example.atlassian.net",
        last_seen_at=datetime(2026, 4, 26, 12, 0),
        entity_type="jira_ticket",
        entity_id="HS-123",
    )

    create_response = test_client.post(
        "/api/activity/project-rules",
        json={
            "project_id": "holdspeak",
            "name": "HoldSpeak Jira",
            "match_type": "entity_id_prefix",
            "entity_type": "jira_ticket",
            "pattern": "HS-",
            "priority": 200,
            "enabled": True,
        },
    )
    assert create_response.status_code == 200
    rule = create_response.json()["rule"]
    assert rule["project_name"] == "HoldSpeak"

    preview_response = test_client.post(
        "/api/activity/project-rules/preview",
        json={
            "project_id": "holdspeak",
            "match_type": "entity_id_prefix",
            "entity_type": "jira_ticket",
            "pattern": "HS-",
        },
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["count"] == 1
    assert preview_response.json()["matches"][0]["entity_id"] == "HS-123"

    apply_response = test_client.post("/api/activity/project-rules/apply")
    assert apply_response.status_code == 200
    assert apply_response.json()["updated"] == 1

    records_response = test_client.get("/api/activity/records?project_id=holdspeak")
    assert records_response.status_code == 200
    assert records_response.json()["records"][0]["project_id"] == "holdspeak"

    update_response = test_client.put(
        f"/api/activity/project-rules/{rule['id']}",
        json={"enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["rule"]["enabled"] is False

    delete_response = test_client.delete(f"/api/activity/project-rules/{rule['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_activity_meeting_candidate_api_previews_persists_and_updates(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://outlook.office.com/calendar/item/customer-sync",
        title="Customer sync meeting",
        domain="outlook.office.com",
        last_seen_at=datetime(2026, 4, 27, 9, 0),
    )

    preview_response = test_client.get("/api/activity/meeting-candidates/preview")
    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["count"] == 1
    assert preview["candidates"][0]["title"] == "Customer sync meeting"
    assert preview["candidates"][0]["source_activity_record_id"] == record.id

    create_response = test_client.post(
        "/api/activity/meeting-candidates",
        json={
            "source_connector_id": preview["candidates"][0]["source_connector_id"],
            "source_activity_record_id": preview["candidates"][0]["source_activity_record_id"],
            "title": preview["candidates"][0]["title"],
            "meeting_url": preview["candidates"][0]["meeting_url"],
            "confidence": preview["candidates"][0]["confidence"],
        },
    )
    assert create_response.status_code == 200
    candidate = create_response.json()["candidate"]
    assert candidate["status"] == "candidate"
    duplicate_response = test_client.post(
        "/api/activity/meeting-candidates",
        json={
            "source_connector_id": preview["candidates"][0]["source_connector_id"],
            "source_activity_record_id": preview["candidates"][0]["source_activity_record_id"],
            "title": "Customer sync meeting updated",
            "meeting_url": preview["candidates"][0]["meeting_url"],
            "confidence": 0.9,
        },
    )
    assert duplicate_response.status_code == 200
    duplicate = duplicate_response.json()["candidate"]
    assert duplicate["id"] == candidate["id"]
    assert duplicate["title"] == "Customer sync meeting updated"

    list_response = test_client.get("/api/activity/meeting-candidates")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    armed_response = test_client.put(
        f"/api/activity/meeting-candidates/{candidate['id']}/status",
        json={"status": "armed"},
    )
    assert armed_response.status_code == 200
    assert armed_response.json()["candidate"]["status"] == "armed"

    delete_response = test_client.delete("/api/activity/meeting-candidates?status=armed")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1


def test_activity_meeting_candidate_manual_start_marks_started(
    activity_db: MeetingDatabase,
) -> None:
    candidate = activity_db.create_activity_meeting_candidate(
        source_connector_id="calendar_activity",
        title="Customer sync meeting",
        meeting_url="https://teams.microsoft.com/l/meetup-join/customer-sync",
        confidence=0.9,
    )
    on_start = MagicMock(return_value={"id": "meeting-1", "title": "Untitled"})
    on_update_meeting = MagicMock(
        return_value={"id": "meeting-1", "title": "Customer sync meeting", "meeting_active": True}
    )
    server = MeetingWebServer(
        on_bookmark=MagicMock(),
        on_stop=MagicMock(),
        on_start=on_start,
        on_update_meeting=on_update_meeting,
        get_state=MagicMock(return_value={}),
    )
    broadcast_events: list[tuple[str, object]] = []
    server.broadcast = lambda message_type, data: broadcast_events.append((message_type, data))
    client = TestClient(server.app)

    before_start = activity_db.get_activity_meeting_candidate(candidate.id)
    assert before_start is not None
    assert before_start.status == "candidate"
    assert before_start.started_meeting_id is None

    response = client.post(f"/api/activity/meeting-candidates/{candidate.id}/start")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meeting"]["id"] == "meeting-1"
    assert payload["meeting"]["title"] == "Customer sync meeting"
    assert payload["candidate"]["status"] == "started"
    assert payload["candidate"]["started_meeting_id"] == "meeting-1"
    on_start.assert_called_once_with()
    on_update_meeting.assert_called_once_with(title="Customer sync meeting", tags=None)
    assert broadcast_events[0][0] == "meeting_started"
    assert broadcast_events[0][1]["activity_meeting_candidate_id"] == candidate.id

    persisted = activity_db.get_activity_meeting_candidate(candidate.id)
    assert persisted is not None
    assert persisted.status == "started"
    assert persisted.started_meeting_id == "meeting-1"


def test_activity_meeting_candidate_manual_start_requires_runtime_start_support(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    candidate = activity_db.create_activity_meeting_candidate(
        source_connector_id="calendar_activity",
        title="Customer sync meeting",
    )

    response = test_client.post(f"/api/activity/meeting-candidates/{candidate.id}/start")

    assert response.status_code == 501
    assert response.json()["success"] is False
    persisted = activity_db.get_activity_meeting_candidate(candidate.id)
    assert persisted is not None
    assert persisted.status == "candidate"
    assert persisted.started_meeting_id is None


def test_github_enrichment_preview_is_visible_and_disabled_by_default(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/42",
        title="PR 42",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 27, 11, 0),
        entity_type="github_pull_request",
        entity_id="openai/codex#42",
    )

    preview_response = test_client.get("/api/activity/enrichment/github/preview")

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["connector"]["id"] == "gh"
    assert preview["connector"]["enabled"] is False
    assert preview["count"] == 1
    assert preview["commands"][0]["activity_record_id"] == record.id
    assert preview["commands"][0]["command"][1:4] == ["pr", "view", "42"]

    run_response = test_client.post("/api/activity/enrichment/github/run", json={})
    assert run_response.status_code == 403
    assert run_response.json()["success"] is False
    assert activity_db.list_activity_annotations(source_connector_id="gh") == []


def test_github_enrichment_run_requires_explicit_enablement(
    test_client: TestClient,
    activity_db: MeetingDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/issues/99",
        title="Issue 99",
        domain="github.com",
        entity_type="github_issue",
        entity_id="openai/codex#99",
    )

    def fake_run(db, records, **kwargs):
        record = list(records)[0]
        annotation = db.create_activity_annotation(
            activity_record_id=record.id,
            source_connector_id="gh",
            annotation_type="github_issue",
            title="Issue 99 enriched",
            value={"state": "OPEN"},
            confidence=1.0,
        )
        return [
            SimpleNamespace(
                to_payload=lambda: {
                    "plan": {"activity_record_id": record.id},
                    "annotation": {
                        "id": annotation.id,
                        "title": annotation.title,
                    },
                    "error": None,
                }
            )
        ]

    monkeypatch.setattr("holdspeak.activity_github.run_github_cli_enrichment", fake_run)
    enable_response = test_client.put(
        "/api/activity/enrichment/connectors/gh",
        json={"enabled": True, "settings": {"timeout_seconds": 2.0}},
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["connector"]["enabled"] is True

    run_response = test_client.post("/api/activity/enrichment/github/run", json={"limit": 1})

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["results"][0]["annotation"]["title"] == "Issue 99 enriched"
    annotations = activity_db.list_activity_annotations(source_connector_id="gh")
    assert len(annotations) == 1
    assert annotations[0].annotation_type == "github_issue"


def test_jira_enrichment_preview_is_visible_and_disabled_by_default(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 activity mapping",
        domain="example.atlassian.net",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="jira_ticket",
        entity_id="HS-123",
    )

    connectors_response = test_client.get("/api/activity/enrichment/connectors")
    assert connectors_response.status_code == 200
    connectors = connectors_response.json()["connectors"]
    assert {connector["id"] for connector in connectors} >= {"gh", "jira"}

    preview_response = test_client.get("/api/activity/enrichment/jira/preview")

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview["connector"]["id"] == "jira"
    assert preview["connector"]["enabled"] is False
    assert preview["count"] == 1
    assert preview["commands"][0]["activity_record_id"] == record.id
    assert preview["commands"][0]["command"][1:] == ["issue", "view", "HS-123", "--plain"]

    run_response = test_client.post("/api/activity/enrichment/jira/run", json={})
    assert run_response.status_code == 403
    assert run_response.json()["success"] is False
    assert activity_db.list_activity_annotations(source_connector_id="jira") == []


def test_jira_enrichment_run_requires_explicit_enablement(
    test_client: TestClient,
    activity_db: MeetingDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 activity mapping",
        domain="example.atlassian.net",
        entity_type="jira_ticket",
        entity_id="HS-123",
    )

    def fake_run(db, records, **kwargs):
        record = list(records)[0]
        annotation = db.create_activity_annotation(
            activity_record_id=record.id,
            source_connector_id="jira",
            annotation_type="jira_ticket",
            title="HS-123 enriched",
            value={"status": "In Progress"},
            confidence=1.0,
        )
        return [
            SimpleNamespace(
                to_payload=lambda: {
                    "plan": {"activity_record_id": record.id},
                    "annotation": {
                        "id": annotation.id,
                        "title": annotation.title,
                    },
                    "error": None,
                }
            )
        ]

    monkeypatch.setattr("holdspeak.activity_jira.run_jira_cli_enrichment", fake_run)
    enable_response = test_client.put(
        "/api/activity/enrichment/connectors/jira",
        json={"enabled": True, "settings": {"timeout_seconds": 2.0}},
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["connector"]["enabled"] is True

    run_response = test_client.post("/api/activity/enrichment/jira/run", json={"limit": 1})

    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["results"][0]["annotation"]["title"] == "HS-123 enriched"
    annotations = activity_db.list_activity_annotations(source_connector_id="jira")
    assert len(annotations) == 1
    assert annotations[0].annotation_type == "jira_ticket"
