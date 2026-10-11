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


# ── the Speak window's teach loop and hotkey custody, on the real hub ──
#
# The successors of tests/e2e/test_hs170_speak_glass.py,
# test_hs176_speak_glass.py, test_hs176_loop_glass.py and
# test_hs200_voice_custody_glass.py (the test diet, 2026-10-11). Each test
# drives the real MeetingWebServer app (TestClient, no port, no browser) on an
# isolated HOME, with the durable journal and correction repositories the
# owner's desk runs (the browser rigs' own `_boot`). The face half replays what
# these tests record: web/src/desk/__tests__/speak.app.test.tsx reads
# web/src/desk/__tests__/fixtures/speak-hub/*.json. HOLDSPEAK_WIRE_WRITE=1
# rewrites those files; without it, each test fails when a stored answer is no
# longer the hub's shape (a field the face reads that the hub stopped sending,
# or a field typed by hand).

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SPEAK_FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "speak-hub"
SPEAK_TOKEN = "desk-speak"

#: The Tuesday sentence and its one wrong span (the browser rigs' own words).
HEARD = "Ship the queue for platform on schedule"
SAID = "Ship the Q4 platform on schedule"
AGAIN = "Ship the queue for platform in October"
SECRET_HEARD = "Set the token to placeholder"
SECRET_SAID = "Set the token to sk-live4f2a9c1b2d3e4f"
TARGET_LABELS = ["Claude Code", "Codex CLI", "Terminal shell", "Browser", "Editor", "Chat"]

#: Every read the Speak window makes on the way in and after a press (found by
#: replaying the face with an empty table and listing every path it asked for).
SPEAK_GETS = (
    "/api/dictation/readiness",
    "/api/dictation/blocks?scope=global",
    "/api/dictation/corrections",
    "/api/dictation/journal?limit=1",
    "/api/dictation/journal?limit=50",
    "/api/inference-targets",
    "/api/setup/local-ai",
)
#: The one read the face makes with POST (the assignment editor's projection).
SPEAK_EDITOR = ("/api/inference/assignments/editor",
                {"scope": {"kind": "capability", "capability_id": "speech.rewrite"},
                 "capability_id": "speech.rewrite"})

AX_TRUSTED, AX_NOT_TRUSTED = True, False
HID_GRANTED, HID_DENIED, HID_NEVER_ASKED = 0, 1, 2
AV_NEVER_ASKED, AV_DENIED, AV_GRANTED = 0, 2, 3

#: The five platform answers of tests/e2e/test_hs200_voice_custody_glass.py
#: (`_Platform`): (ax, hid, av, runtime status).
CUSTODY_STATES: dict[str, tuple[bool, int, int, dict[str, Any]]] = {
    "all_denied": (AX_NOT_TRUSTED, HID_DENIED, AV_DENIED,
                   {"global_hotkey_available": False,
                    "global_hotkey_error": "OSError: permission denied by the operating system"}),
    "one_denied": (AX_TRUSTED, HID_DENIED, AV_GRANTED,
                   {"global_hotkey_available": True, "global_hotkey_error": ""}),
    "never_asked": (AX_NOT_TRUSTED, HID_NEVER_ASKED, AV_NEVER_ASKED,
                    {"global_hotkey_available": False, "global_hotkey_error": ""}),
    "listener_failed": (AX_TRUSTED, HID_GRANTED, AV_GRANTED,
                        {"global_hotkey_available": False,
                         "global_hotkey_error": "RuntimeError: pynput is not available."}),
    "all_granted": (AX_TRUSTED, HID_GRANTED, AV_GRANTED,
                    {"global_hotkey_available": True, "global_hotkey_error": ""}),
}


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _same_shape(stored: Any, live: Any, at: str = "$") -> list[str]:
    """Where the stored shape is not the live one (the agents wire fence's rule:
    a null matches a leaf, never an object or a list)."""
    if stored == "null" or live == "null":
        other = live if stored == "null" else stored
        return [f"{at}: null against {type(other).__name__}"] if isinstance(other, (dict, list)) else []
    if isinstance(stored, dict) and isinstance(live, dict):
        diffs = [f"{at}.{k}: only in the stored answer" for k in stored.keys() - live.keys()]
        diffs += [f"{at}.{k}: only in the hub's answer" for k in live.keys() - stored.keys()]
        for k in stored.keys() & live.keys():
            diffs += _same_shape(stored[k], live[k], f"{at}.{k}")
        return diffs
    if isinstance(stored, list) and isinstance(live, list):
        if len(stored) != len(live):
            return [f"{at}: {len(stored)} stored rows, {len(live)} on the hub"]
        return [d for i, (a, b) in enumerate(zip(stored, live)) for d in _same_shape(a, b, f"{at}[{i}]")]
    return [] if stored == live else [f"{at}: stored {stored}, hub {live}"]


