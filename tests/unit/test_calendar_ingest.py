"""Source-boundary and projection coverage for Calendar ingest."""
from __future__ import annotations

import json
import math
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak import macos_calendar
from holdspeak.calendar_ingest import MAX_FEED_BYTES
from holdspeak.calendar_ingest_conductor import (
    CalendarIngestConductor,
    CalendarSourceError,
    CalendarSourceReader,
)
from holdspeak.config import (
    CalendarConfig,
    CalendarSource,
    Config,
    calendar_source_revision,
    calendar_subscription_revision,
)
from holdspeak.config.meeting import MeetingConfig
from holdspeak.db import Database
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

NOW = datetime(2026, 8, 27, 9, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "calendar-ingest.db")
    yield database
    reset_database()


@pytest.fixture
def subscription_file(tmp_path: Path) -> Path:
    fixture = Path(__file__).parents[1] / "fixtures" / "calendar" / "basic.ics"
    path = tmp_path / "calendar.ics"
    path.write_bytes(fixture.read_bytes())
    return path


class _FetchHandler(BaseHTTPRequestHandler):
    seen_headers: list[dict[str, str]] = []

    def log_message(self, format: str, *args: Any) -> None:
        return None

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        type(self).seen_headers.append(dict(self.headers.items()))
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://calendar-final.example.test/final.ics")
            self.end_headers()
            return
        if self.path == "/oversize":
            self.send_response(200)
            self.send_header("Content-Length", str(MAX_FEED_BYTES + 1))
            self.end_headers()
            return
        if self.path == "/slow":
            time.sleep(1.5)  # past the reader's timeout in the test below
        body = (
            b"BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:basic-1\r\n"
            b"DTSTART:20260827T100000Z\r\nDTEND:20260827T110000Z\r\n"
            b"SUMMARY:Team standup\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def local_http_server() -> str:
    _FetchHandler.seen_headers = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FetchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def _conductor(
    db: Database,
    source: str,
    reader: Any,
    *,
    clock: float = NOW.timestamp(),
) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: clock,
        db_factory=lambda: db,
        source_reader=reader,
        config_loader=lambda: Config(calendar=CalendarConfig(sources=[
            CalendarSource(id="test-src", label="", url=source, enabled=True)
        ])),
    )


def test_file_subscription_projects_then_honestly_removes_vanished_events(
    db: Database, subscription_file: Path
) -> None:
    conductor = _conductor(db, str(subscription_file), CalendarSourceReader())

    assert conductor.refresh() is True
    first = db.calendar_events.list_all()
    assert [(event.uid, event.title) for event in first] == [("basic-1", "Team standup")]

    subscription_file.write_bytes(b"BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n")

    assert conductor.refresh() is True
    assert db.calendar_events.list_all() == []

    subscription_file.write_bytes(b"x" * (MAX_FEED_BYTES + 1))
    with pytest.raises(CalendarSourceError, match="calendar_source_too_large"):
        CalendarSourceReader().read(str(subscription_file))


def test_https_subscription_projects_the_same_contract_without_auth_headers(
    db: Database, local_http_server: str
) -> None:
    # ``read`` rejects http before any I/O. Calling the HTTPS transport seam
    # directly against a local HTTP server is the lawful external-wire fake;
    # it proves redirects/headers/caps without inventing a TLS fixture.
    reader = CalendarSourceReader()
    with pytest.raises(CalendarSourceError, match="calendar_source_invalid"):
        reader.read(f"{local_http_server}/basic")
    conductor = _conductor(
        db,
        "https://calendar.example.test/source.ics",
        lambda _subscription: reader._read_https(f"{local_http_server}/basic"),
    )

    assert conductor.refresh() is True
    assert db.calendar_events.list_all()[0].uid == "basic-1"
    headers = {key.lower(): value for key, value in _FetchHandler.seen_headers[-1].items()}
    assert "authorization" not in headers
    assert "cookie" not in headers


def test_reader_rejects_redirect_timeout_and_oversize_before_projection(
    db: Database, local_http_server: str
) -> None:
    reader = CalendarSourceReader()
    # The production timeout is 10 s. The same socket timeout runs against a
    # live delayed local socket (not a mocked transport timeout), shortened
    # on this reader so the test does not wait out 10 s (fast diet 2026-10-12).
    assert reader.timeout_seconds == 10.0
    reader.timeout_seconds = 0.5

    with pytest.raises(CalendarSourceError) as redirect:
        reader._read_https(f"{local_http_server}/redirect")
    assert redirect.value.error_class == "calendar_source_redirect"
    assert redirect.value.redirect_target == "https://calendar-final.example.test/final.ics"

    with pytest.raises(CalendarSourceError, match="calendar_source_timeout"):
        reader._read_https(f"{local_http_server}/slow")

    with pytest.raises(CalendarSourceError, match="calendar_source_too_large"):
        reader._read_https(f"{local_http_server}/oversize")

    conductor = _conductor(
        db,
        "https://calendar.example.test/source.ics",
        lambda _subscription: (_ for _ in ()).throw(redirect.value),
    )
    assert conductor.refresh() is False
    with db._connection() as conn:
        receipt = conn.execute(
            "SELECT state, outcome, result_ref FROM kernel_receipts"
        ).fetchone()
    assert tuple(receipt) == (
        "refused",
        "calendar_refresh_failed",
        "calendar-source:"
        f"{calendar_source_revision('test-src', 'https://calendar.example.test/source.ics')[:16]}:"
        "https://calendar-final.example.test/final.ics",
    )


def test_bad_event_is_skipped_with_deduplicated_kernel_receipt(db: Database) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "calendar" / "mixed-bad-event.ics"
    conductor = _conductor(db, "/calendar.ics", lambda _source: fixture.read_bytes())

    assert conductor.refresh() is True
    assert conductor.refresh() is True
    assert [event.uid for event in db.calendar_events.list_all()] == ["good-sibling"]
    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT state, outcome, result_ref FROM kernel_receipts ORDER BY created_at"
        ).fetchall()
    assert len(receipts) == 1
    assert receipts[0][0:2] == ("refused", "calendar_event_skipped")
    assert receipts[0][2].startswith("calendar-event:")


def test_feed_failure_retains_last_known_good_projection_and_receipts_once(
    db: Database, subscription_file: Path
) -> None:
    conductor = _conductor(db, str(subscription_file), CalendarSourceReader())
    assert conductor.refresh() is True
    original = db.calendar_events.list_all()
    subscription_file.write_bytes(b"not calendar\xff")

    assert conductor.refresh() is False
    assert conductor.refresh() is False
    assert db.calendar_events.list_all() == original
    with db._connection() as conn:
        receipts = conn.execute(
            "SELECT state, outcome FROM kernel_receipts ORDER BY created_at"
        ).fetchall()
    assert [tuple(receipt) for receipt in receipts] == [
        ("failed", "calendar_refresh_failed")
    ]


# ── from test_hs175_calendar_wire.py: HS-175-02: Calendar events on the desk -- wire tests. ──
#
# Tests:
# 1. The sweep runs the calendar refresh once and receipts it (stub the fetch;
#    a file source needs no network).
# 2. No double refresh with the old thread gone.
# 3. The matcher's title rule as ruled R1 (2026-09-06): full-name phrase,
#    longest wins, a single generic word never links.
# 4. The manual link overrides the matcher.
# 5. `door.week` days/total.
# 6. `upcoming` carries the room (project_id + project_name).
# 7. HTTPS source receipts name the host.
#
# Isolated HOME via tmp_path; never the owner's DB.


OWNER = Principal(PrincipalKind.OWNER, "test-owner")

