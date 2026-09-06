"""HS-175-02 -- orphan recording provenance in the Door wire.

Verify that _scheduled_recording_item produces correct FROM provenance
when the linked calendar event has left the upcoming projection (past event).
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


def _make_recording(
    recording_id: str = "rec-1",
    title: str = "Retro",
    fire_at: float | None = None,
    calendar_event_id: str = "ev-past",
    calendar_source_id: str = "src-work",
    born_from: str = "calendar_event",
) -> Any:
    """Create a minimal ScheduledRecording-like object."""
    now = time.time()
    rec = MagicMock()
    rec.id = recording_id
    rec.title = title
    rec.next_fire_at = fire_at or (now + 3600)
    rec.calendar_event_id = calendar_event_id
    rec.calendar_uid = f"uid-{calendar_event_id}"
    rec.calendar_source_id = calendar_source_id
    rec.born_from = born_from
    rec.duration_minutes = 60
    rec.state = "idle"
    rec.enabled = True
    return rec


def _make_event(
    event_id: str = "ev-past",
    title: str = "Retro",
    source_label: str = "WORK",
    starts_at: str | None = None,
) -> Any:
    """Create a minimal CalendarEvent-like object."""
    now = datetime.now(tz=timezone.utc)
    ev = MagicMock()
    ev.id = event_id
    ev.uid = f"uid-{event_id}"
    ev.title = title
    ev.starts_at = starts_at or (now - timedelta(days=1)).isoformat()
    ev.ends_at = (now - timedelta(days=1) + timedelta(hours=1)).isoformat()
    ev.location = None
    ev.meeting_url = None
    ev.source_id = "src-work"
    ev.source_label = source_label
    return ev


class TestOrphanRecordingProvenance:
    """The FROM token on an orphan recording must carry the event title
    and source_label even when the event has left the upcoming projection."""

    def test_past_event_still_in_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When the calendar event exists in the DB but is past, the FROM
        token should carry its title and source_label."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)
        past = now - timedelta(days=1)

        with db._connection() as conn:
            # Insert a PAST calendar event
            conn.execute(
                "INSERT INTO calendar_events "
                "(id, uid, title, starts_at, ends_at, last_seen_at, "
                "subscription_revision, source_id, source_label) "
                "VALUES (?, ?, ?, ?, ?, ?, 'rev1', 'src-work', 'WORK')",
                (
                    "ev-past",
                    "uid-ev-past",
                    "Retro",
                    past.isoformat(),
                    (past + timedelta(hours=1)).isoformat(),
                    time.time(),
                ),
            )
            # Insert an armed recording linked to that past event
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-past', 'src-work', 'calendar_event')",
                ("rec-orphan", "Retro", time.time(), fire_at, "ev-past"),
            )
            conn.commit()

        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=None,
        )
        result = svc._upcoming(now)

        # The orphan recording should be in the upcoming list
        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        assert orphan["from"]["event_title"] == "Retro", (
            f"event_title wrong: {orphan['from']}"
        )
        assert orphan["from"]["source_label"] == "WORK", (
            f"source_label wrong: {orphan['from']}"
        )

    def test_event_gone_fallback_to_config_label(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the calendar event is gone from the DB entirely, fall back
        to the source label from the configured CalendarSource."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)

        with db._connection() as conn:
            # NO calendar event in the DB -- it was deleted/expired.
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-gone', 'src-work', 'calendar_event')",
                ("rec-orphan2", "Team Sync", time.time(), fire_at, "ev-gone"),
            )
            conn.commit()

        from holdspeak.config.integrations import CalendarConfig, CalendarSource
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        mock_config = MagicMock()
        mock_config.calendar = CalendarConfig(sources=[
            CalendarSource(id="src-work", label="WORK", url="/tmp/fake.ics", enabled=True),
        ])

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=lambda: mock_config,
        )
        result = svc._upcoming(now)

        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        assert orphan["from"]["source_label"] == "WORK", (
            f"source_label should fall back to config label: {orphan['from']}"
        )

    def test_no_empty_parens_when_source_label_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When source_label is empty (no config, no event), the FROM token
        should not produce empty parentheses."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)

        with db._connection() as conn:
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-gone', '', 'calendar_event')",
                ("rec-orphan3", "Retro", time.time(), fire_at, "ev-gone2"),
            )
            conn.commit()

        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=None,
        )
        result = svc._upcoming(now)

        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        # source_label should be empty string, never None
        assert orphan["from"]["source_label"] == "", (
            f"source_label should be empty: {orphan['from']}"
        )
