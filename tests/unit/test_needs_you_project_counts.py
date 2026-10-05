"""The per-Project number is the hub's one rule split by Project.

STATUS 2026-10-05: "the shade and palette show a per-Room count". They
grouped the Room rows alone (``roomItems``), which hold a row the owner waits
on someone else for, so a Project read ``2 OPEN`` while the hub counted 1.
The hub now answers ``projectCounts`` (its members by Project) and every face
reads it (``web/src/desk/__tests__/oneNumberFaces.test.tsx`` renders them).

One desk, minted by the real producers (``scripts/needs_you_faces_fixture.py``):
the PHILO-13 oracle week plus a Room commitment that waits on Priya.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import needs_you_faces_fixture as faces  # noqa: E402
import philo13_needs_you_fixture as fx  # noqa: E402


@pytest.fixture
def desk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import Database, reset_database

    monkeypatch.setenv("HOME", str(tmp_path))
    db_path = tmp_path / ".local" / "share" / "holdspeak" / "holdspeak.db"
    fx.seed_week(db_path, home=tmp_path)
    db = Database(db_path)
    faces._waiting_room_commitment(db)
    yield db
    db.close()
    reset_database()


def _route(db: Any) -> dict[str, Any]:
    with fx._route_client(db) as client:
        response = client.get("/api/desk/needs-you?fresh=1")
        assert response.status_code == 200, response.text
        return response.json()


def _members_by_project(answer: dict[str, Any]) -> dict[str, int]:
    rows = {str(row.get("ref") or row.get("id")): row for row in answer["items"]}
    counts: dict[str, int] = {}
    for member in answer["members"]:
        row = rows.get(str(member["ref"]))
        project_id = (row or {}).get("projectId")
        if member["kind"] == "attention" and project_id:
            counts[str(project_id)] = counts.get(str(project_id), 0) + 1
    return counts


def test_project_counts_are_the_members_by_project(desk: Any) -> None:
    answer = _route(desk)
    room = next(row["projectId"] for row in answer["roomItems"] if row["title"] == faces.WAITING_TASK)
    # The Room rows alone hold the waiting row: grouping them says 2.
    room_rows = [row for row in answer["roomItems"] if row["projectId"] == room and not row.get("muted")]
    assert len(room_rows) == 2, room_rows
    # The hub's one rule counts 1 there, and says so per Project.
    assert answer["projectCounts"] == _members_by_project(answer) == {room: 1}, answer["projectCounts"]
    # The Projects split the count: a member with no Project (a Door card,
    # a blocker, a failed meeting) is in ``count`` and in no Project.
    unprojected = len(answer["members"]) - sum(answer["projectCounts"].values())
    assert sum(answer["projectCounts"].values()) + unprojected == answer["count"]
    # A muted Project is listed apart and is never counted.
    muted = {row["projectId"] for row in answer["items"] if row.get("muted")}
    assert muted and not muted & set(answer["projectCounts"])
    # ``projects`` and ``projectCounts`` name the same Projects.
    assert sorted(answer["projectCounts"]) == answer["projects"]


def test_the_operation_and_the_route_say_the_same_per_project_number(desk: Any) -> None:
    """MCP ``desk.needs_you`` is the declared operation; it answers the same split."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    answer = _route(desk)
    operation = ProjectService(desk).needs_you(Principal(PrincipalKind.OWNER, fx.OWNER_IDENTITY))
    assert operation["projectCounts"] == answer["projectCounts"]
    assert operation["count"] == answer["count"]


def test_the_cache_never_holds_the_split(desk: Any) -> None:
    """Only the Room read is cached; the split is recomposed on every request."""
    from holdspeak.services.needs_you_membership import room_part

    assert "projectCounts" not in room_part(_route(desk))