def _scrub(value: Any, tmp_path: Path) -> Any:
    text = json.dumps(value)
    for real in {str(tmp_path), str(tmp_path.resolve())}:
        text = re.sub(re.escape(real), "/tmp/rig", text, flags=re.IGNORECASE)
    text = text.replace(str(REPO), "/repo")
    text = re.sub(r"/Users/[^/\"]+", "/Users/me", text)
    return json.loads(text)


def _record(name: str, payload: dict[str, Any], tmp_path: Path, source: str,
            folder: Path = SPEAK_FIXTURES) -> None:
    """Write the recorded answers (HOLDSPEAK_WIRE_WRITE=1), else fence their shape."""
    scrubbed = _scrub(payload, tmp_path)
    path = folder / f"{name}.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "_source": f"The hub's own answers, captured by {source} "
                       "(MeetingWebServer + TestClient, isolated HOME, the browser rigs' seeds). "
                       "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit a field a test reads.",
            **scrubbed,
        }, indent=1, sort_keys=False, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = {k: v for k, v in json.loads(path.read_text()).items() if k != "_source"}
    diffs = _same_shape(_shape(stored), _shape(scrubbed))
    assert not diffs, f"{path.name}: the stored answers are not the hub's shape: {diffs[:10]}"


class _Machine:
    """The machine's permission answers: the platform seam the browser rig used."""

    def __init__(self) -> None:
        self.state = "all_granted"

    def __call__(self) -> tuple[bool, int, int, dict[str, Any]]:
        return CUSTODY_STATES[self.state]