# HS-200-03: a sweep held by quiet hours writes no `calendar` sub-receipt
# (holdspeak/services/heartbeat_service.py:334), and quiet hours default to
# 22:00-08:00 LOCAL. These tests read the machine's wall clock, so they passed
# by day and failed at night -- which is exactly what happened on the CI runner
# (Actions run 34007939416 started 04:18 UTC). The sweep clock is pinned to a
# fixed midday instant, IN A FIXED ZONE, instead: both the time and the zone
# are injected, and no tolerance is widened. Pinning the instant alone would
# not be enough -- 12:00 UTC is midnight in Auckland, still inside the window.
SWEEP_NOW = datetime(2026, 9, 6, 12, 0, 0, tzinfo=timezone.utc)


def _daylight_clock():
    """The injected sweep clock: a fixed instant outside any quiet window."""
    return SWEEP_NOW


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
def db_wire(tmp_path: Path) -> Database:
    return Database(tmp_path / "test175.db")


@pytest.fixture
def ics_file(tmp_path: Path) -> Path:
    p = tmp_path / "cal.ics"
    p.write_bytes(_make_ics())
    return p


def _make_config(ics_path: str, source_id: str = "src-1"):
    """Build a minimal Config mock with one file-based calendar source."""
    from holdspeak.config.integrations import CalendarConfig, CalendarSource

    source = CalendarSource(
        id=source_id, label="TEST", url=str(ics_path), enabled=True,
    )
    config = MagicMock()
    config.calendar = CalendarConfig(sources=[source])
    # Prevent the event-born recording code from crashing on MagicMock attributes.
    config.meeting.auto_record = "off"
    config.meeting.auto_record_lead_minutes = 5
    return config


def _make_conductor(db_wire: Database, ics_path: str, source_id: str = "src-1"):
    """Build a CalendarIngestConductor wired to the test DB and file source."""
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    config = _make_config(ics_path, source_id)
    conductor = CalendarIngestConductor(
        db_factory=lambda: db_wire,
        config_loader=lambda: config,
        tick_interval=9999,  # never auto-tick
    )
    return conductor


# -- Test 1: sweep runs the refresh once and receipts it -------------------

