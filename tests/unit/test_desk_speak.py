"""The Speak app: the hub half of two browser rigs the test diet moved.

- The Journal wing's live push (tests/e2e/test_hs176_journal_glass.py): the
  server's ONE recorder pushes one `dictation.journal.entry` frame per stored
  row through the server's broadcast. The frame's own shape is
  tests/unit/test_hs176_text_correction.py::test_recorder_writes_the_ids_and_pushes_one_frame;
  the socket delivery is the live-bus rig; the face (prepend, filter, dedupe)
  is web/src/pages/cores/dictation/__tests__/journal.test.tsx.
- A scheduled recording fires at the wall clock of ITS zone
  (tests/e2e/test_times_local_zone_glass.py): the route stores the instant,
  and the Door hands that instant to the Chair's NEXT line. The face half is
  web/src/desk/__tests__/chair.app.test.tsx ("the NEXT line prints a
  scheduled recording's local wall clock").
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ZONE = "America/Denver"


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
def hub_zone(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    """The hub process's own zone (the rig ran its hub in Denver)."""
    monkeypatch.setenv("TZ", request.param)
    time.tzset()
    yield request.param
    monkeypatch.undo()
    time.tzset()


# ── the Journal: the server's recorder pushes the frame ────────────────


def test_the_servers_recorder_broadcasts_each_stored_row(db: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_hs176_journal_glass.py::test_journal_pushes_without_a_reload (broadcast half)
    replaces: tests/e2e/test_hs176_journal_glass.py::test_journal_live_frame_obeys_the_active_filter (broadcast half)"""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    frames: list[tuple[str, dict[str, Any]]] = []
    # The recorder binds `self.broadcast` at construction (web_server.py, the
    # HS-176-02 block), so the stand-in goes on the class first.
    monkeypatch.setattr(MeetingWebServer, "broadcast", lambda self, kind, data: frames.append((kind, data)))
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
    )

    def record(text: str, source: str, target: str) -> Any:
        run = SimpleNamespace(
            final_text=text, stage_results=[], total_elapsed_ms=31.0, warnings=[],
            intent=None, short_circuited=True, corrections_applied=[],
        )
        stored = server.dictation_journal.record(
            run, source=source, transcript=text,
            target_profile=SimpleNamespace(id=target, details={}),
        )
        assert stored is not None, source
        return stored

    # The glass rig's order: a HOTKEY row, then a BROWSER row.
    hotkey = record("Tail the steward log on the hotkey", "hotkey", "terminal_shell")
    browser = record("Draft the release note in the browser", "browser", "claude_code")

    assert [kind for kind, _ in frames] == ["dictation.journal.entry", "dictation.journal.entry"]
    first, second = frames[0][1], frames[1][1]
    # Every frame carries its source: the wing's filter gate reads it.
    assert (first["id"], first["source"], first["transcript"]) == (
        hotkey.id, "hotkey", "Tail the steward log on the hotkey",
    )
    assert (second["id"], second["source"], second["target_profile"]) == (
        browser.id, "browser", "claude_code",
    )
    assert first["created_at"] and first["taught_from"] is False
    # The pushed row is the stored row: the wire lists the same two, newest first.
    assert [r.id for r in db.dictation_journal.recent()][:2] == [browser.id, hotkey.id]


# ── a scheduled recording fires at the wall clock of its zone ──────────


@pytest.mark.parametrize("hub_zone", [ZONE, "UTC"], indirect=True)
def test_scheduled_recording_fires_at_the_wall_clock_of_its_zone(db: Any, hub_zone: str) -> None:
    """replaces: tests/e2e/test_times_local_zone_glass.py::test_chair_next_shows_the_scheduled_local_time (hub half)"""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.scheduled_recordings import build_scheduled_recordings_router

    app = FastAPI()
    app.include_router(build_scheduled_recordings_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)

    when = (datetime.now(ZoneInfo(ZONE)) + timedelta(hours=2)).replace(second=0, microsecond=0)
    resp = client.post("/api/scheduled-recordings", json={
        "title": "Cutover dry run",
        "cron_expr": f"{when.minute} {when.hour} {when.day} {when.month} *",
        "tz": ZONE,
        "one_shot": True,
        "duration_minutes": 30,
        "enabled": True,
    })
    assert resp.status_code == 201, resp.text
    fire = datetime.fromisoformat(resp.json()["schedule"]["next_fire_at"].replace("Z", "+00:00"))
    assert fire.astimezone(ZoneInfo(ZONE)) == when, (fire, when, hub_zone)

    # The Door the Chair reads hands that instant to the NEXT line.
    ft = MagicMock(spec=FollowThroughService)
    ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
    ft.people_store_state.return_value = None
    rt = MagicMock(spec=RefinementThoughtService)
    rt.list_unfinished.return_value = {"items": [], "next_cursor": None}
    door = DoorService(ft, rt, db.scheduled_recordings, db.calendar_events, db=db).get(
        Principal(PrincipalKind.OWNER, "owner"),
    )
    rows = [i for i in door["upcoming"] if i["title"] == "Cutover dry run"]
    assert len(rows) == 1, door["upcoming"]
    assert rows[0]["source"] == "scheduled_recording"
    starts = datetime.fromisoformat(rows[0]["starts_at"].replace("Z", "+00:00"))
    assert starts == fire and starts.tzinfo is not None
    assert starts.astimezone(timezone.utc).astimezone(ZoneInfo(ZONE)).strftime("%H:%M") == when.strftime("%H:%M")
