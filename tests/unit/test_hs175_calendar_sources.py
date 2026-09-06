"""HS-175-03: Unit tests for the calendar sources API route.

Tests the GET /api/calendar/sources endpoint under isolated HOME with
seeded sources and events. No real network.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    """Boot an isolated DB + Config for the sources route."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    db = get_database()
    config = config_module.Config.load()
    return db, config


class TestCalendarSourcesRoute:
    """GET /api/calendar/sources returns per-source facts."""

    def test_empty_sources(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """No configured sources -> empty list."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import (
            _source_host,
            _source_type,
        )
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="", url="/tmp/cal.ics", enabled=True)
        assert _source_type(src) == "ICS"
        assert _source_host(src) is None

    def test_https_source_host(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTPS source has a host."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_host
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(
            id="x", label="WORK",
            url="https://outlook.office365.com/api/v2.0/me/events",
            enabled=True,
        )
        assert _source_host(src) == "outlook.office365.com"

    def test_snapshot_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Snapshot source type detection."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_type
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="O365 SNAPSHOT", url="/tmp/snap.ics", enabled=True)
        assert _source_type(src) == "SNAPSHOT"

    def test_file_source_no_egress(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """File source has no egress."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import _source_host
        from holdspeak.config.integrations import CalendarSource

        src = CalendarSource(id="x", label="", url="/Users/me/cal.ics", enabled=True)
        assert _source_host(src) is None

    def test_source_stats_from_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Source stats (calendar_count, last_seen) come from calendar_events."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.config.integrations import CalendarSource, CalendarConfig

        sid = str(uuid.uuid4())
        source = CalendarSource(id=sid, label="WORK", url="/tmp/cal.ics", enabled=True)
        config.calendar = CalendarConfig(sources=[source])
        config.save()

        # Seed two events with the same source but different UIDs.
        now = time.time()
        from holdspeak.db.calendar_events import CalendarEvent
        db.calendar_events.replace_projection(
            "rev1",
            [
                _make_event("e1", "uid1", "Standup", "2026-09-08T10:00:00Z", "2026-09-08T11:00:00Z"),
                _make_event("e2", "uid2", "Review", "2026-09-09T14:00:00Z", "2026-09-09T15:00:00Z"),
            ],
            seen_at=now,
            source_id=sid,
            source_label="WORK",
        )

        # Verify via the module functions.
        with db._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(DISTINCT uid) AS cnt, MAX(last_seen_at) AS ls "
                "FROM calendar_events WHERE source_id = ?",
                (sid,),
            ).fetchone()
            assert row["cnt"] == 2
            assert row["ls"] is not None

    def test_matched_this_week(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """matched_this_week counts events with calendar_event_projects links this week."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.config.integrations import CalendarSource, CalendarConfig
        from holdspeak.web.routes.calendar_sources import _iso_week_range_local

        sid = str(uuid.uuid4())
        source = CalendarSource(id=sid, label="WORK", url="/tmp/cal.ics", enabled=True)
        config.calendar = CalendarConfig(sources=[source])
        config.meeting.auto_record = "room_linked"
        config.save()

        week_start, week_end = _iso_week_range_local()

        # Seed an event within this week.
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        # Find a time this week.
        monday = now - timedelta(days=now.weekday())
        event_time = monday.replace(hour=10, minute=0, second=0, microsecond=0)
        if event_time < now:
            event_time = now + timedelta(hours=1)
        event_iso = event_time.isoformat(timespec="seconds").replace("+00:00", "Z")
        end_iso = (event_time + timedelta(hours=1)).isoformat(timespec="seconds").replace("+00:00", "Z")

        eid = str(uuid.uuid4())
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event(eid, "uid-match", "Standup", event_iso, end_iso)],
            seen_at=time.time(),
            source_id=sid,
            source_label="WORK",
        )

        # Link this event to a project.
        pid = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name) VALUES (?, ?)",
                (pid, "Q4 Platform"),
            )
        db.calendar_event_projects.link(eid, pid, "title")

        # Count matched events this week.
        with db._connection() as conn:
            row = conn.execute(
                """SELECT COUNT(DISTINCT ce.id) AS cnt
                   FROM calendar_events ce
                   INNER JOIN calendar_event_projects cep
                       ON cep.calendar_event_id = ce.id
                   WHERE ce.starts_at >= ? AND ce.starts_at < ?""",
                (week_start, week_end),
            ).fetchone()
            assert row["cnt"] >= 1

    def test_auto_record_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """auto_record values round-trip through config."""
        db, config = _setup(tmp_path, monkeypatch)
        for value in ("off", "all_calendar", "room_linked"):
            config.meeting.auto_record = value
            config.save()
            from holdspeak.config import Config
            reloaded = Config.load()
            assert reloaded.meeting.auto_record == value

    def test_auto_record_lead_minutes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """auto_record_lead_minutes defaults to 5 and rejects zero."""
        db, config = _setup(tmp_path, monkeypatch)
        assert config.meeting.auto_record_lead_minutes == 5
        config.meeting.auto_record_lead_minutes = 0
        # __post_init__ clamps to 1.
        from holdspeak.config.meeting import MeetingConfig
        mc = MeetingConfig(auto_record_lead_minutes=0)
        assert mc.auto_record_lead_minutes == 1


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, Any]:
    """Boot isolated DB + Config."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    db = get_database()
    config = config_module.Config.load()
    return db, config


class _FakeEvent:
    """Minimal CalendarEventProjection for seeding."""
    def __init__(self, id: str, uid: str, title: str, starts_at: str, ends_at: str):
        self.id = id
        self.uid = uid
        self.title = title
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.location = None
        self.meeting_url = None


def _make_event(eid: str, uid: str, title: str, starts: str, ends: str) -> _FakeEvent:
    return _FakeEvent(eid, uid, title, starts, ends)


# ── HS-175 counsel C8 / C9(b) / C10 ───────────────────────────────


@pytest.fixture()
def denver(monkeypatch):
    """The hub at America/Denver (-06:00 in September); restored after."""
    import os
    import time as _time
    previous = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "America/Denver")
    _time.tzset()
    yield
    if previous is None:
        monkeypatch.delenv("TZ", raising=False)
    else:
        monkeypatch.setenv("TZ", previous)
    _time.tzset()


