"""PHILO-5-01 round two: the contract keeps what the transports did before it.

Astra's check on built (``checks/story-01-built-astra.md``) found two changes:

1. ``GET /api/decisions?limit=501`` answered 500 rows, because the route sliced
   an already-limited result. The caller's limit now passes through
   ``decision.list``; the fence creates 501 decisions over HTTP.
2. The descriptor's typed schema refused inputs the service accepted before
   (``title=123``, ``decided_at=20260924``, ``tags="one"``). The compatibility
   table below states the base outcome of each input; accepted stays accepted
   and refused stays refused. The ``name`` row is the Info-window rename bug,
   fenced as observed (backlogged, not fixed here).

One base outcome changes on purpose and is NOT in this table: an authority
field (``owner``, ``actor`` ...) in ``desk.update`` data was accepted and
ignored on base; the contract refuses it (the settled Effects position,
``test_philo5_one_decision.py``).

This file imports no symbol the contract adds, so it runs unchanged on a copy
of main (base: green) and on the round-one branch state (red).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo5-01-compat"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The REAL hub app over an isolated database."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "compat.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    test_client = TestClient(server.app, client=("127.0.0.1", 50000))
    test_client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield test_client
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


# ── finding 1: the HTTP list limit ──────────────────────────────────────


def test_http_list_limit_above_500_returns_every_row(client) -> None:
    for i in range(501):
        made = client.post("/api/decisions", json={"id": f"compat_{i}", "title": f"Decision {i}"})
        assert made.status_code == 201, made.text
    assert len(client.get("/api/decisions?limit=501").json()["decisions"]) == 501
    assert len(client.get("/api/decisions").json()["decisions"]) == 200
    assert len(client.get("/api/decisions?limit=7").json()["decisions"]) == 7
    assert len(client.get("/api/decisions?limit=0").json()["decisions"]) == 1
    # MCP desk.list takes no limit; it lists the repository default, as before.
    is_error, rows = _mcp(client, "desk.list", {"kind": "decisions"})
    assert is_error is False and len(rows) == 500


# ── finding 2: the compatibility table ──────────────────────────────────

#: (tool, data, base outcome, field, expected value). ``None`` field = refused.
COMPATIBILITY_TABLE = [
    ("desk.create", {"title": 123}, "accepted", "title", "123"),
    ("desk.create", {"decided_at": 20260924}, "accepted", "decided_at", "20260924"),
    ("desk.create", {"tags": "one"}, "accepted", "tags", []),
    ("desk.create", {"title": "t", "bogus": 1}, "refused", None, None),
    ("desk.create", {"deciders": 5}, "accepted", "deciders", []),
    ("desk.update", {"title": 123}, "accepted", "title", "123"),
    ("desk.update", {"decided_at": 20260924}, "accepted", "decided_at", "20260924"),
    ("desk.update", {"alternatives": "a"}, "accepted", "alternatives", []),
    ("desk.update", {"name": "ignored"}, "accepted", "title", "Before"),
    ("desk.update", {"decision_id": "other"}, "refused", None, None),
]


@pytest.mark.parametrize(("tool", "data", "base", "field", "value"), COMPATIBILITY_TABLE,
                         ids=[f"{row[0]}:{sorted(row[1])}:{row[2]}" for row in COMPATIBILITY_TABLE])
def test_mcp_decision_inputs_keep_their_base_outcome(client, tool, data, base, field, value) -> None:
    arguments: dict[str, Any] = {"kind": "decisions", "data": data}
    if tool == "desk.update":
        is_error, made = _mcp(client, "desk.create", {"kind": "decisions", "data": {"title": "Before"}})
        assert is_error is False, made
        arguments["id"] = made["id"]
    is_error, result = _mcp(client, tool, arguments)
    if base == "refused":
        assert is_error is True, result
        return
    assert is_error is False, result
    assert result[field] == value
