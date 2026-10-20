"""New Project (the Door): a blank create through the REAL hub.

The hub boots over an isolated database (the shared ``_boot`` of
tests/unit/test_philo9_b1_connections.py: the real MeetingWebServer, the
real routes and services; the only seam is the gh/acli runner). The Door's
own call, ``POST /api/projects/door`` with an outcome and no sources, makes
ONE project and ZERO watches, and answers ``{"projectId": ...}`` (the field
the face reads, web/src/features/project-room/door/api.ts decodeCreateResponse).

replaces: tests/e2e/test_hs169_door_legs_glass.py::test_blank_project
  (the project and watch facts; the Door closing is
  web/src/features/project-room/door/__tests__/newProject.app.test.tsx)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

_UNIT = Path(__file__).resolve().parents[1] / "unit"
sys.path.insert(0, str(_UNIT))
from test_philo9_b1_connections import _boot  # noqa: E402
from test_philo9_steward_admission import Runner  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch, Runner(), Runner())
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _count(hub, table: str) -> int:
    with hub.db._connection() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_blank_create_makes_one_project_and_no_watches(hub) -> None:
    assert _count(hub, "projects") == 0

    made = hub.client.post("/api/projects/door", json={"outcome": "Blank project for glass test", "sources": []})

    assert made.status_code == 200, made.text
    body = made.json()
    # The exact answer the face decodes (a blank create is exempt: no kernel fields).
    assert set(body) == {"projectId", "found_links"}
    assert body["found_links"] == []
    project_id = body["projectId"]
    assert project_id
    assert _count(hub, "projects") == 1
    assert _count(hub, "connector_watches") == 0
    assert _count(hub, "project_sources") == 0
    # The outcome is the project's name, and the Room reads it.
    room = hub.client.get(f"/api/projects/{project_id}/room")
    assert room.status_code == 200, room.text
    assert room.json()["project"]["name"] == "Blank project for glass test"

