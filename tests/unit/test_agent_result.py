"""Betterment AG10: the Result of a turn. A launched agent's own MCP calls
(its launch credential) are kept against its launch, and the lane read
serves them as Looked at / Wrote / Prepared beside its files and branch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_conductor_k6_agent_mcp import _call, _client, _launch_credential, _result, hub  # noqa: E402,F401


def test_a_launched_agents_read_is_looked_at_on_its_launch(hub) -> None:  # noqa: F811
    from holdspeak.db import get_database
    from holdspeak.services import run_trace
    from holdspeak.services.launch_lane import _used

    made = hub.client.post("/api/notes", json={"title": "Platform sync notes", "body_markdown": "The flag moves."})
    assert made.status_code == 201, made.text
    note_id = made.json()["note"].get("note_id") or made.json()["note"]["id"]
    agent = _client(hub, _launch_credential("launch_ag10_0001").token)
    is_error, _found = _result(_call(agent, "desk.get", {"kind": "notes", "id": note_id}))
    assert not is_error
    used = _used(get_database(), "launch_ag10_0001")
    assert [row["ref"] for row in used["looked_at"]] == [f"note:{note_id}"]
    assert used["looked_at"][0]["label"] == "Platform sync notes"
    assert used["wrote"] == [] and used["prepared"] == []
    # Another launch's Result never shows it.
    assert _used(get_database(), "launch_other")["looked_at"] == []
    assert run_trace.launch_key_of("agent:launch:launch_x") == "launch:launch_x"
    assert run_trace.launch_key_of("agent:run:r1") == ""