class TestSweepRunsCalendarRefresh:
    def test_sweep_calls_refresh_and_receipts(self, db_wire: Database, ics_file: Path) -> None:
        """The heartbeat sweep calls conductor.refresh() and the receipt
        carries calendar.refresh with applied=True."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        conductor = _make_conductor(db_wire, str(ics_file))
        mock_ws = MagicMock()
        mock_ws.evaluate_due.return_value = []

        hb = HeartbeatService(
            db_wire, watch_service=mock_ws, calendar_conductor=conductor,
            clock=_daylight_clock, local_zone=timezone.utc,
        )
        receipt = hb.run_sweep(OWNER)

        assert "calendar" in receipt, "receipt must carry calendar sub-receipt"
        cal = receipt["calendar"]
        assert cal["kind"] == "calendar.refresh"
        assert cal["applied"] is True

    def test_sweep_receipts_applied_false_when_no_sources(self, db_wire: Database, tmp_path: Path) -> None:
        """When no calendar sources are configured, applied=False."""
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
        from holdspeak.services.heartbeat_service import HeartbeatService

        config = MagicMock()
        config.calendar = MagicMock()
        config.calendar.sources = []  # no sources
        conductor = CalendarIngestConductor(
            db_factory=lambda: db_wire,
            config_loader=lambda: config,
        )
        hb = HeartbeatService(
            db_wire, calendar_conductor=conductor,
            clock=_daylight_clock, local_zone=timezone.utc,
        )
        receipt = hb.run_sweep(OWNER)

        cal = receipt["calendar"]
        assert cal["applied"] is False


# -- Test 2: no double refresh with old thread gone -------------------------

class TestNoDoubleRefresh:
    def test_conductor_start_does_not_spawn_thread(self, db_wire: Database, ics_file: Path) -> None:
        """After HS-175-02, start_calendar_ingest_conductor does NOT spawn
        the standalone thread."""
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

        conductor = _make_conductor(db_wire, str(ics_file))
        # The conductor's thread should be None (never started).
        assert conductor._thread is None
        # Calling refresh() directly works.
        result = conductor.refresh()
        assert result is True
        # Thread still None.
        assert conductor._thread is None


# -- Test 3: matcher's title rule + H3 negative ---------------------------

class TestTitleMatcher:
    def test_title_match_links_event_to_room(self, db_wire: Database, ics_file: Path) -> None:
        """An event titled 'Q4 Platform Standup' matches a Room named
        'Q4 Platform' (Room name is a whole-word substring)."""
        conductor = _make_conductor(db_wire, str(ics_file))
        # Create a project (Room) named "Q4 Platform".
        with db_wire._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-1", "Q4 Platform"),
            )
        conductor.refresh()
        # The matcher should have linked the event to the project.
        links = db_wire.calendar_event_projects.list_for_project("proj-1")
        assert len(links) >= 1
        assert links[0].match_source == "title"

    def test_r1_short_one_word_name_links_when_its_whole_word_appears(
        self, db_wire: Database, ics_file: Path
    ) -> None:
        """R1 supersedes H3's >= 4-char floor: 'Q4' is a one-word Room name
        that is NOT generic meeting vocabulary and appears whole in
        'Q4 Platform Standup', so it links (the old rule refused it on
        length alone)."""
        conductor = _make_conductor(db_wire, str(ics_file))
        _seed_room(db_wire, "proj-short", "Q4")
        conductor.refresh()
        links = db_wire.calendar_event_projects.list_for_project("proj-short")
        assert [l.match_source for l in links] == ["title"]

    def test_r1_generic_one_word_room_never_links(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: counsel's false positive -- a Room named 'Design' must not
        link a '401k enrollment design review' webinar."""
        ics = tmp_path / "webinar.ics"
        ics.write_bytes(_make_ics(title="401k enrollment design review"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-design", "Design")
        conductor.refresh()
        assert db_wire.calendar_event_projects.list_for_project("proj-design") == []

    def test_r1_generic_stoplist_is_case_insensitive(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: a Room named 'Sync' (any case) never links 'Payments sync'."""
        ics = tmp_path / "payments.ics"
        ics.write_bytes(_make_ics(title="Payments sync"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-sync", "SYNC")
        conductor.refresh()
        assert db_wire.calendar_event_projects.list_for_project("proj-sync") == []

    def test_r1_non_generic_one_word_room_links(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: 'Governance' is one word but not generic, so it links
        'Governance sync'."""
        ics = tmp_path / "gov.ics"
        ics.write_bytes(_make_ics(title="Governance sync"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-gov", "Governance")
        conductor.refresh()
        links = db_wire.calendar_event_projects.list_for_project("proj-gov")
        assert [l.match_source for l in links] == ["title"]

    def test_r1_partial_phrase_never_links(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: 'Q4 Platform' does NOT link 'Platform review' -- one word of a
        multi-word Room name is not the Room's full name."""
        ics = tmp_path / "partial.ics"
        ics.write_bytes(_make_ics(title="Platform review"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor.refresh()
        assert db_wire.calendar_event_projects.list_for_project("proj-1") == []

    def test_r1_phrase_match_is_punctuation_insensitive(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: 'Q4 Platform' links 'q4-platform sync' (hyphen, lower case)."""
        ics = tmp_path / "hyphen.ics"
        ics.write_bytes(_make_ics(title="q4-platform sync"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor.refresh()
        links = db_wire.calendar_event_projects.list_for_project("proj-1")
        assert [l.match_source for l in links] == ["title"]

    def test_r1_whole_word_bounded(self, db_wire: Database, tmp_path: Path) -> None:
        """R1: whole-word bounded -- 'Platform' is not a phrase of
        'Platforms roadmap', and 'Q4 Platform' is not one of 'Q4 Platforms'."""
        ics = tmp_path / "plural.ics"
        ics.write_bytes(_make_ics(title="Q4 Platforms roadmap"))
        conductor = _make_conductor(db_wire, str(ics))
        _seed_room(db_wire, "proj-plat", "Platform")
        _seed_room(db_wire, "proj-full", "Q4 Platform")
        conductor.refresh()
        assert db_wire.calendar_event_projects.list_for_project("proj-plat") == []
        assert db_wire.calendar_event_projects.list_for_project("proj-full") == []

    def test_longest_match_wins(self, db_wire: Database, tmp_path: Path) -> None:
        """Two full names present ('Platform' and 'Q4 Platform' both appear
        whole in 'Q4 Platform Architecture Review'): the LONGER wins."""
        ics = tmp_path / "cal2.ics"
        ics.write_bytes(_make_ics(title="Q4 Platform Architecture Review"))
        conductor = _make_conductor(db_wire, str(ics))
        with db_wire._connection() as conn:
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
        links_full = db_wire.calendar_event_projects.list_for_project("proj-full")
        links_plat = db_wire.calendar_event_projects.list_for_project("proj-plat")
        assert len(links_full) == 1
        # "Platform" also matches as a substring, but the test should verify
        # only one project is linked per event (the longest).
        # The matcher picks the BEST match per event, so only one link per event.
        events = db_wire.calendar_events.list_all()
        assert len(events) >= 1
        event_id = events[0].id
        all_links = db_wire.calendar_event_projects.list_for_event(event_id)
        assert len(all_links) == 1
        assert all_links[0].project_id == "proj-full"


# -- Test 4: manual link overrides ----------------------------------------

class TestManualLinkOverrides:
    def test_manual_link_survives_matcher_rerun(self, db_wire: Database, ics_file: Path) -> None:
        """A manual link is preserved across matcher re-runs."""
        conductor = _make_conductor(db_wire, str(ics_file))
        # First refresh to populate events.
        conductor.refresh()
        events = db_wire.calendar_events.list_all()
        assert len(events) >= 1
        event_id = events[0].id

        # Manually link to a different project.
        with db_wire._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-manual", "Manual Project"),
            )
        db_wire.calendar_event_projects.link(event_id, "proj-manual", "manual")

        # Re-run the refresh (which re-runs the matcher).
        conductor.refresh()

        # The manual link must survive.
        links = db_wire.calendar_event_projects.list_for_event(event_id)
        manual_links = [l for l in links if l.match_source == "manual"]
        assert len(manual_links) == 1
        assert manual_links[0].project_id == "proj-manual"


# -- Test 5: door.week days/total -----------------------------------------

class TestDoorWeek:
    def test_week_strip_with_events(self, db_wire: Database, tmp_path: Path) -> None:
        """door.week carries days with counts and total when calendar is connected."""
        # Seed inside the CURRENT LOCAL week (the strip's window). The shared
        # fixture seeds now + 2 h, which on a Sunday after 22:00 local is next
        # week (failed 2026-10-04 22:22 MDT).
        # The ingest keeps only events still to come, so the event sits
        # halfway between now and the end of this local week. One pinned
        # instant drives the seed, the ingest and the Door read, so no
        # midnight can fall between them (Astra, #846).
        local_now = datetime.now().astimezone()
        next_monday = (local_now + timedelta(days=7 - local_now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0)
        start_dt = (local_now + (next_monday - local_now) / 2).astimezone(timezone.utc)
        ics_file = tmp_path / "cal-week.ics"
        ics_file.write_bytes(_make_ics(
            start=start_dt.strftime("%Y%m%dT%H%M%SZ"),
            end=(start_dt + timedelta(minutes=20)).strftime("%Y%m%dT%H%M%SZ"),
        ))
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
        from holdspeak.db.calendar_events import CalendarEventRepository
        from holdspeak.db.scheduled_recordings import ScheduledRecordingRepository
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import (
            RefinementThoughtService,
        )

        ingest_config = _make_config(str(ics_file))
        conductor = CalendarIngestConductor(
            clock=lambda: local_now.timestamp(),
            db_factory=lambda: db_wire,
            config_loader=lambda: ingest_config,
            tick_interval=9999,
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
            db_wire.scheduled_recordings,
            db_wire.calendar_events,
            db=db_wire,
            config_loader=lambda: config,
            clock=lambda: local_now,
        )
        result = service.get(OWNER)
        week = result["week"]
        assert week["has_calendar"] is True
        assert len(week["days"]) == 7
        assert week["total"] >= 1
        # The event we seeded is in this local week, so one day has count > 0.
        day_counts = [d["count"] for d in week["days"]]
        assert sum(day_counts) == week["total"]

    def test_week_strip_absent_when_no_calendar(self, db_wire: Database) -> None:
        """door.week.has_calendar is False when no sources are configured."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import (
            RefinementThoughtService,
        )

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        service = DoorService(
            ft, rt,
            db_wire.scheduled_recordings,
            db_wire.calendar_events,
            db=db_wire,
            config_loader=None,  # no calendar
        )
        result = service.get(OWNER)
        week = result["week"]
        assert week["has_calendar"] is False
        assert week["total"] == 0


# -- Test 6: upcoming carries room ----------------------------------------

class TestUpcomingCarriesRoom:
    def test_upcoming_event_carries_project(self, db_wire: Database, ics_file: Path) -> None:
        """When an event is linked to a Room, upcoming items carry
        project_id and project_name."""
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import (
            RefinementThoughtService,
        )

        conductor = _make_conductor(db_wire, str(ics_file))
        with db_wire._connection() as conn:
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
            db_wire.scheduled_recordings,
            db_wire.calendar_events,
            db=db_wire,
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
    def test_sweep_receipt_names_https_host(self, db_wire: Database, tmp_path: Path) -> None:
        """When a source is an HTTPS URL, the sweep receipt's calendar
        sub-receipt lists the host."""
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
        from holdspeak.config.integrations import CalendarConfig, CalendarSource
        from holdspeak.services.heartbeat_service import HeartbeatService

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
            db_factory=lambda: db_wire,
            config_loader=lambda: config,
        )

        hb = HeartbeatService(
            db_wire, calendar_conductor=conductor,
            clock=_daylight_clock, local_zone=timezone.utc,
        )
        receipt = hb.run_sweep(OWNER)

        cal = receipt.get("calendar", {})
        assert cal.get("kind") == "calendar.refresh"
        sources = cal.get("sources", [])
        assert len(sources) == 1
        assert sources[0]["source_id"] == "https-src"
        assert sources[0]["host"] == "outlook.office365.com"


# -- Test: attendee extraction -----------------------------------------------

class TestAttendeeExtraction:
    def test_attendees_extracted_from_ics(self, db_wire: Database, ics_file: Path) -> None:
        """The parser extracts ATTENDEE mailto: addresses from the ICS feed."""
        conductor = _make_conductor(db_wire, str(ics_file))
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
    def test_link_and_list(self, db_wire: Database) -> None:
        """link() and list_for_event() round-trip."""
        db_wire.calendar_event_projects.link("evt-1", "proj-1", "title")
        links = db_wire.calendar_event_projects.list_for_event("evt-1")
        assert len(links) == 1
        assert links[0].project_id == "proj-1"

    def test_manual_link_survives_replace_auto(self, db_wire: Database) -> None:
        """replace_auto_links preserves manual links."""
        db_wire.calendar_event_projects.link("evt-1", "proj-1", "manual")
        db_wire.calendar_event_projects.replace_auto_links([
            ("evt-1", "proj-2", "title"),
        ])
        links = db_wire.calendar_event_projects.list_for_event("evt-1")
        pids = {l.project_id for l in links}
        assert "proj-1" in pids, "manual link must survive"
        # The auto link may or may not be there (ON CONFLICT DO NOTHING).
        # The manual link is the key assertion.

    def test_unlink(self, db_wire: Database) -> None:
        """unlink() removes one link."""
        db_wire.calendar_event_projects.link("evt-1", "proj-1", "title")
        count = db_wire.calendar_event_projects.unlink("evt-1", "proj-1")
        assert count == 1
        assert len(db_wire.calendar_event_projects.list_for_event("evt-1")) == 0

    def test_build_event_project_index(self, db_wire: Database) -> None:
        """build_event_project_index returns event_id -> (project_id, name)."""
        with db_wire._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                ("proj-1", "Alpha"),
            )
        db_wire.calendar_event_projects.link("evt-1", "proj-1", "title")
        index = db_wire.calendar_event_projects.build_event_project_index()
        assert "evt-1" in index
        assert index["evt-1"] == ("proj-1", "Alpha")


# -- HS-175 counsel-on-built: C5 / C6(a) / C6(c) ----------------------------
#
# C5  DELETE /link is durable: the suppression outlives the next refresh
#     and a time change; a manual link clears it.
# C6a the Watch-query branch is gone -- no "no such column" warning per Room.
# C6c a manual link follows its event across a time change (rebind by uid).

_FMT = "%Y%m%dT%H%M%SZ"


def _seed_room(db_wire: Database, pid: str, name: str) -> None:
    with db_wire._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (pid, name))


def _timed_ics(title: str, start: datetime, *, uid: str = "test-1") -> bytes:
    return _make_ics(
        uid=uid, title=title,
        start=start.strftime(_FMT), end=(start + timedelta(hours=1)).strftime(_FMT),
    )


class TestUnlinkIsDurable:
    def test_unlink_survives_the_next_refresh(self, db_wire: Database, ics_file: Path) -> None:
        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db_wire, str(ics_file))
        conductor.refresh()
        event_id = db_wire.calendar_events.list_all()[0].id
        assert [l.project_id for l in db_wire.calendar_event_projects.list_for_event(event_id)] == ["proj-1"]

        assert db_wire.calendar_event_projects.unlink(event_id, "proj-1") == 1
        assert db_wire.calendar_event_projects.is_suppressed(event_id, "proj-1")

        conductor.refresh()  # the matcher would re-link by title without C5

        assert db_wire.calendar_event_projects.list_for_event(event_id) == []
        assert event_id not in db_wire.calendar_event_projects.build_event_project_index()

    def test_unlink_all_survives_and_a_manual_link_clears_it(self, db_wire: Database, ics_file: Path) -> None:
        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db_wire, str(ics_file))
        conductor.refresh()
        event_id = db_wire.calendar_events.list_all()[0].id

        assert db_wire.calendar_event_projects.unlink_event(event_id) == 1
        conductor.refresh()
        assert db_wire.calendar_event_projects.list_for_event(event_id) == []

        # The owner's newer word: link it by hand -> the suppression is cleared.
        db_wire.calendar_event_projects.link(event_id, "proj-1", "manual")
        assert not db_wire.calendar_event_projects.is_suppressed(event_id, "proj-1")
        conductor.refresh()
        links = db_wire.calendar_event_projects.list_for_event(event_id)
        assert [(l.project_id, l.match_source) for l in links] == [("proj-1", "manual")]

    def test_unlink_survives_a_time_change(self, db_wire: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "moving.ics"
        ics.write_bytes(_timed_ics("Q4 Platform Standup", base))
        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db_wire, str(ics))
        conductor.refresh()
        old_id = db_wire.calendar_events.list_all()[0].id
        db_wire.calendar_event_projects.unlink(old_id, "proj-1")

        ics.write_bytes(_timed_ics("Q4 Platform Standup", base + timedelta(hours=1)))
        conductor.refresh()

        new_id = db_wire.calendar_events.list_all()[0].id
        assert new_id != old_id, "the projection id regenerated on the time change"
        assert db_wire.calendar_event_projects.list_for_event(new_id) == []
        assert db_wire.calendar_event_projects.is_suppressed(new_id, "proj-1")


class TestNoWatchQueryWarning:
    def test_refresh_logs_no_broken_watch_query(self, db_wire: Database, ics_file: Path, caplog) -> None:
        """C6(a): the branch that selected a column that does not exist is gone."""
        import logging

        _seed_room(db_wire, "proj-1", "Q4 Platform")
        conductor = _make_conductor(db_wire, str(ics_file))
        with caplog.at_level(logging.WARNING, logger="holdspeak.calendar_ingest_conductor"):
            conductor.refresh()
        assert "watch query load failed" not in caplog.text
        assert "no such column" not in caplog.text
        # and the title match still links
        assert len(db_wire.calendar_event_projects.list_for_project("proj-1")) == 1


class TestManualLinkFollowsTimeChange:
    def test_manual_link_rebinds_by_uid(self, db_wire: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "vendor.ics"
        ics.write_bytes(_timed_ics("Vendor call", base, uid="vendor-1"))
        _seed_room(db_wire, "proj-a", "Alpha Room")
        conductor = _make_conductor(db_wire, str(ics))
        conductor.refresh()
        old = db_wire.calendar_events.list_all()[0]
        db_wire.calendar_event_projects.link(old.id, "proj-a", "manual")

        ics.write_bytes(_timed_ics("Vendor call", base + timedelta(hours=1), uid="vendor-1"))
        conductor.refresh()

        new = db_wire.calendar_events.list_all()[0]
        assert new.id != old.id
        links = db_wire.calendar_event_projects.list_for_event(new.id)
        assert [(l.project_id, l.match_source) for l in links] == [("proj-a", "manual")]
        # No orphan row survives against the dead id.
        assert [l.calendar_event_id for l in db_wire.calendar_event_projects.list_for_project("proj-a")] == [new.id]

    def test_manual_link_dropped_when_uid_leaves(self, db_wire: Database, tmp_path: Path) -> None:
        base = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
        ics = tmp_path / "vendor.ics"
        ics.write_bytes(_timed_ics("Vendor call", base, uid="vendor-1"))
        _seed_room(db_wire, "proj-a", "Alpha Room")
        conductor = _make_conductor(db_wire, str(ics))
        conductor.refresh()
        old = db_wire.calendar_events.list_all()[0]
        db_wire.calendar_event_projects.link(old.id, "proj-a", "manual")

        ics.write_bytes(_timed_ics("Other call", base, uid="other-9"))
        conductor.refresh()

        assert db_wire.calendar_event_projects.list_for_project("proj-a") == []


# ── from test_hs175_event_recordings.py: HS-175-03: Event-born scheduled recordings. ──
#
# Tests the auto-record setting, the conductor's event-born creation logic,
# idempotency, vanished/moved event handling, the hub read, and the door
# projection.


# -- constants ----------------------------------------------------------------

NOW_recordings = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
NOW_EPOCH = NOW_recordings.timestamp()

ICS_TWO_EVENTS = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T100000Z\r\n"
    b"DTEND:20260905T110000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-no-url\r\n"
    b"DTSTART:20260905T140000Z\r\n"
    b"DTEND:20260905T150000Z\r\n"
    b"SUMMARY:Lunch\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_ONE_WITH_URL = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T100000Z\r\n"
    b"DTEND:20260905T110000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_MOVED_EVENT = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-with-url\r\n"
    b"DTSTART:20260905T120000Z\r\n"
    b"DTEND:20260905T130000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/123\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_EMPTY = (
    b"BEGIN:VCALENDAR\r\n"
    b"END:VCALENDAR\r\n"
)

SOURCE_ID = "test-cal"


# -- helpers ------------------------------------------------------------------

def _cal(url: str = "/test.ics") -> CalendarConfig:
    return CalendarConfig(sources=[
        CalendarSource(id=SOURCE_ID, label="WORK", url=url, enabled=True)
    ])


def _config(auto_record: str = "off", lead: int = 5) -> Config:
    return Config(
        calendar=_cal(),
        meeting=MeetingConfig(auto_record=auto_record, auto_record_lead_minutes=lead),
    )


def _make_conductor_recordings(
    db_recordings: Database,
    config_fn,
    ics_bytes: bytes = ICS_TWO_EVENTS,
) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: NOW_EPOCH,
        db_factory=lambda: db_recordings,
        source_reader=lambda _sub: ics_bytes,
        config_loader=config_fn,
        tick_interval=999,
    )


@pytest.fixture
def db_recordings(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "event-born.db")
    yield database
    reset_database()


# -- tests --------------------------------------------------------------------


class TestAutoRecordOff:
    """When auto_record=off, no event-born recordings are created."""

    def test_off_creates_nothing(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("off"))
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 0


class TestAutoRecordAllCalendar:
    """When auto_record=all_calendar, every event with a meeting_url gets a recording."""

    def test_creates_one_per_event_with_url(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"))
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 1
        rec = recordings[0]
        assert rec.title == "Standup"
        assert rec.calendar_uid == "ev-with-url"
        assert rec.calendar_source_id == SOURCE_ID
        assert rec.born_from == "calendar_event"
        assert rec.enabled is True
        assert rec.state == "idle"

    def test_no_recording_without_url(self, db_recordings: Database) -> None:
        """The Lunch event has no meeting_url -- no recording created."""
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"))
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        titles = [r.title for r in recordings]
        assert "Lunch" not in titles

    def test_lead_time(self, db_recordings: Database) -> None:
        """The recording's next_fire_at is starts_at - lead_minutes."""
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar", lead=5))
        conductor.refresh()

        rec = db_recordings.scheduled_recordings.list_all()[0]
        event_start = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
        expected_fire = (event_start - timedelta(minutes=5)).timestamp()
        assert rec.next_fire_at == pytest.approx(expected_fire, abs=1.0)

    def test_duration_from_event(self, db_recordings: Database) -> None:
        """Duration is computed from event start/end."""
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"))
        conductor.refresh()

        rec = db_recordings.scheduled_recordings.list_all()[0]
        assert rec.duration_minutes == 60  # 10:00 to 11:00


class TestAutoRecordRoomLinked:
    """When auto_record=room_linked, only events with a calendar_event_projects row."""

    def test_creates_only_for_linked(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("room_linked"))
        conductor.refresh()

        # No Rooms and no links -> every event is unlinked -> nothing arms.
        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 0

    def test_creates_when_linked(self, db_recordings: Database) -> None:
        """When the event has a calendar_event_projects row, recording is created."""
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("room_linked"))
        conductor.refresh()

        # The owner links the event to a Room by hand (a manual link is the
        # honest fixture: the matcher clears stale auto links of Rooms that
        # do not exist, and 'proj-1' is no Room here).
        with db_recordings._connection() as conn:
            event_row = conn.execute(
                "SELECT id FROM calendar_events WHERE uid='ev-with-url'"
            ).fetchone()
            assert event_row is not None
        db_recordings.calendar_event_projects.link(event_row["id"], "proj-1", "manual")

        # Refresh again -- now the event is linked.
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 1
        assert recordings[0].title == "Standup"


class TestIdempotency:
    """Re-ingesting the same event does not create duplicate recordings."""

    def test_idempotent_across_refreshes(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"))
        conductor.refresh()
        conductor.refresh()
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 1


class TestVanishedEvent:
    """An event that disappears from the ICS -> its recording is cancelled."""

    def test_vanished_event_cancels_recording(self, db_recordings: Database) -> None:
        # First refresh creates the recording.
        ics_state = {"bytes": ICS_ONE_WITH_URL}
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db_recordings,
            source_reader=lambda _sub: ics_state["bytes"],
            config_loader=lambda: _config("all_calendar"),
            tick_interval=999,
        )
        conductor.refresh()
        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 1
        assert recordings[0].enabled is True
        assert recordings[0].state == "idle"

        # Event vanishes from the feed.
        ics_state["bytes"] = ICS_EMPTY
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        rec = recordings[0]
        assert rec.enabled is False
        assert rec.state == "cancelled"
        assert rec.last_outcome == "event_removed"


class TestMovedEvent:
    """An event whose time changed -> next_fire_at follows."""

    def test_moved_event_updates_fire_time(self, db_recordings: Database) -> None:
        ics_state = {"bytes": ICS_ONE_WITH_URL}
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db_recordings,
            source_reader=lambda _sub: ics_state["bytes"],
            config_loader=lambda: _config("all_calendar", lead=5),
            tick_interval=999,
        )
        conductor.refresh()

        rec_before = db_recordings.scheduled_recordings.list_all()[0]
        old_fire = rec_before.next_fire_at

        # Event moves to 12:00.
        ics_state["bytes"] = ICS_MOVED_EVENT
        conductor.refresh()

        rec_after = db_recordings.scheduled_recordings.list_all()
        # The recording for the old event time was reconciled (R1 or R2),
        # so next_fire_at should have changed.
        enabled_recs = [r for r in rec_after if r.enabled]
        assert len(enabled_recs) >= 1
        # At least one enabled recording should have a different fire time.
        any_changed = any(r.next_fire_at != old_fire for r in enabled_recs)
        assert any_changed or len(enabled_recs) > 1


class TestArmsLikeEveryScheduledRecording:
    """C1 as ruled (design B11): an event-born recording is a 136 scheduled
    recording -- the ingest conductor leaves it idle + enabled with
    next_fire_at = starts_at - lead, and the scheduled-recording conductor
    arms it at that time and records at the event.  This test proves ONLY
    the ingest side's hand-off; it makes no "never started" claim."""

    def test_event_born_row_is_handed_to_the_scheduled_conductor(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar", lead=5))
        conductor.refresh()

        recordings = db_recordings.scheduled_recordings.list_all()
        assert len(recordings) == 1
        rec = recordings[0]
        assert rec.state == "idle" and rec.enabled is True
        assert rec.one_shot is True and rec.born_from == "calendar_event"
        event_start = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)
        assert rec.next_fire_at == pytest.approx(
            (event_start - timedelta(minutes=5)).timestamp(), abs=1.0
        )
        # list_enabled is what the scheduled-recording conductor polls.
        assert [r.id for r in db_recordings.scheduled_recordings.list_enabled()] == [rec.id]


class TestSettingOnHubRead:
    """The hub read exposes the auto_record setting."""

    def test_hub_read_exposes_auto_record(self, db_recordings: Database) -> None:
        """The MeetingConfig carries auto_record; verify it serializes."""
        cfg = MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=10)
        assert cfg.auto_record == "all_calendar"
        assert cfg.auto_record_lead_minutes == 10

    def test_default_is_off(self) -> None:
        cfg = MeetingConfig()
        assert cfg.auto_record == "off"
        assert cfg.auto_record_lead_minutes == 5

    def test_invalid_auto_record_rejected(self) -> None:
        with pytest.raises(ValueError, match="auto_record"):
            MeetingConfig(auto_record="invalid")


