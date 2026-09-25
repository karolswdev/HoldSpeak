"""PHILO-7-01: the shelf-enum alignment (carried from Phase 5, BACKLOG row 1210).

Before: the MCP ``monday_brief.shelf`` schema refused an unknown state with its
own enum, BEFORE the registry, while ``brief.shelf.write`` declared that the
brief service names that refusal ("Unknown shelf state: x") and HTTP reached
the service. Two refusers for one input.

After: the service is the one refuser on both transports. The MCP schema keeps
the type (a string or null) and names the three states in words; an unknown
state reaches the registry's ``invoke`` and the service refuses it with the
same text HTTP returns.

The fence runs the REAL hub and records the ONE registry's ``invoke``. The
refused MCP branch counts as registry reach only because the recording shows
``brief.shelf.write`` was invoked for it. Red on main: the MCP refusal came
from the transport schema and the registry never saw the call.

This file imports no symbol the story adds, so it runs unchanged on a copy of
main.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo7-01-shelf"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "shelf.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield composition.installed(), client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _mcp(client: Any, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def test_an_unknown_shelf_state_is_refused_by_the_one_service_on_both_transports(hub, monkeypatch) -> None:
    root, client = hub
    assert client.post("/api/decisions", json={"title": "Shelf me"}).status_code == 201
    brief = client.post("/api/brief/generate").json()
    item = brief["sections"]["decisions"][0]["id"]

    seen: list[str] = []
    real_invoke = root.operations.invoke

    def recording_invoke(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    monkeypatch.setattr(root.operations, "invoke", recording_invoke)

    http = client.post(f"/api/brief/items/{item}/shelf", json={"state": "filed"})
    assert http.status_code == 422 and http.json()["detail"] == "Unknown shelf state: filed"
    assert seen == ["brief.shelf.write"]

    seen.clear()
    is_error, refused = _mcp(client, "monday_brief.shelf", {"item_id": item, "state": "filed"})
    assert is_error is True
    assert seen == ["brief.shelf.write"], f"the MCP refusal never reached the registry: {refused}"
    assert refused == {"error": "Unknown shelf state: filed"}

    # Nothing was written by either refusal; the lawful states still work.
    assert client.get("/api/brief/shelf").json() == {}
    assert _mcp(client, "monday_brief.shelf", {"item_id": item, "state": "deferred"}) == (False, {"item_id": item, "state": "deferred"})
    assert _mcp(client, "monday_brief.shelf", {"item_id": item, "state": None})[0] is False
    # A non-string state stays refused before the registry on both transports.
    seen.clear()
    is_error, typed = _mcp(client, "monday_brief.shelf", {"item_id": item, "state": 5})
    assert is_error is True and "Invalid arguments" in typed["error"] and seen == []
    assert client.post(f"/api/brief/items/{item}/shelf", json={"state": 5}).status_code == 422 and seen == []


def test_the_published_shelf_schema_names_the_three_states(hub) -> None:
    _root, client = hub
    tools = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).json()["result"]["tools"]
    shelf = next(t for t in tools if t["name"] == "monday_brief.shelf")
    state = shelf["inputSchema"]["properties"]["state"]
    for word in ("acknowledged", "deferred", "null"):
        assert word in state["description"]
    assert shelf["inputSchema"]["required"] == ["item_id", "state"]
