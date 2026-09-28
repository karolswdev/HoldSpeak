"""PHILO-9-07: the project delegation grant, fenced through the REAL hub (the owner's Q2 ruling).

Every fence boots the real ``MeetingWebServer`` over an isolated database and
reaches it by its real transports only: the owner's HTTP routes, and an agent
whose PROJECT credential is issued through the real Settings route and used
from a non-loopback host, over ``/api/mcp`` AND over HTTP (the authenticated
principal, handover XXIX law 5). The grant is minted only through the real
``PUT /api/settings/remote/delegations/{identity}/projects/{project_id}``:
never an inserted row. Only the transports and the database are read.

* **The bound** -- run, stop and publish are refused
  ``project_delegation_required`` WITH a receipt before the grant (red on
  main: a P3-style success with zero rows) and execute with a LIVE grant on
  that project, the receipt naming the delegation.
* **Per project and outside the bound** -- a grant on A does nothing on B,
  whatever project_id the caller claims; every owner-only row stays refused
  with the grant; mark delivered, archive and configure_steward in every case.
* **The run's children (R4-1)** -- each child names the grant AND the policy;
  a revoke mid-run refuses the next child with its receipt and ends the run
  refused; an agent cannot stop another actor's run in the same project.
* **The lifecycle** -- revoke, expiry and a credential revoke end the grant
  (the codes move to ``_revoked`` / ``_expired``); a credential reissue keeps
  it (a real restart: ``test_philo9_project_grant_restart.py``).
* **Owner only** -- grant and revoke are admitted with receipts; an agent is
  refused ``owner_principal_required`` with one; no MCP tool reaches them.
* **The wire** -- ``GET /api/settings/remote``: the issued palette name (DESK
  reads DESK, red on main: ALL), each credential's project grants, and the
  project orphans beside Phase 7's desk orphans.
"""
from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402
from test_philo9_steward_admission import (  # noqa: E402
    AGENT_ID, _agent, _meeting, _project, _published, _review, _suggest, _tool,
)

TERMINAL_RUN = {"completed", "failed", "interrupted"}
OTHER_AGENT = "second-project-agent"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(None, None)
    reset_database()
    composition.install(composition.bare(label="pytest"))


# ── the database and the routes ──────────────────────────────────────────


def _ops(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.parent_operation_id,"
            " o.authority_basis, o.delegator_kind, o.delegator_identity, r.outcome AS outcome, r.state AS receipt_state"
            " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid")]


def _op(hub: Hub, operation_id: str) -> dict[str, Any]:
    found = [o for o in _ops(hub) if o["operation_id"] == operation_id]
    assert found, operation_id
    return found[0]


def _grant_rows(hub: Hub, identity: str = AGENT_ID) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM kernel_project_delegations WHERE agent_identity=? ORDER BY created_at, rowid", (identity,))]


def _grant(hub: Hub, pid: str, identity: str = AGENT_ID, **body: Any) -> dict[str, Any]:
    resp = hub.client.put(f"/api/settings/remote/delegations/{identity}/projects/{pid}", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _revoke(hub: Hub, pid: str, identity: str = AGENT_ID) -> Any:
    return hub.client.delete(f"/api/settings/remote/delegations/{identity}/projects/{pid}")


def _policy(hub: Hub, pid: str, **fields: Any) -> dict[str, Any]:
    resp = hub.client.put(f"/api/projects/{pid}/steward/policy", json=fields)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _draft(hub: Hub, pid: str) -> str:
    return hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]


def _lifecycle(hub: Hub, update_id: str) -> str:
    with hub.db._connection() as conn:
        return str(conn.execute("SELECT lifecycle FROM project_updates WHERE id=?", (update_id,)).fetchone()[0])


def _run_row(hub: Hub, run_id: str) -> dict[str, Any]:
    return hub.db.steward_runs.get_run(run_id) or {}


def _ended(hub: Hub, run_id: str, timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = _run_row(hub, run_id)
        if run.get("state") in TERMINAL_RUN and run.get("operation_id"):
            if _op(hub, run["operation_id"])["receipt_state"] is not None:
                return run
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} never ended: {_run_row(hub, run_id)}")