class TestRecordingReceipt:
    """Every auto-creation is receipted."""

    def test_receipt_written(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"))
        conductor.refresh()

        with db_recordings._connection() as conn:
            receipts = conn.execute(
                "SELECT * FROM kernel_receipts WHERE outcome='scheduled_recording.created.calendar_event'"
            ).fetchall()
        assert len(receipts) == 1


# -- HS-175 counsel-on-built: C3 / C4 / C6(b) --------------------------------
#
# C3  the owner's cancel is final across refreshes (tombstone by source+uid).
# C4  Remove/Disable disarms, even with zero enabled sources.
# C6b the matcher runs before the auto-create, so room_linked arms on the
#     FIRST refresh.

ICS_SECOND_SOURCE = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-personal\r\n"
    b"DTSTART:20260905T160000Z\r\n"
    b"DTEND:20260905T163000Z\r\n"
    b"SUMMARY:Dentist call\r\n"
    b"URL:https://zoom.example.com/j/9\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)

ICS_ROOM_EVENT = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:ev-room\r\n"
    b"DTSTART:20260905T130000Z\r\n"
    b"DTEND:20260905T133000Z\r\n"
    b"SUMMARY:Q4 Platform Standup\r\n"
    b"URL:https://teams.example.com/meet/q4\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)


def _owner_cancel(db_recordings: Database, rec_id: str, outcome: str = "owner_cancelled") -> None:
    """What the owner's Cancel leaves behind (C2's contract on the row):
    enabled=0, state='cancelled', last_outcome='owner_cancelled' -- or the
    136 countdown cancel's 'cancelled'.  Either is the owner's word."""
    db_recordings.scheduled_recordings.set_state(
        rec_id, "cancelled", last_outcome=outcome, enabled=False, next_fire_at=None,
    )


def _receipts(db_recordings: Database, outcome: str) -> int:
    with db_recordings._connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM kernel_receipts WHERE outcome = ?", (outcome,)
        ).fetchone()
    return int(row["n"])


