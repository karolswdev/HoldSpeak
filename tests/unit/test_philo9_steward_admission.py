"""PHILO-9-02: the steward and the connectors under Article XI, fenced through the REAL hub.

Every fence boots the real ``MeetingWebServer`` over an isolated database, with
the REAL provider adapters whose only seam is their own subprocess runner
(``gh_runner`` / ``acli_runner``: a counting runner that answers like the real
CLIs, ``test_philo9_b1_connections.CountingRunner``). It reaches the hub by
its real transports -- HTTP routes and MCP over ``/api/mcp`` -- and a PROJECT
credential issued through the real Settings route and used from a non-loopback
host. Only public transports and the database are read, so each behavioural
fence runs unchanged on an export of main, where the red is the zero or the
edge's 403.

* **Admission** -- each ADMITTED row of the charter's table is ONE kernel
  operation with ONE terminal receipt, on HTTP and MCP; the exempt rows and
  the reads make none; ``watch.create`` from a link is the link's CHILD, not a
  second top-level admission.
* **The agent** -- without story 07's grant every admitted write is refused
  ``project_delegation_required`` WITH a receipt and changes nothing (P3);
  over HTTP too (B2: the edge lets the identifiable admitted request reach its
  operation); a read, an exempt edit, an unknown route and an unauthenticated
  request stay protocol refusals with no receipt.
* **Source addition** (F5, F16, F17) -- a suggestion minted by the real scanner
  becomes a resource AND a watch, read back, or a named refusal with the
  suggestion still pending; never ``accepted`` with nothing added.
* **The residual set** -- exactly the 20 MCP and 3 HTTP identities paid.
* **No test double in product code** (F9) -- an AST fence with its mutation.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub  # noqa: E402
from test_philo7_article_xi import REMOTE_HOST  # noqa: E402
from test_philo9_b1_connections import CountingRunner as _B1Runner, _boot as _b1_boot  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
AGENT_ID = "remote-project-agent"


class Runner(_B1Runner):
    """The b1 runner, plus the GitHub list reads a Door count and a watch make."""

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if argv[:3] in (["gh", "pr", "list"], ["gh", "run", "list"]):
            self.calls.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
        return super().__call__(argv, **kwargs)


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    gh, acli = Runner(), Runner()
    hub = _b1_boot(tmp_path, monkeypatch, gh, acli)
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub, gh, acli
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(None, None)
    reset_database()
    composition.install(composition.bare(label="pytest"))


# ── the database reads ───────────────────────────────────────────────────


def _ops(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity,"
            " o.parent_operation_id, o.authority_basis, r.outcome AS outcome, r.state AS receipt_state"
            " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid"
        )]


class Count:
    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.seen = {op["operation_id"] for op in _ops(hub)}

    def new(self) -> list[dict[str, Any]]:
        return [op for op in _ops(self.hub) if op["operation_id"] not in self.seen]

    def top(self) -> list[dict[str, Any]]:
        """The new TOP-LEVEL operations (a child names its parent)."""
        return [op for op in self.new() if not op["parent_operation_id"]]


def _await(hub: Hub, operation_id: str, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for op in _ops(hub):
            if op["operation_id"] == operation_id and op["receipt_state"] is not None:
                return op
        time.sleep(0.05)
    raise AssertionError(f"{operation_id} never ended")


def _settle(hub: Hub, count: Count, timeout: float = 20.0) -> list[dict[str, Any]]:
    """The new operations once every one has its receipt (the steward's run ends later)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        made = count.new()
        if made and all(op["receipt_state"] is not None for op in made):
            return made
        time.sleep(0.05)
    return count.new()


def _one(count: Count, name: str, outcome: str | None = None) -> dict[str, Any]:
    made = [op for op in _settle(count.hub, count) if not op["parent_operation_id"]]
    assert [op["name"] for op in made] == [name], made
    assert made[0]["receipt_state"] is not None, f"{name}: an operation without its receipt"
    if outcome is not None:
        assert made[0]["outcome"] == outcome, made[0]
    return made[0]


def _none(count: Count) -> None:
    assert count.new() == [], "an exempt row or a read made a kernel operation"


# ── the Room's fixtures, through the real transports ─────────────────────


def _project(hub: Hub, name: str = "Payments ledger cutover") -> str:
    return hub.client.post("/api/projects", json={"name": name}).json()["project"]["id"]


def _meeting(hub: Hub, meeting_id: str = "m-steward", *, overdue: int = 0) -> str:
    with hub.db._connection() as conn:
        conn.execute("INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, datetime('now','-10 days'), 'Standup')",
                     (meeting_id,))
        for i in range(overdue):
            conn.execute(
                "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at)"
                " VALUES (?, ?, ?, 'Priya', '2026-09-01', 'pending', 'accepted', datetime('now','-10 days'))",
                (f"{meeting_id}-ai{i}", meeting_id, f"Follow-through {i}"),
            )
    return meeting_id


def _review(hub: Hub, pid: str, overdue: int = 4) -> tuple[str, list[str]]:
    """A review with ``overdue`` proposals (real producers: the collector and the Delta)."""
    meeting = _meeting(hub, f"m-review-{pid}", overdue=overdue)
    assert hub.client.post(f"/api/projects/{pid}/meetings/{meeting}").status_code == 200
    opened = hub.client.post(f"/api/projects/{pid}/reviews").json()
    return opened["review_id"], [p["id"] for p in opened["proposals"]]


def _published(hub: Hub, pid: str) -> str:
    update = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    assert hub.client.post(f"/api/updates/{update}/publish", json={}).status_code == 200
    return update


def _door_project(hub: Hub) -> tuple[str, str]:
    """A project with an armed GitHub watch, made through the Door (the face's path)."""
    made = hub.client.post("/api/projects/door", json={
        "outcome": "Ship the ledger", "sources": [{"provider": "github", "scope": "example/payments",
                                                  "watches": ["open_prs"]}]})
    assert made.status_code == 200, made.text
    pid = made.json()["projectId"]
    watch = hub.db.automations.list_project_watches(pid)[0]["id"]
    return pid, watch


def _suggest(hub: Hub, pid: str, text: str = "We should watch example/payments and PAY-123 before the cutover.") -> None:
    """Suggestions minted by the REAL scanner and persistence (grounding P1)."""
    from holdspeak.services.suggested_source_service import SuggestedSourceService

    service = SuggestedSourceService(hub.db)
    service.create_suggestions(pid, "mtg-probe", service.scan_transcript(text, pid, "mtg-probe"))


def _agent(hub: Hub, palette: str = "PROJECT", identity: str = AGENT_ID) -> Any:
    """A credential issued through the REAL Settings route, used from a remote host."""
    from starlette.testclient import TestClient

    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": identity, "palette": palette})
    assert issued.status_code == 200, issued.text
    client = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
    return client


def _tool(client: Any, name: str, arguments: Any) -> tuple[bool, Any]:
    resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                         "params": {"name": name, "arguments": arguments}})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    if "error" in body:
        return True, body["error"]
    return body["result"]["isError"], json.loads(body["result"]["content"][0]["text"])