@pytest.fixture
def speak_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The real hub app with the durable journal and correction stores and the
    correction loop on (the browser rigs' `_boot` + `_enable_corrections`)."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak import desktop_permissions as perms
    from holdspeak.db import Database, reset_database
    from holdspeak.runtime import composition
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    for key, value in {
        "HOME": str(home), "HOLDSPEAK_MACOS_CALENDAR": "0", "HOLDSPEAK_AGENT_STATE": "off",
        "HOLDSPEAK_ACTIVE_TARGET": "off", "HOLDSPEAK_DESKTOP_NOTIFY": "0",
        "HOLDSPEAK_TEST_NO_REAL_CLI": "1", "GIT_CONFIG_NOSYSTEM": "1",
        "XDG_CONFIG_HOME": str(home / ".config"),
        "HOLDSPEAK_CHANNEL_KEYSTORE_FILE": str(home / "channel-keys.json"),
        "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(home / "people.key"),
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    machine = _Machine()
    monkeypatch.setattr(perms, "_is_macos", lambda: True)
    monkeypatch.setattr(perms, "_ax_is_process_trusted", lambda: machine()[0])
    monkeypatch.setattr(perms, "_iohid_check_access", lambda: machine()[1])
    monkeypatch.setattr(perms, "_av_authorization_status", lambda: machine()[2])

    cfg = config_module.Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)

    database = Database(tmp_path / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}),
            on_get_status=lambda: dict(machine()[3]),
        ),
        auth_token=SPEAK_TOKEN,
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    server.broadcast = lambda *_a, **_k: None
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {SPEAK_TOKEN}"})
    try:
        yield SimpleNamespace(client=client, machine=machine, db=database)
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def _ok(response: Any) -> Any:
    assert response.status_code == 200, (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _speak_reads(hub: Any) -> dict[str, Any]:
    """Every read the Speak window makes, as the hub answers it now."""
    gets = {path: _ok(hub.client.get(path)) for path in SPEAK_GETS}
    path, body = SPEAK_EDITOR
    gets[f"POST {path}"] = _ok(hub.client.post(path, json=body))
    return gets


def _press(hub: Any, steps: list[dict[str, Any]], name: str, method: str, path: str,
           body: dict[str, Any] | None = None) -> Any:
    response = hub.client.request(method, path, json=body)
    answer = response.json()
    steps.append({"step": name, "call": f"{method} {path}", "body": body,
                  "status": response.status_code, "answer": answer, "reads": _speak_reads(hub)})
    return response.status_code, answer


def test_the_teach_loop_runs_on_the_real_routes(speak_hub: Any, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_hs176_speak_glass.py::test_speak_teach_wire_is_the_real_one
    replaces: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 (T1 half: a taught rule applies
      to the next utterance in the same hub session, no restart; Forget empties the store)
    replaces: tests/e2e/test_hs170_speak_glass.py::test_speak_landed_1440 (T1 half: Teach stores a correction)

    The loop through the real dry-run, correct, corrections and journal routes.
    Its answers are the fixture the face replays (speak.app.test.tsx)."""
    hub = speak_hub
    boot = _speak_reads(hub)
    # The readiness route is the target label source: six, never `auto`.
    overrides = boot["/api/dictation/readiness"]["target"]["overrides"]
    assert [o["label"] for o in overrides] == TARGET_LABELS
    assert "auto" not in [o["id"] for o in overrides]
    assert boot["/api/dictation/corrections"]["items"] == []

    steps: list[dict[str, Any]] = []
    status, first = _press(hub, steps, "land", "POST", "/api/dictation/dry-run", {"utterance": HEARD})
    assert status == 200 and first["raw_text"] == HEARD and first["corrections_applied"] == []
    assert first["journal_id"] is not None

    status, taught = _press(hub, steps, "teach", "POST", f"/api/dictation/journal/{first['journal_id']}/correct",
                            {"kind": "text", "heard": HEARD, "said": SAID})
    assert status == 200 and taught["recorded"] is True
    assert (taught["key"], taught["value"]) == ("queue for", "Q4")

    status, secret = _press(hub, steps, "land_secret", "POST", "/api/dictation/dry-run", {"utterance": SECRET_HEARD})
    assert status == 200
    status, refused = _press(hub, steps, "teach_secret", "POST",
                             f"/api/dictation/journal/{secret['journal_id']}/correct",
                             {"kind": "text", "heard": SECRET_HEARD, "said": SECRET_SAID})
    # A secret-shaped teach is refused by name and writes nothing.
    assert refused.get("recorded") is False and refused.get("reason") == "secret", (status, refused)
    assert len(_ok(hub.client.get("/api/dictation/corrections"))["items"]) == 1

    status, again = _press(hub, steps, "land_again", "POST", "/api/dictation/dry-run", {"utterance": AGAIN})
    assert again["final_text"] == "Ship the Q4 platform in October"
    assert again["corrections_applied"] == [taught["id"]]
    items = _ok(hub.client.get("/api/dictation/corrections"))["items"]
    # `N APPLIED` is a real firing count; the teaching utterance is not one.
    assert len(items) == 1 and items[0]["applied"] == 1 and items[0]["key"] == "queue for"
    # The journal holds both landed utterances of the loop, newest first; the
    # taught one is marked, the second carries the rule that fired.
    journal = _ok(hub.client.get("/api/dictation/journal?limit=50"))["items"]
    by_text = {row["transcript"]: row for row in journal}
    assert by_text[HEARD]["taught_from"] is True
    assert by_text[AGAIN]["corrections_applied"] == [taught["id"]]

    status, _ = _press(hub, steps, "forget", "DELETE", f"/api/dictation/corrections/{taught['id']}")
    assert status == 200
    assert _ok(hub.client.get("/api/dictation/corrections"))["items"] == []

    _record("loop", {"boot": boot, "steps": steps}, tmp_path, "tests/unit/test_desk_speak.py::test_the_teach_loop_runs_on_the_real_routes")


def test_the_readiness_route_carries_the_hotkey_custody(speak_hub: Any, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_hs200_voice_custody_glass.py::test_the_custody_the_face_draws_is_the_wire_the_route_serves
    replaces: tests/e2e/test_hs200_voice_custody_glass.py::test_hotkey_custody_block_1440 (T1 half: the five wires)

    The five platform states through the real readiness route; the answers are
    the fixture the face replays."""
    hub = speak_hub
    states: dict[str, Any] = {}
    for name in CUSTODY_STATES:
        hub.machine.state = name
        states[name] = _ok(hub.client.get("/api/dictation/readiness"))

    hotkey = states["all_denied"]["hotkey"]
    assert hotkey["available"] is False and hotkey["reason"] == "PERMISSION REFUSED"
    assert sorted(hotkey["missing"]) == ["accessibility", "input_monitoring", "microphone"]
    assert [p["state"] for p in hotkey["permissions"]] == ["denied"] * 3
    # The deep link is carried and deliberately unspent (the verb is Re-check).
    assert all(p["settings_url"].startswith("x-apple.systempreferences:") for p in hotkey["permissions"])
    assert states["one_denied"]["hotkey"]["missing"] == ["input_monitoring"]
    assert states["listener_failed"]["hotkey"]["missing"] == []
    assert states["listener_failed"]["hotkey"]["available"] is False
    quiet = states["all_granted"]["hotkey"]
    assert quiet["needs_attention"] is False and quiet["missing"] == [] and quiet["display"] == "⌥R"

    _record("custody", {"readiness": states}, tmp_path, "tests/unit/test_desk_speak.py::test_the_readiness_route_carries_the_hotkey_custody")