def _basis_grant_id(basis: str) -> str:
    kind, grant_id, _sha = basis.split(":", 2)
    assert kind == "project-delegation", basis
    return grant_id


class Hold:
    """Hold the hub's REAL collector (OBSERVE) until released; its own answer is returned."""

    def __init__(self, hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
        self.entered, self.release = threading.Event(), threading.Event()
        collector = hub.root.project_steward_service._collector
        real = collector.collect_all

        def held(project_id: str) -> Any:
            self.entered.set()
            assert self.release.wait(30), "the hold was never released"
            return real(project_id)

        monkeypatch.setattr(collector, "collect_all", held)


# ── the bound: refused before the grant, executes with it (MCP and HTTP) ──


def _call(agent: Any, transport: str, name: str, ids: dict[str, str]) -> tuple[bool, dict[str, Any]]:
    """One bound operation by the agent over one transport: (refused?, body)."""
    if transport == "mcp":
        args = {"project.run_steward": {"project_id": ids.get("pid")},
                "project.stop_steward": {"run_id": ids.get("run")},
                "project.publish_update": {"update_id": ids.get("update")}}[name]
        return _tool(agent, name, args)
    resp = {"project.run_steward": lambda: agent.post(f"/api/projects/{ids['pid']}/steward/runs", json={}),
            "project.stop_steward": lambda: agent.post(f"/api/steward/runs/{ids['run']}/stop", json={}),
            "project.publish_update": lambda: agent.post(f"/api/updates/{ids['update']}/publish", json={})}[name]()
    body = resp.json()
    if resp.status_code >= 400:
        return True, {**body, "code": body.get("code") or body.get("error")}
    return False, body


def _refused_with_receipt(hub: Hub, body: dict[str, Any], name: str, code: str) -> dict[str, Any]:
    assert body.get("code") == code, body
    assert body.get("operation_id") and body.get("receipt"), f"{name}: a refusal without its receipt: {body}"
    op = _op(hub, body["operation_id"])
    assert (op["name"], op["principal_kind"], op["principal_identity"]) == (name, "agent", AGENT_ID), op
    assert op["outcome"] == code and op["receipt_state"] is not None, op
    return op


@pytest.mark.parametrize("transport", ["mcp", "http"])
def test_run_is_refused_without_a_grant_and_runs_with_one_naming_the_delegation(hub: Hub, transport: str) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    agent = _agent(hub)
    refused, body = _call(agent, transport, "project.run_steward", {"pid": pid})
    assert refused, f"the agent's call succeeded without a grant: {body}"
    _refused_with_receipt(hub, body, "project.run_steward", "project_delegation_required")
    assert hub.db.steward_runs.list_runs(pid, limit=5) == [], "a refused run left a run row"

    granted = _grant(hub, pid)
    refused, body = _call(agent, transport, "project.run_steward", {"pid": pid})
    assert not refused, body
    op = _op(hub, body["operation_id"])
    assert (op["principal_kind"], op["principal_identity"]) == ("agent", AGENT_ID)
    assert _basis_grant_id(op["authority_basis"]) == granted["grant_id"], op
    assert (op["delegator_kind"], op["delegator_identity"]) == ("owner", "owner-session")
    run = _ended(hub, body["run_id"])
    assert run["state"] == "completed" and run["requested_by"] == f"principal:{AGENT_ID}", run
    assert _op(hub, body["operation_id"])["outcome"] == "completed"


@pytest.mark.parametrize("transport", ["mcp", "http"])
def test_publish_is_refused_without_a_grant_and_publishes_with_one(hub: Hub, transport: str) -> None:
    pid = _project(hub)
    update = _draft(hub, pid)
    agent = _agent(hub)
    refused, body = _call(agent, transport, "project.publish_update", {"update": update})
    assert refused, f"the agent's call succeeded without a grant: {body}"
    _refused_with_receipt(hub, body, "project.publish_update", "project_delegation_required")
    assert _lifecycle(hub, update) == "draft"

    granted = _grant(hub, pid)
    refused, body = _call(agent, transport, "project.publish_update", {"update": update})
    assert not refused, body
    assert _lifecycle(hub, update) == "published"
    made = [o for o in _ops(hub) if o["name"] == "project.publish_update" and o["outcome"] == "succeeded"]
    assert len(made) == 1 and made[0]["principal_identity"] == AGENT_ID
    assert _basis_grant_id(made[0]["authority_basis"]) == granted["grant_id"]


@pytest.mark.parametrize("transport", ["mcp", "http"])
def test_stop_of_its_own_run_is_refused_without_the_grant_and_stops_with_it(
    hub: Hub, transport: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    agent = _agent(hub)
    grant = _grant(hub, pid)
    hold = Hold(hub, monkeypatch)
    _refused, started = _call(agent, "mcp", "project.run_steward", {"pid": pid})
    assert hold.entered.wait(10)
    # The grant stops (the owner), then the agent tries to stop its own run.
    assert _revoke(hub, pid).status_code == 200
    refused, body = _call(agent, transport, "project.stop_steward", {"run": started["run_id"]})
    assert refused, f"the agent's call succeeded without a grant: {body}"
    _refused_with_receipt(hub, body, "project.stop_steward", "project_delegation_revoked")
    assert _run_row(hub, started["run_id"])["stop_requested_at"] is None
    hold.release.set()
    run = _ended(hub, started["run_id"])
    # The revoke also cut the run off at its next boundary (R4-1).
    assert run["state"] == "interrupted" and _op(hub, started["operation_id"])["outcome"] == "project_delegation_revoked"

    # A new grant, a new run, and the agent stops it.
    regrant = _grant(hub, pid)
    assert regrant["grant_id"] != grant["grant_id"]
    hold2 = Hold(hub, monkeypatch)
    _refused, again = _call(agent, "mcp", "project.run_steward", {"pid": pid})
    assert hold2.entered.wait(10)
    refused, body = _call(agent, transport, "project.stop_steward", {"run": again["run_id"]})
    assert not refused, body
    stop = [o for o in _ops(hub) if o["name"] == "project.stop_steward" and o["outcome"] == "stop_requested"]
    assert len(stop) == 1 and _basis_grant_id(stop[0]["authority_basis"]) == regrant["grant_id"]
    hold2.release.set()
    run = _ended(hub, again["run_id"])
    assert run["state"] == "interrupted" and _op(hub, again["operation_id"])["outcome"] == "stop_requested"


# ── per project; outside the bound; never grantable ──────────────────────


def test_a_grant_on_project_a_does_nothing_on_project_b(hub: Hub) -> None:
    pid_a, pid_b = _project(hub), _project(hub, "Hiring loop")
    _policy(hub, pid_b, eligible_effect_kinds=["draft_update"])
    update_b = _draft(hub, pid_b)
    agent = _agent(hub)
    _grant(hub, pid_a)
    for transport in ("mcp", "http"):
        refused, body = _call(agent, transport, "project.run_steward", {"pid": pid_b})
        assert refused
        _refused_with_receipt(hub, body, "project.run_steward", "project_delegation_required")
        refused, body = _call(agent, transport, "project.publish_update", {"update": update_b})
        assert refused
        _refused_with_receipt(hub, body, "project.publish_update", "project_delegation_required")
    # A spoofed project argument never reaches the check: the declared schema
    # refuses it (the codec derives the project from the stored update anyway).
    is_error, body = _tool(agent, "project.publish_update", {"update_id": update_b, "project_id": pid_a})
    assert is_error and body.get("code") == "validation" and body.get("receipt"), body
    assert _lifecycle(hub, update_b) == "draft"
    assert hub.db.steward_runs.list_runs(pid_b, limit=5) == []


def test_grants_on_two_projects_each_authorise_their_own_project(hub: Hub) -> None:
    """The admission reads THIS project's LIVE row, never another project's."""
    pid_a, pid_b = _project(hub), _project(hub, "Hiring loop")
    update_a, update_b = _draft(hub, pid_a), _draft(hub, pid_b)
    agent = _agent(hub)
    grant_a, grant_b = _grant(hub, pid_a), _grant(hub, pid_b)
    for update, grant in ((update_b, grant_b), (update_a, grant_a)):
        is_error, body = _tool(agent, "project.publish_update", {"update_id": update})
        assert not is_error, body
        assert _basis_grant_id(_op(hub, body["operation_id"])["authority_basis"]) == grant["grant_id"]
    assert (_lifecycle(hub, update_a), _lifecycle(hub, update_b)) == ("published", "published")


def test_a_granted_agent_cannot_stop_or_publish_project_b_objects_under_a_project_a_grant(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A5: the stored run's and update's project decides, never the grant the caller holds."""
    pid_a, pid_b = _project(hub), _project(hub, "Hiring loop")
    _policy(hub, pid_b, eligible_effect_kinds=["draft_update"])
    agent = _agent(hub)
    _grant(hub, pid_b)
    hold = Hold(hub, monkeypatch)
    _refused, started = _call(agent, "mcp", "project.run_steward", {"pid": pid_b})
    assert hold.entered.wait(10)
    assert _revoke(hub, pid_b).status_code == 200
    _grant(hub, pid_a)  # a LIVE grant, but on A
    refused, body = _call(agent, "mcp", "project.stop_steward", {"run": started["run_id"]})
    assert refused and body["code"] == "project_delegation_revoked", body
    hold.release.set()
    _ended(hub, started["run_id"])


OWNER_ONLY: dict[str, Any] = {
    "archive": ("project.archive", lambda h, i: {"project_id": i["pid"]}),
    "unattended on": ("project.configure_steward", lambda h, i: {"project_id": i["pid"], "unattended_enabled": True}),
    "delivered": ("project.mark_update_delivered", lambda h, i: {"update_id": i["published"]}),
    "resource add": ("project.resource.add", lambda h, i: {"project_id": i["pid"], "resource_ref": i["ref"]}),
    "link": ("project.link", lambda h, i: {"project_id": i["pid"], "meeting_id": i["mid"]}),
    "accept review": ("project.accept_review", lambda h, i: {"project_id": i["pid"], "review_id": i["review"]}),
    "trigger": ("project.steward.trigger", lambda h, i: {}),
    "suggested add": ("project.add_suggested_source", lambda h, i: {"project_id": i["pid"], "reference": "example/payments"}),
    "github recheck": ("connection.recheck", lambda h, i: {"provider_id": "github"}),
    **{f"decide {verb}": ("project.decide_proposal",
                          (lambda verb: lambda h, i: {"project_id": i["pid"], "review_id": i["review"],
                                                      "proposal_id": i["proposal"], "verb": verb,
                                                      **({"deferred_until": "2026-12-01"} if verb == "defer" else {}),
                                                      **({"patch": {"title": "T"}} if verb == "edit_accept" else {})})(verb))
       for verb in ("accept", "edit_accept", "defer", "dismiss")},
}


@pytest.mark.parametrize("path", sorted(OWNER_ONLY))
def test_every_operation_outside_the_bound_stays_refused_with_a_live_grant(hub: Hub, path: str) -> None:
    """Outside the bound: refused with a receipt although a LIVE grant names the project (R4-2 incl.)."""
    name, arguments = OWNER_ONLY[path]
    pid = _project(hub)
    review, proposals = _review(hub, pid, overdue=1)
    note = hub.client.post("/api/notes", json={"title": "Ledger notes"}).json()
    ids = {"pid": pid, "review": review, "proposal": proposals[0], "published": _published(hub, pid),
           "mid": _meeting(hub, "m-owner-only"), "ref": f"note:{(note.get('note') or note).get('id')}"}
    _suggest(hub, pid)
    agent = _agent(hub)
    _grant(hub, pid)
    is_error, body = _tool(agent, name, arguments(hub, ids))
    assert is_error is True and body.get("code") == "project_delegation_required", body
    op = _op(hub, body["operation_id"])
    assert (op["name"], op["principal_identity"], op["outcome"]) == (name, AGENT_ID, "project_delegation_required")


def test_mark_delivered_archive_and_configure_are_refused_for_an_agent_in_every_case(hub: Hub) -> None:
    """Without a grant, with a LIVE grant, after its revoke: always refused, over MCP and HTTP."""
    pid = _project(hub)
    published = _published(hub, pid)
    agent = _agent(hub)
    rows = {
        "project.mark_update_delivered": (lambda: _tool(agent, "project.mark_update_delivered", {"update_id": published}),
                                          lambda: agent.post(f"/api/updates/{published}/delivered", json={})),
        "project.archive": (lambda: _tool(agent, "project.archive", {"project_id": pid}),
                            lambda: agent.delete(f"/api/projects/{pid}")),
        "project.configure_steward": (lambda: _tool(agent, "project.configure_steward",
                                                    {"project_id": pid, "unattended_enabled": True}),
                                      lambda: agent.put(f"/api/projects/{pid}/steward/policy",
                                                        json={"unattended_enabled": True})),
    }
    for phase in ("none", "live", "revoked"):
        if phase == "live":
            _grant(hub, pid)
        if phase == "revoked":
            assert _revoke(hub, pid).status_code == 200
        for name, (mcp, http) in rows.items():
            is_error, body = mcp()
            assert is_error and body["code"] in {"project_delegation_required", "project_delegation_revoked"}, (phase, name, body)
            assert _op(hub, body["operation_id"])["outcome"] == body["code"]
            resp = http()
            assert resp.status_code == 403, (phase, name, resp.text)
            assert resp.json().get("operation_id") and resp.json().get("receipt"), (phase, name, resp.text)
    with hub.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM project_update_deliveries").fetchone()[0] == 0
        assert conn.execute("SELECT lifecycle FROM projects WHERE id=?", (pid,)).fetchone()[0] != "archived"
        assert conn.execute("SELECT COUNT(*) FROM steward_policies WHERE project_id=?", (pid,)).fetchone()[0] == 0


# ── the run's children under the grant AND the policy (R4-1, A1/A2) ──────


def test_an_agent_runs_children_each_naming_the_grant_and_the_policy(hub: Hub) -> None:
    pid = _project(hub)
    meeting = _meeting(hub, "m-agent-run", overdue=1)
    assert hub.client.post(f"/api/projects/{pid}/meetings/{meeting}").status_code == 200
    policy = _policy(hub, pid, eligible_effect_kinds=["create_proposals", "apply_proposal_effects", "draft_update"])
    agent = _agent(hub)
    grant = _grant(hub, pid)
    _refused, started = _call(agent, "mcp", "project.run_steward", {"pid": pid})
    run = _ended(hub, started["run_id"])
    assert run["state"] == "completed", run
    authority = json.loads(run["authority_json"])
    assert authority["grant"]["id"] == grant["grant_id"]
    assert authority["authority_terms"]["grant_id"] == grant["grant_id"]
    children = [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]]
    assert sorted(o["name"] for o in children) == ["project.decide_proposal", "project.steward.effect",
                                                   "project.steward.effect"], children
    for child in children:
        assert (child["principal_kind"], child["principal_identity"]) == ("agent", AGENT_ID)
        assert child["authority_basis"] == f"project-steward:{run['id']}:{authority['authority_sha256']}"
        assert (child["delegator_kind"], child["delegator_identity"]) == ("owner", "owner-session")
        assert child["state"] == "succeeded", child
    # One kernel.receipt answer names both authorities (the agent reads its own).
    is_error, read = _tool(agent, "kernel.receipt", {"operation_id": children[0]["operation_id"]})
    assert not is_error, read
    details = read["objects"][0]["native_receipts"][0]
    assert details["grant_id"] == grant["grant_id"] and details["grant_sha256"]
    assert details["policy_id"] == policy["policy"]["id"] and details["configure_operation_id"] == policy["operation_id"]
    assert details["actor_kind"] == "agent"


def test_a_direct_proposal_decision_stays_refused_although_the_run_may_accept(hub: Hub) -> None:
    """A2: the grant authorises starting a steward, never a direct decision."""
    pid = _project(hub)
    review, proposals = _review(hub, pid, overdue=1)
    agent = _agent(hub)
    _grant(hub, pid)
    is_error, body = _tool(agent, "project.decide_proposal", {"project_id": pid, "review_id": review,
                                                              "proposal_id": proposals[0], "verb": "accept"})
    assert is_error and body["code"] == "project_delegation_required", body


def test_a_revoke_mid_run_refuses_the_next_child_with_its_receipt_and_ends_the_run(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R4-1: the cutoff. The first acceptance is held; the owner revokes; the next child is refused."""
    pid = _project(hub)
    meeting = _meeting(hub, "m-cutoff", overdue=2)
    assert hub.client.post(f"/api/projects/{pid}/meetings/{meeting}").status_code == 200
    _policy(hub, pid, eligible_effect_kinds=["apply_proposal_effects"])
    agent = _agent(hub)
    _grant(hub, pid)
    delta = hub.root.project_steward_service._delta
    real = delta.decide_proposal
    first_done, go_on = threading.Event(), threading.Event()
    calls: list[str] = []

    def decide(*args: Any, **kwargs: Any) -> Any:
        result = real(*args, **kwargs)
        calls.append(str(args[2] if len(args) > 2 else kwargs.get("proposal_id")))
        if len(calls) == 1:
            first_done.set()
            assert go_on.wait(30)
        return result

    monkeypatch.setattr(delta, "decide_proposal", decide)
    _refused, started = _call(agent, "mcp", "project.run_steward", {"pid": pid})
    assert first_done.wait(20), "the run never reached its first acceptance"
    assert _revoke(hub, pid).status_code == 200
    go_on.set()
    run = _ended(hub, started["run_id"])
    assert run["state"] == "interrupted", run
    run_op = _op(hub, started["operation_id"])
    assert (run_op["state"], run_op["outcome"]) == ("refused", "project_delegation_revoked"), run_op
    decides = [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]
               and o["name"] == "project.decide_proposal"]
    assert [o["outcome"] for o in decides] == ["succeeded", "project_delegation_revoked"], decides
    assert all(o["receipt_state"] is not None for o in decides)
    assert len(calls) == 1, "a child ran after the cutoff"


def test_a_revoke_with_no_next_child_still_ends_the_run_refused_and_invents_no_child(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The beat, section 3: authority lost when no next child is attempted ends the parent refused."""
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=[])  # a recorded policy with no effect: no child will follow
    agent = _agent(hub)
    _grant(hub, pid)
    hold = Hold(hub, monkeypatch)
    _refused, started = _call(agent, "mcp", "project.run_steward", {"pid": pid})
    assert hold.entered.wait(10)
    assert _revoke(hub, pid).status_code == 200
    hold.release.set()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"]) == ("interrupted", "refused", "project_delegation_revoked"), op
    assert [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]] == []


def test_an_agent_cannot_stop_another_agents_run_in_the_same_project(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    first = _agent(hub)
    second = _agent(hub, identity=OTHER_AGENT)
    _grant(hub, pid)
    _grant(hub, pid, OTHER_AGENT)
    hold = Hold(hub, monkeypatch)
    _refused, started = _call(first, "mcp", "project.run_steward", {"pid": pid})
    assert hold.entered.wait(10)
    is_error, body = _tool(second, "project.stop_steward", {"run_id": started["run_id"]})
    assert is_error and body["code"] == "steward_run_owner_required", body
    assert _op(hub, body["operation_id"])["outcome"] == "steward_run_owner_required"
    resp = second.post(f"/api/steward/runs/{started['run_id']}/stop", json={})
    assert resp.status_code == 403 and resp.json()["code"] == "steward_run_owner_required", resp.text
    assert _run_row(hub, started["run_id"])["stop_requested_at"] is None
    hold.release.set()
    assert _ended(hub, started["run_id"])["state"] == "completed"


# ── the lifecycle: revoke, expiry, credential revoke, reissue ────────────


def test_revoke_and_expiry_move_the_code(hub: Hub) -> None:
    pid = _project(hub)
    update = _draft(hub, pid)
    agent = _agent(hub)
    _grant(hub, pid)
    assert _revoke(hub, pid).status_code == 200
    is_error, body = _tool(agent, "project.publish_update", {"update_id": update})
    assert is_error and body["code"] == "project_delegation_revoked", body
    op = _op(hub, body["operation_id"])
    assert op["authority_basis"].startswith("project-delegation:"), "the refusal names the historical grant"
    # Expiry: a real past-due expires_at on the kernel's own clock.
    _grant(hub, pid, expires_at=time.time() + 1.0)
    time.sleep(1.3)
    assert _grant_rows(hub)[-1]["state"] == "LIVE", "the stored row is still LIVE; the kernel projects it"
    is_error, body = _tool(agent, "project.publish_update", {"update_id": update})
    assert is_error and body["code"] == "project_delegation_expired", body
    assert _lifecycle(hub, update) == "draft"


def test_a_revoke_with_no_live_grant_is_refused_with_its_receipt(hub: Hub) -> None:
    pid = _project(hub)
    resp = _revoke(hub, pid)
    assert resp.status_code == 409 and resp.json()["error"] == "project_delegation_required", resp.text
    op = _op(hub, resp.json()["operation_id"])
    assert (op["name"], op["outcome"]) == ("project.delegation.revoke", "project_delegation_required")


def test_the_owners_credential_revoke_ends_the_project_grants_first_and_a_reissue_keeps_a_live_grant(hub: Hub) -> None:
    pid_a, pid_b = _project(hub), _project(hub, "Hiring loop")
    update = _draft(hub, pid_a)
    _agent(hub)
    _grant(hub, pid_a)
    _grant(hub, pid_b)
    # A reissue (same identity, new token) keeps the LIVE grant: identity-keyed.
    agent = _agent(hub)
    wire = hub.client.get("/api/settings/remote").json()
    [cred] = [c for c in wire["credentials"] if c["identity"] == AGENT_ID]
    assert sorted((g["project_name"], g["state"]) for g in cred["project_delegations"]) == [
        ("Hiring loop", "LIVE"), ("Payments ledger cutover", "LIVE")]
    is_error, body = _tool(agent, "project.publish_update", {"update_id": update})
    assert not is_error, body
    # The owner revokes the credential: both grants end FIRST, each with its receipt.
    resp = hub.client.delete(f"/api/settings/remote/credentials/{cred['id']}")
    assert resp.status_code == 200, resp.text
    ended = resp.json()["project_grants_revoked"]
    assert sorted(e["project_name"] for e in ended) == ["Hiring loop", "Payments ledger cutover"]
    for entry in ended:
        op = _op(hub, entry["operation_id"])
        assert (op["name"], op["outcome"]) == ("project.delegation.revoke", "succeeded")
        assert entry["reason"] == "credential_revoked"
    assert [(r["state"], r["revocation_reason"]) for r in _grant_rows(hub)] == [
        ("REVOKED", "credential_revoked"), ("REVOKED", "credential_revoked")]
    wire = hub.client.get("/api/settings/remote").json()
    assert wire["project_delegations"] == [], "an owner revoke left an orphan"


def test_the_grant_operations_are_owner_only_admitted_and_in_no_palette(hub: Hub) -> None:
    pid = _project(hub)
    agent = _agent(hub, palette="ALL")
    granted = _grant(hub, pid)
    op = _op(hub, granted["operation_id"])
    assert (op["name"], op["principal_kind"], op["outcome"]) == ("project.delegation.grant", "owner", "succeeded")
    assert granted["receipt"]["result_ref"] == f"project-delegation:{granted['grant_id']}"
    for method in ("put", "delete"):
        resp = getattr(agent, method)(f"/api/settings/remote/delegations/{AGENT_ID}/projects/{pid}",
                                      **({"json": {}} if method == "put" else {}))
        assert resp.status_code == 403 and resp.json()["error"] == "owner_principal_required", resp.text
        refused = _op(hub, resp.json()["operation_id"])
        assert refused["principal_identity"] == AGENT_ID and refused["outcome"] == "owner_principal_required"
    assert _grant_rows(hub)[-1]["state"] == "LIVE", "the agent's revoke attempt changed the grant"
    resp = agent.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in resp.json()["result"]["tools"]}
    assert not [n for n in names if "delegation" in n], "a grant operation is reachable over MCP"


def test_a_malformed_grant_body_and_an_unknown_project_are_refused_with_receipts(hub: Hub) -> None:
    pid = _project(hub)
    bad = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}/projects/{pid}", json={"operations": ["x"]})
    assert bad.status_code == 400 and bad.json()["error"] == "invalid_arguments", bad.text
    missing = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}/projects/proj-nope", json={})
    assert missing.status_code == 404 and missing.json()["error"] == "not_found", missing.text
    for resp in (bad, missing):
        assert _op(hub, resp.json()["operation_id"])["name"] == "project.delegation.grant"
    assert _grant_rows(hub) == []


# ── the wire: the issued palette name; project grants; orphans ───────────


def test_a_desk_credential_reads_back_desk(hub: Hub) -> None:
    """The DESK = ALL repair (BACKLOG "PHILO-7-02 canvas follow-ups"). Red on main: ALL."""
    _agent(hub, palette="DESK", identity="desk-agent")
    _agent(hub, palette="ALL", identity="all-agent")
    wire = hub.client.get("/api/settings/remote").json()
    palettes = {c["identity"]: c["palette"] for c in wire["credentials"]}
    assert palettes == {"desk-agent": "DESK", "all-agent": "ALL"}, palettes


def test_the_wire_projects_each_grant_and_lists_project_orphans_beside_desk_orphans(hub: Hub) -> None:
    pid = _project(hub)
    agent = _agent(hub, palette="DESK", identity="desk-agent")
    _agent(hub)
    _grant(hub, pid)
    assert hub.client.put("/api/settings/remote/delegations/desk-agent", json={}).status_code == 200
    # Both credentials lost with their grants still LIVE (never an owner revoke).
    for identity in ("desk-agent", AGENT_ID):
        hub.server.app.state.agent_credentials.revoke(identity)
    assert hub.client.put("/api/settings/remote", json={"enabled": False}).status_code == 200
    wire = hub.client.get("/api/settings/remote").json()
    assert wire["credentials"] == []
    assert [d["identity"] for d in wire["delegations"]] == ["desk-agent"]
    [orphan] = wire["project_delegations"]
    assert (orphan["identity"], orphan["project_id"], orphan["project_name"], orphan["state"]) == (
        AGENT_ID, pid, "Payments ledger cutover", "LIVE")
    # The owner stops the orphan: it leaves the wire, its receipt stays.
    stopped = _revoke(hub, pid)
    assert stopped.status_code == 200
    assert hub.client.get("/api/settings/remote").json()["project_delegations"] == []
    assert _op(hub, stopped.json()["operation_id"])["outcome"] == "succeeded"
    del agent


# ── round three (Codex Astra r1 finding 1): stop binds the stored actor KIND and identity ──


def _stop_both(agent: Any, run_id: str) -> list[tuple[bool, dict[str, Any]]]:
    return [_call(agent, "mcp", "project.stop_steward", {"run": run_id}),
            _call(agent, "http", "project.stop_steward", {"run": run_id})]


def test_an_agent_named_like_the_owner_cannot_stop_the_owners_run(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """A PROJECT credential named ``owner-session`` with a real grant: the owner's run is not its run."""
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    impostor = _agent(hub, identity="owner-session")
    _grant(hub, pid, "owner-session")
    hold = Hold(hub, monkeypatch)
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={}).json()
    assert hold.entered.wait(10)
    for refused, body in _stop_both(impostor, started["run_id"]):
        assert refused and body["code"] == "steward_run_owner_required", body
        assert _op(hub, body["operation_id"])["outcome"] == "steward_run_owner_required"
    assert _run_row(hub, started["run_id"])["stop_requested_at"] is None, "an agent stopped the owner's run"
    hold.release.set()
    assert _ended(hub, started["run_id"])["state"] == "completed"


def test_an_agent_named_like_the_scheduler_cannot_stop_the_schedulers_run(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from test_philo9_steward_lifecycle import _due_effect

    pid = _project(hub)
    _policy(hub, pid, unattended_enabled=True, eligible_effect_kinds=["draft_update"])
    _due_effect(hub, pid)
    impostor = _agent(hub, identity="local-steward-conductor")
    _grant(hub, pid, "local-steward-conductor")
    hold = Hold(hub, monkeypatch)
    outcomes: list[Any] = []
    runner = threading.Thread(target=lambda: outcomes.extend(hub.root.project_steward_service.run_due(
        Principal(PrincipalKind.SCHEDULER, "local-steward-conductor"))), daemon=True)
    runner.start()
    assert hold.entered.wait(10)
    [run] = hub.db.steward_runs.list_runs(pid, limit=5)
    assert _op(hub, run["operation_id"])["principal_kind"] == "scheduler"
    for refused, body in _stop_both(impostor, run["id"]):
        assert refused and body["code"] == "steward_run_owner_required", body
    assert _run_row(hub, run["id"])["stop_requested_at"] is None, "an agent stopped the scheduler's run"
    hold.release.set()
    runner.join(30)
    assert _ended(hub, run["id"])["state"] == "completed"
