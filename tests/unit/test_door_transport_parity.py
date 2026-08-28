"""Reciprocal production-composition HTTP/MCP goldens for Dashboard Door."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.calendar_ingest import CalendarEventCandidate
from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import door
from holdspeak.principals import UNAUTHENTICATED, Principal, PrincipalKind
from holdspeak.services.door_service import DoorService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes.door import build_door_router


OWNER = Principal(PrincipalKind.OWNER, "door-transport-owner")


@dataclass
class Side:
    db: Database
    door_service: DoorService
    client: TestClient | None


def _side(tmp_path: Path, *, http: bool) -> Side:
    db = Database(tmp_path / ("http.db" if http else "mcp.db"))
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    service = DoorService(
        FollowThroughService(db),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        db.calendar_events,
    )
    if not http:
        return Side(db, service, None)

    app = FastAPI()

    @app.middleware("http")
    async def set_principal(request: Request, call_next: Any) -> Any:
        request.state.principal = {
            "owner": OWNER,
            "none": UNAUTHENTICATED,
        }.get(request.headers.get("x-principal"), UNAUTHENTICATED)
        return await call_next(request)

    app.include_router(build_door_router(WebContext(get_state=lambda: {}, door_service=service)))
    return Side(db, service, TestClient(app))


def _seed(side: Side) -> None:
    """Seed real stores and services, never a Door dependency fake."""
    with side.db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES ('door-parity-meeting', ?, 'Parity')",
            ("2026-08-27T09:00:00",),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state)
               VALUES ('door-parity-action', 'door-parity-meeting', 'Parity action', 'Ada', ?, 'open', 'accepted')""",
            (date.today().isoformat(),),
        )
    RefinementThoughtService(side.db).create(
        OWNER,
        request_id="door-parity-thought",
        raw_text="Parity thought",
        source={"kind": "typed"},
    )
    side.db.scheduled_recordings.create(
        title="Parity recording",
        cron_expr="0 9 * * *",
        enabled=True,
        next_fire_at=(datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        duration_minutes=30,
    )
    starts_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    side.db.calendar_events.replace_projection(
        "parity-calendar",
        [
            CalendarEventCandidate(
                id="ce_parity",
                uid="parity-calendar-event",
                title="Parity calendar event",
                starts_at=starts_at.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            )
        ],
        seen_at=starts_at.timestamp(),
    )


def _http_get(side: Side, principal: str) -> tuple[int, dict[str, Any]]:
    assert side.client is not None
    response = side.client.get("/api/door", headers={"x-principal": principal})
    return response.status_code, response.json()


def _mcp_get() -> tuple[bool, dict[str, Any]]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": "door.get",
        "method": "tools/call",
        "params": {"name": "door.get", "arguments": {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _normalize(value: Any, *, key: str = "") -> Any:
    """Replace only independently generated identifiers and temporal values."""
    if isinstance(value, list):
        return [_normalize(item, key=key) for item in value]
    if isinstance(value, dict):
        return {item_key: _normalize(item, key=item_key) for item_key, item in value.items()}
    if not isinstance(value, str):
        return value
    if key.endswith("_at"):
        return "<timestamp>"
    if value.startswith(("thought_", "note_", "sr_")):
        return "<generated-id>"
    if key in {"target_ref", "open_ref"} and ":" in value:
        kind, identifier = value.split(":", 1)
        if identifier.startswith(("thought_", "note_", "sr_")):
            return f"{kind}:<generated-id>"
    return value


def test_door_get_http_and_mcp_parity_on_fresh_production_compositions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    reset_database()
    http_side = _side(tmp_path / "http", http=True)
    mcp_side = _side(tmp_path / "mcp", http=False)
    _seed(http_side)
    _seed(mcp_side)
    # These are the two allowed transport-boundary fakes.  The family still
    # creates its own real FollowThrough/Thought/schedule/Door composition.
    monkeypatch.setattr(door, "get_database", lambda: mcp_side.db)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")

    http_status, http_projection = _http_get(http_side, "owner")
    mcp_is_error, mcp_projection = _mcp_get()

    assert http_status == 200
    assert mcp_is_error is False
    assert _normalize(http_projection) == _normalize(mcp_projection)
    # The whole golden remains compared above; these assertions make the
    # non-normalized contract facts explicit.
    assert http_projection["board"]["now"][0]["source"] == "action_item"
    assert http_projection["board"]["now"][0]["target_ref"] == "action_item:door-parity-action"
    assert http_projection["board"]["now"][0]["lawful_verbs"][0]["name"] == "follow_through.complete"
    assert http_projection["board"]["active"][0]["continuity_state"] == "idle"
    assert set(http_projection["upcoming"][0]) == {
        "id", "source", "target_ref", "title", "starts_at", "ends_at", "location", "meeting_url", "state",
    }
    assert http_projection["counts"] == mcp_projection["counts"]


def test_door_get_owner_refusal_matches_across_transports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    reset_database()
    http_side = _side(tmp_path / "http", http=True)
    mcp_side = _side(tmp_path / "mcp", http=False)
    monkeypatch.setattr(door, "get_database", lambda: mcp_side.db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=UNAUTHENTICATED)
    )
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")

    http_status, http_error = _http_get(http_side, "none")
    mcp_is_error, mcp_error = _mcp_get()

    assert http_status == 422
    assert mcp_is_error is True
    assert http_error == {"error": "thought_owner_required"}
    assert mcp_error["code"] == "thought_owner_required"
    assert "owner" in mcp_error["error"]
