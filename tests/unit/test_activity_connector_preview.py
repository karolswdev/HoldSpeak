"""Unit tests for the shared connector dry-run harness (HS-9-13)."""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.activity_connector_preview import (
    UnknownConnectorError,
    dry_run,
)
from holdspeak.db import MeetingDatabase, reset_database


@pytest.fixture
def test_db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _seed_github_pr(db: MeetingDatabase) -> None:
    db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/42",
        title="PR 42",
        domain="github.com",
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#42",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
    )


def _seed_calendar_event(db: MeetingDatabase) -> None:
    db.upsert_activity_record(
        source_browser="safari",
        url="https://calendar.google.com/calendar/u/0/r/eventedit/abc?starts=2026-05-01T10:00",
        title="2026-05-01 10:00-11:00 Architecture sync",
        domain="calendar.google.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
    )


def test_dry_run_unknown_connector_raises(test_db):
    with pytest.raises(UnknownConnectorError):
        dry_run(test_db, "not-a-connector")


def test_dry_run_gh_returns_uniform_payload_shape(test_db):
    _seed_github_pr(test_db)

    result = dry_run(test_db, "gh", limit=5)
    payload = result.to_payload()

    assert payload["connector_id"] == "gh"
    assert payload["kind"] == "cli_enrichment"
    assert payload["capabilities"] == ["annotations"]
    assert payload["enabled"] is False
    assert payload["cli_required"] == "gh"
    assert isinstance(payload["cli_available"], bool)
    assert isinstance(payload["commands"], list)
    assert isinstance(payload["proposed_annotations"], list)
    assert isinstance(payload["proposed_candidates"], list)
    assert isinstance(payload["warnings"], list)
    assert isinstance(payload["permission_notes"], list)
    assert payload["truncated"] is False

    # Disabled-by-default → permission_notes flags it.
    assert any("disabled" in note for note in payload["permission_notes"])

    # One PR was seeded → one command + one proposed annotation derived
    # from that command, sharing the same activity_record_id.
    assert len(payload["commands"]) == 1
    assert len(payload["proposed_annotations"]) == 1
    assert (
        payload["proposed_annotations"][0]["activity_record_id"]
        == payload["commands"][0]["activity_record_id"]
    )


def test_dry_run_calendar_emits_proposed_candidates(test_db):
    _seed_calendar_event(test_db)

    result = dry_run(test_db, "calendar_activity")
    payload = result.to_payload()

    assert payload["connector_id"] == "calendar_activity"
    assert payload["kind"] == "candidate_inference"
    assert payload["capabilities"] == ["candidates"]
    assert payload["cli_required"] is None
    assert payload["cli_available"] is None
    assert payload["commands"] == []
    assert payload["proposed_annotations"] == []
    assert len(payload["proposed_candidates"]) >= 1
    candidate = payload["proposed_candidates"][0]
    assert candidate["source_connector_id"] == "calendar_activity"
    assert candidate["title"]


def test_dry_run_does_not_mutate_db(test_db):
    _seed_github_pr(test_db)
    _seed_calendar_event(test_db)

    annotations_before = list(test_db.list_activity_annotations(limit=1000))
    candidates_before = list(test_db.list_activity_meeting_candidates())

    dry_run(test_db, "gh")
    dry_run(test_db, "jira")
    dry_run(test_db, "calendar_activity")

    annotations_after = list(test_db.list_activity_annotations(limit=1000))
    candidates_after = list(test_db.list_activity_meeting_candidates())

    assert [a.id for a in annotations_after] == [a.id for a in annotations_before]
    assert [c.id for c in candidates_after] == [c.id for c in candidates_before]


def test_dry_run_warns_when_no_relevant_activity(test_db):
    """Empty activity ledger → a friendly warning, not an exception."""
    result = dry_run(test_db, "gh")
    assert any("No GitHub" in w for w in result.warnings)

    result = dry_run(test_db, "jira")
    assert any("No Jira" in w for w in result.warnings)

    result = dry_run(test_db, "calendar_activity")
    assert any("calendar" in w.lower() for w in result.warnings)


def test_dry_run_disabled_connector_still_returns_a_plan(test_db):
    """The default state is disabled. The plan should still come back —
    that's the whole point of dry-run — with a permission note that
    explains why nothing will execute."""
    _seed_github_pr(test_db)
    result = dry_run(test_db, "gh")
    assert result.commands  # plan is still computed
    assert any("disabled" in note for note in result.permission_notes)
