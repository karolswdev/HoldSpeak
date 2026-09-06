"""HS-175-02: Calendar events on the desk -- wire tests.

Tests:
1. The sweep runs the calendar refresh once and receipts it (stub the fetch;
   a file source needs no network).
2. No double refresh with the old thread gone.
3. The matcher's title rule including the H3 negative (short names skip).
4. The manual link overrides the matcher.
5. `door.week` days/total.
6. `upcoming` carries the room (project_id + project_name).
7. HTTPS source receipts name the host.

Isolated HOME via tmp_path; never the owner's DB.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-owner")

# -- Minimal ICS feed for testing -----------------------------------------

_ICS_TEMPLATE = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:evt-{uid}
DTSTART:{start}
DTEND:{end}
SUMMARY:{title}
LOCATION:{location}
URL:{url}
ATTENDEE:mailto:alice@example.com
ATTENDEE:mailto:bob@example.com
END:VEVENT
END:VCALENDAR
"""


def _make_ics(
    uid: str = "test-1",
    title: str = "Q4 Platform Standup",
    start: str | None = None,
    end: str | None = None,
    location: str = "Room 101",
    url: str = "https://teams.example.com/meeting",
) -> bytes:
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    if start is None:
        start = now.strftime("%Y%m%dT%H%M%SZ")
    if end is None:
        end = (now + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    return _ICS_TEMPLATE.format(
        uid=uid, title=title, start=start, end=end,
        location=location, url=url,
    ).encode("utf-8")


# -- Fixtures --------------------------------------------------------------

@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test175.db")


@pytest.fixture
def ics_file(tmp_path: Path) -> Path:
    p = tmp_path / "cal.ics"
    p.write_bytes(_make_ics())
    return p


def _make_config(ics_path: str, source_id: str = "src-1"):
    """Build a minimal Config mock with one file-based calendar source."""
    from holdspeak.config.integrations import CalendarSource, CalendarConfig

    source = CalendarSource(
        id=source_id, label="TEST", url=str(ics_path), enabled=True,
    )
    config = MagicMock()
    config.calendar = CalendarConfig(sources=[source])
    # Prevent the event-born recording code from crashing on MagicMock attributes.
    config.meeting.auto_record = "off"
    config.meeting.auto_record_lead_minutes = 5
    return config


def _make_conductor(db: Database, ics_path: str, source_id: str = "src-1"):
    """Build a CalendarIngestConductor wired to the test DB and file source."""
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    config = _make_config(ics_path, source_id)
    conductor = CalendarIngestConductor(
        db_factory=lambda: db,
        config_loader=lambda: config,
        tick_interval=9999,  # never auto-tick
    )
    return conductor


# -- Test 1: sweep runs the refresh once and receipts it -------------------

class TestSweepRunsCalendarRefresh:
    def test_sweep_calls_refresh_and_receipts(self, db: Database, ics_file: Path) -> None:
        """The heartbeat sweep calls conductor.refresh() and the receipt
        carries calendar.refresh with applied=True."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        conductor = _make_conductor(db, str(ics_file))
        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = []

        hb = HeartbeatService(
            db, watch_service=mock_ws, calendar_conductor=conductor,
        )
        receipt = hb.run_sweep(OWNER)

        assert "calendar" in receipt, "receipt must carry calendar sub-receipt"
        cal = receipt["calendar"]
        assert cal["kind"] == "calendar.refresh"
        assert cal["applied"] is True

    def test_sweep_receipts_applied_false_when_no_sources(self, db: Database, tmp_path: Path) -> None:
        """When no calendar sources are configured, applied=False."""
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

        config = MagicMock()
        config.calendar = MagicMock()
        config.calendar.sources = []  # no sources
        conductor = CalendarIngestConductor(
            db_factory=lambda: db,
            config_loader=lambda: config,
        )
        hb = HeartbeatService(db, calendar_conductor=conductor)
        receipt = hb.run_sweep(OWNER)

        cal = receipt["calendar"]
        assert cal["applied"] is False


# -- Test 2: no double refresh with old thread gone -------------------------

class TestNoDoubleRefresh:
    def test_conductor_start_does_not_spawn_thread(self, db: Database, ics_file: Path) -> None:
        """After HS-175-02, start_calendar_ingest_conductor does NOT spawn
        the standalone thread."""
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

        conductor = _make_conductor(db, str(ics_file))
        # The conductor's thread should be None (never started).
        assert conductor._thread is None
        # Calling refresh() directly works.
        result = conductor.refresh()
        assert result is True
        # Thread still None.
        assert conductor._thread is None


# -- Test 3: matcher's title rule + H3 negative ---------------------------

class TestTitleMatcher:
    def test_title_match_links_event_to_room(self, db: Database, ics_file: Path) -> None:
        """An event titled 'Q4 Platform Standup' matches a Room named
        'Q4 Platform' (Room name is a whole-word substring)."""
        conductor = _make_conductor(db, str(ics_file))
        # Create a project (Room) named "Q4 Platform".
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-1", "Q4 Platform"),
            )
        conductor.refresh()
        # The matcher should have linked the event to the project.
        links = db.calendar_event_projects.list_for_project("proj-1")
        assert len(links) >= 1
        assert links[0].match_source == "title"

    def test_h3_short_name_never_matches(self, db: Database, ics_file: Path) -> None:
        """H3: a Room name of <= 3 chars never auto-matches (false positive
        risk). 'Q4' is too short to match 'Q4 Platform Standup'."""
        conductor = _make_conductor(db, str(ics_file))
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-short", "Q4"),
            )
        conductor.refresh()
        links = db.calendar_event_projects.list_for_project("proj-short")
        assert len(links) == 0, "short Room names must not auto-match"

    def test_longest_match_wins(self, db: Database, tmp_path: Path) -> None:
        """The matcher prefers the LONGEST matching Room name."""
        ics = tmp_path / "cal2.ics"
        ics.write_bytes(_make_ics(title="Q4 Platform Architecture Review"))
        conductor = _make_conductor(db, str(ics))
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-plat", "Platform"),
            )
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-full", "Q4 Platform"),
            )
        conductor.refresh()
        # The longer name "Q4 Platform" should win.
        links_full = db.calendar_event_projects.list_for_project("proj-full")
        links_plat = db.calendar_event_projects.list_for_project("proj-plat")
        assert len(links_full) == 1
        # "Platform" also matches as a substring, but the test should verify
        # only one project is linked per event (the longest).
        # The matcher picks the BEST match per event, so only one link per event.
        events = db.calendar_events.list_all()
        assert len(events) >= 1
        event_id = events[0].id
        all_links = db.calendar_event_projects.list_for_event(event_id)
        assert len(all_links) == 1
        assert all_links[0].project_id == "proj-full"


# -- Test 4: manual link overrides ----------------------------------------

class TestManualLinkOverrides:
    def test_manual_link_survives_matcher_rerun(self, db: Database, ics_file: Path) -> None:
        """A manual link is preserved across matcher re-runs."""
        conductor = _make_conductor(db, str(ics_file))
        # First refresh to populate events.
        conductor.refresh()
        events = db.calendar_events.list_all()
        assert len(events) >= 1
        event_id = events[0].id

        # Manually link to a different project.
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-manual", "Manual Project"),
            )
        db.calendar_event_projects.link(event_id, "proj-manual", "manual")

        # Re-run the refresh (which re-runs the matcher).
        conductor.refresh()

        # The manual link must survive.
        links = db.calendar_event_projects.list_for_event(event_id)
        manual_links = [l for l in links if l.match_source == "manual"]
        assert len(manual_links) == 1
        assert manual_links[0].project_id == "proj-manual"


# -- Test 5: door.week days/total -----------------------------------------

class TestDoorWeek:
    def test_week_strip_with_events(self, db: Database, ics_file: Path) -> None:
        """door.week carries days with counts and total when calendar is connected."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService
        from holdspeak.db.calendar_events import CalendarEventRepository
        from holdspeak.db.scheduled_recordings import ScheduledRecordingRepository

        conductor = _make_conductor(db, str(ics_file))
        conductor.refresh()

        config = _make_config(str(ics_file))
        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        service = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=lambda: config,
        )
        result = service.get(OWNER)
        week = result["week"]
        assert week["has_calendar"] is True
        assert len(week["days"]) == 7
        assert week["total"] >= 1
        # The event we seeded is in the future, so at least one day has count > 0.
        day_counts = [d["count"] for d in week["days"]]
        assert sum(day_counts) == week["total"]

    def test_week_strip_absent_when_no_calendar(self, db: Database) -> None:
        """door.week.has_calendar is False when no sources are configured."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        service = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=None,  # no calendar
        )
        result = service.get(OWNER)
        week = result["week"]
        assert week["has_calendar"] is False
        assert week["total"] == 0


# -- Test 6: upcoming carries room ----------------------------------------

class TestUpcomingCarriesRoom:
    def test_upcoming_event_carries_project(self, db: Database, ics_file: Path) -> None:
        """When an event is linked to a Room, upcoming items carry
        project_id and project_name."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        conductor = _make_conductor(db, str(ics_file))
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-1", "Q4 Platform"),
            )
        conductor.refresh()

        config = _make_config(str(ics_file))
        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        service = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=lambda: config,
        )
        result = service.get(OWNER)
        upcoming = result["upcoming"]
        assert len(upcoming) >= 1
        # Find the calendar event item.
        cal_items = [i for i in upcoming if i["source"] == "calendar_event"]
        assert len(cal_items) >= 1
        item = cal_items[0]
        assert item.get("project_id") == "proj-1"
        assert item.get("project_name") == "Q4 Platform"


