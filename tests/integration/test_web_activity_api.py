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
    """HS-10-07: page rebuilt on AppLayout. Title text + every DOM ID
    the activity-app.js module reads must still be present. The
    /api/activity/* endpoint strings now live in the bundled JS chunk
    (referenced from the served HTML) rather than inline."""
    import re

    response = test_client.get("/activity")
    assert response.status_code == 200
    body = response.text

    # New page title + DOM contracts JS depends on.
    assert "Local activity" in body
    assert 'id="enabled-pill"' in body
    assert 'id="candidate-status-filter"' in body
    assert 'id="candidates-message"' in body
    assert 'id="record-count"' in body
    assert 'id="rule-project"' in body
    assert 'id="meeting-candidates"' in body

    # HS-9-12: connectors panel container is present.
    assert 'id="connectors"' in body
    assert 'id="connectors-message"' in body

    # Bundled JS still calls the existing /api/activity endpoints, plus
    # the new HS-9-12 connector endpoints.
    match = re.search(r'src="(/_built/_astro/hoisted\.[^"]+\.js)"', body)
    assert match, "expected hoisted activity JS chunk reference"
    js = test_client.get(match.group(1)).text
    assert "/api/activity/status" in js
    assert "/api/activity/meeting-candidates/preview" in js
    assert "/api/activity/enrichment/connectors" in js


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


def test_connector_list_includes_calendar_with_capabilities(
    test_client: TestClient,
) -> None:
    """HS-9-12: the connector list surfaces every known connector
    (gh, jira, calendar_activity), each annotated with its kind and
    capabilities so the browser can render appropriate controls."""
    response = test_client.get("/api/activity/enrichment/connectors")
    assert response.status_code == 200
    payload = response.json()
    by_id = {c["id"]: c for c in payload["connectors"]}
    assert set(by_id) == {"gh", "jira", "calendar_activity"}
    assert by_id["gh"]["capabilities"] == ["annotations"]
    assert by_id["gh"]["kind"] == "cli_enrichment"
    assert by_id["gh"]["requires_cli"] == "gh"
    assert "cli_status" in by_id["gh"]
    assert by_id["jira"]["capabilities"] == ["annotations"]
    assert by_id["calendar_activity"]["capabilities"] == ["candidates"]
    assert by_id["calendar_activity"]["kind"] == "candidate_inference"
    assert by_id["calendar_activity"]["requires_cli"] is None
    assert "cli_status" not in by_id["calendar_activity"]
    # HS-13-04: every first-party pack is labelled first-party.
    for connector_id in ("gh", "jira", "calendar_activity"):
        assert by_id[connector_id]["source"] == "first-party"


