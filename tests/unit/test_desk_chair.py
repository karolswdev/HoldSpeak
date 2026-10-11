"""The Chair app, The week window: the hub half (HS-175-02, counsel C2, C5, C9).

The test diet (2026-10-11) moves the arrival glass rig
(tests/e2e/test_hs175_arrival_glass.py) to two tiers. The face half is
web/src/desk/__tests__/chair.app.test.tsx; this file is the hub half. It
seeds the SAME rows the glass rig seeded (its SQL, copied: the e2e module
imports Playwright at import time), reads the real Door projection the face
draws from, and drives the real cancel and unlink routes.

The Door's clock is pinned to a Wednesday 10:00 at -06:00, so no week edge
moves a row (the glass rig needed `pinned_desk_zone` for the same reason).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

MINUS_SIX = timezone(timedelta(hours=-6))
NOW = datetime(2026, 10, 7, 10, 0, tzinfo=MINUS_SIX)  # Wednesday
ANCHOR = NOW + timedelta(hours=1)


# ── isolation (HOME, config and the DB singleton inside tmp_path) ──────


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    yield get_database()
    reset_database()


@pytest.fixture
def ics(tmp_path: Path) -> str:
    path = tmp_path / "work.ics"
    path.write_text("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//desk-chair//EN\nEND:VCALENDAR\n")
    return str(path)


def _door(db: Any, calendar_url: str | None) -> Any:
    """The real DoorService over the real repositories; the board stubbed."""
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    ft = MagicMock(spec=FollowThroughService)
    ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
    ft.people_store_state.return_value = None
    rt = MagicMock(spec=RefinementThoughtService)
    rt.list_unfinished.return_value = {"items": [], "next_cursor": None}
    sources = (
        [SimpleNamespace(id="src-work", label="WORK", url=calendar_url, enabled=True)]
        if calendar_url else []
    )
    config = SimpleNamespace(calendar=SimpleNamespace(sources=sources))
    return DoorService(
        ft, rt, db.scheduled_recordings, db.calendar_events,
        db=db, clock=lambda: NOW, config_loader=lambda: config, local_tz=MINUS_SIX,
    )


def _projection(db: Any, calendar_url: str | None) -> dict[str, Any]:
    from holdspeak.principals import Principal, PrincipalKind

    return _door(db, calendar_url).get(Principal(PrincipalKind.OWNER, "owner"))


def _client() -> TestClient:
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.calendar_events import build_calendar_events_router
    from holdspeak.web.routes.scheduled_recordings import build_scheduled_recordings_router

    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_scheduled_recordings_router(ctx))
    app.include_router(build_calendar_events_router(ctx))
    return TestClient(app)


# ── the glass rig's seed (tests/e2e/test_hs175_arrival_glass.py) ───────


def _seed_project(conn: Any, project_id: str, name: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "target_at, created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
        "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
        (project_id, name),
    )


def _seed_calendar_event(conn: Any, event_id: str, title: str, starts: datetime, ends: datetime,
                         meeting_url: str | None = None) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO calendar_events "
        "(id, uid, title, starts_at, ends_at, location, meeting_url, "
        "last_seen_at, subscription_revision, source_id, source_label) "
        "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, 'rev1', 'src-work', 'WORK')",
        (event_id, f"uid-{event_id}", title,
         starts.astimezone(timezone.utc).isoformat(), ends.astimezone(timezone.utc).isoformat(),
         meeting_url, time.time()),
    )


def _seed_link(conn: Any, event_id: str, project_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO calendar_event_projects "
        "(calendar_event_id, project_id, match_source) VALUES (?, ?, 'title')",
        (event_id, project_id),
    )


def _seed_armed_recording(conn: Any, recording_id: str, title: str, fire_at: float,
                          calendar_event_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO scheduled_recordings "
        "(id, title, cron_expr, tz, one_shot, duration_minutes, "
        "enabled, revision, created_at, next_fire_at, state, "
        "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
        "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
        "?, ?, 'src-work', 'calendar_event')",
        (recording_id, title, time.time(), fire_at, calendar_event_id, f"uid-{calendar_event_id}"),
    )


def _seed_week_strip(db: Any) -> None:
    """Three events today (one armed, one linked to Q4 Platform)."""
    with db._connection() as conn:
        _seed_project(conn, "proj-q4", "Q4 Platform")
        _seed_calendar_event(conn, "ev-standup", "Standup", ANCHOR, ANCHOR + timedelta(minutes=30),
                             meeting_url="https://teams.example.com/standup")
        _seed_link(conn, "ev-standup", "proj-q4")
        _seed_armed_recording(conn, "rec-standup", "Standup",
                              (ANCHOR - timedelta(minutes=5)).timestamp(), "ev-standup")
        design = ANCHOR + timedelta(hours=2)
        _seed_calendar_event(conn, "ev-design", "Design review", design, design + timedelta(hours=1))
        ania = ANCHOR + timedelta(hours=4)
        _seed_calendar_event(conn, "ev-ania", "1:1 Ania", ania, ania + timedelta(minutes=30))
        conn.commit()


def _receipts(db: Any, outcome: str) -> list[Any]:
    with db._connection() as conn:
        return conn.execute(
            "SELECT receipt_id, state, result_ref FROM kernel_receipts WHERE outcome = ?",
            (outcome,),
        ).fetchall()


def _calendar_rows(door: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {i["id"]: i for i in door["upcoming"] if i["source"] == "calendar_event"}


# ── the projection the face draws ──────────────────────────────────────


def test_week_strip_projection_carries_the_face_fields(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_week_strip (hub half)"""
    _seed_week_strip(db)
    door = _projection(db, ics)

    assert door["calendar_configured"] is True
    week = door["week"]
    assert week["has_calendar"] is True and week["total"] == 3
    assert [d["dow"] for d in week["days"]] == ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    assert {d["dow"]: d["count"] for d in week["days"]}["WED"] == 3
    assert week["days"][2]["date"] == "2026-10-07"
    assert week["ends_at"] == "2026-10-12T06:00:00+00:00"

    rows = _calendar_rows(door)
    assert set(rows) == {"ev-standup", "ev-design", "ev-ania"}
    standup = rows["ev-standup"]
    assert standup["project_name"] == "Q4 Platform" and standup["source_label"] == "WORK"
    assert standup["armed_schedule_id"] == "rec-standup"
    assert standup["armed"] == {
        "recording_id": "rec-standup",
        "arms_at": (ANCHOR - timedelta(minutes=5)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "state": "idle",
    }
    assert "armed" not in rows["ev-design"] and "project_name" not in rows["ev-design"]
    # No orphan: the armed recording's event is on the rail.
    assert [i for i in door["upcoming"] if i["source"] == "scheduled_recording"] == []


def test_orphan_recording_rides_with_its_provenance(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_orphan (hub half)"""
    with db._connection() as conn:
        _seed_calendar_event(conn, "ev-standup2", "Standup", ANCHOR, ANCHOR + timedelta(minutes=30))
        design = ANCHOR + timedelta(hours=2)
        _seed_calendar_event(conn, "ev-design2", "Design review", design, design + timedelta(hours=1))
        past = datetime(2026, 10, 4, 10, 0, tzinfo=MINUS_SIX)  # the Sunday before
        _seed_calendar_event(conn, "ev-retro-past", "Retro", past, past + timedelta(hours=1))
        _seed_armed_recording(conn, "rec-retro-orphan", "Retro",
                              (NOW + timedelta(hours=3)).timestamp(), "ev-retro-past")
        conn.commit()
    door = _projection(db, ics)

    assert door["week"]["total"] == 2
    assert set(_calendar_rows(door)) == {"ev-standup2", "ev-design2"}
    orphans = [i for i in door["upcoming"] if i["source"] == "scheduled_recording"]
    assert len(orphans) == 1
    assert orphans[0]["id"] == "rec-retro-orphan"
    assert orphans[0]["from"] == {"event_title": "Retro", "source_label": "WORK"}


def test_past_event_counts_in_the_strip_not_in_upcoming(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_past_future_mix (hub half)"""
    with db._connection() as conn:
        past = NOW - timedelta(hours=1)
        _seed_calendar_event(conn, "ev-past-today", "Morning standup", past, past + timedelta(minutes=30))
        _seed_calendar_event(conn, "ev-future1", "Design review", ANCHOR, ANCHOR + timedelta(hours=1))
        later = ANCHOR + timedelta(hours=3)
        _seed_calendar_event(conn, "ev-future2", "Retro", later, later + timedelta(hours=1))
        conn.commit()
    door = _projection(db, ics)

    assert door["week"]["total"] == 3
    assert set(_calendar_rows(door)) == {"ev-future1", "ev-future2"}


def test_no_calendar_projects_no_strip(db: Any) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_no_calendar (hub half)"""
    door = _projection(db, None)
    assert door["calendar_configured"] is False
    assert door["week"]["has_calendar"] is False
    assert door["week"]["days"] == [] and door["week"]["total"] == 0


def test_next_week_event_rides_upcoming_but_not_the_strip(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_this_week_bound (hub half)"""
    _seed_week_strip(db)
    with db._connection() as conn:
        starts = datetime(2026, 10, 12, 10, 0, tzinfo=MINUS_SIX)
        _seed_calendar_event(conn, "ev-next-week", "Next week planning", starts, starts + timedelta(hours=1))
        conn.commit()
    door = _projection(db, ics)

    assert "ev-next-week" in _calendar_rows(door)
    assert door["week"]["total"] == 3
    ends = datetime.fromisoformat(door["week"]["ends_at"])
    starts_at = datetime.fromisoformat(_calendar_rows(door)["ev-next-week"]["starts_at"])
    assert starts_at >= ends, "the face bounds THIS WEEK by week.ends_at"


# ── the row verbs, through the real routes ─────────────────────────────


def test_cancel_over_the_route_disables_and_receipts(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_cancel_idle_event_born (hub half)"""
    _seed_week_strip(db)
    client = _client()

    resp = client.post("/api/scheduled-recordings/rec-standup/cancel")
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True

    schedule = client.get("/api/scheduled-recordings/rec-standup").json()["schedule"]
    assert schedule["enabled"] is False, schedule
    assert schedule["state"] == "cancelled", schedule
    assert schedule["last_outcome"] == "owner_cancelled", schedule
    assert schedule["next_fire_at"] is None, schedule
    receipts = _receipts(db, "scheduled_recording.cancelled.owner")
    assert len(receipts) == 1, receipts
    assert receipts[0]["state"] == "succeeded"
    assert "ev-standup" in receipts[0]["result_ref"]

    # The Door the face refetches: the row stays, without ARMS.
    rows = _calendar_rows(_projection(db, ics))
    assert set(rows) == {"ev-standup", "ev-design", "ev-ania"}
    assert "armed" not in rows["ev-standup"]


def test_cancel_while_recording_is_refused_by_name(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_cancel_refused_names_reason (hub half)"""
    _seed_week_strip(db)
    with db._connection() as conn:
        conn.execute("UPDATE scheduled_recordings SET state='recording' WHERE id='rec-standup'")
        conn.commit()
    client = _client()

    resp = client.post("/api/scheduled-recordings/rec-standup/cancel")
    assert resp.status_code == 409, resp.text
    body = resp.json()
    assert body["code"] == "already_recording", body
    assert body["error"] == "Already recording; stop the meeting instead", body

    schedule = client.get("/api/scheduled-recordings/rec-standup").json()["schedule"]
    assert schedule["state"] == "recording" and schedule["enabled"] is True, schedule
    assert _receipts(db, "scheduled_recording.cancelled.owner") == []
    # The Door the face refetches says RECORDING, so Cancel is withheld.
    assert _calendar_rows(_projection(db, ics))["ev-standup"]["armed"]["state"] == "recording"


def test_unlink_over_the_route_drops_the_room_and_keeps_the_arm(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_unlink_room (hub half)"""
    _seed_week_strip(db)
    resp = _client().delete("/api/calendar/events/ev-standup/link")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"unlinked": 1, "event_id": "ev-standup", "durable": True}

    with db._connection() as conn:
        links = conn.execute(
            "SELECT COUNT(*) FROM calendar_event_projects WHERE calendar_event_id='ev-standup'"
        ).fetchone()[0]
        receipts = conn.execute(
            "SELECT args_summary FROM pipeline_events "
            "WHERE service='CalendarEventLink' AND method='unlink'"
        ).fetchall()
    assert links == 0
    assert len(receipts) == 1 and json.loads(receipts[0]["args_summary"])["event_id"] == "ev-standup"

    standup = _calendar_rows(_projection(db, ics))["ev-standup"]
    assert "project_name" not in standup
    assert standup["armed"]["recording_id"] == "rec-standup"
