"""Pure bounded ICS projection proofs for HS-144-02."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from holdspeak.calendar_ingest import (
    HORIZON_DAYS,
    MAX_FEED_BYTES,
    MAX_OCCURRENCES_PER_MASTER,
    parse_calendar_bytes,
)


FIXTURES = Path(__file__).parents[1] / "fixtures" / "calendar"
NOW = datetime(2026, 8, 27, tzinfo=timezone.utc)
REVISION = "calendar-source-revision"


def _parse(name: str):
    return parse_calendar_bytes(
        (FIXTURES / name).read_bytes(), now=NOW, subscription_revision=REVISION
    )


def test_basic_ics_projects_only_the_door_fields() -> None:
    result = _parse("basic.ics")

    assert result.succeeded
    assert result.skips == ()
    assert len(result.events) == 1
    event = result.events[0]
    assert event.uid == "basic-1"
    assert event.title == "Team standup"
    assert event.starts_at == "2026-08-27T10:00:00Z"
    assert event.ends_at == "2026-08-27T11:00:00Z"
    assert event.location == "Room 4"
    assert event.meeting_url == "https://meet.example.test/standup"
    assert event.id.startswith("ce_")


def test_folded_ics_and_url_property_project_without_a_hand_rolled_parser() -> None:
    result = _parse("folded-url.ics")

    assert result.succeeded
    assert result.skips == ()
    assert len(result.events) == 1
    event = result.events[0]
    assert event.title == "Planning, review; now"
    assert event.meeting_url == "https://meet.example.test/join/abcdef?token=oneandtwo"


def test_tzid_event_projects_the_correct_utc_instants() -> None:
    result = _parse("tzid-new-york.ics")

    assert result.succeeded
    assert result.skips == ()
    assert [(event.starts_at, event.ends_at) for event in result.events] == [
        ("2026-08-27T13:00:00Z", "2026-08-27T14:00:00Z")
    ]


def test_rrule_expands_only_the_fourteen_day_window_and_hard_occurrence_cap() -> None:
    result = _parse("rrule-bound.ics")

    assert result.succeeded
    assert len(result.events) == MAX_OCCURRENCES_PER_MASTER
    assert result.events[0].starts_at == "2026-08-27T00:00:00Z"
    assert result.events[-1].starts_at == "2026-09-01T07:00:00Z"
    assert all(
        event.starts_at < "2026-09-10T00:00:00Z" for event in result.events
    )
    assert "calendar_event_skipped_occurrence_cap" in {
        skip.reason for skip in result.skips
    }


def test_exdate_removes_a_recurring_occurrence() -> None:
    raw = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:excepted\r
DTSTART:20260827T090000Z\r
DTEND:20260827T100000Z\r
RRULE:FREQ=DAILY;COUNT=3\r
EXDATE:20260828T090000Z\r
END:VEVENT\r
END:VCALENDAR\r
"""

    result = parse_calendar_bytes(raw, now=NOW, subscription_revision=REVISION)

    assert result.succeeded
    assert [event.starts_at for event in result.events] == [
        "2026-08-27T09:00:00Z",
        "2026-08-29T09:00:00Z",
    ]


def test_rdate_adds_a_decoded_datetime_occurrence() -> None:
    raw = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:extra-date\r
DTSTART:20260827T090000Z\r
DTEND:20260827T100000Z\r
RDATE:20260829T090000Z\r
END:VEVENT\r
END:VCALENDAR\r
"""

    result = parse_calendar_bytes(raw, now=NOW, subscription_revision=REVISION)

    assert result.succeeded
    assert [event.starts_at for event in result.events] == [
        "2026-08-27T09:00:00Z",
        "2026-08-29T09:00:00Z",
    ]


def test_malformed_event_becomes_a_named_skip_while_good_sibling_survives() -> None:
    result = _parse("mixed-bad-event.ics")

    assert result.succeeded
    assert [event.uid for event in result.events] == ["good-sibling"]
    assert [(skip.event_ref, skip.reason) for skip in result.skips] == [
        ("bad-no-end", "calendar_event_skipped_invalid_dtend")
    ]


def test_garbage_bytes_and_huge_feed_are_bounded_feed_failures() -> None:
    garbage = _parse("garbage-bytes.ics")
    huge = parse_calendar_bytes(
        b"x" * (MAX_FEED_BYTES + 1), now=NOW, subscription_revision=REVISION
    )

    assert garbage.feed_error == "calendar_feed_invalid_utf8"
    assert huge.feed_error == "calendar_feed_too_large"
    assert huge.events == ()
    assert huge.skips == ()


def test_date_only_and_recurrence_override_are_explicitly_skipped_not_misrepresented() -> None:
    raw = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:all-day\r
DTSTART;VALUE=DATE:20260828\r
DTEND;VALUE=DATE:20260829\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:override\r
RECURRENCE-ID:20260828T090000Z\r
DTSTART:20260828T093000Z\r
DTEND:20260828T103000Z\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:too-fast\r
DTSTART:20260827T010000Z\r
DTEND:20260827T010100Z\r
RRULE:FREQ=SECONDLY\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:too-often\r
DTSTART:20000101T010000Z\r
DTEND:20000101T010100Z\r
RRULE:FREQ=MINUTELY\r
END:VEVENT\r
END:VCALENDAR\r
"""

    result = parse_calendar_bytes(raw, now=NOW, subscription_revision=REVISION)

    assert result.succeeded
    assert result.events == ()
    assert {(skip.event_ref, skip.reason) for skip in result.skips} == {
        ("all-day", "calendar_event_skipped_unsupported_date_only"),
        ("override", "calendar_event_skipped_unsupported_recurrence_override"),
        ("too-fast", "calendar_event_skipped_unsupported_rrule_frequency"),
        ("too-often", "calendar_event_skipped_unsupported_rrule_frequency"),
    }


def test_unresolvable_tzid_and_malformed_rrule_are_named_skips() -> None:
    raw = b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
BEGIN:VEVENT\r
UID:unknown-zone\r
DTSTART;TZID=Nope/Nowhere:20260827T090000\r
DTEND;TZID=Nope/Nowhere:20260827T100000\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:bad-rule\r
DTSTART:20260827T090000Z\r
DTEND:20260827T100000Z\r
RRULE:FREQ=NOT-A-FREQUENCY\r
END:VEVENT\r
END:VCALENDAR\r
"""

    result = parse_calendar_bytes(raw, now=NOW, subscription_revision=REVISION)

    assert result.succeeded
    assert result.events == ()
    assert {(skip.event_ref, skip.reason) for skip in result.skips} == {
        ("unknown-zone", "calendar_event_skipped_unresolvable_tzid"),
        ("bad-rule", "calendar_event_skipped_invalid_rrule"),
    }


def test_horizon_constant_is_the_declared_two_week_window() -> None:
    assert HORIZON_DAYS == 14
