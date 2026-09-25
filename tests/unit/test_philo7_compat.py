"""PHILO-7-01: the three-state compatibility tables (notes, zones, knowledge bases).

One table per kind, in the Phase 5 story 01 form (``test_philo5_compat.py``):
each row names an input, the transport, and the outcome BASE MAIN gave it.
Accepted stays accepted with the same stored value; refused stays refused.
The three states are recorded in ``evidence-story-01.md``: base main (green),
round one (the first build), built (green).

What changes on purpose, stated in full (and so NOT asserted as an exact text
here, only as a refusal):

* the refusal TEXT for an unknown or misplaced field in ``desk.create`` /
  ``desk.update`` data for these kinds. Base: a Python ``TypeError`` text
  ("got an unexpected keyword argument ..."); built: the contract's
  ``Invalid arguments for note.create: ...``. Same ``isError`` envelope.
* the refusal TEXT for an authority field (``owner``, ``actor`` ...) in that
  data. Base: a ``TypeError``; built: ``authority_in_arguments``. Refused in
  both (unlike decisions in Phase 5, nothing here was accepted-and-ignored).

The rename rows are fenced in ``test_philo7_rename_repair.py`` (they change on
purpose only under an interleaving; sequentially they are the same as base).

This file imports no symbol the story adds, so it runs unchanged on a copy of
main (base: green).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo7-01-compat"
CHANGED_TEXT = "refused (text changes)"

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _kernel_fields import plain  # noqa: E402  (PHILO-7-02)



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


def _seed(client: Any, kind: str) -> str:
    """One row per kind, made over HTTP (on base main the MCP zone writes fail)."""
    if kind == "notes":
        body = {"id": "seed", "title": "Before", "body_markdown": "b", "tags": ["t"]}
    elif kind == "directories":
        root = client.post("/api/directories", json={"id": "root1", "name": "Root"})
        assert root.status_code == 201, root.text
        body = {"id": "seed", "name": "Before", "parent_id": "root1"}
    else:
        body = {"id": "seed", "name": "Before", "member_ids": ["note:a"]}
    made = client.post(f"/api/{kind}", json=body)
    assert made.status_code == 201, made.text
    return "seed"


def _pick(row: Any, fields: dict[str, Any]) -> dict[str, Any]:
    source = row.get("directory", row) if isinstance(row, dict) else row
    return {key: source.get(key) for key in fields}


# ── MCP desk.create / desk.update data: (kind, tool, data, base, fields) ──

MCP_TABLE = [
    # notes
    ("notes", "desk.create", {"title": 123}, "accepted", {"title": "123"}),
    ("notes", "desk.create", {"tags": "one"}, "accepted", {"tags": []}),
    ("notes", "desk.create", {"note_id": "compat_n1", "title": "t"}, "accepted", {"id": "compat_n1", "title": "t"}),
    ("notes", "desk.create", {}, "accepted", {"title": "", "body_markdown": ""}),
    ("notes", "desk.create", {"note_id": "seed", "title": "Again"}, "accepted", {"id": "seed", "title": "Again", "tags": []}),
    ("notes", "desk.create", {"id": "x"}, CHANGED_TEXT, None),
    ("notes", "desk.create", {"title": "t", "bogus": 1}, CHANGED_TEXT, None),
    ("notes", "desk.create", {"title": "t", "owner": "x"}, CHANGED_TEXT, None),
    ("notes", "desk.update", {"title": 123}, "accepted", {"title": "123", "body_markdown": "b"}),
    ("notes", "desk.update", {}, "accepted", {"title": "Before", "tags": ["t"]}),
    ("notes", "desk.update", {"tags": None, "body_markdown": "new"}, "accepted", {"tags": ["t"], "body_markdown": "new"}),
    ("notes", "desk.update", {"expected_aggregate_revision": 3}, "accepted", {"title": "Before"}),
    ("notes", "desk.update", {"note_id": "other"}, CHANGED_TEXT, None),
    ("notes", "desk.update", {"bogus": 1}, CHANGED_TEXT, None),
    # knowledge bases
    ("kbs", "desk.create", {"name": "K"}, "accepted", {"name": "K", "member_ids": []}),
    ("kbs", "desk.create", {"name": "K", "member_ids": ["note:a"]}, "accepted", {"member_ids": ["note:a"]}),
    ("kbs", "desk.create", {"kb_id": "seed", "name": "Over"}, "accepted", {"id": "seed", "name": "Over", "member_ids": []}),
    ("kbs", "desk.create", {"name": ""}, "refused", {"error": "kb name is required", "code": "validation_error"}),
    ("kbs", "desk.create", {"name": 5}, CHANGED_TEXT, None),
    ("kbs", "desk.create", {"id": "x", "name": "K"}, CHANGED_TEXT, None),
    ("kbs", "desk.update", {"name": "K2"}, "accepted", {"name": "K2", "member_ids": ["note:a"]}),
    ("kbs", "desk.update", {}, "accepted", {"name": "Before", "member_ids": ["note:a"]}),
    ("kbs", "desk.update", {"member_ids": []}, "accepted", {"name": "Before", "member_ids": []}),
    ("kbs", "desk.update", {"member_ids": None}, "accepted", {"member_ids": ["note:a"]}),
    ("kbs", "desk.update", {"kb_id": "o"}, CHANGED_TEXT, None),
]


@pytest.mark.parametrize(("kind", "tool", "data", "base", "fields"), MCP_TABLE,
                         ids=[f"{r[0]}:{r[1]}:{json.dumps(r[2], sort_keys=True)}" for r in MCP_TABLE])
def test_mcp_inputs_keep_their_base_outcome(client, kind, tool, data, base, fields) -> None:
    seed = _seed(client, kind)
    arguments: dict[str, Any] = {"kind": kind, "data": data}
    if tool == "desk.update":
        arguments["id"] = seed
    is_error, result = _mcp(client, tool, arguments)
    if base == CHANGED_TEXT:
        assert is_error is True, result
        return
    if base == "refused":
        assert is_error is True, result
        assert {key: result.get(key) for key in fields} == fields
        return
    assert is_error is False, result
    assert _pick(result, fields) == fields
    # The same outcome is durable: read it back through the other transport.
    back = client.get(f"/api/{kind}/{result['id']}")
    assert back.status_code == 200, back.text


# ── zones over MCP: base main REFUSED every one of these (a defect) ──────
#
# On base main ``desk.create/get/update/delete kind=directories`` and their
# ``desk.verb`` aliases never reached the zone service: ``_KIND_ALIASES``
# stripped one letter ("directories" -> "directorie") and the generic getattr
# asked for ``create_directorie`` (``holdspeak/mcp/tools.py:34`` at main
# ``02a862f2``). Every call answered ``isError`` with "'PrimitiveService'
# object has no attribute 'create_directorie'" (only ``desk.list`` worked). The
# explicit descriptor rows repair it, so this table is BASE: refused (the
# defect) / BUILT: the zone service's own outcome, which the HTTP routes gave
# on base for the same input. Red on main, green on the branch, by design.

ZONE_MCP_TABLE = [
    ("desk.create", {"name": "Zone A"}, "accepted", {"name": "Zone A", "parent_id": None}),
    ("desk.create", {"name": 5}, "accepted", {"name": "5"}),
    ("desk.create", {"name": "Z", "parent_id": "root1"}, "accepted", {"parent_id": "root1"}),
    ("desk.create", {"name": "Z", "parent_id": None}, "accepted", {"parent_id": None}),
    ("desk.create", {"directory_id": "seed", "name": "Moved"}, "accepted", {"id": "seed", "name": "Moved", "parent_id": None}),
    ("desk.create", {"name": ""}, "refused", {"error": "zone name is required", "code": "validation_error"}),
    ("desk.create", {"name": "before"}, "refused", {"error": "zone_name_taken", "code": "conflict", "existing_name": "Before"}),
    ("desk.create", {"id": "x", "name": "Z"}, CHANGED_TEXT, None),
    ("desk.update", {"name": "Renamed"}, "accepted", {"name": "Renamed", "parent_id": "root1"}),
    ("desk.update", {}, "accepted", {"name": "Before", "parent_id": "root1"}),
    ("desk.update", {"parent_id": None}, "accepted", {"name": "Before", "parent_id": None}),
    ("desk.update", {"name": "Up", "parent_id": "root1"}, "accepted", {"name": "Up", "parent_id": "root1"}),
    ("desk.update", {"name": ""}, "refused", {"error": "zone name is required", "code": "validation_error"}),
    ("desk.update", {"name": "  "}, "refused", {"error": "zone name is required", "code": "validation_error"}),
    ("desk.update", {"name": "root"}, "refused", {"error": "zone_name_taken", "code": "conflict", "existing_name": "Root"}),
    ("desk.update", {"directory_id": "o"}, CHANGED_TEXT, None),
]


@pytest.mark.parametrize(("tool", "data", "base", "fields"), ZONE_MCP_TABLE,
                         ids=[f"{r[0]}:{json.dumps(r[1], sort_keys=True)}" for r in ZONE_MCP_TABLE])
def test_zone_mcp_inputs_reach_the_zone_service(client, tool, data, base, fields) -> None:
    seed = _seed(client, "directories")
    arguments: dict[str, Any] = {"kind": "directories", "data": data}
    if tool == "desk.update":
        arguments["id"] = seed
    is_error, result = _mcp(client, tool, arguments)
    assert "has no attribute" not in json.dumps(result), f"the zone call never reached the zone service: {result}"
    if base == CHANGED_TEXT:
        assert is_error is True, result
        return
    if base == "refused":
        assert is_error is True, result
        assert {key: result.get(key) for key in fields} == fields
        return
    assert is_error is False, result
    assert _pick(result, fields) == fields
    assert client.get(f"/api/directories/{result['id']}").status_code == 200


# ── MCP reads, deletes and the desk.verb aliases ────────────────────────


@pytest.mark.parametrize("kind", ["notes", "kbs"])
def test_mcp_get_list_delete_and_verbs_keep_their_envelopes(client, kind) -> None:
    _envelopes(client, kind)


def test_zone_mcp_get_delete_and_verbs_reach_the_zone_service(client) -> None:
    """Red on base main (the ``directorie`` defect above); the envelopes are the notes' and kbs'."""
    _envelopes(client, "directories")


def _envelopes(client: Any, kind: str) -> None:
    seed = _seed(client, kind)
    is_error, got = _mcp(client, "desk.get", {"kind": kind, "id": seed})
    assert is_error is False
    if kind == "directories":
        assert set(got) == {"directory", "member_ids", "members"} and got["directory"]["id"] == seed
    else:
        assert got["id"] == seed
    is_error, rows = _mcp(client, "desk.list", {"kind": kind})
    assert is_error is False and seed in [row["id"] for row in rows]
    if kind == "directories":
        assert all("member_ids" in row for row in rows)
    singular = {"notes": "note", "directories": "directory", "kbs": "kb"}[kind]
    is_error, missing = _mcp(client, "desk.get", {"kind": kind, "id": "nope"})
    assert is_error is True and missing == {"error": f"Unknown {singular}: nope", "code": "not_found", "kind": singular, "id": "nope"}
    # desk.verb desk.create / desk.update reach the same writes.
    data = {"notes": {"title": "Verb"}, "directories": {"name": "Verb zone"}, "kbs": {"name": "Verb kb"}}[kind]
    is_error, made = _mcp(client, "desk.verb", {"verb_id": "desk.create", "arguments": {"kind": kind, "data": data}})
    assert is_error is False, made
    rename = {"notes": {"title": "Verb 2"}, "directories": {"name": "Verb zone 2"}, "kbs": {"name": "Verb kb 2"}}[kind]
    is_error, changed = _mcp(client, "desk.verb", {"verb_id": "desk.update", "arguments": {"kind": kind, "id": made["id"], "data": rename}})
    assert is_error is False and _pick(changed, rename) == rename
    is_error, deleted = _mcp(client, "desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": kind, "id": made["id"]}})
    assert (is_error, plain(deleted)) == (False, {"deleted": True, "id": made["id"]})
    is_error, deleted = _mcp(client, "desk.delete", {"kind": kind, "id": seed})
    assert (is_error, plain(deleted)) == (False, {"deleted": True, "id": seed})
    is_error, again = _mcp(client, "desk.delete", {"kind": kind, "id": seed})
    assert is_error is True and again["code"] == "not_found"
    assert client.get(f"/api/{kind}/{seed}").status_code == 404
    is_error, unknown = _mcp(client, "desk.verb", {"verb_id": "desk.update", "arguments": {"kind": kind, "id": "nope", "data": rename}})
    assert is_error is True and unknown["code"] == "not_found"


def test_the_primitive_resource_reads_each_kind(client) -> None:
    for kind in ("notes", "directories", "kbs"):
        seed = _seed(client, kind)
        resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "resources/read",
                                             "params": {"uri": f"holdspeak://primitives/{kind}/{seed}"}})
        body = json.loads(resp.json()["result"]["contents"][0]["text"])
        assert (body.get("directory") or body)["id"] == seed
    missing = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "resources/read",
                                            "params": {"uri": "holdspeak://primitives/notes/nope"}}).json()
    assert missing["error"]["code"] == -32002 and missing["error"]["data"]["code"] == "not_found"


# ── HTTP: (method, path, body, status, expected) per kind ───────────────

HTTP_TABLE = [
    # notes
    ("notes", "POST", "/api/notes", {"title": 123}, 201, {"note": {"title": "123"}}),
    ("notes", "POST", "/api/notes", {"id": "h1", "tags": "x"}, 201, {"note": {"id": "h1", "tags": ["x"]}}),
    ("notes", "POST", "/api/notes", [], 400, {"error": "expected a JSON object"}),
    ("notes", "GET", "/api/notes/nope", None, 404, {"error": "Unknown note: nope"}),
    ("notes", "PUT", "/api/notes/nope", {"title": "x"}, 404, {"error": "Unknown note: nope"}),
    ("notes", "PUT", "/api/notes/seed", {"title": "x", "bogus": 1}, 200, {"note": {"title": "x", "body_markdown": "b"}}),
    ("notes", "PUT", "/api/notes/seed", [], 400, {"error": "expected a JSON object"}),
    ("notes", "DELETE", "/api/notes/nope", None, 404, {"error": "Unknown note: nope"}),
    ("notes", "DELETE", "/api/notes/seed", None, 200, {"success": True}),
    # zones
    ("directories", "POST", "/api/directories", {"name": ""}, 422, {"error": "zone name is required"}),
    ("directories", "POST", "/api/directories", {"name": "BEFORE"}, 409, {"error": "zone_name_taken", "existing_name": "Before"}),
    ("directories", "POST", "/api/directories", {"name": "Z", "parent_id": ""}, 201, {"directory": {"name": "Z", "parent_id": None}}),
    ("directories", "POST", "/api/directories", {"id": "seed", "name": "Moved"}, 201, {"directory": {"id": "seed", "parent_id": None}}),
    ("directories", "GET", "/api/directories/nope", None, 404, {"error": "Unknown directory: nope"}),
    ("directories", "PUT", "/api/directories/nope", {"name": "x"}, 404, {"error": "Unknown directory: nope"}),
    ("directories", "PUT", "/api/directories/seed", {"name": "Renamed"}, 200, {"directory": {"name": "Renamed", "parent_id": "root1"}}),
    ("directories", "PUT", "/api/directories/seed", {"parent_id": None}, 200, {"directory": {"name": "Before", "parent_id": None}}),
    ("directories", "PUT", "/api/directories/seed", {"name": "root"}, 409, {"error": "zone_name_taken", "existing_name": "Root"}),
    ("directories", "PUT", "/api/directories/seed", {"name": " "}, 422, {"error": "zone name is required"}),
    ("directories", "DELETE", "/api/directories/nope", None, 404, {"error": "Unknown directory: nope"}),
    ("directories", "DELETE", "/api/directories/seed", None, 200, {"success": True}),
    # knowledge bases
    ("kbs", "POST", "/api/kbs", {"name": ""}, 400, {"error": "kb name is required"}),
    ("kbs", "POST", "/api/kbs", {"name": "K", "member_ids": ["note:a"]}, 201, {"kb": {"name": "K", "member_ids": ["note:a"]}}),
    ("kbs", "POST", "/api/kbs", {"name": 7}, 201, {"kb": {"name": "7"}}),
    ("kbs", "POST", "/api/kbs", [], 400, {"error": "expected a JSON object"}),
    ("kbs", "GET", "/api/kbs/nope", None, 404, {"error": "Unknown kb: nope"}),
    ("kbs", "PUT", "/api/kbs/nope", {"name": "x"}, 404, {"error": "Unknown kb: nope"}),
    ("kbs", "PUT", "/api/kbs/seed", {"name": "K2"}, 200, {"kb": {"name": "K2", "member_ids": ["note:a"]}}),
    ("kbs", "PUT", "/api/kbs/seed", {"member_ids": ["note:b"]}, 200, {"kb": {"name": "Before", "member_ids": ["note:b"]}}),
    ("kbs", "DELETE", "/api/kbs/nope", None, 404, {"error": "Unknown kb: nope"}),
    ("kbs", "DELETE", "/api/kbs/seed", None, 200, {"success": True}),
]


def _subset(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and _subset(actual[k], v) for k, v in expected.items())
    return actual == expected


@pytest.mark.parametrize(("kind", "method", "path", "body", "status", "expected"), HTTP_TABLE,
                         ids=[f"{r[1]} {r[2]} {json.dumps(r[3], sort_keys=True)}" for r in HTTP_TABLE])
def test_http_inputs_keep_their_base_outcome(client, kind, method, path, body, status, expected) -> None:
    _seed(client, kind)
    kwargs: dict[str, Any] = {}
    if body is not None:
        kwargs["content"] = json.dumps(body).encode()
        kwargs["headers"] = {"Content-Type": "application/json"}
    resp = client.request(method, path, **kwargs)
    assert resp.status_code == status, resp.text
    assert _subset(resp.json(), expected), resp.json()


def test_http_reads_keep_their_shapes(client) -> None:
    _seed(client, "notes")
    _seed(client, "directories")
    _seed(client, "kbs")
    assert client.get("/api/notes?tag=t").json()["notes"][0]["id"] == "seed"
    assert client.get("/api/notes?tag=missing").json() == {"notes": []}
    assert "seed" in [n["id"] for n in client.get("/api/notes").json()["notes"]]
    zone = client.get("/api/directories/seed").json()
    assert set(zone) == {"directory", "member_ids", "members"}
    assert all("member_ids" in row for row in client.get("/api/directories").json()["directories"])
    assert client.get("/api/kbs/seed").json()["kb"]["member_ids"] == ["note:a"]
    assert [k["id"] for k in client.get("/api/kbs").json()["kbs"]] == ["seed"]


def test_a_thought_owned_note_keeps_its_revision_rules(client) -> None:
    """The Thought's note: no plain create over it; updates need the cursors."""
    assert client.post("/api/directories", json={"id": "hs-seed-inbox", "name": "Inbox"}).status_code == 201
    made = client.post("/api/thoughts", json={"request_id": "compat-1", "raw_text": "raw", "source": {"kind": "typed"}})
    assert made.status_code == 201, made.text
    thought = made.json()["thought"]
    note_id = thought["working_note"]["id"]
    over = client.post("/api/notes", json={"id": note_id, "title": "over"})
    assert over.status_code == 409 and over.json()["error"] == "thought_expected_revision_required"
    is_error, refused = _mcp(client, "desk.create", {"kind": "notes", "data": {"note_id": note_id, "title": "over"}})
    assert is_error is True and refused["code"] == "thought_expected_revision_required"
    no_cas = client.put(f"/api/notes/{note_id}", json={"title": "no CAS"})
    assert no_cas.status_code == 409 and no_cas.json()["error"] == "thought_expected_revision_required"
    is_error, no_cas = _mcp(client, "desk.update", {"kind": "notes", "id": note_id, "data": {"title": "no CAS"}})
    assert is_error is True and no_cas["code"] == "thought_expected_revision_required"
    # MCP desk.delete carries no revisions: a Thought's note is refused there.
    is_error, no_delete = _mcp(client, "desk.delete", {"kind": "notes", "id": note_id})
    assert is_error is True and no_delete["code"] == "thought_expected_revision_required"
