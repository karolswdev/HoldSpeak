"""MCP coverage for the Dashboard Door's closed read twin."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import door
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)


OWNER = Principal(PrincipalKind.OWNER, "door-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "door-mcp.db")
    database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    yield database
    reset_database()


@pytest.fixture(autouse=True)
def mcp_door(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject only the MCP process boundaries; Door dependencies stay real."""
    monkeypatch.setattr(door, "get_database", lambda: db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER)
    )
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")


def _call(name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _seed_door_sources(db: Database) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES ('door-mcp-meeting', ?, 'Door MCP')",
            ("2026-08-27T09:00:00",),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state)
               VALUES ('door-mcp-action', 'door-mcp-meeting', 'MCP action', 'Ada', ?, 'open', 'accepted')""",
            (date.today().isoformat(),),
        )
    RefinementThoughtService(db).create(
        OWNER,
        request_id="door-mcp-thought",
        raw_text="MCP thought",
        source={"kind": "typed"},
    )
    db.scheduled_recordings.create(
        title="MCP recording",
        cron_expr="0 9 * * *",
        enabled=True,
        next_fire_at=(datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
        duration_minutes=30,
    )


def test_door_get_is_discoverable_with_a_closed_versioned_schema() -> None:
    response = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    door_tools = [
        tool for tool in response["result"]["tools"] if tool["name"].startswith("door.")
    ]

    assert [tool["name"] for tool in door_tools] == ["door.get"]
    assert door_tools[0]["inputSchema"] == {
        "$id": "holdspeak://mcp/door.get@1",
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    resources = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "resources/list"})
    assert resources is not None
    assert all(
        "door" not in (resource.get("uri") or resource.get("uriTemplate") or "")
        for resource in [
            *resources["result"].get("resources", []),
            *resources["result"].get("resourceTemplates", []),
        ]
    )
    assert _call("door.get", {"unrecognized": True})[0] is True


def test_door_get_dispatches_the_real_door_service(db: Database) -> None:
    _seed_door_sources(db)

    is_error, projection = _call("door.get")

    assert is_error is False
    assert projection["board"]["now"][0]["target_ref"] == "action_item:door-mcp-action"
    assert projection["board"]["active"][0]["source"] == "thought"
    assert projection["upcoming"][0]["source"] == "scheduled_recording"
    # The disabled encrypted disclosure boundary is an ordinary safe-empty
    # Follow-Through overlay, not a plaintext stand-in or an aggregate failure.
    assert all(
        card["source"] != "people_commitment"
        for lane in projection["board"].values()
        for card in lane
    )