# ── ADMISSION: one operation and one receipt per admitted call ───────────

Setup = Callable[[Hub], dict[str, Any]]


def _s_project(hub: Hub) -> dict[str, Any]:
    return {"pid": _project(hub)}


def _s_meeting(hub: Hub) -> dict[str, Any]:
    return {"pid": _project(hub), "mid": _meeting(hub)}


def _s_linked(hub: Hub) -> dict[str, Any]:
    ids = _s_meeting(hub)
    hub.client.post(f"/api/projects/{ids['pid']}/meetings/{ids['mid']}")
    return ids


def _s_note(hub: Hub) -> dict[str, Any]:
    note = hub.client.post("/api/notes", json={"title": "Runbook"}).json()["note"]["id"]
    return {"pid": _project(hub), "ref": f"note:{note}"}


def _s_filed(hub: Hub) -> dict[str, Any]:
    ids = _s_note(hub)
    hub.client.put(f"/api/projects/{ids['pid']}/resources/{ids['ref']}", json={})
    return ids


def _s_review(hub: Hub) -> dict[str, Any]:
    pid = _project(hub)
    review, proposals = _review(hub, pid)
    return {"pid": pid, "review": review, "proposal": proposals[0]}


def _s_draft(hub: Hub) -> dict[str, Any]:
    pid = _project(hub)
    return {"pid": pid, "update": hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]}


def _s_published(hub: Hub) -> dict[str, Any]:
    pid = _project(hub)
    return {"pid": pid, "update": _published(hub, pid)}


def _s_watch(hub: Hub) -> dict[str, Any]:
    pid, watch = _door_project(hub)
    return {"pid": pid, "watch": watch}


def _s_suggested(hub: Hub) -> dict[str, Any]:
    pid = _project(hub)
    _suggest(hub, pid)
    return {"pid": pid}


