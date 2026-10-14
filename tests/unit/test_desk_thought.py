"""The Desk Thought action wells use the owner-only Door write seam."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.services.door_service import DoorService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.door import build_door_router


OWNER = Principal(PrincipalKind.OWNER, "desk-thought-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "desk-thought.db")
    database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    yield database
    reset_database()


def _service(db: Database) -> DoorService:
    return DoorService(
        FollowThroughService(db),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        db.calendar_events,
        db=db,
    )


def _client(service: DoorService, principal: Principal = OWNER) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def set_principal(request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_door_router(WebContext(get_state=lambda: {}, door_service=service)))
    return TestClient(app)


def test_owner_can_file_a_thought_as_an_accepted_open_task(db: Database) -> None:
    response = _client(_service(db)).post(
        "/api/door/items",
        json={
            "task": "Send the rollback note",
            "owner": "Me",
            "due": "2026-10-16",
            "source_type": "thought",
            "source_ref": "note:thought-1",
        },
    )

    assert response.status_code == 201
    item = response.json()["item"]
    assert item["task"] == "Send the rollback note"
    assert item["status"] == "open"
    assert item["source_type"] == "thought"
    assert item["source_ref"] == "note:thought-1"
    with db._connection() as conn:
        row = conn.execute(
            "SELECT task, owner, due, status, review_state, source_type, source_ref "
            "FROM action_items WHERE id = ?",
            (item["id"],),
        ).fetchone()
    assert tuple(row) == (
        "Send the rollback note", "Me", "2026-10-16", "open", "accepted", "thought", "note:thought-1",
    )
    board = _client(_service(db)).get("/api/door").json()["board"]
    card = next(card for lane in board.values() for card in lane if card["id"] == item["id"])
    assert card["open_ref"] == "note:thought-1"
    assert card["source_ref"] == "note:thought-1"
    assert card["provenance"]["source_ref"] == "note:thought-1"
    assert card["provenance"]["available"] is False


def test_thought_task_write_is_owner_only(db: Database) -> None:
    response = _client(_service(db), principal=UNAUTHENTICATED).post(
        "/api/door/items",
        json={"task": "Should not be written", "source_type": "thought", "source_ref": "note:n"},
    )

    assert response.status_code == 403
    assert response.json() == {"error": "owner_required"}