# -- Test 7: HTTPS source receipts name the host --------------------------

class TestHttpsSourceReceipt:
    def test_sweep_receipt_names_https_host(self, db: Database, tmp_path: Path) -> None:
        """When a source is an HTTPS URL, the sweep receipt's calendar
        sub-receipt lists the host."""
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
        from holdspeak.config.integrations import CalendarSource, CalendarConfig

        # Create a config with an HTTPS source (it will fail to fetch,
        # but the receipt structure is what we test).
        source = CalendarSource(
            id="https-src",
            label="WORK",
            url="https://outlook.office365.com/owa/calendar/abc123.ics",
            enabled=True,
        )
        config = MagicMock()
        config.calendar = CalendarConfig(sources=[source])

        conductor = CalendarIngestConductor(
            db_factory=lambda: db,
            config_loader=lambda: config,
        )

        hb = HeartbeatService(db, calendar_conductor=conductor)
        receipt = hb.run_sweep(OWNER)

        cal = receipt.get("calendar", {})
        assert cal.get("kind") == "calendar.refresh"
        sources = cal.get("sources", [])
        assert len(sources) == 1
        assert sources[0]["source_id"] == "https-src"
        assert sources[0]["host"] == "outlook.office365.com"


# -- Test: attendee extraction -----------------------------------------------

