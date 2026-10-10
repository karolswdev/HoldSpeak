"""PHILO-17 U10: Add source in the Room (the Door's rows, a project that exists).

Through the REAL ProjectDoorService over the REAL ProjectService and a real
database: the sources join the existing project as armed watches with their
Room bindings, one revision, one ``watch.created`` change per watch; no new
project is made. The hub route is the Door's own (``project_id`` in the body).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError

OWNER = Principal(PrincipalKind.OWNER, "test-philo17-u10")


@pytest.fixture()
def db(tmp_path: Path) -> Any:
    return Database(tmp_path / "u10.db")


def _door(db: Any):
    from holdspeak.services.project_door_service import ProjectDoorService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.watch_service import WatchService

    ws = WatchService(db, snapshot_fetcher=lambda principal, **kw: [])
    return ProjectDoorService(project_service=ProjectService(db), watch_service=ws)


def _bindings(db: Any, project_id: str) -> list[str]:
    with db._connection() as conn:
        return [r[0] for r in conn.execute(
            "SELECT source_ref FROM project_sources WHERE project_id=?", (project_id,)).fetchall()]


def _project_count(db: Any) -> int:
    with db._connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0])


def test_sources_join_a_project_that_exists(db: Any) -> None:
    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    assert _bindings(db, project_id) == []
    with db._connection() as conn:
        revision = int(conn.execute("SELECT revision FROM projects WHERE id=?", (project_id,)).fetchone()[0])

    out = door.create(OWNER, "", [{"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"]}],
                      project_id=project_id)

    assert out["projectId"] == project_id
    assert _project_count(db) == 1, "Add source must never make a second project"
    watches = [w for w in db.automations.list_watches() if w.get("project_id") == project_id]
    # open_prs + its open issues, and CI: the same three watches the Door arms on create.
    assert sorted(w["query_kind"] for w in watches) == ["branch_ci", "issues", "pull_requests"]
    assert all(w["next_evaluation_at"] for w in watches), "an added watch is armed for the scheduler"
    assert sorted(_bindings(db, project_id)) == sorted(f"watch:{w['id']}" for w in watches)
    with db._connection() as conn:
        new_revision = int(conn.execute("SELECT revision FROM projects WHERE id=?", (project_id,)).fetchone()[0])
        kinds = [r[0] for r in conn.execute(
            "SELECT change_kind FROM project_changes WHERE project_id=? AND project_revision=?",
            (project_id, new_revision)).fetchall()]
    assert new_revision == revision + 1
    assert kinds == ["watch.created"] * 3


def test_room_read_lists_the_added_source(db: Any) -> None:
    from holdspeak.services.project_service import ProjectService

    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    door.add_sources(OWNER, project_id, [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}])
    room = ProjectService(db).room(OWNER, project_id)
    assert room["sources"]["state"] == "ok"
    assert any(item.get("scope") == "acme/app" for item in room["sources"]["items"])


def test_a_source_already_watched_is_never_armed_twice(db: Any) -> None:
    """Astra r1 on #1068: repeated Add is refused, never hidden duplicate polling."""
    from holdspeak.services.errors import ConflictError

    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    source = [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}]
    door.add_sources(OWNER, project_id, source)
    before = sorted(w["id"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    with pytest.raises(ConflictError) as refused:
        door.add_sources(OWNER, project_id, source)
    assert refused.value.code == "already_watched"
    assert refused.value.detail == "Already watched"
    after = sorted(w["id"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    assert after == before
    # A wider pick adds only what is new (CI), never a second PR queue.
    door.add_sources(OWNER, project_id, [{"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"]}])
    kinds = sorted(w["query_kind"] for w in db.automations.list_watches() if w.get("project_id") == project_id)
    assert kinds == ["branch_ci", "issues", "pull_requests"]


def test_nothing_to_add_is_refused(db: Any) -> None:
    door = _door(db)
    project_id = door.create(OWNER, "Ship the release", [])["projectId"]
    with pytest.raises(ValidationError):
        door.add_sources(OWNER, project_id, [])
    with pytest.raises(ValidationError):
        door.create(OWNER, "", [])


def test_hub_route_adds_to_the_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/projects/door with project_id: the Door's route, the same op, the real hub."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from test_philo9_b1_connections import _boot  # noqa: E402
    from test_philo9_steward_admission import Runner  # noqa: E402

    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    hub = _boot(tmp_path, monkeypatch, Runner(), Runner())
    try:
        c = hub.client
        made = c.post("/api/projects/door", json={"outcome": "A bare Room"})
        assert made.status_code == 200, made.text
        project_id = made.json()["projectId"]
        added = c.post("/api/projects/door", json={
            "project_id": project_id,
            "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
        })
        assert added.status_code == 200, added.text
        assert added.json()["projectId"] == project_id
        room = c.get(f"/api/projects/{project_id}/room").json()
        assert any(item.get("scope") == "acme/app" for item in room["sources"]["items"]), room["sources"]
        again = c.post("/api/projects/door", json={
            "project_id": project_id,
            "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
        })
        assert again.status_code == 409, again.text
        assert again.json()["message"] == "Already watched"
        empty = c.post("/api/projects/door", json={"project_id": project_id, "sources": []})
        assert empty.status_code == 400, empty.text
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))