def _s_run(hub: Hub) -> dict[str, Any]:
    """A run held in OBSERVE (the fixture's hold), so a stop reaches a live run."""
    pid = _project(hub)
    return {"pid": pid}


def _s_trigger(hub: Hub) -> dict[str, Any]:
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(hub.root.watch_service, hub.root.project_steward_service)
    return {}


_D = "/decide"
HTTP_ADMITTED: dict[str, tuple[str, Setup, Callable[[Hub, dict[str, Any]], Any]]] = {
    "archive": ("project.archive", _s_project, lambda h, i: h.client.delete(f"/api/projects/{i['pid']}")),
    "link": ("project.link", _s_meeting, lambda h, i: h.client.post(f"/api/projects/{i['pid']}/meetings/{i['mid']}")),
    "unlink": ("project.unlink", _s_linked, lambda h, i: h.client.delete(f"/api/projects/{i['pid']}/meetings/{i['mid']}")),
    "resource add": ("project.resource.add", _s_note, lambda h, i: h.client.put(f"/api/projects/{i['pid']}/resources/{i['ref']}", json={})),
    "resource remove": ("project.resource.remove", _s_filed, lambda h, i: h.client.delete(f"/api/projects/{i['pid']}/resources/{i['ref']}")),
    "decide accept": ("project.decide_proposal", _s_review, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/reviews/{i['review']}/proposals/{i['proposal']}{_D}", json={"verb": "accept"})),
    "decide edit_accept": ("project.decide_proposal", _s_review, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/reviews/{i['review']}/proposals/{i['proposal']}{_D}",
        json={"verb": "edit_accept", "patch": {"title": "Chase the follow-through"}})),
    "decide defer": ("project.decide_proposal", _s_review, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/reviews/{i['review']}/proposals/{i['proposal']}{_D}",
        json={"verb": "defer", "deferred_until": "2026-12-01"})),
    "decide dismiss": ("project.decide_proposal", _s_review, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/reviews/{i['review']}/proposals/{i['proposal']}{_D}", json={"verb": "dismiss"})),
    "accept review": ("project.accept_review", _s_review, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/reviews/{i['review']}/accept", json={})),
    "publish": ("project.publish_update", _s_draft, lambda h, i: h.client.post(f"/api/updates/{i['update']}/publish", json={})),
    "delivered": ("project.mark_update_delivered", _s_published, lambda h, i: h.client.post(
        f"/api/updates/{i['update']}/delivered", json={"delivered_to": "Priya"})),
    "door count": ("project.door.count", lambda h: {}, lambda h, i: h.client.post(
        "/api/projects/door/count", json={"provider": "github", "scope": "example/payments", "watches": ["open_prs"]})),
    "door create with sources": ("project.door.create", lambda h: {}, lambda h, i: h.client.post(
        "/api/projects/door", json={"outcome": "Ship", "sources": [{"provider": "github", "scope": "example/payments",
                                                                     "watches": ["open_prs"]}]})),
    "policy write": ("project.configure_steward", _s_project, lambda h, i: h.client.put(
        f"/api/projects/{i['pid']}/steward/policy", json={"unattended_enabled": True})),
    "run": ("project.run_steward", _s_project, lambda h, i: h.client.post(f"/api/projects/{i['pid']}/steward/runs", json={})),
    "trigger": ("project.steward.trigger", _s_trigger, lambda h, i: h.client.post("/api/steward/trigger", json={})),
    "nudge send": ("nudge.send", lambda h: {}, lambda h, i: h.client.post("/api/nudges/pststep_none/send", json={"text": "Ping"})),
    "watch test": ("project.watch.test", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/test")),
    "watch evaluate": ("project.watch.evaluate", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/evaluate")),
    "watch rules": ("project.watch.set_rules", _s_watch, lambda h, i: h.client.put(f"/api/watches/{i['watch']}/rules", json={"rules": []})),
    "watch pause": ("project.watch.pause", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/pause")),
    "watch resume": ("project.watch.resume", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/resume")),
    "watch retire": ("project.watch.retire", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/retire")),
    "watch update": ("project.watch.update", _s_watch, lambda h, i: h.client.patch(f"/api/watches/{i['watch']}", json={"name": "PRs"})),
    "watch baseline": ("project.watch.baseline", _s_watch, lambda h, i: h.client.post(f"/api/watches/{i['watch']}/baseline")),
    "suggested add": ("project.add_suggested_source", _s_suggested, lambda h, i: h.client.post(
        f"/api/projects/{i['pid']}/suggested-sources/example/payments/add")),
    "github recheck": ("connection.recheck", lambda h: {}, lambda h, i: h.client.post("/api/connections/github/recheck")),
    "confluence recheck": ("connection.recheck", lambda h: {}, lambda h, i: h.client.post("/api/connections/confluence/recheck")),
}

MCP_ADMITTED: dict[str, tuple[str, Setup, Callable[[Hub, dict[str, Any]], Any]]] = {
    "archive": ("project.archive", _s_project, lambda h, i: h.mcp("project.archive", {"project_id": i["pid"]})),
    "link": ("project.link", _s_meeting, lambda h, i: h.mcp("project.link", {"project_id": i["pid"], "meeting_id": i["mid"]})),
    "decide dismiss": ("project.decide_proposal", _s_review, lambda h, i: h.mcp("project.decide_proposal", {
        "project_id": i["pid"], "review_id": i["review"], "proposal_id": i["proposal"], "verb": "dismiss"})),
    "decide defer": ("project.decide_proposal", _s_review, lambda h, i: h.mcp("project.decide_proposal", {
        "project_id": i["pid"], "review_id": i["review"], "proposal_id": i["proposal"], "verb": "defer",
        "deferred_until": "2026-12-01"})),
    "accept review": ("project.accept_review", _s_review, lambda h, i: h.mcp("project.accept_review", {
        "project_id": i["pid"], "review_id": i["review"]})),
    "publish": ("project.publish_update", _s_draft, lambda h, i: h.mcp("project.publish_update", {"update_id": i["update"]})),
    "delivered": ("project.mark_update_delivered", _s_published, lambda h, i: h.mcp(
        "project.mark_update_delivered", {"update_id": i["update"], "delivered_to": "Priya"})),
    "policy write": ("project.configure_steward", _s_project, lambda h, i: h.mcp(
        "project.configure_steward", {"project_id": i["pid"], "unattended_enabled": True})),
    "run": ("project.run_steward", _s_project, lambda h, i: h.mcp("project.run_steward", {"project_id": i["pid"]})),
    "trigger": ("project.steward.trigger", _s_trigger, lambda h, i: h.mcp("project.steward.trigger", {})),
    "nudge send": ("nudge.send", lambda h: {}, lambda h, i: h.mcp("nudge.send", {"step_id": "pststep_none", "text": "Ping"})),
    "watch test": ("project.watch.test", _s_watch, lambda h, i: h.mcp("project.watch.test", {"watch_id": i["watch"]})),
    "watch evaluate": ("project.watch.evaluate", _s_watch, lambda h, i: h.mcp("project.watch.evaluate", {"watch_id": i["watch"]})),
    "watch rules": ("project.watch.set_rules", _s_watch, lambda h, i: h.mcp("project.watch.set_rules", {"watch_id": i["watch"], "rules": []})),
    "watch pause": ("project.watch.pause", _s_watch, lambda h, i: h.mcp("project.watch.pause", {"watch_id": i["watch"]})),
    "watch resume": ("project.watch.resume", _s_watch, lambda h, i: h.mcp("project.watch.resume", {"watch_id": i["watch"]})),
    "watch retire": ("project.watch.retire", _s_watch, lambda h, i: h.mcp("project.watch.retire", {"watch_id": i["watch"]})),
    "suggested add": ("project.add_suggested_source", _s_suggested, lambda h, i: h.mcp(
        "project.add_suggested_source", {"project_id": i["pid"], "reference": "example/payments"})),
    "github recheck": ("connection.recheck", lambda h: {}, lambda h, i: h.mcp("connection.recheck", {"provider_id": "github"})),
    "jira recheck": ("connection.recheck", lambda h: {}, lambda h, i: h.mcp("connection.recheck", {"provider_id": "jira"})),
}

#: The admitted calls whose ONE receipt is a named refusal on this rig (the refusal class is fenced too).
REFUSED_ON_THE_RIG = {"nudge send": "nudge_not_found"}


@pytest.mark.parametrize("path", sorted(HTTP_ADMITTED))
def test_each_admitted_http_route_is_one_operation_with_one_receipt(rig: Any, path: str) -> None:
    hub, _gh, _acli = rig
    name, setup, call = HTTP_ADMITTED[path]
    ids = setup(hub)
    count = Count(hub)
    resp = call(hub, ids)
    refused = REFUSED_ON_THE_RIG.get(path)
    assert resp.status_code == (404 if refused else 200), resp.text
    made = _one(count, name, refused)
    assert (made["principal_kind"], made["principal_identity"]) == ("owner", "owner-session")
    body = resp.json()
    assert body.get("operation_id") == made["operation_id"], body  # the answer carries its operation


@pytest.mark.parametrize("path", sorted(MCP_ADMITTED))
def test_each_admitted_mcp_tool_is_one_operation_with_one_receipt(rig: Any, path: str) -> None:
    hub, _gh, _acli = rig
    name, setup, call = MCP_ADMITTED[path]
    ids = setup(hub)
    count = Count(hub)
    is_error, value = call(hub, ids)
    refused = REFUSED_ON_THE_RIG.get(path)
    assert is_error is bool(refused), value
    made = _one(count, name, refused)
    assert value.get("operation_id") == made["operation_id"], value


def test_the_exempt_rows_and_the_reads_make_no_operation(rig: Any) -> None:
    hub, _gh, _acli = rig
    pid, watch = _door_project(hub)
    _suggest(hub, pid, "Track OPS-9 please.")
    count = Count(hub)
    c = hub.client
    assert c.get(f"/api/projects/{pid}/steward/policy").status_code == 200
    assert c.get("/api/connections").status_code == 200
    assert c.post("/api/connections/calendar/recheck").status_code == 200
    assert c.post("/api/connections/models/recheck").status_code == 200
    assert c.get(f"/api/watches/{watch}").status_code == 200
    assert c.get(f"/api/projects/{pid}/suggested-sources").status_code == 200
    assert c.post(f"/api/projects/{pid}/suggested-sources/OPS-9/dismiss").status_code == 200
    assert c.get(f"/api/projects/{pid}/nudges").status_code == 200
    assert c.post("/api/projects/door", json={"outcome": "A bare Room"}).status_code == 200
    for name, args in (("connection.list", {}), ("project.configure_steward", {"project_id": pid}),
                       ("project.watch.inspect", {"watch_id": watch}),
                       ("steward.nudges", {"project_id": pid}), ("connection.recheck", {"provider_id": "calendar"})):
        is_error, value = hub.mcp(name, args)
        assert is_error is False, (name, value)
    _none(count)


def test_a_link_is_one_top_level_admission_and_its_meeting_watch_is_its_child(rig: Any) -> None:
    hub, _gh, _acli = rig
    ids = _s_meeting(hub)
    count = Count(hub)
    assert hub.client.post(f"/api/projects/{ids['pid']}/meetings/{ids['mid']}").status_code == 200
    made = _settle(hub, count)
    top = [op for op in made if not op["parent_operation_id"]]
    assert [op["name"] for op in top] == ["project.link"], made
    children = [op for op in made if op["parent_operation_id"]]
    assert [op["name"] for op in children] == ["watch.create"], made
    assert children[0]["parent_operation_id"] == top[0]["operation_id"]


# ── archive (F18, P2): one admitted operation; the pause and unattended-off inside it ──


def test_archive_as_the_owner_is_one_operation_and_its_pause_and_unattended_off_are_inside(rig: Any) -> None:
    hub, _gh, _acli = rig
    pid, watch = _door_project(hub)
    assert hub.client.put(f"/api/projects/{pid}/steward/policy", json={"unattended_enabled": True}).status_code == 200
    count = Count(hub)
    assert hub.client.delete(f"/api/projects/{pid}").status_code == 200
    made = _one(count, "project.archive", "succeeded")
    assert hub.db.automations.get_watch(watch)["state"] == "paused"
    policy = hub.db.steward_policies.get_policy_for_project(pid)
    assert policy["unattended_enabled"] == 0
    # The beat, section 4 (Muad'Dib r1 C1): archive wrote the terms, so its
    # operation is now the policy's recorded owner operation.
    assert policy["configure_operation_id"] == made["operation_id"]


# ── the agent without a grant (Q2, P3), through dispatch with a REAL PROJECT credential ──


AGENT_WRITES: dict[str, tuple[str, Setup, Callable[[Hub, dict[str, Any]], dict[str, Any]]]] = {
    "unattended on": ("project.configure_steward", _s_project,
                      lambda h, i: {"project_id": i["pid"], "unattended_enabled": True}),
    "archive": ("project.archive", _s_project, lambda h, i: {"project_id": i["pid"]}),
    "run": ("project.run_steward", _s_project, lambda h, i: {"project_id": i["pid"]}),
    "publish": ("project.publish_update", _s_draft, lambda h, i: {"update_id": i["update"]}),
    "delivered": ("project.mark_update_delivered", _s_published, lambda h, i: {"update_id": i["update"]}),
    "resource add": ("project.resource.add", _s_note, lambda h, i: {"project_id": i["pid"], "resource_ref": i["ref"]}),
    "suggested add": ("project.add_suggested_source", _s_suggested,
                      lambda h, i: {"project_id": i["pid"], "reference": "example/payments"}),
    "github recheck": ("connection.recheck", lambda h: {}, lambda h, i: {"provider_id": "github"}),
    "watch pause": ("project.watch.pause", _s_watch, lambda h, i: {"watch_id": i["watch"]}),
    **{f"decide {verb}": ("project.decide_proposal", _s_review,
                          (lambda verb: lambda h, i: {"project_id": i["pid"], "review_id": i["review"],
                                                      "proposal_id": i["proposal"], "verb": verb,
                                                      **({"deferred_until": "2026-12-01"} if verb == "defer" else {}),
                                                      **({"patch": {"title": "T"}} if verb == "edit_accept" else {})})(verb))
       for verb in ("accept", "edit_accept", "defer", "dismiss")},
}


def _room_state(hub: Hub) -> dict[str, Any]:
    with hub.db._connection() as conn:
        return {
            "projects": [tuple(r) for r in conn.execute("SELECT id, lifecycle, revision FROM projects ORDER BY id")],
            "policies": [tuple(r) for r in conn.execute("SELECT project_id, enabled, unattended_enabled FROM steward_policies")],
            "runs": conn.execute("SELECT COUNT(*) FROM steward_runs").fetchone()[0],
            "resources": conn.execute("SELECT COUNT(*) FROM project_resources WHERE deleted=0").fetchone()[0],
            "watches": [tuple(r) for r in conn.execute("SELECT id, state FROM connector_watches ORDER BY id")],
            "updates": [tuple(r) for r in conn.execute("SELECT id, lifecycle FROM project_updates ORDER BY id")],
            "deliveries": conn.execute("SELECT COUNT(*) FROM project_update_deliveries").fetchone()[0],
            "proposals": [tuple(r) for r in conn.execute("SELECT id, lifecycle FROM project_proposals ORDER BY id")],
            "suggestions": [tuple(r) for r in conn.execute("SELECT id, status FROM source_suggestions ORDER BY id")],
        }


@pytest.mark.parametrize("path", sorted(AGENT_WRITES))
def test_an_agent_without_a_grant_is_refused_with_a_receipt_and_nothing_changes(rig: Any, path: str) -> None:
    hub, gh, _acli = rig
    name, setup, arguments = AGENT_WRITES[path]
    ids = setup(hub)
    agent = _agent(hub)
    before, calls = _room_state(hub), gh.count()
    count = Count(hub)
    is_error, refused = _tool(agent, name, arguments(hub, ids))
    assert is_error is True and refused.get("code") == "project_delegation_required", refused
    made = _one(count, name, "project_delegation_required")
    assert (made["principal_kind"], made["principal_identity"]) == ("agent", AGENT_ID)
    assert refused.get("operation_id") == made["operation_id"] and refused.get("receipt"), refused
    assert _room_state(hub) == before, "an agent's refused write changed the Room"
    assert gh.count() == calls, "an agent's refused write reached the provider"


def test_an_agent_reads_and_exempt_edits_keep_todays_behaviour(rig: Any) -> None:
    hub, _gh, _acli = rig
    pid = _project(hub)
    _suggest(hub, pid, "See example/other now.")
    agent = _agent(hub)
    count = Count(hub)
    for name, args in (("project.configure_steward", {"project_id": pid}), ("connection.list", {}),
                       ("project.suggested_sources", {"project_id": pid}),
                       ("project.dismiss_suggested_source", {"project_id": pid, "reference": "example/other"})):
        is_error, value = _tool(agent, name, args)
        assert is_error is False, (name, value)
    _none(count)


# ── B2: over HTTP the edge lets the identifiable admitted request reach its operation ──


def test_b2_a_project_credential_over_http_is_refused_with_a_receipt(rig: Any) -> None:
    hub, gh, _acli = rig
    agent = _agent(hub)
    requests = [
        ("project.door.count", lambda: agent.post("/api/projects/door/count", json={
            "provider": "github", "scope": "example/payments", "watches": ["open_prs"]})),
        ("project.door.create", lambda: agent.post("/api/projects/door", json={
            "outcome": "Ship", "sources": [{"provider": "github", "scope": "example/payments", "watches": ["open_prs"]}]})),
        ("connection.recheck", lambda: agent.post("/api/connections/github/recheck")),
    ]
    for name, send in requests:
        before_projects, calls = _room_state(hub)["projects"], gh.count()
        count = Count(hub)
        resp = send()
        assert resp.status_code == 403, (name, resp.text)
        body = resp.json()
        assert body.get("code") == "project_delegation_required", (name, body)
        made = _one(count, name, "project_delegation_required")
        assert body.get("operation_id") == made["operation_id"] and body.get("receipt")
        assert _room_state(hub)["projects"] == before_projects and gh.count() == calls, name


def test_b2_protocol_refusals_stay_receipt_less(rig: Any) -> None:
    hub, _gh, _acli = rig
    from starlette.testclient import TestClient

    pid = _project(hub)
    agent = _agent(hub)
    count = Count(hub)
    # A read, an exempt edit, the exempt form of a conditional route, an unknown route.
    for resp in (agent.get(f"/api/projects/{pid}"), agent.patch(f"/api/projects/{pid}", json={"description": "d"}),
                 agent.post("/api/projects/door", json={"outcome": "Bare"}),
                 agent.post("/api/connections/calendar/recheck"),
                 agent.post(f"/api/projects/{pid}/restore", json={}),
                 agent.get("/api/no-such-route")):
        assert resp.status_code == 403, resp.text
        assert resp.json().get("error") == "principal_right_required", resp.text
    # An unauthenticated request: the edge's 401, no receipt.
    anonymous = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    anonymous.headers.pop("x-holdspeak-token", None)
    assert anonymous.delete(f"/api/projects/{pid}").status_code == 401
    _none(count)


def test_b2_a_malformed_identifiable_write_is_refused_invalid_arguments_with_a_receipt(rig: Any) -> None:
    hub, _gh, _acli = rig
    pid = _project(hub)
    count = Count(hub)
    resp = hub.client.put(f"/api/projects/{pid}/steward/policy", content=b"[1, 2]",
                          headers={"content-type": "application/json"})
    assert resp.status_code == 400, resp.text
    made = _one(count, "project.configure_steward", "invalid_arguments")
    assert resp.json().get("operation_id") == made["operation_id"]


def test_a_contract_refusal_of_an_admitted_tool_leaves_its_receipt(rig: Any) -> None:
    """R2 class 3: the descriptor refuses an argument name; the attempt is identifiable and admitted."""
    hub, _gh, _acli = rig
    pid = _project(hub)
    count = Count(hub)
    is_error, refused = hub.mcp("project.archive", {"project_id": pid, "cascade": True})
    assert is_error is True and refused.get("refusal") == "invalid_arguments", refused
    made = _one(count, "project.archive", "invalid_arguments")
    assert refused.get("operation_id") == made["operation_id"]
    assert _room_state(hub)["projects"][0][1] != "archived"


# ── source addition (F5, F16, F17): a durable, truthful outcome ──────────


def _source_rows(hub: Hub, pid: str) -> dict[str, Any]:
    with hub.db._connection() as conn:
        return {
            "resources": [r[0] for r in conn.execute(
                "SELECT resource_ref FROM project_resources WHERE project_id=? AND deleted=0 AND relationship='source'", (pid,))],
            "watches": [dict(r) for r in conn.execute(
                "SELECT id, connector_id, state, query_json FROM connector_watches WHERE project_id=?", (pid,))],
            "sources": [r[0] for r in conn.execute("SELECT source_ref FROM project_sources WHERE project_id=?", (pid,))],
            "status": {r[0]: r[1] for r in conn.execute(
                "SELECT reference, status FROM source_suggestions WHERE project_id=?", (pid,))},
        }


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_a_github_suggestion_becomes_a_resource_and_a_watch(rig: Any, transport: str) -> None:
    hub, _gh, _acli = rig
    pid = _project(hub)
    _suggest(hub, pid)
    if transport == "http":
        resp = hub.client.post(f"/api/projects/{pid}/suggested-sources/example%2Fpayments/add")
        assert resp.status_code == 200, resp.text
    else:
        is_error, value = hub.mcp("project.add_suggested_source", {"project_id": pid, "reference": "example/payments"})
        assert is_error is False, value
    rows = _source_rows(hub, pid)
    assert rows["resources"] == ["integration:github:example/payments"], rows
    assert [(w["connector_id"], w["state"]) for w in rows["watches"]] == [("gh", "active")], rows
    assert json.loads(rows["watches"][0]["query_json"])["repository"] == "example/payments"
    assert rows["sources"] == [f"watch:{rows['watches'][0]['id']}"]
    assert rows["status"]["example/payments"] == "accepted"
    room = hub.client.get(f"/api/projects/{pid}/room").json()
    assert any("example/payments" == s.get("scope") for s in room["sources"]["items"]), room["sources"]


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_a_jira_suggestion_without_a_connected_account_is_refused_and_stays_pending(rig: Any, transport: str) -> None:
    hub, _gh, _acli = rig
    pid = _project(hub)
    _suggest(hub, pid)
    if transport == "http":
        resp = hub.client.post(f"/api/projects/{pid}/suggested-sources/PAY-123/add")
        assert resp.status_code == 409, resp.text
        code = resp.json().get("code")
    else:
        is_error, value = hub.mcp("project.add_suggested_source", {"project_id": pid, "reference": "PAY-123"})
        assert is_error is True, value
        code = value.get("code")
    assert code == "jira_connection_required"
    rows = _source_rows(hub, pid)
    assert rows["status"]["PAY-123"] == "pending" and rows["resources"] == [] and rows["watches"] == [], rows


def test_a_jira_suggestion_with_a_connected_account_becomes_a_resource_and_a_watch(rig: Any) -> None:
    hub, _gh, _acli = rig
    from test_philo9_b1_connections import JIRA_EMAIL, JIRA_SITE

    # The account connected through the REAL producers (add, then a recheck the runner answers).
    assert hub.client.post("/api/providers/jira/connections", json={"site": JIRA_SITE, "email": JIRA_EMAIL}).status_code == 200
    assert hub.client.post(f"/api/providers/jira/connections/{JIRA_SITE}|{JIRA_EMAIL}/recheck").status_code == 200
    pid = _project(hub)
    _suggest(hub, pid)
    resp = hub.client.post(f"/api/projects/{pid}/suggested-sources/PAY-123/add")
    assert resp.status_code == 200, resp.text
    rows = _source_rows(hub, pid)
    assert rows["resources"] == ["integration:jira:PAY-123"], rows
    assert [(w["connector_id"], w["state"]) for w in rows["watches"]] == [("jira", "active")], rows
    assert json.loads(rows["watches"][0]["query_json"])["projects"] == ["PAY"]
    assert rows["status"]["PAY-123"] == "accepted"


# ── the residual set: exactly the enumerated identities paid ─────────────

_PAID_HERE = {
    *(("mcp", tool, "") for tool in (
        "project.configure_steward", "project.run_steward", "project.stop_steward", "project.get_steward_run",
        "project.steward.trigger", "steward.nudges", "nudge.send", "nudge.dismiss", "project.watch.inspect",
        "project.watch.test", "project.watch.evaluate", "project.watch.set_rules", "project.watch.pause",
        "project.watch.resume", "project.watch.retire", "project.suggested_sources", "project.add_suggested_source",
        "project.dismiss_suggested_source", "connection.list", "connection.recheck")),
    *(("http", f"holdspeak/web/routes/projects.py::build_projects_router.{fn}", "SuggestedSourceService")
      for fn in ("api_suggested_sources", "api_add_suggested_source", "api_dismiss_suggested_source")),
}


def test_the_residual_set_paid_exactly_the_story_02_identities() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("residual_census", REPO / "scripts" / "residual_census.py")
    census = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(census)
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    paid = {census._key(e) for e in committed["paid"] if e["story"] == "PHILO-9-02"}
    assert len(_PAID_HERE) == 23 and paid == _PAID_HERE
    assert not (paid & {census._key(e) for e in committed["entries"]})
    assert census.check(REPO, committed) == []
    assert committed["measurements"]["residual_identities"] == 240
    assert [a["tool"] for a in committed["public_tools_added"] if a["story"] == "PHILO-9-02"] == ["project.mark_update_delivered"]


# ── F9: no test double in product code ───────────────────────────────────


def _mock_imports(root: Path) -> list[str]:
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            if any(name == "unittest.mock" or name.startswith("unittest.mock.") or name == "mock" for name in names):
                found.append(f"{path.relative_to(root.parent)}:{node.lineno}")
    return found


def test_no_product_module_imports_unittest_mock() -> None:
    assert _mock_imports(REPO / "holdspeak") == []


def test_the_mock_import_fence_turns_red_on_a_mutation(tmp_path: Path) -> None:
    package = tmp_path / "holdspeak"
    package.mkdir()
    (package / "clean.py").write_text("import json\n")
    assert _mock_imports(package) == []
    (package / "mutated.py").write_text("def build():\n    from unittest.mock import MagicMock\n    return MagicMock()\n")
    assert _mock_imports(package) == ["holdspeak/mutated.py:2"]
