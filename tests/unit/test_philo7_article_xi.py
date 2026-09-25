"""PHILO-7-02: membership and decisions under Article XI, fenced through the REAL hub.

Every fence boots the real ``MeetingWebServer`` over an isolated database and
reaches it by its real transports: HTTP routes, MCP over ``/api/mcp`` (the
owner's loopback path) and a DESK credential issued through the real settings
route, used from a non-loopback host (Phase 5's boundary-fence form). Only
public transports and the database are read, so each behavioural fence runs
unchanged on a ``git archive`` copy of main, where the red is the zero: zero
kernel operations, zero receipts, an agent's write landing with no receipt,
a 404 for the grant route.

* **Admission** -- every ADMITTED row of the admission table is ONE operation
  with ONE terminal receipt per logical operation, on HTTP and MCP (supersede's
  two rows are one; a KB rename + members is one); the hidden filing effects
  are fenced BY THEIR EFFECT; the EXEMPT rows make none.
* **The owner path** -- approved inline by the same principal, in the call.
* **The agent path (R1)** -- without a grant, revoked, expired, granted to
  another identity, or outside the stored set: refused at admission with a
  receipt naming the rule, the membership unchanged, nothing waiting; with a
  LIVE grant: executed at once with a receipt naming the delegation.
* **The grant** -- ``delegation.grant``/``revoke`` by the owner: one operation
  and one receipt each; by an agent: ``owner_principal_required`` with a
  receipt; unauthenticated: 401, no receipt; malformed: ``invalid_arguments``.
* **Refusal receipts (R2)** -- one fence per class, both transports where the
  class reaches both, and the protocol boundary (no receipt).
* **Readback** -- the write's result carries its operation and receipt; the
  HTTP kernel read and the MCP ``kernel.receipt`` answer the same receipt.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

REMOTE_HOST = "192.0.2.123"  # TEST-NET-1: never loopback
AGENT_ID = "remote-desk-agent"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    # The credential store is the process's one module singleton: start clean.
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


# ── helpers over the real transports and the database ───────────────────


def _ops(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.authority_basis,"
            " o.delegator_kind, o.delegator_identity, r.outcome AS outcome, r.state AS receipt_state"
            " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid"
        )]


class Count:
    """The operations and receipts one step made."""

    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.start = len(_ops(hub))

    def new(self) -> list[dict[str, Any]]:
        return _ops(self.hub)[self.start:]


def _one(count: Count, name: str, outcome: str = "succeeded") -> dict[str, Any]:
    made = count.new()
    assert [(o["name"], o["outcome"]) for o in made] == [(name, outcome)], made
    assert made[0]["receipt_state"] is not None, "an operation without its receipt"
    return made[0]


def _none(count: Count) -> None:
    assert count.new() == [], "an exempt or protocol-refused call made a kernel operation"


def _waiting(hub: Hub) -> int:
    with hub.db._connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE state='awaiting_decision'").fetchone()[0]


def _rpc(client: Any, name: str, arguments: Any) -> dict[str, Any]:
    resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                         "params": {"name": name, "arguments": arguments}})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _tool(client: Any, name: str, arguments: Any) -> tuple[bool, Any]:
    body = _rpc(client, name, arguments)
    return body["result"]["isError"], json.loads(body["result"]["content"][0]["text"])


def _agent(hub: Hub, palette: str = "DESK", identity: str = AGENT_ID) -> Any:
    """A DESK credential issued through the REAL settings route, used from a remote host."""
    from starlette.testclient import TestClient

    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": identity, "palette": palette})
    assert issued.status_code == 200, issued.text
    client = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
    return client


def _seed(hub: Hub) -> dict[str, str]:
    c = hub.client
    return {
        "note": c.post("/api/notes", json={"title": "n"}).json()["note"]["id"],
        "note2": c.post("/api/notes", json={"title": "n2"}).json()["note"]["id"],
        "zone": c.post("/api/directories", json={"name": "Zone"}).json()["directory"]["id"],
        "zone2": c.post("/api/directories", json={"name": "Zone two"}).json()["directory"]["id"],
        "kb": c.post("/api/kbs", json={"name": "Knowledge"}).json()["kb"]["id"],
    }


def _decision(hub: Hub, title: str = "D") -> str:
    return hub.client.post("/api/decisions", json={"title": title}).json()["decision"]["id"]


def _filed(hub: Hub, zone: str) -> list[str]:
    return [m.primitive_id for m in hub.db.directory_memberships.list_for_directory(zone)]


def _kb_members(hub: Hub, kb: str) -> list[str]:
    return sorted(m.resource_ref for m in hub.db.knowledge_memberships.list_for_knowledge(kb))


def _thought_note(hub: Hub, request_id: str) -> dict[str, Any]:
    made = hub.client.post("/api/thoughts", json={"request_id": request_id, "raw_text": "raw", "source": {"kind": "typed"}})
    assert made.status_code == 201, made.text
    return made.json()["thought"]


# ── ADMISSION: one operation, one receipt, per admitted logical operation ──


# One fence per path (Astra's check on built, MISSED 3: a multi-path fence
# that fails on its first call proves red for one path only). Each path: its
# own setup, ONE call, then exactly one operation + one receipt of that name.


ADMISSION_PATHS: dict[str, tuple[str, Any]] = {
    # HTTP, decisions
    "http decision.create": ("decision.create", lambda hub, ids: hub.client.post("/api/decisions", json={"title": "D"})),
    "http decision.update": ("decision.update", lambda hub, ids: hub.client.put(f"/api/decisions/{ids['decision']}", json={"title": "D2"})),
    "http decision.status": ("decision.status", lambda hub, ids: hub.client.put(f"/api/decisions/{ids['decision']}/status", json={"status": "accepted"})),
    "http decision.supersede": ("decision.supersede", lambda hub, ids: hub.client.post(f"/api/decisions/{ids['decision']}/supersede")),
    "http decision.delete": ("decision.delete", lambda hub, ids: hub.client.delete(f"/api/decisions/{ids['decision']}")),
    # MCP, decisions (every alias once)
    "mcp desk.create decisions": ("decision.create", lambda hub, ids: hub.mcp("desk.create", {"kind": "decisions", "data": {"title": "D"}})),
    "mcp desk.update decisions": ("decision.update", lambda hub, ids: hub.mcp("desk.update", {"kind": "decisions", "id": ids["decision"], "data": {"status": "proposed"}})),
    "mcp desk.verb desk.update decisions": ("decision.update", lambda hub, ids: hub.mcp("desk.verb", {"verb_id": "desk.update", "arguments": {"kind": "decisions", "id": ids["decision"], "data": {"title": "T"}}})),
    "mcp desk.verb desk.create decisions": ("decision.create", lambda hub, ids: hub.mcp("desk.verb", {"verb_id": "desk.create", "arguments": {"kind": "decisions", "data": {"title": "Verb"}}})),
    "mcp decision.supersede": ("decision.supersede", lambda hub, ids: hub.mcp("decision.supersede", {"decision_id": ids["decision"]})),
    "mcp desk.delete decisions": ("decision.delete", lambda hub, ids: hub.mcp("desk.delete", {"kind": "decisions", "id": ids["decision"]})),
    "mcp desk.verb desk.delete decisions": ("decision.delete", lambda hub, ids: hub.mcp("desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": "decisions", "id": ids["decision"]}})),
    # filing and membership, both transports
    "http zone.file": ("zone.file", lambda hub, ids: hub.client.put(f"/api/directories/{ids['zone']}/members/note:{ids['note']}")),
    "http zone.unfile": ("zone.unfile", lambda hub, ids: hub.client.delete(f"/api/directories/{ids['zone']}/members/note:{ids['filed']}")),
    "http kb.member.add": ("kb.member.add", lambda hub, ids: hub.client.put(f"/api/kbs/{ids['kb']}/members/note:{ids['note']}")),
    "http kb.member.remove": ("kb.member.remove", lambda hub, ids: hub.client.delete(f"/api/kbs/{ids['kb']}/members/note:{ids['member']}")),
    "mcp zone.file": ("zone.file", lambda hub, ids: hub.mcp("zone.file", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})),
    "mcp zone.unfile": ("zone.unfile", lambda hub, ids: hub.mcp("zone.unfile", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['filed']}"})),
    "mcp kb.add_member": ("kb.member.add", lambda hub, ids: hub.mcp("kb.add_member", {"kb_id": ids["kb"], "ref": f"note:{ids['note']}"})),
    "mcp kb.remove_member": ("kb.member.remove", lambda hub, ids: hub.mcp("kb.remove_member", {"kb_id": ids["kb"], "ref": f"note:{ids['member']}"})),
    # the conditional rows, with their admission argument (a KB rename + members is ONE)
    "http kb.create with member_ids": ("kb.create", lambda hub, ids: hub.client.post("/api/kbs", json={"name": "K2", "member_ids": [f"note:{ids['note']}"]})),
    "mcp desk.create kbs with member_ids": ("kb.create", lambda hub, ids: hub.mcp("desk.create", {"kind": "kbs", "data": {"name": "K3", "member_ids": [f"note:{ids['note']}"]}})),
    "http kb.update rename plus members": ("kb.update", lambda hub, ids: hub.client.put(f"/api/kbs/{ids['kb']}", json={"name": "Renamed", "member_ids": [f"note:{ids['note']}"]})),
    "mcp desk.update directories parent_id": ("zone.update", lambda hub, ids: hub.mcp("desk.update", {"kind": "directories", "id": ids["zone2"], "data": {"parent_id": ids["zone"]}})),
    "http zone.update parent_id null": ("zone.update", lambda hub, ids: hub.client.put(f"/api/directories/{ids['zone2']}", json={"parent_id": None})),
    "mcp desk.create directories over an id": ("zone.create", lambda hub, ids: hub.mcp("desk.create", {"kind": "directories", "data": {"directory_id": ids["zone2"], "name": "Zone two", "parent_id": ids["zone"]}})),
}


@pytest.mark.parametrize("path", sorted(ADMISSION_PATHS))
def test_each_admitted_path_makes_one_operation_and_one_receipt(hub: Hub, path: str) -> None:
    ids = _seed(hub)
    ids["decision"] = _decision(hub)
    ids["filed"] = ids["note2"]
    hub.client.put(f"/api/directories/{ids['zone']}/members/note:{ids['filed']}")
    ids["member"] = ids["note2"]
    hub.client.put(f"/api/kbs/{ids['kb']}/members/note:{ids['member']}")
    name, call = ADMISSION_PATHS[path]
    count = Count(hub)
    result = call(hub, ids)
    if isinstance(result, tuple):
        assert result[0] is False, result
    else:
        assert result.status_code in {200, 201}, result.text
    made = _one(count, name)
    assert (made["principal_kind"], made["principal_identity"]) == ("owner", "owner-session")
    assert _waiting(hub) == 0
    if path == "http kb.update rename plus members":
        assert hub.db.kbs.get(ids["kb"]).name == "Renamed" and _kb_members(hub, ids["kb"]) == [f"note:{ids['note']}"]
    if path.endswith("supersede"):
        assert any(d["title"].startswith("Superseding") for d in hub.client.get("/api/decisions").json()["decisions"])


def test_the_exempt_rows_make_no_operation(hub: Hub) -> None:
    ids = _seed(hub)
    count = Count(hub)
    note = hub.client.post("/api/notes", json={"title": "plain"}).json()["note"]
    hub.client.put(f"/api/notes/{note['id']}", json={"body_markdown": "edit"})
    hub.mcp("desk.update", {"kind": "notes", "id": note["id"], "data": {"title": "again"}})
    hub.client.put(f"/api/directories/{ids['zone']}", json={"name": "Zone renamed"})
    hub.mcp("desk.update", {"kind": "kbs", "id": ids["kb"], "data": {"name": "K renamed"}})
    hub.client.post("/api/directories", json={"name": "New zone", "parent_id": ids["zone"]})
    hub.mcp("desk.create", {"kind": "kbs", "data": {"name": "Plain kb"}})
    hub.client.post("/api/kbs", json={"name": "Plain kb 2"})
    thought = _thought_note(hub, "exempt-save")
    saved = hub.client.patch(f"/api/thoughts/{thought['id']}/working", json={
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"], "body_markdown": "saved"})
    assert saved.status_code == 200, saved.text
    assert hub.client.delete(f"/api/notes/{note['id']}").status_code == 200  # a plain note delete
    assert hub.client.delete(f"/api/kbs/{ids['kb']}").status_code == 200
    hub.client.get(f"/api/directories/{ids['zone']}/members")
    hub.mcp("kb.list_members", {"kb_id": ids["kb"]})
    _none(count)


# ── the hidden filing effects, fenced BY THEIR EFFECT ────────────────────


def test_a_zone_delete_that_unfiles_is_admitted(hub: Hub) -> None:
    ids = _seed(hub)
    hub.client.put(f"/api/directories/{ids['zone']}/members/note:{ids['note']}")
    count = Count(hub)
    assert hub.client.delete(f"/api/directories/{ids['zone']}").status_code == 200
    assert hub.db.directory_memberships.get(f"note:{ids['note']}") is None  # the effect: unfiled
    _one(count, "zone.delete")


def test_a_member_ids_write_that_adds_and_removes_is_admitted(hub: Hub) -> None:
    ids = _seed(hub)
    a, b = f"note:{ids['note']}", f"note:{ids['note2']}"
    hub.client.put(f"/api/kbs/{ids['kb']}/members/{a}")
    count = Count(hub)
    is_error, _ = hub.mcp("desk.update", {"kind": "kbs", "id": ids["kb"], "data": {"member_ids": [b]}})
    assert is_error is False
    assert _kb_members(hub, ids["kb"]) == [b]  # the effect: a removed, b added
    _one(count, "kb.update")


def test_a_kb_create_over_an_existing_id_that_clears_memberships_is_admitted(hub: Hub) -> None:
    ids = _seed(hub)
    hub.mcp("kb.add_member", {"kb_id": ids["kb"], "ref": f"note:{ids['note']}"})
    count = Count(hub)
    is_error, _ = hub.mcp("desk.create", {"kind": "kbs", "data": {"kb_id": ids["kb"], "name": "Knowledge"}})
    assert is_error is False
    assert _kb_members(hub, ids["kb"]) == []  # the effect: the membership set replaced
    _one(count, "kb.create")


def test_a_zone_move_by_parent_and_by_create_over_an_id_is_admitted(hub: Hub) -> None:
    ids = _seed(hub)
    count = Count(hub)
    assert hub.client.put(f"/api/directories/{ids['zone2']}", json={"parent_id": ids["zone"]}).status_code == 200
    assert hub.db.directories.get(ids["zone2"]).parent_id == ids["zone"]
    _one(count, "zone.update")
    count = Count(hub)
    assert hub.client.post("/api/directories", json={"id": ids["zone2"], "name": "Zone two"}).status_code == 201
    assert hub.db.directories.get(ids["zone2"]).parent_id is None  # the effect: moved to the root
    _one(count, "zone.create")


def test_a_thought_tombstone_that_unfiles_is_admitted_on_both_transports(hub: Hub) -> None:
    ids = _seed(hub)
    for transport in ("http", "mcp"):
        thought = _thought_note(hub, f"tomb-{transport}")
        note_id = thought["working_note"]["id"]
        hub.client.put(f"/api/directories/{ids['zone']}/members/note:{note_id}")
        assert hub.db.directory_memberships.get(f"note:{note_id}") is not None
        revisions = {"expected_aggregate_revision": thought["aggregate_revision"],
                     "expected_lifecycle_revision": thought["lifecycle_revision"]}
        count = Count(hub)
        if transport == "http":
            deleted = hub.client.request("DELETE", f"/api/notes/{note_id}", json=revisions)
            assert deleted.status_code == 200, deleted.text
        else:
            is_error, value = hub.mcp("desk.delete", {"kind": "notes", "id": note_id, "data": revisions})
            assert is_error is False, value
        assert hub.db.directory_memberships.get(f"note:{note_id}") is None  # the effect: unfiled
        _one(count, "note.delete")


# ── the AGENT path (R1), through the REAL remote route ───────────────────


def test_an_agent_without_a_grant_is_refused_then_granted_then_revoked(hub: Hub) -> None:
    ids = _seed(hub)
    agent = _agent(hub)
    ref = f"note:{ids['note']}"
    count = Count(hub)
    is_error, refused = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": ref})
    assert is_error is True and refused["code"] == "desk_delegation_required", refused
    made = _one(count, "zone.file", "desk_delegation_required")
    assert (made["principal_kind"], made["principal_identity"]) == ("agent", AGENT_ID)
    assert _filed(hub, ids["zone"]) == [] and _waiting(hub) == 0

    granted = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={})
    assert granted.status_code == 200, granted.text
    grant_id = granted.json()["grant_id"]
    count = Count(hub)
    is_error, filed = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": ref})
    assert is_error is False, filed
    row = _one(count, "zone.file")
    assert row["authority_basis"].startswith(f"desk-delegation:{grant_id}:sha256:")
    assert (row["delegator_kind"], row["delegator_identity"]) == ("owner", "owner-session")
    assert filed["receipt"]["authority_basis"] == row["authority_basis"]
    assert _filed(hub, ids["zone"]) == [ref]

    assert hub.client.delete(f"/api/settings/remote/delegations/{AGENT_ID}").status_code == 200
    count = Count(hub)
    is_error, refused = _tool(agent, "zone.unfile", {"directory_id": ids["zone"], "primitive_id": ref})
    assert is_error is True and refused["code"] == "desk_delegation_revoked", refused
    _one(count, "zone.unfile", "desk_delegation_revoked")
    assert _filed(hub, ids["zone"]) == [ref] and _waiting(hub) == 0


def test_an_agent_with_an_expired_grant_is_refused_expired(hub: Hub) -> None:
    ids = _seed(hub)
    agent = _agent(hub)
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={"expires_at": time.time() + 0.4}).status_code == 200
    time.sleep(0.6)
    count = Count(hub)
    is_error, refused = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})
    assert is_error is True and refused["code"] == "desk_delegation_expired", refused
    _one(count, "zone.file", "desk_delegation_expired")
    assert _filed(hub, ids["zone"]) == [] and _waiting(hub) == 0


def test_a_grant_to_another_agent_and_an_operation_outside_the_set_are_refused(hub: Hub) -> None:
    ids = _seed(hub)
    agent = _agent(hub)
    assert hub.client.put("/api/settings/remote/delegations/someone-else", json={}).status_code == 200
    count = Count(hub)
    is_error, refused = _tool(agent, "kb.add_member", {"kb_id": ids["kb"], "ref": f"note:{ids['note']}"})
    assert is_error is True and refused["code"] == "desk_delegation_required"
    _one(count, "kb.member.add", "desk_delegation_required")
    # A stored set without the operation (a grant never widens with the code).
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 200
    with hub.db._connection() as conn:
        row = conn.execute("SELECT id, operations_json FROM kernel_desk_delegations WHERE agent_identity=? AND state='LIVE'", (AGENT_ID,)).fetchone()
        narrowed = [n for n in json.loads(row["operations_json"]) if n != "kb.member.add"]
        conn.execute("UPDATE kernel_desk_delegations SET operations_json=? WHERE id=?", (json.dumps(narrowed), row["id"]))
    count = Count(hub)
    is_error, refused = _tool(agent, "kb.add_member", {"kb_id": ids["kb"], "ref": f"note:{ids['note']}"})
    assert is_error is True and refused["code"] == "desk_delegation_required"
    _one(count, "kb.member.add", "desk_delegation_required")
    assert _kb_members(hub, ids["kb"]) == [] and _waiting(hub) == 0


def test_an_agent_decides_under_its_grant_including_delete(hub: Hub) -> None:
    agent = _agent(hub)
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 200
    for tool, arguments, name in (
        ("desk.create", {"kind": "decisions", "data": {"title": "Agent", "status": "proposed"}}, "decision.create"),
    ):
        count = Count(hub)
        is_error, made = _tool(agent, tool, arguments)
        assert is_error is False, made
        assert _one(count, name)["authority_basis"].startswith("desk-delegation:")
    count = Count(hub)
    is_error, deleted = _tool(agent, "desk.delete", {"kind": "decisions", "id": made["id"]})
    assert is_error is False and deleted["deleted"] is True  # R5: decision.delete is in the grant
    _one(count, "decision.delete")
    assert hub.client.get(f"/api/decisions/{made['id']}").status_code == 404


def test_an_agent_cannot_grant_or_revoke_and_the_edge_refuses_the_unauthenticated(hub: Hub) -> None:
    agent = _agent(hub)
    for method in ("put", "delete"):
        count = Count(hub)
        resp = getattr(agent, method)(f"/api/settings/remote/delegations/{AGENT_ID}", **({"json": {}} if method == "put" else {}))
        assert resp.status_code == 403 and resp.json()["error"] == "owner_principal_required", resp.text
        name = "delegation.grant" if method == "put" else "delegation.revoke"
        _one(count, name, "owner_principal_required")
    with hub.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_desk_delegations").fetchone()[0] == 0
    from starlette.testclient import TestClient

    anonymous = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    anonymous.headers.pop("x-holdspeak-token", None)
    count = Count(hub)
    assert anonymous.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 401
    _none(count)


def test_the_owner_grant_and_revoke_are_one_operation_each(hub: Hub) -> None:
    count = Count(hub)
    granted = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={})
    assert granted.status_code == 200
    _one(count, "delegation.grant")
    assert granted.json()["receipt"]["result_ref"] == f"desk-delegation:{granted.json()['grant_id']}"
    count = Count(hub)
    assert hub.client.delete(f"/api/settings/remote/delegations/{AGENT_ID}").status_code == 200
    _one(count, "delegation.revoke")
    count = Count(hub)
    nothing = hub.client.delete(f"/api/settings/remote/delegations/{AGENT_ID}")
    assert nothing.status_code == 409 and nothing.json()["error"] == "desk_delegation_required"
    _one(count, "delegation.revoke", "desk_delegation_required")


@pytest.mark.parametrize("body, path", [
    (b"[1, 2]", AGENT_ID), (b'{"expires_at": "soon"}', AGENT_ID), (b"{}", "%20"),
])
def test_malformed_grant_requests_leave_an_invalid_arguments_receipt(hub: Hub, body: bytes, path: str) -> None:
    count = Count(hub)
    resp = hub.client.put(f"/api/settings/remote/delegations/{path}", content=body, headers={"Content-Type": "application/json"})
    assert resp.status_code == 400 and resp.json()["error"] == "invalid_arguments", resp.text
    _one(count, "delegation.grant", "invalid_arguments")
    with hub.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_desk_delegations").fetchone()[0] == 0


# ── refusal receipts (R2), one fence per class ───────────────────────────


def _tombstoned_thought_note(hub: Hub) -> str:
    thought = _thought_note(hub, "guard")
    note_id = thought["working_note"]["id"]
    tomb = hub.client.request("DELETE", f"/api/notes/{note_id}", json={
        "expected_aggregate_revision": thought["aggregate_revision"], "expected_lifecycle_revision": thought["lifecycle_revision"]})
    assert tomb.status_code == 200, tomb.text
    return note_id


def _mcp_error(result: tuple[bool, Any]) -> Any:
    is_error, value = result
    assert is_error is True, value
    return value


#: Class 2, one path each: (operation, outcome, the call; asserts its own response).
CLASS_2: dict[str, tuple[str, str, Any]] = {
    "http NotFound": ("zone.file", "not_found", lambda hub, ids: hub.client.put(f"/api/directories/nope/members/note:{ids['note']}").status_code == 404),
    "mcp NotFound": ("zone.file", "not_found", lambda hub, ids: _mcp_error(hub.mcp("zone.file", {"directory_id": "nope", "primitive_id": f"note:{ids['note']}"}))["code"] == "not_found"),
    "http zone_name_taken": ("zone.create", "zone_name_taken", lambda hub, ids: hub.client.post("/api/directories", json={"id": ids["zone2"], "name": "Zone"}).status_code == 409),
    "mcp zone_name_taken": ("zone.create", "zone_name_taken", lambda hub, ids: _mcp_error(hub.mcp("desk.create", {"kind": "directories", "data": {"directory_id": ids["zone2"], "name": "zone"}}))["error"] == "zone_name_taken"),
    "http thought_tombstoned": ("zone.file", "thought_tombstoned", lambda hub, ids: hub.client.put(f"/api/directories/{ids['zone']}/members/note:{ids['tomb']}").status_code == 500),
    "mcp thought_tombstoned": ("zone.file", "thought_tombstoned", lambda hub, ids: _mcp_error(hub.mcp("zone.file", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['tomb']}"}))["code"] == "thought_tombstoned"),
}


@pytest.mark.parametrize("path", sorted(CLASS_2))
def test_class_2_each_domain_refusal_after_approval(hub: Hub, path: str) -> None:
    ids = _seed(hub)
    if "tombstoned" in path:
        ids["tomb"] = _tombstoned_thought_note(hub)
    name, outcome, call = CLASS_2[path]
    count = Count(hub)
    assert call(hub, ids) is True
    _one(count, name, outcome)
    assert _filed(hub, ids["zone"]) == [] and _waiting(hub) == 0


CLASS_3: dict[str, tuple[str, str, Any]] = {
    "mcp authority_in_arguments": ("decision.create", "authority_in_arguments", lambda hub, ids: "owner cannot be an argument" in _mcp_error(hub.mcp("desk.create", {"kind": "decisions", "data": {"title": "x", "owner": "forged"}}))["error"]),
    "mcp invalid_arguments": ("decision.create", "invalid_arguments", lambda hub, ids: _mcp_error(hub.mcp("desk.create", {"kind": "decisions", "data": {"title": "x", "bogus": 1}}))["error"].startswith("Invalid arguments for decision.create")),
    "http authority_in_arguments": ("decision.update", "authority_in_arguments", lambda hub, ids: "cannot be an argument" in hub.client.put(f"/api/decisions/{ids['decision']}", json={"principal": "owner"}).json()["error"]),
}


@pytest.mark.parametrize("path", sorted(CLASS_3))
def test_class_3_each_contract_refusal_keeps_its_error_and_leaves_a_receipt(hub: Hub, path: str) -> None:
    ids = {"decision": _decision(hub)}
    name, outcome, call = CLASS_3[path]
    count = Count(hub)
    assert call(hub, ids) is True
    _one(count, name, outcome)
    assert hub.client.get(f"/api/decisions/{ids['decision']}").json()["decision"]["title"] == "D"


CLASS_4: dict[str, tuple[str, str, Any]] = {
    "http duplicate decision_id": ("decision.update", "invalid_arguments", lambda hub, ids: hub.client.put(f"/api/decisions/{ids['decision']}", json={"decision_id": "other", "title": "x"}).status_code == 400),
    "mcp duplicate decision_id": ("decision.update", "invalid_arguments", lambda hub, ids: bool(_mcp_error(hub.mcp("desk.update", {"kind": "decisions", "id": ids["decision"], "data": {"decision_id": "other"}})))),
    "mcp schema refusal": ("zone.file", "invalid_arguments", lambda hub, ids: "directory_id" in _mcp_error(hub.mcp("zone.file", {"primitive_id": f"note:{ids['note']}"}))["error"]),
    "mcp non-object arguments": ("zone.file", "invalid_arguments", lambda hub, ids: "must be an object" in _rpc(hub.client, "zone.file", [ids["zone"], ids["note"]])["result"]["content"][0]["text"]),
    "http non-object decision body": ("decision.create", "invalid_arguments", lambda hub, ids: hub.client.post("/api/decisions", content=b"[]", headers={"Content-Type": "application/json"}).status_code == 400),
    "mcp palette refusal": ("zone.file", "mcp_palette_refused", lambda hub, ids: _rpc(ids["project"], "zone.file", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})["error"]["data"]["code"] == "MCP-005"),
}


@pytest.mark.parametrize("path", sorted(CLASS_4))
def test_class_4_each_adapter_refusal_before_invoke(hub: Hub, path: str) -> None:
    ids = _seed(hub)
    ids["decision"] = _decision(hub)
    if path == "mcp palette refusal":
        ids["project"] = _agent(hub, palette="PROJECT", identity="project-agent")
    name, outcome, call = CLASS_4[path]
    count = Count(hub)
    assert call(hub, ids) is True
    _one(count, name, outcome)
    assert _filed(hub, ids["zone"]) == []
    assert hub.client.get(f"/api/decisions/{ids['decision']}").json()["decision"]["title"] == "D"


BOUNDARY: dict[str, Any] = {
    "unknown tool": lambda hub, ids: _rpc(hub.client, "zone.fil", {})["result"]["isError"] is True,
    # Round three (Astra r2 finding 1): AUTHENTICATED principals, and the named
    # error asserted. A principal=None call could never journal (no receipt is
    # written without an authenticated principal), so it hid a mutation.
    "unknown operation, owner": lambda hub, ids: _refused_as(
        lambda: hub.root.operations.invoke(_OWNER, "no.such.operation", {}), "unknown_operation"),
    "unknown operation, agent": lambda hub, ids: _refused_as(
        lambda: hub.root.operations.invoke(_AGENT, "no.such.operation", {"kind": "notes"}), "unknown_operation"),
    "failed read": lambda hub, ids: hub.mcp("desk.get", {"kind": "notes", "id": "missing"})[0] is True,
    "palette refusal of a read": lambda hub, ids: "error" in _rpc(ids["project"], "desk.list", {"kind": "notes"}),
    "palette refusal of an exempt write": lambda hub, ids: "error" in _rpc(ids["project"], "desk.create", {"kind": "notes", "data": {"title": "x"}}),
    "non-object payload, conditional operation": lambda hub, ids: hub.mcp("desk.create", {"kind": "kbs", "data": [1]})[0] is True,
    "malformed exempt operation": lambda hub, ids: hub.mcp("desk.create", {"kind": "notes", "data": {"owner": "x"}})[0] is True,
    "http non-object body, conditional operation": lambda hub, ids: hub.client.post("/api/kbs", content=b"[]", headers={"Content-Type": "application/json"}).status_code == 400,
}


_OWNER = Principal(PrincipalKind.OWNER, "owner-session")
_AGENT = Principal(PrincipalKind.AGENT, AGENT_ID)


def _refused_as(call: Any, code: str) -> bool:
    from holdspeak.operations import OperationRefused

    with pytest.raises(OperationRefused) as refused:
        call()
    assert refused.value.code == code, refused.value.code
    return True


@pytest.mark.parametrize("path", sorted(BOUNDARY))
def test_the_protocol_boundary_leaves_no_receipt(hub: Hub, path: str) -> None:
    ids = _seed(hub)
    if "palette" in path:
        ids["project"] = _agent(hub, palette="PROJECT", identity="project-agent")
    count = Count(hub)
    assert BOUNDARY[path](hub, ids) is True
    _none(count)


# ── readback ─────────────────────────────────────────────────────────────


def test_the_receipt_reads_back_the_same_over_http_and_mcp(hub: Hub) -> None:
    made = hub.client.post("/api/decisions", json={"title": "Read me"})
    body = made.json()
    operation_id, receipt = body["operation_id"], body["receipt"]
    assert receipt["state"] == "succeeded" and receipt["operation_id"] == operation_id
    count = Count(hub)
    over_http = hub.client.get("/api/kernel/read", params={"refs": f"operation:{operation_id}", "view": "receipt"})
    assert over_http.status_code == 200
    is_error, over_mcp = hub.mcp("kernel.receipt", {"operation_id": operation_id})
    assert is_error is False
    assert over_mcp["objects"][0]["receipt"] == over_http.json()["objects"][0]["receipt"] == receipt
    _none(count)  # a read makes no operation


def test_an_agent_reads_its_own_receipts_and_not_anothers(hub: Hub) -> None:
    ids = _seed(hub)
    agent = _agent(hub)
    other = _agent(hub, identity="other-agent")
    is_error, refused = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})
    assert is_error is True
    operation_id = refused["operation_id"]
    is_error, own = _tool(agent, "kernel.receipt", {"operation_id": operation_id})
    assert is_error is False and own["objects"][0]["receipt"]["outcome"] == "desk_delegation_required"
    is_error, denied = _tool(other, "kernel.receipt", {"operation_id": operation_id})
    assert is_error is True and "principal_read_scope_required" in denied["error"]


def test_the_receipt_tool_is_declared_in_the_desk_palette_and_refused_outside_it(hub: Hub) -> None:
    from holdspeak.mcp.palettes import resolve_palette

    assert "kernel.receipt" in resolve_palette("DESK") and "kernel.receipt" not in resolve_palette("PROJECT")
    project = _agent(hub, palette="PROJECT", identity="project-agent")
    count = Count(hub)
    refused = _rpc(project, "kernel.receipt", {"operation_id": "op_x"})
    assert refused["error"]["data"] == {"code": "MCP-005", "tool": "kernel.receipt"}
    _none(count)  # a read tool's palette refusal: the protocol boundary


# ── the ledger fields the face binds to ──────────────────────────────────


def test_the_remote_settings_carry_the_grants_effective_state(hub: Hub) -> None:
    _agent(hub)
    ledger = hub.client.get("/api/settings/remote").json()
    assert ledger["credentials"][0]["delegation"] is None and ledger["delegations"] == []
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 200
    row = hub.client.get("/api/settings/remote").json()["credentials"][0]["delegation"]
    assert row["state"] == "LIVE" and row["grant_id"].startswith("deskdeleg_") and row["expires_at"] is None
    # The credential goes by the agent's own hand: the grant stays, shown without a credential.
    agent_token = hub.client.post("/api/settings/remote/credentials", json={"identity": AGENT_ID, "palette": "DESK"}).json()["token"]
    from starlette.testclient import TestClient

    agent = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    agent.headers.pop("x-holdspeak-token", None)
    agent.headers.update({"Authorization": f"Bearer {agent_token}"})
    assert agent.delete("/api/principals/self").json()["revoked"] is True
    after = hub.client.get("/api/settings/remote").json()
    assert after["credentials"] == []
    assert [(d["identity"], d["state"]) for d in after["delegations"]] == [(AGENT_ID, "LIVE")]
    # The owner revokes by identity with no credential left: the grant is revoked, with a receipt.
    revoked = hub.client.delete(f"/api/principals/agents/{AGENT_ID}")
    assert revoked.status_code == 200 and revoked.json()["grant_revoked"] is True and revoked.json()["revoked"] is False
    assert revoked.json()["receipt"]["state"] == "succeeded"
    # The stopped orphan leaves the ledger (LIVE in storage only, the ratified wire contract).
    assert hub.client.get("/api/settings/remote").json()["delegations"] == []


# ── invariant 5: reissue, the credential's own ends, durable-first revoke ─


def _token_client(hub: Hub, token: str) -> Any:
    from starlette.testclient import TestClient

    client = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def _issue(hub: Hub, identity: str = AGENT_ID, **extra: Any) -> dict[str, Any]:
    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": identity, "palette": "DESK", **extra})
    assert issued.status_code == 200, issued.text
    return issued.json()


def _live_grants(hub: Hub) -> list[tuple[str, str]]:
    with hub.db._connection() as conn:
        return [(r[0], r[1]) for r in conn.execute("SELECT id, state FROM kernel_desk_delegations WHERE agent_identity=?", (AGENT_ID,))]


def test_f12_a_reissue_keeps_the_grant_and_the_old_token_dies(hub: Hub) -> None:
    ids = _seed(hub)
    first = _issue(hub)
    grant_id = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).json()["grant_id"]
    second = _issue(hub)
    assert second["id"] != first["id"]
    assert _token_client(hub, first["token"]).post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code == 401
    count = Count(hub)
    is_error, filed = _tool(_token_client(hub, second["token"]), "zone.file",
                            {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})
    assert is_error is False, filed
    assert _one(count, "zone.file")["authority_basis"].split(":", 2)[1] == grant_id
    assert hub.client.get("/api/settings/remote").json()["credentials"][0]["delegation"]["state"] == "LIVE"


def test_f14_self_revoke_and_ttl_cleanup_leave_the_grant_live(hub: Hub) -> None:
    issued = _issue(hub)
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 200
    assert _token_client(hub, issued["token"]).delete("/api/principals/self").json()["revoked"] is True
    assert [state for _id, state in _live_grants(hub)] == ["LIVE"]
    short = _issue(hub, ttl_seconds=1)
    time.sleep(1.2)
    assert _token_client(hub, short["token"]).post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code == 401
    assert hub.client.get("/api/settings/remote").json()["credentials"] == []  # cleaned up
    assert [state for _id, state in _live_grants(hub)] == ["LIVE"]


def test_f21a_the_owner_credential_revoke_ends_the_grant_first(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    ids = _seed(hub)
    issued = _issue(hub)
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).status_code == 200
    store = hub.server.app.state.agent_credentials
    real = store.revoke_by_id

    def interrupted(credential_id: str) -> bool:
        raise RuntimeError("interrupted before the credential removal")

    monkeypatch.setattr(store, "revoke_by_id", interrupted)
    count = Count(hub)
    with pytest.raises(RuntimeError):
        hub.client.delete(f"/api/settings/remote/credentials/{issued['id']}")
    revoke = _one(count, "delegation.revoke")
    with hub.db._connection() as conn:
        assert conn.execute("SELECT state, revocation_reason FROM kernel_desk_delegations WHERE agent_identity=?", (AGENT_ID,)).fetchone()[:] == ("REVOKED", "credential_revoked")
    # The safe direction: the token still authenticates, and every desk grant operation is refused.
    is_error, refused = _tool(_token_client(hub, issued["token"]), "zone.file",
                              {"directory_id": ids["zone"], "primitive_id": f"note:{ids['note']}"})
    assert is_error is True and refused["code"] == "desk_delegation_revoked"
    # The owner's retry removes the token; no second revoke operation.
    monkeypatch.setattr(store, "revoke_by_id", real)
    count = Count(hub)
    retried = hub.client.delete(f"/api/settings/remote/credentials/{issued['id']}")
    assert retried.status_code == 200 and retried.json()["grant_revoked"] is False
    _none(count)
    assert revoke["name"] == "delegation.revoke"


def test_f22_f23_a_grant_with_no_credential_is_listed_time_aware_and_revocable(hub: Hub) -> None:
    issued = _issue(hub)
    assert hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={"expires_at": time.time() + 0.5}).status_code == 200
    assert _token_client(hub, issued["token"]).delete("/api/principals/self").status_code == 200
    listed = hub.client.get("/api/settings/remote").json()
    assert listed["credentials"] == [] and [(d["identity"], d["state"]) for d in listed["delegations"]] == [(AGENT_ID, "LIVE")]
    time.sleep(0.7)
    # Stored LIVE, past its expiry: the projection says EXPIRED (never ALLOWED from the stored state).
    assert [d["state"] for d in hub.client.get("/api/settings/remote").json()["delegations"]] == ["EXPIRED"]
    with hub.db._connection() as conn:
        assert conn.execute("SELECT state FROM kernel_desk_delegations WHERE agent_identity=?", (AGENT_ID,)).fetchone()[0] == "LIVE"
    # The switch governs transport, not authority: the rows read the same with it OFF.
    assert hub.client.put("/api/settings/remote", json={"enabled": False}).status_code == 200
    assert [d["state"] for d in hub.client.get("/api/settings/remote").json()["delegations"]] == ["EXPIRED"]