def _feed_conductor(db_recordings: Database, config_fn, feed_state: dict) -> CalendarIngestConductor:
    return CalendarIngestConductor(
        clock=lambda: NOW_EPOCH,
        db_factory=lambda: db_recordings,
        source_reader=lambda _sub: feed_state["bytes"],
        config_loader=config_fn,
        tick_interval=999,
    )


class TestOwnerCancelIsFinal:
    """C3: cancel -> refresh -> still zero enabled rows, one skip receipt."""

    @pytest.mark.parametrize("outcome", ["owner_cancelled", "cancelled"])
    def test_cancel_then_refresh_does_not_rearm(self, db_recordings: Database, outcome: str) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db_recordings.scheduled_recordings.list_all()[0]
        _owner_cancel(db_recordings, rec.id, outcome)

        conductor.refresh()

        rows = db_recordings.scheduled_recordings.list_all()
        assert [r.id for r in rows] == [rec.id], "the refresh must not insert a second row"
        assert rows[0].enabled is False and rows[0].state == "cancelled"
        assert db_recordings.scheduled_recordings.list_enabled() == [], "a cancelled row is never armed"
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 1
        assert _receipts(db_recordings, "scheduled_recording.created.calendar_event") == 1

        # Idempotent: a third refresh adds neither a row nor a receipt.
        conductor.refresh()
        assert len(db_recordings.scheduled_recordings.list_all()) == 1
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 1

    def test_moved_occurrence_is_a_new_one_and_rearms(self, db_recordings: Database) -> None:
        """Counsel re-read (1): the tombstone is keyed by OCCURRENCE
        (source, uid, starts_at) so Cancel means "this one".  A single event
        whose time moves is a new occurrence under the toggle's standing
        consent -- it re-arms, and the cancelled row stays cancelled.
        (Carried to the owner: "this one or the series?")"""
        feed = {"bytes": ICS_ONE_WITH_URL}
        conductor = _feed_conductor(db_recordings, lambda: _config("all_calendar"), feed)
        conductor.refresh()
        rec = db_recordings.scheduled_recordings.list_all()[0]
        assert rec.calendar_starts_at == "2026-09-05T10:00:00Z"
        _owner_cancel(db_recordings, rec.id)

        feed["bytes"] = ICS_MOVED_EVENT
        conductor.refresh()

        enabled = db_recordings.scheduled_recordings.list_enabled()
        assert [r.calendar_starts_at for r in enabled] == ["2026-09-05T12:00:00Z"]
        cancelled = db_recordings.scheduled_recordings.get(rec.id)
        assert cancelled is not None and cancelled.enabled is False
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 0
        assert _receipts(db_recordings, "scheduled_recording.created.calendar_event") == 2

    def test_event_removed_is_not_a_tombstone(self, db_recordings: Database) -> None:
        """R3's cancel is the feed's doing, receipted as such; if the event
        returns, the toggle's standing consent arms it again."""
        feed = {"bytes": ICS_ONE_WITH_URL}
        conductor = _feed_conductor(db_recordings, lambda: _config("all_calendar"), feed)
        conductor.refresh()
        first = db_recordings.scheduled_recordings.list_all()[0]

        feed["bytes"] = ICS_EMPTY
        conductor.refresh()
        gone = db_recordings.scheduled_recordings.get(first.id)
        assert gone is not None and gone.last_outcome == "event_removed"
        assert _receipts(db_recordings, "scheduled_recording.cancelled.calendar_event_removed") == 1

        feed["bytes"] = ICS_ONE_WITH_URL
        conductor.refresh()
        enabled = db_recordings.scheduled_recordings.list_enabled()
        assert len(enabled) == 1 and enabled[0].id != first.id
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 0


