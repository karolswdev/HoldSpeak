"""HS-175 C8/C9 -- the arrival's WEEK strip buckets LOCAL days and carries
the local week's bounds.

Counsel H4-1: ``_week_strip`` bucketed on the stored UTC date, so a Monday
20:00 meeting at -06:00 was a TUE dot and Sunday evening was already next
week. The desk's clock is the hub's local zone (injectable here as
``local_tz``); the bounds ride so the THIS WEEK section is bounded to the
same week the strip draws (C9), and the armed row carries its recording
state so the face can withhold Cancel while recording (C2).
"""
from __future__ import annotations

import time
import time as time_module
from datetime import datetime, time as time_of_day, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

MINUS_SIX = timezone(timedelta(hours=-6))


def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database

    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    return get_database()


def _seed_event(conn: Any, event_id: str, title: str, starts_at: datetime) -> None:
    starts_utc = starts_at.astimezone(timezone.utc)
    conn.execute(
        "INSERT INTO calendar_events "
        "(id, uid, title, starts_at, ends_at, meeting_url, last_seen_at, "
        "subscription_revision, source_id, source_label) "
        "VALUES (?, ?, ?, ?, ?, 'https://teams.example.com/x', ?, 'rev1', 'src-work', 'WORK')",
        (
            event_id, f"uid-{event_id}", title,
            starts_utc.isoformat(),
            (starts_utc + timedelta(hours=1)).isoformat(),
            time.time(),
        ),
    )


def _service(db: Any, now: datetime, local_tz: Any) -> Any:
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    ft = MagicMock(spec=FollowThroughService)
    ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
    ft.people_store_state.return_value = None
    rt = MagicMock(spec=RefinementThoughtService)
    rt.list_unfinished.return_value = {"items": [], "next_cursor": None}
    return DoorService(
        ft, rt, db.scheduled_recordings, db.calendar_events,
        db=db, config_loader=None, clock=lambda: now, local_tz=local_tz,
    )


