"""Integration tests for local activity intelligence web APIs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
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