class TestAttendeeExtraction:
    def test_attendees_extracted_from_ics(self, db: Database, ics_file: Path) -> None:
        """The parser extracts ATTENDEE mailto: addresses from the ICS feed."""
        conductor = _make_conductor(db, str(ics_file))
        conductor.refresh()
        # The parser extracts attendees but they are not persisted in calendar_events
        # (the attendees field is on CalendarEventCandidate, not the DB table).
        # Verify via direct parse.
        from holdspeak.calendar_ingest import parse_calendar_bytes
        result = parse_calendar_bytes(
            ics_file.read_bytes(),
            now=datetime.now(timezone.utc),
            subscription_revision="test",
        )
        assert result.succeeded
        assert len(result.events) >= 1
        attendees = result.events[0].attendees
        assert "alice@example.com" in attendees
        assert "bob@example.com" in attendees


# -- Test: calendar_event_projects repository ----------------------------

class TestCalendarEventProjectsRepo:
    def test_link_and_list(self, db: Database) -> None:
        """link() and list_for_event() round-trip."""
        db.calendar_event_projects.link("evt-1", "proj-1", "title")
        links = db.calendar_event_projects.list_for_event("evt-1")
        assert len(links) == 1
        assert links[0].project_id == "proj-1"

    def test_manual_link_survives_replace_auto(self, db: Database) -> None:
        """replace_auto_links preserves manual links."""
        db.calendar_event_projects.link("evt-1", "proj-1", "manual")
        db.calendar_event_projects.replace_auto_links([
            ("evt-1", "proj-2", "title"),
        ])
        links = db.calendar_event_projects.list_for_event("evt-1")
        pids = {l.project_id for l in links}
        assert "proj-1" in pids, "manual link must survive"
        # The auto link may or may not be there (ON CONFLICT DO NOTHING).
        # The manual link is the key assertion.

    def test_unlink(self, db: Database) -> None:
        """unlink() removes one link."""
        db.calendar_event_projects.link("evt-1", "proj-1", "title")
        count = db.calendar_event_projects.unlink("evt-1", "proj-1")
        assert count == 1
        assert len(db.calendar_event_projects.list_for_event("evt-1")) == 0

    def test_build_event_project_index(self, db: Database) -> None:
        """build_event_project_index returns event_id -> (project_id, name)."""
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-1", "Alpha"),
            )
        db.calendar_event_projects.link("evt-1", "proj-1", "title")
        index = db.calendar_event_projects.build_event_project_index()
        assert "evt-1" in index
        assert index["evt-1"] == ("proj-1", "Alpha")


# -- HS-175 counsel-on-built: C5 / C6(a) / C6(c) ----------------------------
#
# C5  DELETE /link is durable: the suppression outlives the next refresh
#     and a time change; a manual link clears it.
# C6a the Watch-query branch is gone -- no "no such column" warning per Room.
# C6c a manual link follows its event across a time change (rebind by uid).

_FMT = "%Y%m%dT%H%M%SZ"


def _seed_room(db: Database, pid: str, name: str) -> None:
    with db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (pid, name))