class TestLocalWeekBuckets:
    """The strip at -06:00: a Monday 20:00 local meeting is a MON dot."""

    def test_monday_evening_west_of_utc_is_a_monday_dot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        # Tuesday 2026-09-08 12:00 at -06:00.
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            # Monday 20:00 local == Tuesday 02:00Z: the UTC date lies.
            _seed_event(conn, "ev-mon-late", "Late standup",
                        datetime(2026, 9, 7, 20, 0, tzinfo=MINUS_SIX))
            # Sunday 22:00 local == Monday 04:00Z next week in UTC terms;
            # it is still THIS week's Sunday on the desk.
            _seed_event(conn, "ev-sun-late", "Sunday prep",
                        datetime(2026, 9, 13, 22, 0, tzinfo=MINUS_SIX))
            # Wednesday 09:00 local: an ordinary in-week day.
            _seed_event(conn, "ev-wed", "Design review",
                        datetime(2026, 9, 9, 9, 0, tzinfo=MINUS_SIX))
            conn.commit()

        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), True,
        )
        by_dow = {d["dow"]: d["count"] for d in week["days"]}
        assert by_dow == {
            "MON": 1, "TUE": 0, "WED": 1, "THU": 0, "FRI": 0, "SAT": 0, "SUN": 1,
        }, by_dow
        assert week["total"] == 3
        assert week["days"][0]["date"] == "2026-09-07"
        assert week["days"][6]["date"] == "2026-09-13"
        # The bounds are the local week as UTC instants (ends_at exclusive).
        assert week["starts_at"] == "2026-09-07T06:00:00+00:00"
        assert week["ends_at"] == "2026-09-14T06:00:00+00:00"

    def test_sunday_evening_is_still_this_week(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Counsel H4-1: at 18:00 local on Sunday the UTC strip was already
        next week. The local strip is still on Sunday."""
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 13, 18, 0, tzinfo=MINUS_SIX)  # Sunday 18:00, 00:00Z Monday
        with db._connection() as conn:
            _seed_event(conn, "ev-sun", "Sunday prep",
                        datetime(2026, 9, 13, 20, 0, tzinfo=MINUS_SIX))
            _seed_event(conn, "ev-next-mon", "Next Monday kickoff",
                        datetime(2026, 9, 14, 9, 0, tzinfo=MINUS_SIX))
            conn.commit()
        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), True,
        )
        assert week["days"][0]["date"] == "2026-09-07"
        by_dow = {d["dow"]: d["count"] for d in week["days"]}
        assert by_dow["SUN"] == 1 and week["total"] == 1, by_dow

    def test_next_week_event_stays_out_of_the_strip_but_in_upcoming(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """C9: the door's ``upcoming`` keeps the projection (the NEXT line may
        name next week's event); the strip and its ``ends_at`` bound exclude it."""
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            _seed_event(conn, "ev-wed", "Design review",
                        datetime(2026, 9, 9, 9, 0, tzinfo=MINUS_SIX))
            _seed_event(conn, "ev-next", "Next week planning",
                        datetime(2026, 9, 15, 10, 0, tzinfo=MINUS_SIX))
            conn.commit()
        svc = _service(db, now, MINUS_SIX)
        now_utc = now.astimezone(timezone.utc)
        week = svc._week_strip(now_utc, True)
        assert week["total"] == 1
        upcoming = [i["id"] for i in svc._upcoming(now_utc)]
        assert upcoming == ["ev-wed", "ev-next"]
        end = datetime.fromisoformat(week["ends_at"])
        in_week = [
            i["id"] for i in svc._upcoming(now_utc)
            if datetime.fromisoformat(i["starts_at"].replace("Z", "+00:00")) < end
        ]
        assert in_week == ["ev-wed"]

    def test_bounds_ride_without_a_calendar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), False,
        )
        assert week["days"] == [] and week["total"] == 0
        assert week["has_calendar"] is False
        assert week["ends_at"] == "2026-09-14T06:00:00+00:00"

    def test_default_zone_is_the_hubs_local_clock(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime.now().astimezone()
        svc = _service(db, now, None)
        assert svc._local_zone() == datetime.now().astimezone().tzinfo
        monday, next_monday = svc._local_week_bounds(now.astimezone(timezone.utc))
        assert monday.weekday() == 0 and (monday.hour, monday.minute) == (0, 0)
        # The bound carries the offset in force ON that day (per instant).
        assert monday.utcoffset() == datetime.combine(monday.date(), time_of_day.min).astimezone().utcoffset()
        assert (next_monday.date() - monday.date()).days == 7


class TestDstEdge:
    """Counsel re-read condition 4 (hunt H-C): the week that crosses a DST
    edge keeps every event on its true local day and the Monday bound at the
    offset in force on Monday -- never the fixed offset of `now`."""

    @staticmethod
    def _seed_pair(db: Any, zone: Any, monday: datetime, sunday: datetime) -> None:
        with db._connection() as conn:
            _seed_event(conn, "e-mon", "Monday 00:30", monday)
            _seed_event(conn, "e-sun", "Sunday 00:30", sunday)
            conn.commit()

    def test_fall_back_week_with_zoneinfo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Denver, Sun 2026-11-01 20:00 MST (after the fall-back). Monday Oct 26
        was MDT (-6): the bound is 06:00Z, not the fixed -7's 07:00Z."""
        db = _isolate(tmp_path, monkeypatch)
        denver = ZoneInfo("America/Denver")
        now = datetime(2026, 11, 1, 20, 0, tzinfo=denver)
        self._seed_pair(
            db, denver,
            datetime(2026, 10, 26, 0, 30, tzinfo=denver),  # Monday 00:30 MDT
            datetime(2026, 11, 1, 0, 30, tzinfo=denver),   # Sunday 00:30 MDT
        )
        strip = _service(db, now, denver)._week_strip(now.astimezone(timezone.utc), True)
        assert strip["starts_at"] == "2026-10-26T06:00:00+00:00"
        assert strip["ends_at"] == "2026-11-02T07:00:00+00:00"
        assert strip["total"] == 2
        assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]
        assert [d["date"] for d in strip["days"]][::6] == ["2026-10-26", "2026-11-01"]

    def test_fall_back_week_with_the_hubs_system_zone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The production default (no injected zone) under TZ=America/Denver."""
        db = _isolate(tmp_path, monkeypatch)
        monkeypatch.setenv("TZ", "America/Denver")
        time_module.tzset()
        try:
            denver = ZoneInfo("America/Denver")
            now = datetime(2026, 11, 1, 20, 0, tzinfo=denver)
            # What production passes: a fixed-offset `now` from astimezone().
            now_fixed = now.astimezone()
            assert now_fixed.utcoffset() == timedelta(hours=-7)
            self._seed_pair(
                db, denver,
                datetime(2026, 10, 26, 0, 30, tzinfo=denver),
                datetime(2026, 11, 1, 0, 30, tzinfo=denver),
            )
            strip = _service(db, now_fixed, None)._week_strip(now_fixed.astimezone(timezone.utc), True)
            assert strip["starts_at"] == "2026-10-26T06:00:00+00:00"
            assert strip["total"] == 2
            assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]
        finally:
            monkeypatch.delenv("TZ", raising=False)
            time_module.tzset()

    def test_spring_forward_week_with_zoneinfo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Denver, Sun 2026-03-08 20:00 MDT (after the spring-forward). Monday
        Mar 2 was MST (-7): the bound is 07:00Z; Sunday's 23:30 MDT is still SUN."""
        db = _isolate(tmp_path, monkeypatch)
        denver = ZoneInfo("America/Denver")
        now = datetime(2026, 3, 8, 20, 0, tzinfo=denver)
        self._seed_pair(
            db, denver,
            datetime(2026, 3, 2, 0, 30, tzinfo=denver),   # Monday 00:30 MST
            datetime(2026, 3, 8, 23, 30, tzinfo=denver),  # Sunday 23:30 MDT (05:30Z Monday)
        )
        strip = _service(db, now, denver)._week_strip(now.astimezone(timezone.utc), True)
        assert strip["starts_at"] == "2026-03-02T07:00:00+00:00"
        assert strip["ends_at"] == "2026-03-09T06:00:00+00:00"
        assert strip["total"] == 2
        assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]


class TestArmedRowState:
    """C2: the armed row carries the recording's state."""

    def test_armed_projection_carries_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        starts = datetime(2026, 9, 8, 14, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            _seed_event(conn, "ev-standup", "Standup", starts)
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, enabled, "
                "revision, created_at, next_fire_at, state, calendar_event_id, "
                "calendar_uid, calendar_source_id, born_from) "
                "VALUES ('rec-1', 'Standup', '', 'UTC', 1, 60, 1, 1, ?, ?, 'recording', "
                "'ev-standup', 'uid-ev-standup', 'src-work', 'calendar_event')",
                (time.time(), (starts - timedelta(minutes=5)).timestamp()),
            )
            conn.commit()
        items = _service(db, now, MINUS_SIX)._upcoming(now.astimezone(timezone.utc))
        row = next(i for i in items if i["id"] == "ev-standup")
        assert row["armed"]["recording_id"] == "rec-1"
        assert row["armed"]["state"] == "recording"
        # arms_at is a UTC instant; the face formats it in the browser's zone.
        assert row["armed"]["arms_at"] == "2026-09-08T19:55:00Z"
