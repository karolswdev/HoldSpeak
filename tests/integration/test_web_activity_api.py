"""Integration tests for local activity intelligence web APIs."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# DEFAULT_DB_PATH now lives in holdspeak.db.core (Phase 31 split); patch it there
# so Database.__init__ / get_database see the override.
from holdspeak.db import core as db_module
from holdspeak.db import Database, reset_database
from holdspeak.principals import PrincipalKind
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]


@pytest.fixture
def activity_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    # HS-200-03: order matters, and owning the singleton matters.
    #
    # This used to reset FIRST and repoint `DEFAULT_DB_PATH` second, then build
    # a Database it never published. Between the reset and the repoint the
    # singleton was None while the default path was still the real one, so any
    # thread calling `get_database()` in that window published a foreign
    # database to the very routes under test — and the routes then read a
    # different file from the one this fixture wrote to. That is the three
    # CI-only failures on Actions run 34007939416 (`assert 0 == 1`,
    # `assert 404 == 200`, `assert None is not None`).
    #
    # Repoint first, then reset, then INSTALL this database as the singleton,
    # so there is no moment at which the default path and the singleton
    # disagree with what this test is asserting about.
    db_path = tmp_path / "holdspeak.db"
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_path)
    reset_database()
    database = Database(db_path)
    monkeypatch.setattr(db_module, "_db", database, raising=False)
    yield database
    reset_database()


@pytest.fixture
def test_client(activity_db: Database) -> TestClient:
    server = MeetingWebServer(
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     get_state=MagicMock(return_value={}),
                 )
             )
    return TestClient(server.app)


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
    activity_db: Database,
) -> None:
    activity_db.activity.upsert_activity_record(
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


def test_activity_meeting_candidate_manual_start_marks_started(
    activity_db: Database,
) -> None:
    candidate = activity_db.activity.create_activity_meeting_candidate(
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
                 WebRuntimeCallbacks(
                     on_bookmark=MagicMock(),
                     on_stop=MagicMock(),
                     on_start=on_start,
                     on_update_meeting=on_update_meeting,
                     get_state=MagicMock(return_value={}),
                 )
             )
    broadcast_events: list[tuple[str, object]] = []
    server.broadcast = lambda message_type, data: broadcast_events.append((message_type, data))
    client = TestClient(server.app)

    before_start = activity_db.activity.get_activity_meeting_candidate(candidate.id)
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
    # HS-131-08: capture start now carries the authenticated route principal,
    # because live meeting intelligence is admitted under exactly that principal.
    on_start.assert_called_once()
    assert list(on_start.call_args.args) == []
    started_principal = on_start.call_args.kwargs["principal"]
    assert started_principal.kind is PrincipalKind.OWNER
    on_update_meeting.assert_called_once_with(title="Customer sync meeting", tags=None)
    assert broadcast_events[0][0] == "meeting_started"
    assert broadcast_events[0][1]["activity_meeting_candidate_id"] == candidate.id

    persisted = activity_db.activity.get_activity_meeting_candidate(candidate.id)
    assert persisted is not None
    assert persisted.status == "started"
    assert persisted.started_meeting_id == "meeting-1"


def test_activity_meeting_candidate_manual_start_requires_runtime_start_support(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    candidate = activity_db.activity.create_activity_meeting_candidate(
        source_connector_id="calendar_activity",
        title="Customer sync meeting",
    )

    response = test_client.post(f"/api/activity/meeting-candidates/{candidate.id}/start")

    assert response.status_code == 501
    assert response.json()["success"] is False
    persisted = activity_db.activity.get_activity_meeting_candidate(candidate.id)
    assert persisted is not None
    assert persisted.status == "candidate"
    assert persisted.started_meeting_id is None


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
    assert set(by_id) == {"gh", "jira", "acli_jira", "acli_confluence", "calendar_activity"}  # HS-166: the acli pack; HS-174: Confluence
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


def test_extension_events_endpoint_creates_records(
    test_client: TestClient,
    activity_db: Database,
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

    records = activity_db.activity.list_activity_records(source_browser="firefox_ext")
    assert len(records) == 1
    assert records[0].entity_type == "github_pull_request"


def test_extension_events_rejects_sensitive_fields(
    test_client: TestClient,
    activity_db: Database,
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

    assert activity_db.activity.list_activity_records(source_browser="firefox_ext") == []


def test_extension_events_applies_project_rules(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    """HS-9-03: extension records pick up the same project mapping
    as imported history records."""
    activity_db.projects.create_project(project_id="holdspeak", name="HoldSpeak")
    activity_db.activity.create_activity_project_rule(
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
    records = activity_db.activity.list_activity_records(source_browser="firefox_ext")
    assert records[0].project_id == "holdspeak"


def test_connector_dry_run_returns_uniform_shape_per_connector(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    """HS-9-13: every connector returns the same dry-run payload shape."""
    activity_db.activity.upsert_activity_record(
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
    activity_db: Database,
) -> None:
    """HS-9-13: dry-run is mutation-free — the DB row counts for
    annotations and candidates are unchanged after dry-running every
    connector."""
    activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/7",
        title="PR 7",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#7",
    )
    activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://calendar.google.com/calendar/u/0/r/eventedit/abc?starts=2026-05-01T10:00",
        title="2026-05-01 10:00-11:00 Architecture sync",
        domain="calendar.google.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
    )

    annotations_before = activity_db.activity.list_activity_annotations(limit=1000)
    candidates_before = activity_db.activity.list_activity_meeting_candidates()

    for connector_id in ("gh", "jira", "calendar_activity"):
        response = test_client.get(
            f"/api/activity/enrichment/connectors/{connector_id}/dry-run"
        )
        assert response.status_code == 200

    annotations_after = activity_db.activity.list_activity_annotations(limit=1000)
    candidates_after = activity_db.activity.list_activity_meeting_candidates()
    assert [a.id for a in annotations_after] == [a.id for a in annotations_before]
    assert [c.id for c in candidates_after] == [c.id for c in candidates_before]


def test_connector_dry_run_unknown_connector_returns_404(
    test_client: TestClient,
) -> None:
    response = test_client.get(
        "/api/activity/enrichment/connectors/nope/dry-run"
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
    activity_db: Database,
) -> None:
    """A fresh `meeting_context_briefing` annotation + a
    matching run row both come back; the briefing carries its
    value payload (including `markdown`)."""
    activity_db.activity.create_activity_annotation(
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
    activity_db.activity.record_connector_run(
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


def test_activity_project_rule_api_creates_previews_updates_and_deletes(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    activity_db.projects.create_project(project_id="holdspeak", name="HoldSpeak")
    activity_db.activity.upsert_activity_record(
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

    update_response = test_client.put(
        f"/api/activity/project-rules/{rule['id']}",
        json={"enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["rule"]["enabled"] is False

    delete_response = test_client.delete(f"/api/activity/project-rules/{rule['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_activity_meeting_candidate_api_persists_lists_and_deletes(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    record = activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://outlook.office.com/calendar/item/customer-sync",
        title="Customer sync meeting",
        domain="outlook.office.com",
        last_seen_at=datetime(2026, 4, 27, 9, 0),
    )
    body = {
        "source_connector_id": "calendar_activity",
        "source_activity_record_id": record.id,
        "title": "Customer sync meeting",
        "meeting_url": record.url,
        "confidence": 0.8,
    }

    create_response = test_client.post("/api/activity/meeting-candidates", json=body)
    assert create_response.status_code == 200
    candidate = create_response.json()["candidate"]
    assert candidate["status"] == "candidate"
    duplicate_response = test_client.post(
        "/api/activity/meeting-candidates",
        json={**body, "title": "Customer sync meeting updated", "confidence": 0.9},
    )
    assert duplicate_response.status_code == 200
    duplicate = duplicate_response.json()["candidate"]
    assert duplicate["id"] == candidate["id"]
    assert duplicate["title"] == "Customer sync meeting updated"

    list_response = test_client.get("/api/activity/meeting-candidates")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    delete_response = test_client.delete("/api/activity/meeting-candidates?status=candidate")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1
