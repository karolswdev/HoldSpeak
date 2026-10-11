"""The hub's own answers for face tests that typed their hub bodies by hand
(the test diet, 2026-10-11; lane A's list).

Each test boots the real hub (``MeetingWebServer`` through ``TestClient``) on
an isolated HOME and database, seeds it through the product, and fences the
answers the face tests read into ``web/src/test/wire/*.wire.json``
(``HOLDSPEAK_WIRE_WRITE=1`` rewrites them). The face tests check that every
field their typed bodies carry is a field the hub sends, at the same place
and of the same JSON type (``web/src/test/wireShape.ts``): no invented field
(the SCAR LAW).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402
from tests.integration import test_desk_agents_wire as wire  # noqa: E402

pytestmark = pytest.mark.timeout(240)

WIRE_DIR = REPO / "web" / "src" / "test" / "wire"
BY = "tests/integration/test_face_wire_fences.py"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    yield seeds._boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any) -> Any:
    assert response.status_code in (200, 201), (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _fence(name: str, payload: Any, tmp_path: Path, hub: Any) -> None:
    wire._fence(name, payload, tmp_path, str(hub.client.base_url), by=BY)


def test_rhythm_reads(hub: Any, tmp_path: Path) -> None:
    """rhythm.app.test.tsx: heartbeat settings, cadence status, the Door, the Brief."""
    for name, path in (
        ("heartbeat", "/api/settings/heartbeat"),
        ("cadence-status", "/api/cadence/status"),
        ("door.fresh", "/api/door"),
    ):
        _fence(name, _ok(hub.client.get(path)), tmp_path, hub)
    _ok(hub.client.post("/api/brief/generate", json={}))
    _fence("brief-latest.generated", _ok(hub.client.get("/api/brief/latest")), tmp_path, hub)


def test_journal_reads(hub: Any, tmp_path: Path) -> None:
    """speak.app.test.tsx: the Journal envelope and a row, and the readiness overrides."""
    from holdspeak.plugins.dictation.journal import passthrough_run

    recorder = hub.server.dictation_journal
    # The live runtime gives the recorder the durable repository
    # (web_runtime._dictation_journal_repo); the bare test server gives none.
    recorder._repository = hub.db.dictation_journal
    for source, text in (("dictation", "Cut the Q4 scope to the payments path"),
                         ("hotkey", "Draft the release note for the metrics change")):
        assert recorder.record(passthrough_run(text), source=source, transcript=text) is not None
    _fence("dictation-journal", _ok(hub.client.get("/api/dictation/journal?limit=50")), tmp_path, hub)
    # The Journal reads only the readiness answer's target overrides; the rest
    # of that answer reports this machine (agent hooks, block files).
    readiness = _ok(hub.client.get("/api/dictation/readiness"))
    _fence("dictation-readiness.target", {"target": {"overrides": readiness["target"]["overrides"]}}, tmp_path, hub)


def test_first_run_reads(hub: Any, tmp_path: Path) -> None:
    """FirstRun / OneScreen: the onboarding, local AI, settings and notes answers."""
    for name, path in (
        ("setup-local-ai", "/api/setup/local-ai"),
        ("onboarding-calendar", "/api/onboarding/calendar"),
        ("onboarding-connections", "/api/onboarding/connections"),
    ):
        _fence(name, _ok(hub.client.get(path)), tmp_path, hub)
    # First run reads the owner block of /api/settings; the rest reports this
    # machine's runtime (placement, counters).
    # One calendar source, so the settings and sources answers carry a row.
    _ok(hub.client.put("/api/settings", json={"calendar": {"sources": [
        {"id": "src_work", "label": "WORK", "url": "https://cal.example.com/a.ics", "enabled": True}]}}))
    settings = _ok(hub.client.get("/api/settings"))
    _fence("settings.owner", {"owner": settings["owner"], "calendar": settings["calendar"]}, tmp_path, hub)
    _fence("calendar-sources", _ok(hub.client.get("/api/calendar/sources")), tmp_path, hub)
    note = _ok(hub.client.post("/api/notes", json={"title": "First words", "body_markdown": "Send the plan."}))
    _fence("notes-create", note, tmp_path, hub)


def test_parked_reads(hub: Any, tmp_path: Path) -> None:
    """parkedDrawer.test.tsx: the parked list and each kind's restore answer."""
    from test_philo15_desk_parked import _seed

    _seed(hub.db)
    _fence("desk-parked", _ok(hub.client.get("/api/desk/parked")), tmp_path, hub)
    _fence("restore.project", _ok(hub.client.post("/api/projects/p-old/restore", json={})), tmp_path, hub)
    _fence("restore.workbench-item",
           _ok(hub.client.post("/api/workbenches/wb-1/items/wbi-park/restore", json={})), tmp_path, hub)
    _fence("restore.meeting", _ok(hub.client.post("/api/meetings/m-park/restore", json={})), tmp_path, hub)


def test_start_here_note(hub: Any, tmp_path: Path) -> None:
    """materialDoors.test.tsx: the fresh desk's Start here note, as the hub serves it."""
    from holdspeak.db.seed import apply_seed

    apply_seed(hub.db)  # what setup_service does for a fresh desk
    note = _ok(hub.client.get("/api/notes/hs-seed-start-here"))
    _fence("note.start-here", note, tmp_path, hub)
    assert "(door:record-live)" in str(note)
