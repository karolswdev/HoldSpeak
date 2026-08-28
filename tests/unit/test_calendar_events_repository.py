"""Projection repository proofs for HS-144-02 calendar ingest."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db.calendar_events import CalendarEvent
from holdspeak.db.core import Database


def _event(
    event_id: str,
    *,
    uid: str,
    starts_at: str,
    title: str = "Calendar event",
    location: str | None = None,
    meeting_url: str | None = None,
) -> CalendarEvent:
    return CalendarEvent(
        id=event_id,
        uid=uid,
        title=title,
        starts_at=starts_at,
        ends_at="2026-08-27T11:00:00Z",
        location=location,
        meeting_url=meeting_url,
        last_seen_at=0.0,
        subscription_revision="ignored-by-replacement",
    )


def test_replace_projection_upserts_and_removes_vanished_rows_atomically(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "calendar-events.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "source-a",
            [
                _event("ce_first", uid="first", starts_at="2026-08-27T10:00:00Z"),
                _event("ce_vanished", uid="vanished", starts_at="2026-08-27T12:00:00Z"),
            ],
            seen_at=100.0,
        )
        repo.replace_projection(
            "source-a",
            [
                _event(
                    "ce_first",
                    uid="first",
                    starts_at="2026-08-27T10:00:00Z",
                    title="Updated event",
                    location="Studio",
                )
            ],
            seen_at=200.0,
        )

        rows = repo.list_all()
        assert [(row.id, row.title, row.location, row.last_seen_at) for row in rows] == [
            ("ce_first", "Updated event", "Studio", 200.0)
        ]
        assert rows[0].subscription_revision == "source-a"

        # One configured source means a source change replaces rather than
        # mingling the previous projection with a new calendar.
        repo.replace_projection(
            "source-b",
            [_event("ce_new_source", uid="new", starts_at="2026-08-27T09:00:00Z")],
            seen_at=300.0,
        )
        assert [(row.id, row.subscription_revision) for row in repo.list_all()] == [
            ("ce_new_source", "source-b")
        ]
    finally:
        db.close()


def test_list_upcoming_orders_future_rows_without_raw_sql_in_consumers(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "calendar-upcoming.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "source-a",
            [
                _event("ce_later", uid="later", starts_at="2026-08-27T12:00:00Z"),
                _event("ce_past", uid="past", starts_at="2026-08-26T12:00:00Z"),
                _event("ce_earlier_b", uid="earlier-b", starts_at="2026-08-27T10:00:00Z"),
                _event("ce_earlier_a", uid="earlier-a", starts_at="2026-08-27T10:00:00Z"),
            ],
            seen_at=100.0,
        )

        rows = repo.list_upcoming("2026-08-27T10:00:00Z")

        assert [row.id for row in rows] == ["ce_earlier_a", "ce_earlier_b", "ce_later"]
        assert all(row.starts_at >= "2026-08-27T10:00:00Z" for row in rows)
    finally:
        db.close()