def test_clear_connector_annotations_deletes_only_that_connectors_output(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-12: clearing annotations is scoped to the connector
    that produced them; other connectors' annotations stay put."""
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/issues/99",
        title="Issue 99",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_issue",
        entity_id="anthropic/holdspeak#99",
    )
    activity_db.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_issue",
        title="Issue 99 enriched",
    )
    activity_db.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="jira",
        annotation_type="jira_ticket",
        title="HS-123 enriched",
    )

    response = test_client.delete("/api/activity/enrichment/connectors/gh/annotations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["deleted"] == 1
    assert payload["connector_id"] == "gh"
    # HS-13-05: clear surfaces also report runs_deleted; this
    # connector had no run history so the count is zero.
    assert payload["runs_deleted"] == 0

    assert activity_db.list_activity_annotations(source_connector_id="gh") == []
    remaining = activity_db.list_activity_annotations(source_connector_id="jira")
    assert len(remaining) == 1


def test_clear_connector_candidates_deletes_only_that_connectors_output(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-12: calendar_activity candidates can be cleared via the
    connector-scoped DELETE endpoint."""
    activity_db.create_activity_meeting_candidate(
        source_connector_id="calendar_activity",
        title="Architecture sync",
    )

    response = test_client.delete(
        "/api/activity/enrichment/connectors/calendar_activity/candidates"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["deleted"] == 1
    assert payload["connector_id"] == "calendar_activity"

    assert activity_db.list_activity_meeting_candidates() == []


def test_clear_connector_unknown_connector_returns_404(test_client: TestClient) -> None:
    """HS-9-12: only known connector ids are accepted."""
    response = test_client.delete(
        "/api/activity/enrichment/connectors/not-a-connector/annotations"
    )
    assert response.status_code == 404


def test_extension_events_endpoint_creates_records(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-03: posting events to the loopback endpoint upserts
    activity records under source_browser=firefox_ext."""
    response = test_client.post(
        "/api/activity/extension/events",
        json={
            "events": [
                {
                    "url": "https://github.com/anthropic/holdspeak/pull/9",
                    "title": "PR 9",
                    "visited_at": "2026-04-29T20:30:00",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["accepted"]) == 1
    assert payload["rejected"] == []

    records = activity_db.list_activity_records(source_browser="firefox_ext")
    assert len(records) == 1
    assert records[0].entity_type == "github_pull_request"


def test_extension_events_rejects_sensitive_fields(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-03: events shipping page-body / cookies / form data
    are rejected. The DB stays empty."""
    response = test_client.post(
        "/api/activity/extension/events",
        json={
            "events": [
                {
                    "url": "https://example.com/page",
                    "title": "Has cookies",
                    "visited_at": "2026-04-29T20:30:00",
                    "cookies": "session=abc123",
                },
                {
                    "url": "https://example.com/page2",
                    "title": "Has form data",
                    "visited_at": "2026-04-29T20:30:01",
                    "form_data": {"username": "a"},
                },
                {
                    "url": "https://example.com/page3",
                    "title": "Private",
                    "visited_at": "2026-04-29T20:30:02",
                    "private": True,
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] == []
    rejected_reasons = sorted(r["reason"] for r in payload["rejected"])
    assert rejected_reasons[0].startswith("forbidden_field:")
    assert rejected_reasons[1].startswith("forbidden_field:")
    assert "private_browsing_blocked" in rejected_reasons

    assert activity_db.list_activity_records(source_browser="firefox_ext") == []


def test_extension_events_applies_project_rules(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-03: extension records pick up the same project mapping
    as imported history records."""
    activity_db.create_project(project_id="holdspeak", name="HoldSpeak")
    activity_db.create_activity_project_rule(
        project_id="holdspeak",
        match_type="domain",
        pattern="github.com",
        name="GitHub",
    )

    response = test_client.post(
        "/api/activity/extension/events",
        json={
            "events": [
                {
                    "url": "https://github.com/anthropic/holdspeak/pull/10",
                    "title": "PR 10",
                    "visited_at": "2026-04-29T20:30:00",
                },
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["project_rule_updates"] >= 1
    records = activity_db.list_activity_records(source_browser="firefox_ext")
    assert records[0].project_id == "holdspeak"


def test_connector_dry_run_returns_uniform_shape_per_connector(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-13: every connector returns the same dry-run payload shape."""
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/7",
        title="PR 7",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#7",
    )

    for connector_id in ("gh", "jira", "calendar_activity"):
        response = test_client.get(
            f"/api/activity/enrichment/connectors/{connector_id}/dry-run"
        )
        assert response.status_code == 200, response.text
        payload = response.json()["dry_run"]
        assert payload["connector_id"] == connector_id
        for key in (
            "kind",
            "capabilities",
            "enabled",
            "cli_required",
            "cli_available",
            "commands",
            "proposed_annotations",
            "proposed_candidates",
            "warnings",
            "permission_notes",
            "truncated",
        ):
            assert key in payload, f"missing key {key} for {connector_id}"


def test_connector_dry_run_does_not_mutate_db(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-9-13: dry-run is mutation-free — the DB row counts for
    annotations and candidates are unchanged after dry-running every
    connector."""
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/7",
        title="PR 7",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#7",
    )
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://calendar.google.com/calendar/u/0/r/eventedit/abc?starts=2026-05-01T10:00",
        title="2026-05-01 10:00-11:00 Architecture sync",
        domain="calendar.google.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
    )

    annotations_before = activity_db.list_activity_annotations(limit=1000)
    candidates_before = activity_db.list_activity_meeting_candidates()

    for connector_id in ("gh", "jira", "calendar_activity"):
        response = test_client.get(
            f"/api/activity/enrichment/connectors/{connector_id}/dry-run"
        )
        assert response.status_code == 200

    annotations_after = activity_db.list_activity_annotations(limit=1000)
    candidates_after = activity_db.list_activity_meeting_candidates()
    assert [a.id for a in annotations_after] == [a.id for a in annotations_before]
    assert [c.id for c in candidates_after] == [c.id for c in candidates_before]


def test_connector_dry_run_unknown_connector_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/api/activity/enrichment/connectors/nope/dry-run"
    )
    assert response.status_code == 404


def test_clear_connector_capability_mismatch_returns_400(
    test_client: TestClient,
) -> None:
    """HS-9-12: clearing candidates on an annotations-only connector
    is rejected — it would silently no-op otherwise."""
    response = test_client.delete(
        "/api/activity/enrichment/connectors/gh/candidates"
    )
    assert response.status_code == 400
    response = test_client.delete(
        "/api/activity/enrichment/connectors/calendar_activity/annotations"
    )
    assert response.status_code == 400


def test_put_connector_settings_accepts_schema_keys(test_client: TestClient) -> None:
    """HS-13-03: a setting key declared on the gh pack's schema
    is accepted, persisted, and reflected back."""
    response = test_client.put(
        "/api/activity/enrichment/connectors/gh",
        json={"enabled": False, "settings": {"timeout_seconds": 10.0}},
    )
    assert response.status_code == 200
    assert response.json()["connector"]["settings"]["timeout_seconds"] == 10.0


def test_put_connector_settings_rejects_unknown_key(test_client: TestClient) -> None:
    """HS-13-03: a key not on the pack's schema returns 400 with
    a message naming the offending keys + the allowed set, so a
    misconfigured client can fix the call without guessing."""
    response = test_client.put(
        "/api/activity/enrichment/connectors/gh",
        json={"enabled": False, "settings": {"hidden_token": "leak"}},
    )
    assert response.status_code == 400
    body = response.json()
    assert "hidden_token" in body["error"]
    assert "timeout_seconds" in body["error"]


def test_github_run_records_a_connector_run_row(
    test_client: TestClient,
    activity_db: MeetingDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HS-13-05: a successful gh enrichment writes one
    `connector_runs` row with succeeded=true, populated counts,
    and the run shows up via the new GET runs endpoint."""
    activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/issues/99",
        title="Issue 99",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_issue",
        entity_id="anthropic/holdspeak#99",
    )

    from holdspeak.activity_github import (
        GithubCliCommandPlan,
        GithubCliRunResult,
    )

    def fake_run(db, records, **kwargs):
        from datetime import datetime as _dt

        started = _dt.now()
        finished = _dt.now()
        record = next(iter(records))
        annotation = db.create_activity_annotation(
            activity_record_id=record.id,
            source_connector_id="gh",
            annotation_type="github_issue",
            title="Issue 99 enriched",
        )
        db.record_connector_run(
            connector_id="gh",
            started_at=started,
            finished_at=finished,
            succeeded=True,
            output_bytes=128,
            annotation_count=1,
            command_count=1,
        )
        plan = GithubCliCommandPlan(
            activity_record_id=record.id,
            entity_type="github_issue",
            entity_id="anthropic/holdspeak#99",
            repo="anthropic/holdspeak",
            number=99,
            command=("gh", "issue", "view", "99"),
            annotation_type="github_issue",
        )
        return [GithubCliRunResult(plan=plan, annotation=annotation)]

    monkeypatch.setattr("holdspeak.activity_github.run_github_cli_enrichment", fake_run)

    enable = test_client.put(
        "/api/activity/enrichment/connectors/gh",
        json={"enabled": True, "settings": {}},
    )
    assert enable.status_code == 200
    run_response = test_client.post(
        "/api/activity/enrichment/github/run", json={"limit": 1}
    )
    assert run_response.status_code == 200

    runs_response = test_client.get(
        "/api/activity/enrichment/connectors/gh/runs"
    )
    assert runs_response.status_code == 200
    payload = runs_response.json()
    assert payload["connector_id"] == "gh"
    assert len(payload["runs"]) == 1
    assert payload["runs"][0]["succeeded"] is True
    assert payload["runs"][0]["annotation_count"] == 1
    assert payload["runs"][0]["output_bytes"] == 128


def test_clear_annotations_also_clears_run_history(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-13-05: clearing a connector's annotations also drops
    its run rows — run history is part of the pack's output."""
    base = datetime(2026, 5, 1, 12, 0, 0)
    activity_db.record_connector_run(
        connector_id="gh",
        started_at=base,
        finished_at=base,
        succeeded=True,
    )
    activity_db.record_connector_run(
        connector_id="gh",
        started_at=base,
        finished_at=base,
        succeeded=False,
        error="boom",
    )
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/o/r/issues/1",
        title="x",
        domain="github.com",
        last_seen_at=base,
        entity_type="github_issue",
        entity_id="o/r#1",
    )
    activity_db.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_issue",
        title="annotated",
    )

    response = test_client.delete(
        "/api/activity/enrichment/connectors/gh/annotations"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] == 1
    assert body["runs_deleted"] == 2
    assert activity_db.list_connector_runs(connector_id="gh") == []


def test_list_connector_runs_unknown_connector_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/api/activity/enrichment/connectors/nope/runs"
    )
    assert response.status_code == 404


def test_briefing_endpoint_returns_null_when_no_annotation(
    test_client: TestClient,
) -> None:
    """HS-13-08: GET /api/activity/briefing returns
    `briefing: null, last_run: null` when the pipeline has
    never run. The dashboard's empty-state copy renders from
    that null."""
    response = test_client.get("/api/activity/briefing")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"briefing": None, "last_run": None}


def test_briefing_endpoint_returns_latest_briefing_and_run(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """A fresh `meeting_context_briefing` annotation + a
    matching run row both come back; the briefing carries its
    value payload (including `markdown`)."""
    activity_db.create_activity_annotation(
        source_connector_id="meeting_context",
        annotation_type="meeting_context_briefing",
        title="HoldSpeak — meeting context",
        value={
            "project_id": "holdspeak",
            "project_name": "HoldSpeak",
            "markdown": "# x\n\n- y",
            "gh_count": 1,
            "jira_count": 0,
            "calendar_count": 0,
        },
    )
    base = datetime(2026, 5, 2, 12, 0, 0)
    activity_db.record_connector_run(
        connector_id="meeting_context",
        started_at=base,
        finished_at=base,
        succeeded=True,
        annotation_count=1,
    )

    response = test_client.get("/api/activity/briefing")
    assert response.status_code == 200
    payload = response.json()
    assert payload["briefing"] is not None
    assert payload["briefing"]["title"].startswith("HoldSpeak")
    assert payload["briefing"]["value"]["markdown"].startswith("# x")
    assert payload["last_run"] is not None
    assert payload["last_run"]["succeeded"] is True


def test_run_pipeline_endpoint_executes_meeting_context(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """POST /api/activity/enrichment/pipelines/meeting_context/run
    drives the pipeline end-to-end. Upstreams are seeded as
    fresh so the runner skips them; the pipeline writes its
    annotation."""
    activity_db.create_project(
        project_id="holdspeak", name="HoldSpeak", keywords=["holdspeak"]
    )
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/7",
        title="PR 7",
        domain="github.com",
        last_seen_at=datetime(2026, 5, 2, 9, 0),
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#7",
    )
    activity_db.assign_activity_record_project(record.id, "holdspeak")
    activity_db.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_pr",
        title="Wire runtime",
        value={"entity_id": "anthropic/holdspeak#7"},
    )
    base = datetime(2026, 5, 2, 11, 0, 0)
    for upstream in ("gh", "jira", "calendar_activity"):
        activity_db.record_connector_run(
            connector_id=upstream,
            started_at=base,
            finished_at=base,
            succeeded=True,
        )

    response = test_client.post(
        "/api/activity/enrichment/pipelines/meeting_context/run"
    )
    assert response.status_code == 200
    body = response.json()["result"]
    assert body["target"] == "meeting_context"
    assert body["succeeded"] is True
    statuses = {s["pack_id"]: s["status"] for s in body["steps"]}
    assert statuses["meeting_context"] == "ran"
    # The briefing endpoint now reflects the freshly-written
    # annotation.
    follow = test_client.get("/api/activity/briefing").json()
    assert follow["briefing"] is not None
    assert follow["briefing"]["value"]["project_id"] == "holdspeak"


def test_run_pipeline_endpoint_rejects_non_pipeline(
    test_client: TestClient,
) -> None:
    response = test_client.post(
        "/api/activity/enrichment/pipelines/gh/run"
    )
    assert response.status_code == 400
    assert "kind=" in response.json()["error"]


def test_run_pipeline_endpoint_rejects_unknown_id(
    test_client: TestClient,
) -> None:
    response = test_client.post(
        "/api/activity/enrichment/pipelines/no_such_pipe/run"
    )
    assert response.status_code == 404


def test_list_activity_annotations_filters_by_connector(
    test_client: TestClient,
    activity_db: MeetingDatabase,
) -> None:
    """HS-13-07: the meeting_context briefing is queryable
    via the new GET annotations endpoint, scoped by connector
    id so a UI can render exactly the rows it cares about."""
    record = activity_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/o/r/issues/1",
        title="Issue 1",
        domain="github.com",
        last_seen_at=datetime(2026, 5, 1, 9, 0),
        entity_type="github_issue",
        entity_id="o/r#1",
    )
    activity_db.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_issue",
        title="local enriched",
    )
    activity_db.create_activity_annotation(
        source_connector_id="meeting_context",
        annotation_type="meeting_context_briefing",
        title="HoldSpeak — meeting context",
        value={"project_id": "holdspeak", "markdown": "# x\n- y"},
    )

    response = test_client.get(
        "/api/activity/annotations?source_connector_id=meeting_context"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["annotations"]) == 1
    only = body["annotations"][0]
    assert only["source_connector_id"] == "meeting_context"
    assert only["value"]["project_id"] == "holdspeak"


def test_put_connector_settings_rejects_keys_on_empty_schema(
    test_client: TestClient,
) -> None:
    """HS-13-03: firefox_ext declares an empty schema; any key in
    settings is unknown and the PUT is rejected. The connector
    still appears in the registry (HS-13-01) but the enrichment
    PUT shape recognises it."""
    response = test_client.put(
        "/api/activity/enrichment/connectors/firefox_ext",
        json={"enabled": False, "settings": {"limit": 25}},
    )
    assert response.status_code == 400
    assert "limit" in response.json()["error"]
