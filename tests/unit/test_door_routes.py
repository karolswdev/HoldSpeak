"""HTTP coverage for the Dashboard Door aggregate route."""
from __future__ import annotations

from datetime import date, datetime, timezone
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


OWNER = Principal(PrincipalKind.OWNER, "door-route-owner")
FIXED_NOW = datetime.now().astimezone().replace(
    hour=12, minute=0, second=0, microsecond=0
).astimezone(timezone.utc)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "door-routes.db")
    database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    yield database
    reset_database()


def _service(db: Database) -> DoorService:
    return DoorService(
        FollowThroughService(db),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        clock=lambda: FIXED_NOW,
    )


def _client(service: DoorService, principal: Principal = OWNER) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def set_principal(request, call_next):
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_door_router(WebContext(get_state=lambda: {}, door_service=service)))
    return TestClient(app)


def _insert_action(db: Database) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES ('route-meeting', ?, 'Route meeting')",
            ("2026-08-01T09:00:00",),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state)
               VALUES ('route-action', 'route-meeting', 'Route action', 'Ada', ?, 'open', 'accepted')""",
            (date.today().isoformat(),),
        )


def _working_thought(db: Database) -> None:
    RefinementThoughtService(db).create(
        OWNER,
        request_id="route-thought",
        raw_text="Route thought",
        source={"kind": "typed"},
    )


def test_get_door_returns_one_complete_aggregate_from_real_service(db: Database) -> None:
    _insert_action(db)
    _working_thought(db)
    db.scheduled_recordings.create(
        title="Route recording",
        cron_expr="0 9 * * *",
        enabled=True,
        next_fire_at=FIXED_NOW.timestamp() + 3600,
        duration_minutes=30,
    )

    response = _client(_service(db)).get("/api/door")

    assert response.status_code == 200
    assert set(response.json()) == {"board", "upcoming", "counts"}
    assert response.json()["board"]["now"][0]["target_ref"] == "action_item:route-action"
    assert response.json()["board"]["active"][0]["source"] == "thought"
    assert response.json()["upcoming"][0]["source"] == "scheduled_recording"


def test_get_door_carries_existing_thought_authority_refusal(db: Database) -> None:
    response = _client(_service(db), principal=UNAUTHENTICATED).get("/api/door")

    assert response.status_code == 422
    assert response.json() == {"error": "thought_owner_required"}


def test_route_does_not_replace_follow_through_or_schedule_authorities(db: Database) -> None:
    _insert_action(db)
    recording = db.scheduled_recordings.create(
        title="Authority recording",
        cron_expr="0 9 * * *",
        enabled=True,
        next_fire_at=FIXED_NOW.timestamp() + 3600,
    )
    client = _client(_service(db))

    response = client.get("/api/door")

    assert response.status_code == 200
    assert [card["id"] for card in response.json()["board"]["now"]] == ["route-action"]
    assert [item["id"] for item in response.json()["upcoming"]] == [recording.id]
    assert [route.path for route in client.app.routes if route.path == "/api/door"] == ["/api/door"]
