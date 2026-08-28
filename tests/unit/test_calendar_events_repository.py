"""Projection repository proofs for HS-144-02 / HS-146-01 calendar ingest."""
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
            source_id="src-1",
            source_label="Work",
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
            source_id="src-1",
            source_label="Work",
        )

        rows = repo.list_all()
        assert [(row.id, row.title, row.location, row.last_seen_at) for row in rows] == [
            ("ce_first", "Updated event", "Studio", 200.0)
        ]
        assert rows[0].subscription_revision == "source-a"
        assert rows[0].source_id == "src-1"
        assert rows[0].source_label == "Work"
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
            source_id="src-1",
        )

        rows = repo.list_upcoming("2026-08-27T10:00:00Z")

        assert [row.id for row in rows] == ["ce_earlier_a", "ce_earlier_b", "ce_later"]
        assert all(row.starts_at >= "2026-08-27T10:00:00Z" for row in rows)
    finally:
        db.close()


def test_two_sources_coexist_independently(tmp_path: Path) -> None:
    db = Database(tmp_path / "calendar-two-sources.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "rev-a",
            [_event("ce_work", uid="work-1", starts_at="2026-08-27T10:00:00Z", title="Work standup")],
            seen_at=100.0,
            source_id="src-work",
            source_label="Work",
        )
        repo.replace_projection(
            "rev-b",
            [_event("ce_personal", uid="pers-1", starts_at="2026-08-27T14:00:00Z", title="Dentist")],
            seen_at=100.0,
            source_id="src-personal",
            source_label="Personal",
        )

        rows = repo.list_all()
        assert len(rows) == 2
        assert [(r.id, r.source_id, r.source_label) for r in rows] == [
            ("ce_work", "src-work", "Work"),
            ("ce_personal", "src-personal", "Personal"),
        ]
    finally:
        db.close()


def test_scoped_replace_leaves_other_source_untouched(tmp_path: Path) -> None:
    db = Database(tmp_path / "calendar-scoped.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "rev-a",
            [_event("ce_work", uid="w1", starts_at="2026-08-27T10:00:00Z", title="Work")],
            seen_at=100.0,
            source_id="src-work",
            source_label="Work",
        )
        repo.replace_projection(
            "rev-b",
            [_event("ce_pers", uid="p1", starts_at="2026-08-27T14:00:00Z", title="Personal")],
            seen_at=100.0,
            source_id="src-personal",
            source_label="Personal",
        )
        repo.replace_projection(
            "rev-a-2",
            [_event("ce_work_v2", uid="w2", starts_at="2026-08-27T11:00:00Z", title="Work v2")],
            seen_at=200.0,
            source_id="src-work",
            source_label="Work",
        )

        rows = repo.list_all()
        assert len(rows) == 2
        ids = {r.id for r in rows}
        assert "ce_work_v2" in ids
        assert "ce_pers" in ids
        assert "ce_work" not in ids
    finally:
        db.close()


def test_failed_source_leaves_other_sources_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "calendar-fail-isolation.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "rev-a",
            [_event("ce_ok", uid="ok1", starts_at="2026-08-27T10:00:00Z")],
            seen_at=100.0,
            source_id="src-ok",
        )

        rows_before = repo.list_all()
        assert len(rows_before) == 1
        assert rows_before[0].id == "ce_ok"
        assert rows_before[0].source_id == "src-ok"
    finally:
        db.close()


def test_orphan_cleanup_removes_disabled_source_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "calendar-orphan.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "rev-a",
            [_event("ce_keep", uid="k1", starts_at="2026-08-27T10:00:00Z")],
            seen_at=100.0,
            source_id="src-keep",
        )
        repo.replace_projection(
            "rev-b",
            [_event("ce_gone", uid="g1", starts_at="2026-08-27T14:00:00Z")],
            seen_at=100.0,
            source_id="src-gone",
        )

        deleted = repo.delete_sources_not_in(["src-keep"])
        assert deleted == 1

        rows = repo.list_all()
        assert len(rows) == 1
        assert rows[0].id == "ce_keep"
    finally:
        db.close()


def test_orphan_cleanup_with_empty_list_removes_all(tmp_path: Path) -> None:
    db = Database(tmp_path / "calendar-orphan-all.db")
    try:
        repo = db.calendar_events
        repo.replace_projection(
            "rev-a",
            [_event("ce_1", uid="u1", starts_at="2026-08-27T10:00:00Z")],
            seen_at=100.0,
            source_id="src-1",
        )
        deleted = repo.delete_sources_not_in([])
        assert deleted == 1
        assert repo.list_all() == []
    finally:
        db.close()