class TestSourceRemovedDisarms:
    """C4: Remove/Disable cancels the source's idle event-born recordings
    with a receipt, and the prune runs even with zero enabled sources."""

    WORK = CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=True)
    HOME = CalendarSource(id="cal-home", label="HOME", url="/home.ics", enabled=True)

    def _two_source_conductor(self, db_recordings: Database):
        state = {"sources": [self.WORK, self.HOME]}
        feeds = {"/work.ics": ICS_ONE_WITH_URL, "/home.ics": ICS_SECOND_SOURCE}

        def cfg() -> Config:
            return Config(
                calendar=CalendarConfig(sources=list(state["sources"])),
                meeting=MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=5),
            )

        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db_recordings,
            source_reader=lambda sub: feeds[sub],
            config_loader=cfg,
            tick_interval=999,
        )
        return conductor, state

    def test_remove_cancels_its_recordings_with_a_receipt(self, db_recordings: Database) -> None:
        conductor, state = self._two_source_conductor(db_recordings)
        conductor.refresh()
        assert len(db_recordings.scheduled_recordings.list_enabled()) == 2

        state["sources"] = [self.WORK]  # the owner pressed Remove on HOME
        conductor.refresh()

        enabled = db_recordings.scheduled_recordings.list_enabled()
        assert [r.calendar_source_id for r in enabled] == ["cal-work"]
        home = [r for r in db_recordings.scheduled_recordings.list_all() if r.calendar_source_id == "cal-home"]
        assert len(home) == 1
        assert home[0].state == "cancelled"
        assert home[0].last_outcome == "calendar_source_removed"
        assert home[0].next_fire_at is None
        assert _receipts(db_recordings, "scheduled_recording.cancelled.calendar_source_removed") == 1
        assert {e.source_id for e in db_recordings.calendar_events.list_all()} == {"cal-work"}

    def test_disable_last_source_prunes_with_zero_enabled(self, db_recordings: Database) -> None:
        conductor, state = self._two_source_conductor(db_recordings)
        conductor.refresh()

        state["sources"] = [
            CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=False),
            CalendarSource(id="cal-home", label="HOME", url="/home.ics", enabled=False),
        ]
        assert conductor.refresh() is False, "nothing applied -- but the prune ran"

        assert db_recordings.calendar_events.list_all() == [], "the projection of a disabled source is gone"
        assert db_recordings.scheduled_recordings.list_enabled() == []
        outcomes = sorted(r.last_outcome for r in db_recordings.scheduled_recordings.list_all())
        assert outcomes == ["calendar_source_disabled", "calendar_source_disabled"]
        assert _receipts(db_recordings, "scheduled_recording.cancelled.calendar_source_disabled") == 2

        # Idempotent: the next refresh cancels nothing twice.
        conductor.refresh()
        assert _receipts(db_recordings, "scheduled_recording.cancelled.calendar_source_disabled") == 2

    def test_remove_everything_prunes_with_zero_configured(self, db_recordings: Database) -> None:
        conductor, state = self._two_source_conductor(db_recordings)
        conductor.refresh()

        state["sources"] = []
        assert conductor.refresh() is False

        assert db_recordings.calendar_events.list_all() == []
        assert db_recordings.scheduled_recordings.list_enabled() == []
        outcomes = sorted(r.last_outcome for r in db_recordings.scheduled_recordings.list_all())
        assert outcomes == ["calendar_source_removed", "calendar_source_removed"]

    def test_reenabled_source_rearms_under_the_toggle(self, db_recordings: Database) -> None:
        """A source-gone cancel is the owner's Disable of the SOURCE, not a
        cancel of the meeting: Enable brings the arm back under the toggle."""
        conductor, state = self._two_source_conductor(db_recordings)
        conductor.refresh()
        state["sources"] = [
            CalendarSource(id="cal-work", label="WORK", url="/work.ics", enabled=False),
            self.HOME,
        ]
        conductor.refresh()
        assert [r.calendar_source_id for r in db_recordings.scheduled_recordings.list_enabled()] == ["cal-home"]

        state["sources"] = [self.WORK, self.HOME]
        conductor.refresh()
        assert sorted(r.calendar_source_id for r in db_recordings.scheduled_recordings.list_enabled()) == [
            "cal-home", "cal-work",
        ]
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 0

    def test_zero_sources_ever_is_quiet(self, db_recordings: Database) -> None:
        conductor = CalendarIngestConductor(
            clock=lambda: NOW_EPOCH,
            db_factory=lambda: db_recordings,
            source_reader=lambda _sub: ICS_EMPTY,
            config_loader=lambda: Config(calendar=CalendarConfig(sources=[]), meeting=MeetingConfig()),
            tick_interval=999,
        )
        assert conductor.refresh() is False
        with db_recordings._connection() as conn:
            n = conn.execute("SELECT COUNT(*) AS n FROM kernel_receipts").fetchone()["n"]
        assert int(n) == 0