def _seed_source(config, *, label="WORK", url="/tmp/cal.ics", auto_record="off"):
    from holdspeak.config.integrations import CalendarSource, CalendarConfig
    sid = str(uuid.uuid4())
    config.calendar = CalendarConfig(sources=[CalendarSource(id=sid, label=label, url=url, enabled=True)])
    config.meeting.auto_record = auto_record
    config.save()
    return sid


class TestSourcesPayloadClocks:
    """The GET payload: EVENTS not CALENDARS, LAST READ as an instant, the
    local week for MATCHED THIS WEEK."""

    def test_event_count_names_what_it_counts(self, tmp_path, monkeypatch):
        """C9(b): COUNT(DISTINCT uid) is the VEVENT count -> ``event_count``."""
        db, config = _setup(tmp_path, monkeypatch)
        from holdspeak.web.routes.calendar_sources import read_calendar_sources
        sid = _seed_source(config)
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event("e1", "uid1", "Standup", "2026-09-08T10:00:00Z", "2026-09-08T11:00:00Z"),
             _make_event("e2", "uid2", "Review", "2026-09-09T14:00:00Z", "2026-09-09T15:00:00Z")],
            seen_at=time.time(), source_id=sid, source_label="WORK",
        )
        payload = read_calendar_sources(config, db)
        row = payload["sources"][0]
        assert row["event_count"] == 2
        assert "calendar_count" not in row
        assert row["status"] == "success"

    def test_last_read_is_an_instant_and_a_local_clock(self, tmp_path, monkeypatch, denver):
        """C8: ``last_read_at`` is ISO-UTC (the browser formats it); the
        hub-local ``last_read`` reads 17:47 for 23:47Z at -06:00."""
        db, config = _setup(tmp_path, monkeypatch)
        from datetime import datetime, timezone
        from holdspeak.web.routes.calendar_sources import read_calendar_sources
        sid = _seed_source(config)
        seen = datetime(2026, 9, 5, 23, 47, 0, tzinfo=timezone.utc).timestamp()
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event("e1", "uid1", "Standup", "2026-09-08T10:00:00Z", "2026-09-08T11:00:00Z")],
            seen_at=seen, source_id=sid, source_label="WORK",
        )
        row = read_calendar_sources(config, db)["sources"][0]
        assert row["last_read_at"] == "2026-09-05T23:47:00Z"
        assert row["last_read"] == "17:47"

    def test_matched_this_week_uses_the_local_week(self, tmp_path, monkeypatch, denver):
        """A linked event on Sunday 23:00 Denver (Monday 05:00Z) counts THIS
        week; one at Sunday 23:00 Denver LAST week does not (H4-1 inverted)."""
        from datetime import timedelta
        from holdspeak.services.project_service import local_week_bounds, utc_z
        from holdspeak.web.routes.calendar_sources import read_calendar_sources
        db, config = _setup(tmp_path, monkeypatch)
        sid = _seed_source(config, auto_record="room_linked")
        monday, next_monday = local_week_bounds()
        e_in, e_out = str(uuid.uuid4()), str(uuid.uuid4())
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event(e_in, "in", "Late Sunday", utc_z(next_monday - timedelta(hours=1)), utc_z(next_monday)),
             _make_event(e_out, "out", "Last Sunday", utc_z(monday - timedelta(hours=1)), utc_z(monday))],
            seen_at=time.time(), source_id=sid, source_label="WORK",
        )
        pid = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (pid, "Q4 Platform"))
        db.calendar_event_projects.link(e_in, pid, "title")
        db.calendar_event_projects.link(e_out, pid, "title")
        assert read_calendar_sources(config, db)["matched_this_week"] == 1

    def test_iso_week_range_local_at_denver(self, denver):
        from datetime import datetime
        from holdspeak.web.routes.calendar_sources import _iso_week_range_local
        now = datetime(2026, 9, 7, 20, 0).astimezone()  # Monday 20:00 Denver
        assert _iso_week_range_local(now) == ("2026-09-07T06:00:00Z", "2026-09-14T06:00:00Z")


