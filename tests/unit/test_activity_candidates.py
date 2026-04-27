"""Unit tests for local meeting-candidate extraction."""

from __future__ import annotations

from datetime import datetime

from holdspeak.activity_candidates import preview_calendar_meeting_candidates
from holdspeak.db import MeetingDatabase


def test_preview_calendar_meeting_candidates_uses_local_activity_records(tmp_path):
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    outlook = db.upsert_activity_record(
        source_browser="safari",
        url="https://outlook.office.com/calendar/item/123",
        title="Customer planning meeting",
        domain="outlook.office.com",
        last_seen_at=datetime(2026, 4, 27, 9, 0, 0),
    )
    db.upsert_activity_record(
        source_browser="safari",
        url="https://example.com/not-calendar",
        title="Regular page",
        domain="example.com",
    )

    previews = preview_calendar_meeting_candidates(db.list_activity_records(limit=10))

    assert len(previews) == 1
    assert previews[0].title == "Customer planning meeting"
    assert previews[0].meeting_url == outlook.url
    assert previews[0].source_activity_record_id == outlook.id
    assert previews[0].source_connector_id == "calendar_activity"
    assert previews[0].confidence == 0.75


def test_preview_calendar_meeting_candidates_falls_back_to_domain_titles(tmp_path):
    db = MeetingDatabase(tmp_path / "holdspeak.db")
    record = db.upsert_activity_record(
        source_browser="firefox",
        url="https://meet.google.com/abc-defg-hij",
        title=None,
        domain="meet.google.com",
    )

    previews = preview_calendar_meeting_candidates([record])

    assert previews[0].title == "Google Meet meeting"
    assert previews[0].confidence == 0.7