class TestMatcherRunsBeforeAutoCreate:
    """C6(b): under room_linked a new Room-titled event arms on the FIRST refresh."""

    def test_room_linked_event_arms_on_the_first_refresh(self, db_recordings: Database) -> None:
        with db_recordings._connection() as conn:
            conn.execute("INSERT INTO projects (id, name) VALUES ('p-q4', 'Q4 Platform')")
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("room_linked"), ICS_ROOM_EVENT)

        conductor.refresh()

        links = db_recordings.calendar_event_projects.list_for_project("p-q4")
        assert len(links) == 1 and links[0].match_source == "title"
        enabled = db_recordings.scheduled_recordings.list_enabled()
        assert len(enabled) == 1
        assert enabled[0].title == "Q4 Platform Standup"
        assert enabled[0].calendar_event_id == links[0].calendar_event_id


class TestOwnerCancelStamp:
    """C3: the owner's Cancel stamps ``owner_cancelled_at`` (the C2 lane's
    write, holdspeak/services/scheduled_recording_service.py); the stamp
    alone is a tombstone, whatever ``last_outcome`` later says."""

    def test_stamp_alone_blocks_the_rearm(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db_recordings.scheduled_recordings.list_all()[0]
        db_recordings.scheduled_recordings.set_state(rec.id, "cancelled", last_outcome="", enabled=False, next_fire_at=None)
        with db_recordings._connection() as conn:
            conn.execute(
                "UPDATE scheduled_recordings SET owner_cancelled_at = ? WHERE id = ?",
                (NOW_EPOCH, rec.id),
            )
        assert db_recordings.scheduled_recordings.get(rec.id).owner_cancelled_at == NOW_EPOCH

        conductor.refresh()

        assert [r.id for r in db_recordings.scheduled_recordings.list_all()] == [rec.id]
        assert db_recordings.scheduled_recordings.list_enabled() == []
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 1


# -- HS-175 counsel re-read: (1) Cancel means THIS occurrence, (2) every arm
#    receipted, (5-test) B11 -- both conductors on one temp DB.

ICS_SERIES_OF_FOUR = (
    b"BEGIN:VCALENDAR\r\n"
    b"BEGIN:VEVENT\r\n"
    b"UID:u-standup\r\n"
    b"DTSTART:20260907T150000Z\r\n"
    b"DTEND:20260907T153000Z\r\n"
    b"SUMMARY:Standup\r\n"
    b"URL:https://teams.example.com/meet/standup\r\n"
    b"RRULE:FREQ=DAILY;COUNT=4\r\n"
    b"END:VEVENT\r\n"
    b"END:VCALENDAR\r\n"
)


class TestCancelIsThisOccurrence:
    """Re-read (1): a series shares one uid; the tombstone is keyed by
    (source, uid, starts_at).  Cancel one standup -> the other three stay
    armed, only that occurrence is skipped on refresh, one skip receipt."""

    def test_cancel_one_of_four_leaves_three_armed(self, db_recordings: Database) -> None:
        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar"), ICS_SERIES_OF_FOUR)
        conductor.refresh()
        armed = sorted(db_recordings.scheduled_recordings.list_enabled(), key=lambda r: r.calendar_starts_at)
        assert len(armed) == 4
        assert {r.calendar_uid for r in armed} == {"u-standup"}
        assert [r.calendar_starts_at for r in armed] == [
            "2026-09-07T15:00:00Z", "2026-09-08T15:00:00Z",
            "2026-09-09T15:00:00Z", "2026-09-10T15:00:00Z",
        ]
        assert _receipts(db_recordings, "scheduled_recording.created.calendar_event") == 4

        tuesday = armed[1]
        _owner_cancel(db_recordings, tuesday.id)
        conductor.refresh()

        still = sorted(db_recordings.scheduled_recordings.list_enabled(), key=lambda r: r.calendar_starts_at)
        assert [r.id for r in still] == [armed[0].id, armed[2].id, armed[3].id], "siblings untouched"
        assert db_recordings.scheduled_recordings.get(tuesday.id).enabled is False
        assert len(db_recordings.scheduled_recordings.list_all()) == 4, "no new row for Tuesday"
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 1
        assert db_recordings.scheduled_recordings.list_owner_cancelled_occurrences(SOURCE_ID) == {
            ("u-standup", "2026-09-08T15:00:00Z"),
        }

        conductor.refresh()  # idempotent
        assert len(db_recordings.scheduled_recordings.list_all()) == 4
        assert _receipts(db_recordings, "scheduled_recording.skipped.owner_cancelled") == 1


class TestEveryArmReceipted:
    """Re-read (2): the create receipt carries the schedule id, so a re-arm
    after Disable -> Enable has its own receipt."""

    def test_disable_enable_writes_two_create_receipts(self, db_recordings: Database) -> None:
        state = {"enabled": True}

        def cfg() -> Config:
            return Config(
                calendar=CalendarConfig(sources=[
                    CalendarSource(id=SOURCE_ID, label="WORK", url="/test.ics", enabled=state["enabled"])
                ]),
                meeting=MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=5),
            )

        conductor = _make_conductor_recordings(db_recordings, cfg, ICS_ONE_WITH_URL)
        conductor.refresh()
        first = db_recordings.scheduled_recordings.list_enabled()[0]
        assert _receipts(db_recordings, "scheduled_recording.created.calendar_event") == 1

        state["enabled"] = False
        conductor.refresh()
        assert db_recordings.scheduled_recordings.list_enabled() == []

        state["enabled"] = True
        conductor.refresh()
        second = db_recordings.scheduled_recordings.list_enabled()[0]
        assert second.id != first.id
        assert _receipts(db_recordings, "scheduled_recording.created.calendar_event") == 2


