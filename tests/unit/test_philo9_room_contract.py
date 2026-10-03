"""PHILO-9-01: the Room's operations on the contract, fenced through the REAL hub.

Every fence boots the real ``MeetingWebServer`` over an isolated database and
reaches it by its real transports: HTTP routes and MCP over ``/api/mcp``.
The BEHAVIOURAL fences (A1, F2, F6, F7, F13, F22) read only public transports
and the database, so they run unchanged on an export of main, where each is
red (the phase's red-first law). The new tools have no red: their proof is the
equivalence of durable outcome, result body and refusal mapping with the
existing HTTP route, in one hub and across a restart (the charter's
compatibility mapping is the only difference; message text is never compared).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

REMOTE_HOST = "192.0.2.124"  # TEST-NET-1: never loopback


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


# ── helpers over the real transports ────────────────────────────────────


def _rpc(client: Any, name: str, arguments: Any) -> dict[str, Any]:
    resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                         "params": {"name": name, "arguments": arguments}})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _tool(client: Any, name: str, arguments: Any) -> tuple[bool, Any]:
    body = _rpc(client, name, arguments)
    return body["result"]["isError"], json.loads(body["result"]["content"][0]["text"])


def _project(hub: Hub, name: str = "Payments ledger cutover") -> str:
    made = hub.client.post("/api/projects", json={"name": name})
    assert made.status_code == 200, made.text
    return made.json()["project"]["id"]


def _revision(hub: Hub, project_id: str) -> int:
    return int(hub.client.get(f"/api/projects/{project_id}/room").json()["revision"])


def _days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


# ── A1: the resource routes forward expected_revision and command_id ─────


def test_a1_the_resource_put_refuses_a_stale_revision(hub: Hub) -> None:
    pid = _project(hub)
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    before = _revision(hub, pid)
    resp = hub.client.put(f"/api/projects/{pid}/resources/note:{note}", json={"expected_revision": -1})
    assert resp.status_code == 409, resp.text
    assert resp.json()["error_code"] == "stale_revision"
    assert _revision(hub, pid) == before, "a stale revision wrote"
    assert hub.client.get(f"/api/projects/{pid}/resources").json()["resources"] == []


def test_a1_the_resource_put_honours_the_command_id(hub: Hub) -> None:
    pid = _project(hub)
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    first = hub.client.put(f"/api/projects/{pid}/resources/note:{note}",
                           json={"relationship": "member", "command_id": "pcmd_a1_put"})
    assert first.status_code == 200, first.text
    after_first = _revision(hub, pid)
    # The same key with the same body: the recorded result, nothing written again.
    replay = hub.client.put(f"/api/projects/{pid}/resources/note:{note}",
                            json={"relationship": "member", "command_id": "pcmd_a1_put"})
    assert replay.status_code == 200, replay.text
    assert replay.json()["resource"]["project_revision"] == first.json()["resource"]["project_revision"]
    assert _revision(hub, pid) == after_first
    # The same key with a different body: refused, nothing written.
    conflict = hub.client.put(f"/api/projects/{pid}/resources/note:{note}",
                              json={"relationship": "related", "command_id": "pcmd_a1_put"})
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error_code"] == "idempotency_conflict"
    assert _revision(hub, pid) == after_first
    rows = hub.client.get(f"/api/projects/{pid}/resources").json()["resources"]
    assert [r["relationship"] for r in rows] == ["member"]


def test_a1_the_resource_delete_refuses_a_stale_revision(hub: Hub) -> None:
    pid = _project(hub)
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    assert hub.client.put(f"/api/projects/{pid}/resources/note:{note}", json={}).status_code == 200
    before = _revision(hub, pid)
    resp = hub.client.request("DELETE", f"/api/projects/{pid}/resources/note:{note}", json={"expected_revision": -1})
    assert resp.status_code == 409, resp.text
    assert resp.json()["error_code"] == "stale_revision"
    assert _revision(hub, pid) == before
    assert len(hub.client.get(f"/api/projects/{pid}/resources").json()["resources"]) == 1


# ── F2: a past-due milestone turns the Room and needs him ────────────────


def test_f2_a_past_due_milestone_turns_health_and_is_in_needs_you(hub: Hub) -> None:
    pid = _project(hub)
    made = hub.client.post(f"/api/projects/{pid}/items", json={
        "item_type": "milestone", "title": "Cutover rehearsal", "due_at": _days_ago(3)})
    assert made.status_code == 200, made.text
    room = hub.client.get(f"/api/projects/{pid}/room").json()
    assert room["health"]["assessment"] == "at_risk", room["health"]
    assert room["health"]["reason"] == "1 OVERDUE"
    rows = [r for r in room["needsYou"]["items"] if r.get("title") == "Cutover rehearsal"]
    assert len(rows) == 1, room["needsYou"]
    assert rows[0]["why"] == "OVERDUE · 3 DAYS" and rows[0]["severity"] == "danger"
    # The same over MCP.
    is_error, mcp_room = _tool(hub.client, "project.get_room", {"project_id": pid})
    assert not is_error and mcp_room["health"]["assessment"] == "at_risk"


def test_f2_preservation_a_milestone_not_yet_due_or_reached_keeps_the_room_on_track(hub: Hub) -> None:
    pid = _project(hub)
    future = (date.today() + timedelta(days=5)).isoformat()
    assert hub.client.post(f"/api/projects/{pid}/items", json={
        "item_type": "milestone", "title": "Later", "due_at": future}).status_code == 200
    reached = hub.client.post(f"/api/projects/{pid}/items", json={
        "item_type": "milestone", "title": "Done early", "due_at": _days_ago(2)}).json()["item"]
    assert hub.client.post(f"/api/projects/{pid}/items/{reached['id']}/transition",
                           json={"verb": "reached"}).status_code == 200
    room = hub.client.get(f"/api/projects/{pid}/room").json()
    assert room["health"]["assessment"] == "on_track", room["health"]
    assert not [r for r in room["needsYou"]["items"] if r.get("kind") == "milestone"]


# ── F6: the Room read reports the updates and the steward ───────────────


def _published_update(hub: Hub, pid: str) -> str:
    draft = hub.client.post(f"/api/projects/{pid}/updates/draft", json={})
    assert draft.status_code == 200, draft.text
    update_id = draft.json()["update"]["id"]
    published = hub.client.post(f"/api/updates/{update_id}/publish", json={})
    assert published.status_code == 200, published.text
    return update_id


def _completed_run(hub: Hub, pid: str) -> str:
    import time

    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={})
    assert started.status_code == 200, started.text
    run_id = started.json()["run_id"]
    for _ in range(200):
        run = hub.client.get(f"/api/steward/runs/{run_id}").json()
        state = (run.get("run") or run).get("state")
        if state in {"completed", "failed", "stopped"}:
            break
        time.sleep(0.05)
    assert state == "completed", run
    return run_id


def test_f6_the_room_reports_a_published_update_and_a_completed_steward_run(hub: Hub) -> None:
    pid = _project(hub)
    update_id = _published_update(hub, pid)
    run_id = _completed_run(hub, pid)
    http_room = hub.client.get(f"/api/projects/{pid}/room").json()
    is_error, mcp_room = _tool(hub.client, "project.get_room", {"project_id": pid})
    assert not is_error, mcp_room
    for room in (http_room, mcp_room):
        assert room["updates"]["state"] == "ok", room["updates"]
        assert room["updates"]["latest_published"]["id"] == update_id
        assert room["updates"]["counts"].get("published") == 1
        assert room["steward"]["state"] == "ok", room["steward"]
        assert room["steward"]["latest_run"]["id"] == run_id
        assert room["steward"]["latest_run"]["state"] == "completed"


# ── F7: the Room's RECEIPTS are its writes ───────────────────────────────


def test_f7_the_rooms_receipts_are_its_writes_not_its_reads(hub: Hub) -> None:
    pid = _project(hub)
    assert hub.client.post(f"/api/projects/{pid}/items", json={"item_type": "risk", "title": "Old ledger freeze slips",
                                                                "details": {"likelihood": "medium", "impact": "high"}}).status_code == 200
    for _ in range(3):  # reads: the Room, its meetings, its summary
        hub.client.get(f"/api/projects/{pid}/room")
        hub.client.get(f"/api/projects/{pid}/meetings")
    receipts = hub.client.get(f"/api/projects/{pid}/room").json()["receipts"]
    assert receipts["state"] == "ok"
    ops = [item["op"] for item in receipts["items"]]
    assert "create_item" in ops, ops
    reads = [op for op in ops if op in {"room", "list_meetings", "get_project", "list_projects", "list_items"}]
    assert reads == [], f"the Room's reads are listed as receipts: {ops}"


# ── F13: one needs-you count with a muted project ────────────────────────


def test_f13_one_needs_you_count_with_a_muted_project(hub: Hub) -> None:
    loud, quiet = _project(hub, "Loud room"), _project(hub, "Muted room")
    # Mint the meeting the proposals cite through the real producer: since
    # PHILO-13-02 needs-you shows only proposals of a visible (unparked,
    # existing) meeting, so a made-up meeting id is a double that lies.
    from datetime import datetime as _dt
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    hub.db.meetings.save_meeting(MeetingState(
        id="m-philo9", started_at=_dt(2026, 9, 20, 9, 0), ended_at=_dt(2026, 9, 20, 9, 30),
        title="Cutover planning", tags=[],
        segments=[TranscriptSegment(text="Send the cutover plan.", speaker="Me",
                                    start_time=0.0, end_time=2.0)]))
    for pid, text in ((loud, "Send the cutover plan"), (quiet, "Book the rehearsal room")):
        assert hub.db.proposals.create_proposal(
            meeting_id="m-philo9", project_id=pid, kind="action", text=text,
            source_plugin="action_owner_enforcer") is not None
    is_error, muted = _tool(hub.client, "heartbeat.set", {"muted_projects": [quiet]})
    assert not is_error, muted
    http = hub.client.get("/api/desk/needs-you?fresh=1").json()
    is_error, mcp = _tool(hub.client, "desk.needs_you", {})
    assert not is_error, mcp
    assert http["count"] == 1 and http["mutedCount"] == 1, http
    assert mcp["count"] == http["count"], (mcp["count"], http["count"])
    assert mcp.get("mutedCount") == 1
    assert sorted(mcp["projects"]) == sorted(http["projects"]) == [loud]


# ── F22: "1 proposal waiting" ────────────────────────────────────────────


def test_f22_one_waiting_proposal_is_singular(hub: Hub) -> None:
    pid = _project(hub)
    assert hub.db.project_observations.insert_observation(
        observation_id="pobs_philo9_f22", project_id=pid, source_id="decision_records",
        observation_kind="decision.review_due", subject_ref="decision_record:dr-philo9",
        observed_at="2026-09-20T09:00:00", fact_json=json.dumps({"title": "Freeze the schema"}),
    )
    opened = hub.client.post(f"/api/projects/{pid}/reviews")
    assert opened.status_code == 200, opened.text
    pending = [p for p in opened.json()["proposals"] if p.get("lifecycle") == "open"]
    room = hub.client.get(f"/api/projects/{pid}/room").json()
    rows = [r for r in room["needsYou"]["items"] if r.get("source") == "delta"]
    assert len(pending) == 1, opened.json()["proposals"]
    assert [r["title"] for r in rows] == ["1 proposal waiting"]


# ── the seven new tools: the charter's table, and the route's outcome ────


_NEW_TOOLS = ("project.item.list", "project.item.create", "project.item.update", "project.item.transition",
              "project.resource.list", "project.resource.add", "project.resource.remove")


def test_the_seven_tools_are_listed_with_the_charters_schemas(hub: Hub) -> None:
    from holdspeak.mcp.palettes import resolve_palette

    listed = hub.client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    tools = {t["name"]: t for t in listed.json()["result"]["tools"]}
    for name in _NEW_TOOLS:
        assert name in tools, name
        schema = tools[name]["inputSchema"]
        assert schema["additionalProperties"] is False, name
        assert name in resolve_palette("PROJECT") and name in resolve_palette("SWEEP"), name
    assert tools["project.item.create"]["inputSchema"]["required"] == ["project_id", "item_type", "title"]
    assert tools["project.item.create"]["inputSchema"]["properties"]["item_type"]["enum"] == [
        "milestone", "risk", "dependency", "signal", "workstream"]
    patch = tools["project.item.update"]["inputSchema"]["properties"]["patch"]
    assert set(patch["properties"]) == {"title", "summary", "severity", "owner_ref", "due_at", "sort_key", "details", "lifecycle"}
    assert patch["additionalProperties"] is False and patch["minProperties"] == 1
    assert tools["project.resource.add"]["inputSchema"]["properties"]["relationship"]["enum"] == [
        "member", "source", "output", "related"]
    # The operations are bound to the hub's ONE ProjectService (the identity fence).
    for name in _NEW_TOOLS:
        assert hub.root.operations.target(name) is hub.root.project_service, name


def _strip(value: Any) -> Any:
    """Drop what differs between two equal outcomes: ids, times, revisions, command ids."""
    volatile = {"id", "item_id", "project_id", "created_at", "updated_at", "last_modified", "command_id",
                "project_revision", "revision", "created_by_ref", "changed_refs",
                # PHILO-9-02: an admitted write's own operation and receipt (one per call).
                "operation_id", "receipt"}
    if isinstance(value, dict):
        return {k: _strip(v) for k, v in value.items() if k not in volatile}
    if isinstance(value, list):
        return [_strip(v) for v in value]
    return value


def _items_by_mcp(hub: Hub, pid: str, note: str) -> dict[str, Any]:
    c = hub.client
    out: dict[str, Any] = {}
    _, made = _tool(c, "project.item.create", {"project_id": pid, "item_type": "milestone", "title": "Cutover rehearsal",
                                               "due_at": "2026-09-24"})
    out["create"] = made
    item = made["item"]["id"]
    _, out["update"] = _tool(c, "project.item.update", {"project_id": pid, "item_id": item, "patch": {"summary": "Dry run"}})
    _, out["transition"] = _tool(c, "project.item.transition", {"project_id": pid, "item_id": item, "verb": "missed"})
    _, out["list"] = _tool(c, "project.item.list", {"project_id": pid})
    _, out["add"] = _tool(c, "project.resource.add", {"project_id": pid, "resource_ref": f"note:{note}"})
    _, out["resources"] = _tool(c, "project.resource.list", {"project_id": pid})
    _, out["remove"] = _tool(c, "project.resource.remove", {"project_id": pid, "resource_ref": f"note:{note}"})
    _, out["resources_after"] = _tool(c, "project.resource.list", {"project_id": pid})
    return out


def _items_by_http(hub: Hub, pid: str, note: str) -> dict[str, Any]:
    c = hub.client
    out: dict[str, Any] = {}
    out["create"] = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "Cutover rehearsal",
                                                                "due_at": "2026-09-24"}).json()
    item = out["create"]["item"]["id"]
    out["update"] = c.patch(f"/api/projects/{pid}/items/{item}", json={"summary": "Dry run"}).json()
    out["transition"] = c.post(f"/api/projects/{pid}/items/{item}/transition", json={"verb": "missed"}).json()
    out["list"] = c.get(f"/api/projects/{pid}/items").json()
    out["add"] = c.put(f"/api/projects/{pid}/resources/note:{note}", json={}).json()
    out["resources"] = c.get(f"/api/projects/{pid}/resources").json()
    out["remove"] = c.delete(f"/api/projects/{pid}/resources/note:{note}").json()
    out["resources_after"] = c.get(f"/api/projects/{pid}/resources").json()
    return out


def test_the_seven_tools_equal_the_http_routes_in_one_hub_and_across_a_restart(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.db import reset_database

    mcp_pid, http_pid = _project(hub, "Over MCP"), _project(hub, "Over HTTP")
    note = hub.client.post("/api/notes", json={"title": "Runbook"}).json()["note"]["id"]
    by_mcp = _items_by_mcp(hub, mcp_pid, note)
    by_http = _items_by_http(hub, http_pid, note)
    assert _strip(by_mcp) == _strip(by_http)
    # The durable outcome, read back after a restart on the same database, by both transports.
    reset_database()
    composition.install(composition.bare(label="pytest"))
    again = _boot(tmp_path, monkeypatch)
    for pid in (mcp_pid, http_pid):
        _, items = _tool(again.client, "project.item.list", {"project_id": pid})
        assert _strip(items) == _strip(again.client.get(f"/api/projects/{pid}/items").json())
        assert [(i["title"], i["lifecycle"], i["summary"]) for i in items["items"]] == [("Cutover rehearsal", "missed", "Dry run")]
        _, resources = _tool(again.client, "project.resource.list", {"project_id": pid})
        assert resources == again.client.get(f"/api/projects/{pid}/resources").json()
        assert resources["resources"] == [], "the removed resource is still filed"


#: The charter's compatibility mapping: status <-> code (never message text).
_STATUS_FOR = {"validation": 400, "not_found": 404, "stale_revision": 409, "idempotency_conflict": 409}


def _refusals(hub: Hub, pid: str, note: str) -> list[tuple[str, str, int]]:
    c = hub.client
    item = c.post(f"/api/projects/{pid}/items", json={"item_type": "risk", "title": "Old ledger freeze slips",
                                                      "details": {"likelihood": "medium", "impact": "high"}}).json()["item"]["id"]
    rev = _revision(hub, pid)
    cases: list[tuple[str, dict[str, Any], str, str, dict[str, Any] | None]] = [
        ("project.item.list", {"project_id": "proj-none"}, "GET", "/api/projects/proj-none/items", None),
        ("project.item.create", {"project_id": pid, "item_type": "milestone", "title": "x", "expected_revision": rev - 1},
         "POST", f"/api/projects/{pid}/items", {"item_type": "milestone", "title": "x", "expected_revision": rev - 1}),
        ("project.item.create", {"project_id": pid, "item_type": "risk", "title": "No details"},
         "POST", f"/api/projects/{pid}/items", {"item_type": "risk", "title": "No details"}),
        ("project.item.update", {"project_id": pid, "item_id": "pitem-none", "patch": {"title": "y"}},
         "PATCH", f"/api/projects/{pid}/items/pitem-none", {"title": "y"}),
        ("project.item.transition", {"project_id": pid, "item_id": item, "verb": "exploded"},
         "POST", f"/api/projects/{pid}/items/{item}/transition", {"verb": "exploded"}),
        ("project.resource.list", {"project_id": "proj-none"}, "GET", "/api/projects/proj-none/resources", None),
        ("project.resource.add", {"project_id": pid, "resource_ref": "github:example/payments"},
         "PUT", f"/api/projects/{pid}/resources/github:example/payments", {}),
        ("project.resource.remove", {"project_id": pid, "resource_ref": f"note:{note}", "expected_revision": -1},
         "DELETE", f"/api/projects/{pid}/resources/note:{note}", {"expected_revision": -1}),
    ]
    out = []
    for tool, args, method, path, body in cases:
        is_error, answer = _tool(c, tool, args)
        assert is_error, (tool, answer)
        resp = c.request(method, path, json=body) if body is not None else c.request(method, path)
        out.append((tool, answer.get("code"), resp.status_code))
    return out


def test_the_seven_tools_refuse_as_the_routes_do(hub: Hub) -> None:
    pid = _project(hub)
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    for tool, code, status in _refusals(hub, pid, note):
        assert code in _STATUS_FOR, (tool, code)
        assert _STATUS_FOR[code] == status, (tool, code, status)


def test_a_reused_command_id_with_a_different_body_is_idempotency_conflict_on_both(hub: Hub) -> None:
    pid = _project(hub)
    item = hub.client.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M"}).json()["item"]["id"]
    ok, first = _tool(hub.client, "project.item.transition", {"project_id": pid, "item_id": item, "verb": "missed",
                                                              "command_id": "pcmd_philo9_t"})
    assert not ok, first
    is_error, answer = _tool(hub.client, "project.item.transition", {"project_id": pid, "item_id": item, "verb": "dropped",
                                                                    "command_id": "pcmd_philo9_t"})
    assert is_error and answer["code"] == "idempotency_conflict", answer
    resp = hub.client.post(f"/api/projects/{pid}/items/{item}/transition", json={"verb": "dropped", "command_id": "pcmd_philo9_t"})
    assert resp.status_code == 409 and resp.json()["error_code"] == "idempotency_conflict", resp.text


# ── the rig's ``op`` step reaches the same operations over /api/mcp ──────


def test_the_rigs_op_step_reaches_the_new_operations(hub: Hub) -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import graph_walk as gw

    pid = _project(hub)

    def op(name: str, args: dict[str, Any]) -> Any:
        request = gw._op_request(name, args, 1)
        envelope = hub.client.post("/api/mcp", json=request).json()
        response, refusal = gw._decode_mcp_envelope(envelope)
        assert refusal is None, (name, refusal)
        return response

    made = op("project.item.create", {"project_id": pid, "item_type": "milestone", "title": "Rig"})
    listed = op("project.item.list", {"project_id": pid})
    assert [i["id"] for i in listed["items"]] == [made["item"]["id"]]
    assert listed == hub.client.get(f"/api/projects/{pid}/items").json()


# ── kernel.receipt on PROJECT and SWEEP: own read answered, foreign refused ─


def _agent(hub: Hub, palette: str, identity: str) -> Any:
    from starlette.testclient import TestClient

    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": identity, "palette": palette})
    assert issued.status_code == 200, issued.text
    client = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
    return client


@pytest.mark.parametrize("palette", ["PROJECT", "SWEEP"])
def test_kernel_receipt_on_the_palette_reads_its_own_and_refuses_a_foreign_operation(hub: Hub, palette: str) -> None:
    agent = _agent(hub, palette, f"philo9-{palette.lower()}-agent")
    # The agent's own operation: a consequential tool outside its palette is
    # refused with a kernel refusal receipt under the agent's principal.
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    refused = _rpc(agent, "zone.file", {"directory_id": "hs-seed-inbox", "primitive_id": f"note:{note}"})
    own = refused["error"]["data"].get("operation_id")
    assert own, refused
    is_error, receipt = _tool(agent, "kernel.receipt", {"operation_id": own})
    assert not is_error, receipt
    assert receipt["objects"][0]["ref"] == f"operation:{own}", receipt
    # A foreign operation: the owner's admitted decision write.
    foreign = hub.client.post("/api/decisions", json={"title": "Owner's"}).json()["operation_id"]
    is_error, answer = _tool(agent, "kernel.receipt", {"operation_id": foreign})
    # The kernel's read scope (holdspeak/kernel/broker.py) names its rule.
    assert is_error and (answer.get("code") or answer.get("error")) == "principal_read_scope_required", answer


# ── Round two: Codex Astra r1 on PR #680 (checks/story-01-built-astra-r1.md) ─
#
# Ported from Astra's executable reproductions (test_pr680_review.py); each
# was red at 74a9bdd5 and is green after the repair.


def _note(hub: Hub, title: str) -> str:
    return hub.client.post("/api/notes", json={"title": title}).json()["note"]["id"]


def _refs(hub: Hub, pid: str) -> list[str]:
    return [r["resource_ref"] for r in hub.client.get(f"/api/projects/{pid}/resources").json()["resources"]]


@pytest.mark.parametrize("method", ["PUT", "DELETE"])
def test_r1_p1_the_url_owns_the_target_room(hub: Hub, method: str) -> None:
    """Finding 1 (P1): a body that names another Room or reference is refused 400;
    neither Room changes. The URL identifies the target; the body cannot."""
    a, b = _project(hub, "URL room"), _project(hub, "Body room")
    n1, n2 = _note(hub, "URL"), _note(hub, "Body")
    if method == "DELETE":
        for pid, nid in ((a, n1), (b, n2)):
            assert hub.client.put(f"/api/projects/{pid}/resources/note:{nid}", json={}).status_code == 200
    before = (_refs(hub, a), _refs(hub, b), _revision(hub, a), _revision(hub, b))
    for body in ({"project_id": b}, {"resource_ref": f"note:{n2}"}, {"project_id": b, "resource_ref": f"note:{n2}"}):
        resp = hub.client.request(method, f"/api/projects/{a}/resources/note:{n1}", json=body)
        assert resp.status_code == 400, (body, resp.text)
    assert (_refs(hub, a), _refs(hub, b), _revision(hub, a), _revision(hub, b)) == before


def test_r1_p1_the_url_owns_the_item_routes_too(hub: Hub) -> None:
    a, b = _project(hub, "URL room"), _project(hub, "Body room")
    made = hub.client.post(f"/api/projects/{a}/items", json={"item_type": "milestone", "title": "M", "project_id": b})
    assert made.status_code == 400, made.text
    item = hub.client.post(f"/api/projects/{a}/items", json={"item_type": "milestone", "title": "M"}).json()["item"]["id"]
    moved = hub.client.post(f"/api/projects/{a}/items/{item}/transition", json={"verb": "missed", "item_id": "pitem-other"})
    assert moved.status_code == 400, moved.text
    assert hub.client.get(f"/api/projects/{b}/items").json()["items"] == []


def test_r1_p2_a_resource_replay_returns_the_first_response_whole(hub: Hub) -> None:
    pid, n = _project(hub), _note(hub, "Replay")
    url = f"/api/projects/{pid}/resources/note:{n}"
    payload = {"relationship": "member", "command_id": "pcmd_r1_replay"}
    first = hub.client.put(url, json=payload)
    second = hub.client.put(url, json=payload)
    assert first.status_code == second.status_code == 200, (first.text, second.text)
    assert second.json() == first.json()
    _, over_mcp = _tool(hub.client, "project.resource.add", {"project_id": pid, "resource_ref": f"note:{n}",
                                                             "relationship": "member", "command_id": "pcmd_r1_replay"})
    assert over_mcp == first.json()


def test_r1_p4_latest_published_survives_eleven_newer_drafts(hub: Hub) -> None:
    pid = _project(hub)
    update_id = _published_update(hub, pid)
    hub.db.project_update_deliveries.insert_delivery(
        update_id=update_id, operation_id=hub.client.post("/api/decisions", json={"title": "op"}).json()["operation_id"],
        delivered_to="Priya")
    for i in range(11):
        assert hub.client.post(f"/api/projects/{pid}/updates/draft", json={"command_id": f"pcmd_r1_draft_{i}"}).status_code == 200
    updates = hub.client.get(f"/api/projects/{pid}/room").json()["updates"]
    assert updates["counts"]["published"] == 1
    assert (updates["latest_published"] or {}).get("id") == update_id, updates["latest_published"]
    assert [d["delivered_to"] for d in updates["latest_published"]["deliveries"]] == ["Priya"]


def test_r1_p5_http_item_create_keeps_source_observation_id(hub: Hub) -> None:
    pid = _project(hub)
    obs = "pobs_r1_source"
    hub.db.project_observations.insert_observation(
        observation_id=obs, project_id=pid, source_id="decision_records", observation_kind="decision.review_due",
        subject_ref="decision_record:dr-r1", observed_at="2026-09-20T09:00:00", fact_json=json.dumps({"title": "Freeze"}))
    resp = hub.client.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "Source",
                                                                "source_observation_id": obs})
    assert resp.status_code == 200, resp.text
    assert resp.json()["item"]["source_observation_id"] == obs


# ── Finding 3: every advertised id path resolves on a REAL producer ─────

_PATH_FROM = re.compile(r"([a-z_]+(?:\[\])?(?:\.[a-z_]+(?:\[\])?)*) from ([a-z_]+(?:\.[a-z_]+)+)")


def _resolve(value: Any, path: str) -> list[Any]:
    found = [value]
    for part in path.split("."):
        many = part.endswith("[]")
        key = part[:-2] if many else part
        nxt: list[Any] = []
        for v in found:
            assert isinstance(v, dict) and key in v, (path, key, v if not isinstance(v, dict) else sorted(v))
            nxt.extend(v[key] if many else [v[key]])
        found = nxt
    return found


def test_r1_p3_every_advertised_id_path_resolves_on_its_real_producer(hub: Hub) -> None:
    c = hub.client
    pid = _project(hub)
    note = _note(hub, "Filed")
    meeting = "m-r1-paths"
    with hub.db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES (?, datetime('now'), 'Paths')", (meeting,))
    assert c.put(f"/api/projects/{pid}/resources/note:{note}", json={}).status_code == 200
    assert hub.db.project_observations.insert_observation(
        observation_id="pobs_r1_paths", project_id=pid, source_id="decision_records",
        observation_kind="decision.review_due", subject_ref="decision_record:dr-paths",
        observed_at="2026-09-20T09:00:00", fact_json=json.dumps({"title": "Freeze"}))
    # An open review with a proposal, an item and an update, so every list has one to point at.
    assert not _tool(c, "project.open_review", {"project_id": pid})[0]
    assert c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "Seed"}).status_code == 200
    assert c.post(f"/api/projects/{pid}/updates/draft", json={}).status_code == 200
    producers: dict[str, dict[str, Any]] = {
        "project.list": {}, "project.create": {"name": "Paths two"},
        "project.list_updates": {"project_id": pid}, "project.draft_update": {"project_id": pid},
        "project.open_review": {"project_id": pid}, "project.get_delta": {"project_id": pid},
        "project.item.create": {"project_id": pid, "item_type": "milestone", "title": "M"},
        "project.item.list": {"project_id": pid}, "project.resource.list": {"project_id": pid},
        "meeting.list": {},
    }
    tools = {t["name"]: t for t in c.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list",
                                                             "params": {}}).json()["result"]["tools"]}
    checked = 0
    for name, tool in sorted(tools.items()):
        if not (name.startswith("project.") and name.split(".")[1] in {
                "get", "get_room", "update", "archive", "restore", "link", "unlink", "open_review", "get_delta",
                "decide_proposal", "accept_review", "list_updates", "draft_update", "update_draft",
                "publish_update", "item", "resource"}):
            continue
        for argument, spec in tool["inputSchema"]["properties"].items():
            if not (argument.endswith("_id") or argument == "resource_ref") or argument == "command_id":
                continue
            pairs = _PATH_FROM.findall(spec.get("description", ""))
            if argument == "resource_ref" and name != "project.resource.remove":
                continue
            assert pairs, (name, argument, spec.get("description"))
            for path, producer in pairs:
                assert producer in producers, (name, argument, producer)
                is_error, answer = _tool(c, producer, producers[producer])
                assert not is_error, (producer, answer)
                values = [v for v in _resolve(answer, path) if v]
                assert values, (name, argument, path, producer)
                checked += 1
    assert checked >= 20, checked
    # The review id both producers advertise is the one open_review returned.
    _, opened = _tool(c, "project.open_review", {"project_id": pid})
    _, delta = _tool(c, "project.get_delta", {"project_id": pid})
    assert _resolve(delta, "review_id") == [opened["review_id"]]


# ── Round three: Codex Astra r2 on PR #680 (checks/story-01-built-astra-r2.md) ─
#
# Ported from Astra's probes (test_review_r2.py). A replay answers the ORIGINAL
# response the command recorded, never one rebuilt from the row as it is now:
# after a later write, and for a DELETE that removed nothing. Red at c74a214d.


@pytest.mark.parametrize("later", ["edit", "remove"])
@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_r2_a_replay_after_a_later_write_answers_the_original(hub: Hub, later: str, transport: str) -> None:
    pid, nid = _project(hub), _note(hub, "Replay")
    url = f"/api/projects/{pid}/resources/note:{nid}"
    args = {"relationship": "member", "command_id": "pcmd_r2_first"}
    first = hub.client.put(url, json=args)
    assert first.status_code == 200, first.text
    if later == "edit":
        changed = hub.client.put(url, json={"relationship": "output", "command_id": "pcmd_r2_later"})
    else:
        changed = hub.client.request("DELETE", url, json={"command_id": "pcmd_r2_later"})
    assert changed.status_code == 200, changed.text
    before = _revision(hub, pid)
    if transport == "http":
        replay = hub.client.put(url, json=args)
        assert replay.status_code == 200, replay.text
        body = replay.json()
    else:
        is_error, body = _tool(hub.client, "project.resource.add", {"project_id": pid, "resource_ref": f"note:{nid}", **args})
        assert not is_error, body
    assert _revision(hub, pid) == before, "a replay wrote"
    assert body == first.json()


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_r2_a_delete_replay_keeps_its_original_false(hub: Hub, transport: str) -> None:
    pid, nid = _project(hub), _note(hub, "Not filed")
    url = f"/api/projects/{pid}/resources/note:{nid}"
    args = {"command_id": "pcmd_r2_remove"}
    first = hub.client.request("DELETE", url, json=args)
    assert first.status_code == 200 and first.json()["removed"] is False, first.text
    if transport == "http":
        replay = hub.client.request("DELETE", url, json=args)
        assert replay.status_code == 200, replay.text
        body = replay.json()
    else:
        is_error, body = _tool(hub.client, "project.resource.remove", {"project_id": pid, "resource_ref": f"note:{nid}", **args})
        assert not is_error, body
    assert body == first.json()


@pytest.mark.parametrize("method,key", [("PUT", "project_id"), ("PUT", "resource_ref"), ("DELETE", "project_id"),
                                        ("DELETE", "resource_ref"), ("CREATE", "project_id"),
                                        ("TRANSITION", "project_id"), ("TRANSITION", "item_id"), ("PATCH", "item_id")])
def test_r2_a_body_id_equal_to_the_url_is_still_refused_without_a_write(hub: Hub, method: str, key: str) -> None:
    """Astra r2 confirmed R1-1 with these probes; kept as the preservation fence."""
    pid, nid = _project(hub), _note(hub, "Equal")
    c = hub.client
    item = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M"}).json()["item"]["id"]
    before = _revision(hub, pid)
    body = {key: {"project_id": pid, "resource_ref": f"note:{nid}", "item_id": item}[key]}
    if method in {"PUT", "DELETE"}:
        r = c.request(method, f"/api/projects/{pid}/resources/note:{nid}", json=body)
    elif method == "CREATE":
        r = c.post(f"/api/projects/{pid}/items", json={**body, "item_type": "milestone", "title": "Ignored"})
    elif method == "TRANSITION":
        r = c.post(f"/api/projects/{pid}/items/{item}/transition", json={**body, "verb": "missed"})
    else:
        r = c.patch(f"/api/projects/{pid}/items/{item}", json={**body, "title": "Ignored"})
    assert r.status_code == 400, r.text
    assert _revision(hub, pid) == before