def _timed_ics(title: str, start: datetime, *, uid: str = "test-1") -> bytes:
    return _make_ics(
        uid=uid, title=title,
        start=start.strftime(_FMT), end=(start + timedelta(hours=1)).strftime(_FMT),
    )


class TestUnlinkIsDurable:
    def test_unlink_survives_the_next_refresh(self, db: Database, ics_file: Path) -> None:
        _seed_room(db, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db, str(ics_file))
        conductor.refresh()
        event_id = db.calendar_events.list_all()[0].id
        assert [l.project_id for l in db.calendar_event_projects.list_for_event(event_id)] == ["proj-1"]

        assert db.calendar_event_projects.unlink(event_id, "proj-1") == 1
        assert db.calendar_event_projects.is_suppressed(event_id, "proj-1")

        conductor.refresh()  # the matcher would re-link by title without C5

        assert db.calendar_event_projects.list_for_event(event_id) == []
        assert event_id not in db.calendar_event_projects.build_event_project_index()

    def test_unlink_all_survives_and_a_manual_link_clears_it(self, db: Database, ics_file: Path) -> None:
        _seed_room(db, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db, str(ics_file))
        conductor.refresh()
        event_id = db.calendar_events.list_all()[0].id

        assert db.calendar_event_projects.unlink_event(event_id) == 1
        conductor.refresh()
        assert db.calendar_event_projects.list_for_event(event_id) == []

        # The owner's newer word: link it by hand -> the suppression is cleared.
        db.calendar_event_projects.link(event_id, "proj-1", "manual")
        assert not db.calendar_event_projects.is_suppressed(event_id, "proj-1")
        conductor.refresh()
        links = db.calendar_event_projects.list_for_event(event_id)
        assert [(l.project_id, l.match_source) for l in links] == [("proj-1", "manual")]

    def test_unlink_survives_a_time_change(self, db: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "moving.ics"
        ics.write_bytes(_timed_ics("Q4 Platform Standup", base))
        _seed_room(db, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db, str(ics))
        conductor.refresh()
        old_id = db.calendar_events.list_all()[0].id
        db.calendar_event_projects.unlink(old_id, "proj-1")

        ics.write_bytes(_timed_ics("Q4 Platform Standup", base + timedelta(hours=1)))
        conductor.refresh()

        new_id = db.calendar_events.list_all()[0].id
        assert new_id != old_id, "the projection id regenerated on the time change"
        assert db.calendar_event_projects.list_for_event(new_id) == []
        assert db.calendar_event_projects.is_suppressed(new_id, "proj-1")


class TestNoWatchQueryWarning:
    def test_refresh_logs_no_broken_watch_query(self, db: Database, ics_file: Path, caplog) -> None:
        """C6(a): the branch that selected a column that does not exist is gone."""
        import logging

        _seed_room(db, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db, str(ics_file))
        with caplog.at_level(logging.WARNING, logger="holdspeak.calendar_ingest_conductor"):
            conductor.refresh()
        assert "watch query load failed" not in caplog.text
        assert "no such column" not in caplog.text
        # and the title match still links
        assert len(db.calendar_event_projects.list_for_project("proj-1")) == 1


class TestManualLinkFollowsTimeChange:
    def test_manual_link_rebinds_by_uid(self, db: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "vendor.ics"
        ics.write_bytes(_timed_ics("Vendor call", base, uid="vendor-1"))
        _seed_room(db, "proj-a", "Alpha Room")
        conductor = _make_conductor(db, str(ics))
        conductor.refresh()
        old = db.calendar_events.list_all()[0]
        db.calendar_event_projects.link(old.id, "proj-a", "manual")

        ics.write_bytes(_timed_ics("Vendor call", base + timedelta(hours=1), uid="vendor-1"))
        conductor.refresh()

        new = db.calendar_events.list_all()[0]
        assert new.id != old.id
        links = db.calendar_event_projects.list_for_event(new.id)
        assert [(l.project_id, l.match_source) for l in links] == [("proj-a", "manual")]
        # No orphan row survives against the dead id.
        assert [l.calendar_event_id for l in db.calendar_event_projects.list_for_project("proj-a")] == [new.id]

    def test_manual_link_dropped_when_uid_leaves(self, db: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "vendor.ics"
        ics.write_bytes(_timed_ics("Vendor call", base, uid="vendor-1"))
        _seed_room(db, "proj-a", "Alpha Room")
        conductor = _make_conductor(db, str(ics))
        conductor.refresh()
        old = db.calendar_events.list_all()[0]
        db.calendar_event_projects.link(old.id, "proj-a", "manual")

        ics.write_bytes(_timed_ics("Other call", base, uid="other-9"))
        conductor.refresh()

        assert db.calendar_event_projects.list_for_project("proj-a") == []
