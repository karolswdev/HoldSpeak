"""An unknown id is a typed ``not_found`` refusal on MCP, never a raw exception text.

Until 2026-10-05 three tools leaked raw text for a bad id: the two
``decision_record.create_from_*`` tools answered ``"'x'"`` (a bare KeyError) and
``project.open_review`` answered ``"FOREIGN KEY constraint failed"``.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server, tools
from holdspeak.mcp.families import project as project_family
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "unknown-id-owner")


@pytest.fixture(autouse=True)
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    reset_database()
    database = Database(tmp_path / "unknown-id.db")
    monkeypatch.setattr(tools, "get_database", lambda: database)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    monkeypatch.setattr(project_family, "get_database", lambda: database)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")
    yield database
    reset_database()


def _call(name: str, arguments: dict) -> tuple[bool, dict]:
    response = server.handle_message({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("decision_record.create_from_meeting", {"decision_id": "no-such-decision"}),
        ("decision_record.create_from_desk", {"decision_id": "no-such-decision"}),
        ("project.open_review", {"project_id": "no-such-project"}),
    ],
)
def test_unknown_id_is_a_typed_not_found(tool: str, arguments: dict) -> None:
    is_error, payload = _call(tool, arguments)
    assert is_error is True
    assert payload.get("code") == "not_found", payload
    assert payload.get("id") == next(iter(arguments.values())), payload