class TestSnapshotEgress:
    """C10: the vision host on the face BEFORE the upload, from the same
    resolution the dispatch uses."""

    def _no_routed(self, monkeypatch):
        """Force the direct path: the routed broker is unavailable."""
        from holdspeak.services import calendar_snapshot_service as svc

        def _raise():
            raise RuntimeError("no broker in this test")
        monkeypatch.setattr(svc, "_service", _raise)

    def test_lan_vision_profile_names_its_host(self, tmp_path, monkeypatch):
        from holdspeak.services.calendar_snapshot_service import resolve_snapshot_egress
        db, config = _setup(tmp_path, monkeypatch)
        self._no_routed(monkeypatch)
        db.profiles.upsert(profile_id="prof_lan", name="LAN vision", kind="openAICompatible",
                           base_url="http://192.168.1.50:8080", model="vision", requires_key=False)
        assert resolve_snapshot_egress(db) == {"scope": "private_network", "host": "192.168.1.50"}

    def test_lan_preferred_over_cloud(self, tmp_path, monkeypatch):
        from holdspeak.services.calendar_snapshot_service import resolve_snapshot_egress
        db, config = _setup(tmp_path, monkeypatch)
        self._no_routed(monkeypatch)
        db.profiles.upsert(profile_id="prof_cloud", name="Cloud vision", kind="openAICompatible",
                           base_url="https://api.example.com/v1", model="vision", requires_key=False)
        assert resolve_snapshot_egress(db) == {"scope": "cloud", "host": "api.example.com"}
        db.profiles.upsert(profile_id="prof_lan", name="LAN vision", kind="openAICompatible",
                           base_url="http://192.168.1.50:8080", model="vision", requires_key=False)
        assert resolve_snapshot_egress(db) == {"scope": "private_network", "host": "192.168.1.50"}

    def test_no_vision_model_is_none(self, tmp_path, monkeypatch):
        from holdspeak.services.calendar_snapshot_service import resolve_snapshot_egress
        db, config = _setup(tmp_path, monkeypatch)
        self._no_routed(monkeypatch)
        assert resolve_snapshot_egress(db) is None

    def test_local_scope_carries_no_host_and_mesh_names_its_node(self):
        from holdspeak.services.calendar_snapshot_service import (
            _TARGET_BOUNDARY_SCOPE, _egress_for_scope,
        )
        assert _TARGET_BOUNDARY_SCOPE["same_device"] == "local"
        assert _egress_for_scope("local", "http://127.0.0.1:1") == {"scope": "local"}
        assert _egress_for_scope("mesh", "", "desktop") == {"scope": "mesh", "host": "desktop"}
        assert _egress_for_scope("cloud", "https://api.example.com/v1") == {"scope": "cloud", "host": "api.example.com"}

    def test_route_entries_resolution_is_the_dispatchs(self, tmp_path, monkeypatch):
        """The routed path and the face share ``_egress_from_route_entries``."""
        import inspect
        from holdspeak.services import calendar_snapshot_service as svc
        db, config = _setup(tmp_path, monkeypatch)
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO deployment_revisions
                   (id, destination_id, kind, engine, model, node, boundary, endpoint)
                   VALUES ('dep1', 'dest', 'private_endpoint', 'openai_compatible', 'vision',
                           '', 'private_network', 'http://192.168.1.43:8080/v1')""",
            )
        entries = [{"boundary": "private_network", "deployment_revision_id": "dep1"}]
        assert svc._egress_from_route_entries(entries, db) == {"scope": "private_network", "host": "192.168.1.43"}
        assert svc._egress_from_route_entries([{"boundary": "local"}], db) == {"scope": "local"}
        source = inspect.getsource(svc.extract_via_router)
        assert "_egress_from_route_entries(entries)" in source
        assert "_rank_vision_targets(db)" in source

    def test_payload_carries_snapshot_egress(self, tmp_path, monkeypatch):
        from holdspeak.web.routes.calendar_sources import read_calendar_sources
        db, config = _setup(tmp_path, monkeypatch)
        _seed_source(config)
        payload = read_calendar_sources(config, db, snapshot_egress={"scope": "private_network", "host": "192.168.1.50"})
        assert payload["snapshot_egress"] == {"scope": "private_network", "host": "192.168.1.50"}
        assert read_calendar_sources(config, db)["snapshot_egress"] is None

    def test_direct_dispatch_failure_still_names_the_egress(self, tmp_path, monkeypatch):
        """H2-1: a dispatch that fails after the revision is captured returns
        the egress it would have used (the bytes may already have left)."""
        from types import SimpleNamespace
        from holdspeak.services import calendar_snapshot_service as svc
        db, config = _setup(tmp_path, monkeypatch)
        db.profiles.upsert(profile_id="prof_lan", name="LAN vision", kind="openAICompatible",
                           base_url="http://192.168.1.50:8080", model="vision", requires_key=False)

        def _admit(*_a, **_k):
            raise RuntimeError("no assignment")

        def _invoke(*_a, **_k):
            raise RuntimeError("engine down")

        broker = SimpleNamespace(
            inference_adoption_service=SimpleNamespace(admit=_admit),
            inference_runner=SimpleNamespace(invoke=_invoke),
        )
        monkeypatch.setattr(svc, "_service", lambda: broker)
        from holdspeak.principals import Principal, PrincipalKind
        result = svc.extract_via_router(
            Principal(PrincipalKind.OWNER, "t"),
            {"system_prompt": "", "user_prompt": "", "image_base64": "", "image_media_type": "image/png"},
        )
        assert result["egress"] == {"scope": "private_network", "host": "192.168.1.50"}
        assert "no_vision_model_assigned" in result["output"]


# ── HS-175 counsel C4 (the Remove half): the snapshot's ICS goes with it ──


class TestSnapshotIcsRemoval:
    """Removing the SNAPSHOT source deletes the ICS the Snapshot verb wrote,
    receipted; a plain file source outside the snapshot dir is never touched."""

    def _receipts(self, db, kind: str) -> list[dict]:
        import json as _json
        with db._connection() as conn:
            rows = conn.execute("SELECT outcome FROM kernel_receipts").fetchall()
        return [r for r in (_json.loads(x["outcome"]) for x in rows) if r.get("kind") == kind]

    def test_generated_ics_is_deleted_and_receipted(self, tmp_path, monkeypatch):
        from holdspeak.services.calendar_snapshot_service import (
            delete_generated_ics, is_generated_ics, snapshot_dir,
        )
        db, config = _setup(tmp_path, monkeypatch)
        target = snapshot_dir() / "snap-1.ics"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
        assert is_generated_ics(str(target))

        assert delete_generated_ics(str(target), db=db) is True
        assert not target.exists()
        receipts = self._receipts(db, "calendar.source.removed")
        assert len(receipts) == 1
        assert receipts[0]["path"] == str(target.resolve())

    def test_owner_file_outside_snapshot_dir_is_never_touched(self, tmp_path, monkeypatch):
        from holdspeak.services.calendar_snapshot_service import (
            delete_generated_ics, is_generated_ics,
        )
        db, config = _setup(tmp_path, monkeypatch)
        mine = tmp_path / "work.ics"
        mine.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
        assert not is_generated_ics(str(mine))
        assert delete_generated_ics(str(mine), db=db) is False
        assert mine.exists()
        assert self._receipts(db, "calendar.source.removed") == []
        # a traversal into the directory's parent is refused too
        assert not is_generated_ics(str(tmp_path / "home" / ".local" / "share" / "holdspeak" / "config.json"))
        assert delete_generated_ics("", db=db) is False
        assert delete_generated_ics(None, db=db) is False

    def test_settings_write_removes_only_the_removed_snapshot_source(self, tmp_path, monkeypatch):
        """The route's diff: before/after source maps -> the removed snapshot
        source's file is deleted; a kept snapshot and a removed plain file
        source are untouched."""
        from holdspeak.services.calendar_snapshot_service import snapshot_dir
        from holdspeak.web.routes.system.settings import (
            remove_generated_ics_for_removed_sources,
        )
        db, config = _setup(tmp_path, monkeypatch)
        gone = snapshot_dir() / "gone.ics"
        kept = snapshot_dir() / "kept.ics"
        gone.parent.mkdir(parents=True, exist_ok=True)
        gone.write_text("x"); kept.write_text("x")
        mine = tmp_path / "work.ics"; mine.write_text("x")
        before = {"snap-gone": str(gone), "snap-kept": str(kept), "file-mine": str(mine)}
        after = {"snap-kept": str(kept)}
        removed = remove_generated_ics_for_removed_sources(before, after)
        assert removed == [str(gone)]
        assert not gone.exists() and kept.exists() and mine.exists()
        assert len(self._receipts(db, "calendar.source.removed")) == 1

    def test_route_wires_the_cleanup_after_a_successful_write(self):
        import inspect
        from holdspeak.web.routes.system import settings as route
        source = inspect.getsource(route.build_settings_router)
        assert "remove_generated_ics_for_removed_sources(before, _calendar_sources_snapshot())" in source
        assert 'result.get("success", True)' in source

    def test_full_remove_through_the_settings_service(self, tmp_path, monkeypatch):
        """End to end on the wire: register a snapshot source through the
        service, then remove it the way the face does (PUT calendar.sources
        without it) -> the file is gone and receipted."""
        from holdspeak.config.integrations import CalendarSource, CalendarConfig
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.calendar_snapshot_service import snapshot_dir
        from holdspeak.services.settings_service import SettingsService
        from holdspeak.web.routes.system.settings import (
            _calendar_sources_snapshot, remove_generated_ics_for_removed_sources,
        )
        db, config = _setup(tmp_path, monkeypatch)
        ics = snapshot_dir() / "snap-e2e.ics"
        ics.parent.mkdir(parents=True, exist_ok=True)
        ics.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
        mine = tmp_path / "work.ics"; mine.write_text("BEGIN:VCALENDAR\nEND:VCALENDAR\n")
        config.calendar = CalendarConfig(sources=[
            CalendarSource(id="snap-e2e", label="O365 SNAPSHOT", url=str(ics), enabled=True),
            CalendarSource(id="file-mine", label="WORK", url=str(mine), enabled=True),
        ])
        config.save()

        owner = Principal(PrincipalKind.OWNER, "owner")
        service = SettingsService(db) if "db" in inspect_params(SettingsService) else SettingsService()
        before = _calendar_sources_snapshot()
        result = service.update_settings(owner, {
            "calendar": {"sources": [{"id": "file-mine", "label": "WORK", "url": str(mine), "enabled": True}]},
        })
        assert result.get("success", True), result
        removed = remove_generated_ics_for_removed_sources(before, _calendar_sources_snapshot())
        assert removed == [str(ics)]
        assert not ics.exists() and mine.exists()
        assert len(self._receipts(db, "calendar.source.removed")) == 1


def inspect_params(cls) -> set[str]:
    import inspect
    return set(inspect.signature(cls.__init__).parameters)


class TestDstEdgeSources:
    """Counsel re-read condition 4: matched_this_week's week is DST-safe."""

    def test_iso_week_range_local_across_fall_back(self, denver):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from holdspeak.web.routes.calendar_sources import _iso_week_range_local
        tz = ZoneInfo("America/Denver")
        now_fixed = datetime(2026, 11, 1, 20, 0, tzinfo=tz).astimezone()
        assert _iso_week_range_local(now_fixed) == ("2026-10-26T06:00:00Z", "2026-11-02T07:00:00Z")

    def test_matched_this_week_across_fall_back(self, tmp_path, monkeypatch, denver):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from holdspeak.services.project_service import utc_z
        from holdspeak.web.routes.calendar_sources import read_calendar_sources
        db, config = _setup(tmp_path, monkeypatch)
        sid = _seed_source(config, auto_record="room_linked")
        tz = ZoneInfo("America/Denver")
        now_fixed = datetime(2026, 11, 1, 20, 0, tzinfo=tz).astimezone()
        rows = {
            "e-mon": datetime(2026, 10, 26, 0, 30, tzinfo=tz),   # in (Monday 00:30 MDT)
            "e-sun": datetime(2026, 11, 1, 0, 30, tzinfo=tz),    # in
            "e-prev": datetime(2026, 10, 25, 23, 30, tzinfo=tz), # out (Sunday before)
        }
        db.calendar_events.replace_projection(
            "rev1",
            [_make_event(eid, eid, eid, utc_z(local), utc_z(local)) for eid, local in rows.items()],
            seen_at=time.time(), source_id=sid, source_label="WORK",
        )
        pid = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (pid, "Q4"))
        for eid in rows:
            db.calendar_event_projects.link(eid, pid, "title")
        assert read_calendar_sources(config, db, now=now_fixed)["matched_this_week"] == 2