class TestB11BothConductors:
    """B11 in the suite: the calendar conductor arms an event-born row; the
    scheduled-recording conductor's tick then arms it and starts capture
    (a stubbed capture entry) -- the hand-off the ruling names."""

    def test_event_born_row_is_armed_and_started_by_the_136_conductor(self, db_recordings: Database) -> None:
        from holdspeak.scheduled_recording_conductor import ScheduledRecordingConductor

        conductor = _make_conductor_recordings(db_recordings, lambda: _config("all_calendar", lead=5), ICS_ONE_WITH_URL)
        conductor.refresh()
        rec = db_recordings.scheduled_recordings.list_enabled()[0]
        assert rec.state == "idle" and rec.born_from == "calendar_event"

        started: list[dict] = []
        capture_started = threading.Event()

        def start_meeting(**kw: Any) -> None:
            started.append(kw)
            capture_started.set()

        clock = {"t": rec.next_fire_at + 1}
        sc = ScheduledRecordingConductor(
            clock=lambda: clock["t"],
            db_factory=lambda: db_recordings,
            start_meeting_fn=start_meeting,
            countdown_seconds=0,
        )
        try:
            sc._tick()
            # Recording state is durable before the admission receipt and
            # capture callback; only the callback proves capture was started.
            assert capture_started.wait(timeout=5), "scheduled capture did not start"
            after = db_recordings.scheduled_recordings.get(rec.id)
            assert after is not None and after.state == "recording"
            assert after.last_outcome == "recording_started"
            with db_recordings._connection() as conn:
                receipt = conn.execute(
                    "SELECT state, outcome FROM kernel_receipts WHERE receipt_id = ?",
                    (after.last_receipt_id,),
                ).fetchone()
            assert receipt is not None
            assert receipt["state"] == "succeeded" and receipt["outcome"] == "recording_started"
            assert len(started) == 1
            assert started[0]["calendar_event_id"] == rec.calendar_event_id
            assert started[0]["title"] == "Standup"
        finally:
            # _fire installs its auto-stop timer after calling start_meeting.
            # Wait for that work before stop() cancels all timers.
            fire_finished = sc._fire_lock.acquire(timeout=5)
            try:
                sc.stop()
            finally:
                if fire_finished:
                    sc._fire_lock.release()
            assert fire_finished, "scheduled fire did not finish"


# ── from test_philo15_calendar_open_settings.py: PHILO-15 04 (gap 12): a denied calendar has a way forward. ──
#
# ``POST /api/onboarding/calendar/macos/settings`` is ``calendar.open_settings``:
# the owner's press opens System Settings at Privacy & Security > Calendars. It
# is an owner-only, admitted kernel operation with one receipt (succeeded, or
# refused by name when the open fails). An agent is refused. The real hub app,
# the real kernel; only the macOS ``open`` is a double.


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_k6_agent_mcp import (  # noqa: E402,F401
    _client,
    _launch_credential,
    _reach,
    hub,
)

PATH = "/api/onboarding/calendar/macos/settings"


class _Mac:
    def __init__(self, opens: bool) -> None:
        self.opens = opens
        self.calls = 0

    def open_privacy_settings(self) -> bool:
        self.calls += 1
        return self.opens


def _service(hub: Any) -> Any:
    return hub.root.operations.target("calendar.open_settings")


def test_the_owner_opens_the_calendars_pane_with_a_receipt(hub, monkeypatch) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    resp = hub.client.post(PATH, json={})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["opened"], body["pane"]) == (True, "privacy_calendars")
    assert body["receipt"]["outcome"] == "succeeded" and body["operation_id"]
    assert mac.calls == 1


def test_a_failed_open_is_refused_by_name_with_a_receipt(hub, monkeypatch) -> None:
    monkeypatch.setattr(_service(hub), "_macos", _Mac(False))
    resp = hub.client.post(PATH, json={})
    assert resp.status_code == 409, resp.text
    body = resp.json()
    assert body.get("code") == "system_settings_not_opened" or body.get("error_code") == "system_settings_not_opened"


def test_an_agent_never_opens_it(hub, monkeypatch) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    _reach(hub, False)
    agent = _client(hub, _launch_credential().token)
    assert agent.post(PATH, json={}).status_code == 403
    assert mac.calls == 0


def test_the_descriptor_is_owner_only_http_only_and_admitted() -> None:
    from holdspeak.kernel.project import ONBOARDING_ADMITTED
    from holdspeak.onboarding_operations import CALENDAR_OPEN_SETTINGS as op

    assert op.owner_only and op.owner_press and op.admission.rule == "admitted"
    assert op.exposure == ("http:POST /api/onboarding/calendar/macos/settings",)
    assert "calendar.open_settings" in ONBOARDING_ADMITTED


def test_the_open_targets_the_calendars_privacy_pane(monkeypatch) -> None:
    from holdspeak import macos_calendar

    ran: list[list[str]] = []

    class Done:
        returncode = 0

    monkeypatch.setattr(macos_calendar.sys, "platform", "darwin")
    monkeypatch.setattr("subprocess.run", lambda argv, **_: ran.append(argv) or Done())
    assert macos_calendar.open_privacy_settings() is True
    assert ran == [["/usr/bin/open",
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars"]]
    monkeypatch.setattr(macos_calendar.sys, "platform", "linux")
    assert macos_calendar.open_privacy_settings() is False


@pytest.mark.parametrize("extra", [{"url": "x"}])
def test_the_op_takes_no_arguments(hub, monkeypatch, extra) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    assert hub.client.post(PATH, json=extra).status_code == 400
    assert mac.calls == 0


# ── from test_philo16_macos_calendar_switch.py: PHILO-16 R2: the macOS calendar reader has an off switch, and every rig sets it. ──
#
# EventKit is per macOS user, not per HOME. A fresh isolated HOME showed the
# owner's real calendar names on the first-run Calendar step ("FOUND · 5").
# `HOLDSPEAK_MACOS_CALENDAR=0` turns the reader off at its one gate
# (`macos_calendar._eventkit`); the graph-walk hub and the glass hub set it.


def test_reader_is_on_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_MACOS_CALENDAR", raising=False)
    assert macos_calendar.reader_enabled() is True
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "1")
    assert macos_calendar.reader_enabled() is True


@pytest.mark.parametrize("value", ["0", "off", "false", "no", " OFF "])
def test_off_switch_closes_every_read(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", value)
    monkeypatch.setattr(macos_calendar.sys, "platform", "darwin")
    # Even with EventKit classes already loaded in this process, nothing reads.
    monkeypatch.setattr(macos_calendar, "_classes", {"EKEventStore": object(), "NSDate": object()})
    assert macos_calendar.reader_enabled() is False
    assert macos_calendar.available() is False
    assert macos_calendar.access_state() == "unavailable"
    assert macos_calendar.list_calendars() == []


def test_graph_walk_hub_env_turns_the_reader_off(tmp_path: Path) -> None:
    from scripts import graph_walk

    env = graph_walk._isolated_hub_env(tmp_path, inherited={"HOLDSPEAK_MACOS_CALENDAR": "1"})
    assert env["HOLDSPEAK_MACOS_CALENDAR"] == "0"


def test_glass_boot_turns_the_reader_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    import holdspeak.web_server as web_server
    from tests.e2e import glass_infra

    seen: dict[str, str | None] = {}

    class _Server:
        def __init__(self, *_args, **_kwargs) -> None:
            seen["env"] = os.environ.get("HOLDSPEAK_MACOS_CALENDAR")

        def start(self) -> str:
            return "http://127.0.0.1:0"

    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "1")
    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    assert seen["env"] == "0"
