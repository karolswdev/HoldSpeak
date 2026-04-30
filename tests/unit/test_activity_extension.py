"""Unit tests for HS-9-03 companion-extension event ingestion."""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.activity_extension import (
    EXTENSION_SOURCE_BROWSER,
    FORBIDDEN_FIELDS,
    ingest_extension_events,
    parse_extension_event,
)
from holdspeak.db import MeetingDatabase, reset_database


@pytest.fixture
def test_db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _good_event(**overrides):
    base = {
        "url": "https://github.com/anthropic/holdspeak/pull/7",
        "title": "PR 7 — connector dry-run",
        "visited_at": "2026-04-29T20:30:00",
    }
    base.update(overrides)
    return base


def test_parse_accepts_minimal_https_event():
    event, reason = parse_extension_event(_good_event())
    assert reason is None
    assert event is not None
    assert event.url == "https://github.com/anthropic/holdspeak/pull/7"
    assert event.title == "PR 7 — connector dry-run"
    assert event.visited_at == datetime.fromisoformat("2026-04-29T20:30:00")


@pytest.mark.parametrize("forbidden_field", sorted(FORBIDDEN_FIELDS))
def test_parse_rejects_any_forbidden_field(forbidden_field):
    """Even if the value is empty/null, the field's *presence* alone
    is treated as misconfiguration. The parser is the last line of
    defense if the extension is ever modified to ship sensitive data."""
    raw = _good_event()
    raw[forbidden_field] = "anything"
    event, reason = parse_extension_event(raw)
    assert event is None
    assert reason is not None
    assert reason.startswith("forbidden_field:")


def test_parse_rejects_private_or_incognito_events():
    event, reason = parse_extension_event(_good_event(private=True))
    assert event is None and reason == "private_browsing_blocked"

    event, reason = parse_extension_event(_good_event(incognito=True))
    assert event is None and reason == "private_browsing_blocked"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/secret",
        "javascript:alert(1)",
        "about:config",
        "chrome://settings",
        "data:text/html,<script>alert(1)</script>",
    ],
)
def test_parse_rejects_non_http_schemes(url):
    event, reason = parse_extension_event(_good_event(url=url))
    assert event is None
    assert reason is not None and reason.startswith("scheme_not_allowed:")


def test_parse_rejects_missing_url():
    event, reason = parse_extension_event(_good_event(url=""))
    assert event is None and reason == "url_required"


def test_parse_rejects_bad_visited_at():
    event, reason = parse_extension_event(_good_event(visited_at="yesterday"))
    assert event is None and reason == "visited_at_not_iso"


def test_parse_handles_z_suffix_iso_timestamps():
    event, reason = parse_extension_event(_good_event(visited_at="2026-04-29T20:30:00Z"))
    assert reason is None
    assert event.visited_at.utcoffset() is not None  # tz-aware


def test_ingest_creates_record_under_extension_source(test_db):
    result = ingest_extension_events(test_db, [_good_event()])
    assert len(result.accepted) == 1
    assert result.rejected == ()
    records = test_db.list_activity_records(source_browser=EXTENSION_SOURCE_BROWSER)
    assert len(records) == 1
    record = records[0]
    assert record.url == "https://github.com/anthropic/holdspeak/pull/7"
    # Entity extraction kicked in via extract_activity_entity.
    assert record.entity_type == "github_pull_request"
    assert record.entity_id == "anthropic/holdspeak#7"


def test_ingest_rejects_forbidden_fields_per_event(test_db):
    """One bad event in a batch does not poison the rest. Each
    rejection is reported with its index."""
    payload = [
        _good_event(),
        _good_event(url="https://example.com/two", cookies="session=abc"),
        _good_event(url="https://example.com/three", visited_at="not-iso"),
        _good_event(url="https://example.com/four", body="<html>…</html>"),
    ]
    result = ingest_extension_events(test_db, payload)
    assert len(result.accepted) == 1
    rejected = sorted(result.rejected, key=lambda r: r["index"])
    assert [r["index"] for r in rejected] == [1, 2, 3]
    assert rejected[0]["reason"].startswith("forbidden_field:")
    assert rejected[1]["reason"] == "visited_at_not_iso"
    assert rejected[2]["reason"].startswith("forbidden_field:")


def test_ingest_does_not_persist_record_for_rejected_event(test_db):
    """Rejection means no row is upserted at all."""
    before = len(test_db.list_activity_records(limit=100))
    result = ingest_extension_events(
        test_db,
        [_good_event(url="https://example.com/x", cookies="s=1")],
    )
    after = len(test_db.list_activity_records(limit=100))
    assert result.accepted == ()
    assert after == before


def test_ingest_applies_project_rules(test_db):
    """Once a record is upserted, project rules run so the
    extension's events get the same project mapping as imported
    history records."""
    project_id = "holdspeak"
    test_db.create_project(project_id=project_id, name="HoldSpeak")
    test_db.create_activity_project_rule(
        project_id=project_id,
        match_type="domain",
        pattern="github.com",
        name="GitHub",
    )
    result = ingest_extension_events(
        test_db,
        [_good_event(url="https://github.com/anthropic/holdspeak/pull/8")],
    )
    assert len(result.accepted) == 1
    records = test_db.list_activity_records(source_browser=EXTENSION_SOURCE_BROWSER)
    assert len(records) == 1
    assert records[0].project_id == project_id
    assert result.project_rule_updates >= 1
