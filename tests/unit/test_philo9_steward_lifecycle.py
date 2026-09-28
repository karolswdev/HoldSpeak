"""PHILO-9-02: the steward's lifecycle and its children's authority (the RATIFIED beat), in one hub.

``docs/internal/philo/phase-9/steward-beat/README.md`` section 7 names the
fences; these are the ones one process can prove (L6, the real restart, is
``test_philo9_steward_restart.py``). Every fence boots the real hub over an
isolated database and reaches it through HTTP and ``/api/mcp``; a run is held
in a REAL phase by holding its real collector (a hold, never a lying double:
the collector's own answer is returned once released). Only public transports
and the database are read.

* **L1** a start returns the run AND its operation at once; the operation is
  non-terminal while the run works; one run and one operation for a command
  key under concurrent replay.
* **L2** a second start while a run is active: ``active_run_exists``, its own
  refused receipt, and no spare queued run.
* **L3** each end -- completed, failed, stopped, disabled, cooling down, an
  unknown project -- leaves the mapped run state and exactly ONE receipt; a
  fault inside the terminal transaction rolls all of it back.
* **L4** stop against completion: one winner, both directions.
* **L5** stop is its own admitted operation with its own receipt; a stop
  between two proposal acceptances prevents the second.
* **L7 / F20** COMPARE and proposal creation record the review ``open_review``
  returned.
* **A1** each executed effect is a CHILD of the run (the run's actor, the
  run's frozen authority); ``kernel.receipt`` names the policy; a forged child
  is refused.
* **A4** a changed or disabled policy cuts the run off at its next child; an
  identical re-save does not; a first policy saved during a no-policy owner run
  does not stop it.
* **A6** the scheduler's run acts as SCHEDULER under the owner's recorded
  policy; without a recorded policy it is refused ``steward_policy_required``;
  the trigger returns its pending handle and its runs are its children.
* **R4-1** an agent's stop of the owner's run is refused
  ``steward_run_owner_required`` with a receipt.
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
from test_philo9_steward_admission import _agent, _meeting, _tool  # noqa: E402

TERMINAL_RUN = {"completed", "failed", "interrupted"}


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


def _project(hub: Hub, name: str = "Payments ledger cutover") -> str:
    return hub.client.post("/api/projects", json={"name": name}).json()["project"]["id"]


def _op(hub: Hub, operation_id: str) -> dict[str, Any]:
    with hub.db._connection() as conn:
        row = conn.execute(
            "SELECT o.*, r.outcome AS outcome, r.state AS receipt_state FROM kernel_operations o"
            " LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id WHERE o.operation_id=?",
            (operation_id,)).fetchone()
        receipts = conn.execute("SELECT COUNT(*) FROM kernel_receipts WHERE operation_id=?", (operation_id,)).fetchone()[0]
    assert row is not None, operation_id
    return {**dict(row), "receipts": receipts}


def _ops(hub: Hub, name: str | None = None) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        rows = conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.parent_operation_id,"
            " o.authority_basis, o.delegator_kind, o.delegator_identity, r.outcome AS outcome"
            " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid").fetchall()
    return [dict(r) for r in rows if name is None or r["name"] == name]


def _run_row(hub: Hub, run_id: str) -> dict[str, Any]:
    return hub.db.steward_runs.get_run(run_id) or {}


def _ended(hub: Hub, run_id: str, timeout: float = 30.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = _run_row(hub, run_id)
        if run.get("state") in TERMINAL_RUN and run.get("operation_id"):
            op = _op(hub, run["operation_id"])
            if op["receipt_state"] is not None:
                return run
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} never ended: {_run_row(hub, run_id)}")


def _start(hub: Hub, pid: str, body: dict[str, Any] | None = None) -> Any:
    return hub.client.post(f"/api/projects/{pid}/steward/runs", json=body or {})


def _policy(hub: Hub, pid: str, **fields: Any) -> dict[str, Any]:
    resp = hub.client.put(f"/api/projects/{pid}/steward/policy", json=fields)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── L1: the pending handle ───────────────────────────────────────────────


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_l1_a_start_returns_the_run_and_its_operation_non_terminal_while_it_works(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, transport: str,
) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    if transport == "http":
        resp = _start(hub, pid)
        assert resp.status_code == 200, resp.text
        started = resp.json()
    else:
        is_error, started = hub.mcp("project.run_steward", {"project_id": pid})
        assert is_error is False, started
    assert started["run_id"] and started["operation_id"] and started["receipt"] is None
    assert hold.entered.wait(10)
    run = _run_row(hub, started["run_id"])
    assert run["operation_id"] == started["operation_id"] and run["state"] == "running"
    op = _op(hub, started["operation_id"])
    assert (op["name"], op["state"], op["receipts"]) == ("project.run_steward", "claimed", 0)
    polled = hub.client.get(f"/api/steward/runs/{started['run_id']}").json()
    assert polled["operation_id"] == started["operation_id"] and polled["receipt"] is None
    hold.release.set()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"], op["receipts"]) == ("completed", "succeeded", "completed", 1)
    assert hub.client.get(f"/api/steward/runs/{started['run_id']}").json()["receipt"]["state"] == "succeeded"


def test_l1_one_run_and_one_operation_for_a_command_key_under_concurrent_replay(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    answers: list[Any] = [None, None, None]
    start = threading.Barrier(3)

    def go(index: int) -> None:
        start.wait(5)
        answers[index] = _start(hub, pid, {"command_id": "run-once-1"})

    threads = [threading.Thread(target=go, args=(i,)) for i in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert [a.status_code for a in answers] == [200, 200, 200], [a.text for a in answers]
    assert len({a.json()["run_id"] for a in answers}) == 1
    assert len({a.json()["operation_id"] for a in answers}) == 1
    hold.release.set()
    _ended(hub, answers[0].json()["run_id"])
    assert len(hub.db.steward_runs.list_runs(pid)) == 1
    assert len(_ops(hub, "project.run_steward")) == 1


# ── L2: one active run ───────────────────────────────────────────────────


def test_l2_a_second_start_is_refused_with_its_own_receipt_and_no_spare_queued_run(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    first = _start(hub, pid).json()
    assert hold.entered.wait(10)
    second = _start(hub, pid)
    assert second.status_code == 409, second.text
    body = second.json()
    assert body["code"] == "active_run_exists" and body["receipt"]["outcome"] == "active_run_exists"
    assert _op(hub, body["operation_id"])["state"] == "refused"
    assert [r["id"] for r in hub.db.steward_runs.list_runs(pid)] == [first["run_id"]]  # no spare queued row
    hold.release.set()
    _ended(hub, first["run_id"])


# ── L3: each end, exactly one receipt ────────────────────────────────────


def test_l3_a_known_failure_ends_the_run_failed_with_one_receipt(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    pid = _project(hub)
    delta = hub.root.project_steward_service._delta

    def broken(principal: Any, project_id: str) -> Any:
        raise RuntimeError("the review could not open")

    monkeypatch.setattr(delta, "open_review", broken)
    started = _start(hub, pid).json()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"], op["receipts"]) == ("failed", "failed", "RuntimeError", 1)


@pytest.mark.parametrize("case", ["disabled", "cooldown", "unknown project"])
def test_l3_a_refused_start_has_its_receipt_and_no_run(hub: Hub, case: str) -> None:
    pid = _project(hub)
    if case == "disabled":
        _policy(hub, pid, enabled=False)
    if case == "cooldown":
        _policy(hub, pid, cooldown_seconds=3600)
        _ended(hub, _start(hub, pid).json()["run_id"])
    runs_before = len(hub.db.steward_runs.list_runs(pid))
    resp = _start(hub, "proj-none" if case == "unknown project" else pid)
    code = {"disabled": "steward_disabled", "cooldown": "cooldown_active", "unknown project": "not_found"}[case]
    assert resp.status_code in (404, 409), resp.text
    body = resp.json()
    assert body["code"] == code and body["receipt"]["outcome"] == code, body
    assert _op(hub, body["operation_id"])["receipts"] == 1
    assert len(hub.db.steward_runs.list_runs(pid)) == runs_before


def test_l3_a_fault_inside_the_terminal_transaction_rolls_all_three_writes_back(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.db.steward import StewardRunRepository

    pid = _project(hub)
    real = StewardRunRepository.update_run_state_in_transaction
    faulted = threading.Event()

    def fault(self: Any, conn: Any, run_id: str, **kwargs: Any) -> Any:
        real(self, conn, run_id, **kwargs)
        if kwargs.get("state") in TERMINAL_RUN:
            faulted.set()
            raise RuntimeError("injected inside the terminal transaction")

    monkeypatch.setattr(StewardRunRepository, "update_run_state_in_transaction", fault)
    started = _start(hub, pid).json()
    assert faulted.wait(20)
    time.sleep(0.3)
    run, op = _run_row(hub, started["run_id"]), _op(hub, started["operation_id"])
    assert run["state"] not in TERMINAL_RUN, run  # the run row rolled back
    assert (op["state"], op["receipts"]) == ("claimed", 0), op  # no terminal state, no receipt


# ── L4 + L5: stop ────────────────────────────────────────────────────────


def test_l5_stop_is_its_own_operation_and_the_run_ends_cancelled_with_its_own_receipt(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    stopped = hub.client.post(f"/api/steward/runs/{started['run_id']}/stop", json={})
    assert stopped.status_code == 200, stopped.text
    stop_op = _op(hub, stopped.json()["operation_id"])
    assert (stop_op["name"], stop_op["state"], stop_op["outcome"]) == ("project.stop_steward", "succeeded", "stop_requested")
    assert _op(hub, started["operation_id"])["receipts"] == 0  # stop requested, not stopped
    hold.release.set()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"], op["receipts"]) == ("interrupted", "cancelled", "stop_requested", 1)


def test_l4_a_stop_committed_before_completion_wins(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """The stop commits between the run's last boundary check and its completion callback."""
    service = hub.root.project_steward_service
    pid = _project(hub)
    real_close = service._close_run
    injected: list[Any] = []

    def close_after_a_stop(handle: Any, run_id: str, run_state: str, kernel_state: str, outcome: str,
                           summary: dict[str, Any]) -> None:
        if kernel_state == "succeeded" and not injected:
            injected.append(hub.client.post(f"/api/steward/runs/{run_id}/stop", json={}))
        real_close(handle, run_id, run_state, kernel_state, outcome, summary)

    monkeypatch.setattr(service, "_close_run", close_after_a_stop)
    started = _start(hub, pid).json()
    run = _ended(hub, started["run_id"])
    assert injected and injected[0].status_code == 200, injected
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"], op["receipts"]) == ("interrupted", "cancelled", "stop_requested", 1)


def test_l4_a_completion_committed_before_a_stop_wins_and_the_stop_is_refused(hub: Hub) -> None:
    pid = _project(hub)
    started = _start(hub, pid).json()
    run = _ended(hub, started["run_id"])
    assert run["state"] == "completed"
    late = hub.client.post(f"/api/steward/runs/{started['run_id']}/stop", json={})
    assert late.status_code == 409, late.text
    assert late.json()["code"] == "steward_run_already_terminal"
    assert _op(hub, late.json()["operation_id"])["outcome"] == "steward_run_already_terminal"
    assert _run_row(hub, started["run_id"])["state"] == "completed"
    op = _op(hub, started["operation_id"])
    assert (op["state"], op["receipts"]) == ("succeeded", 1)


def test_l5_a_stop_between_two_proposal_acceptances_prevents_the_second(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    meeting = _meeting(hub, "m-l5", overdue=2)
    assert hub.client.post(f"/api/projects/{pid}/meetings/{meeting}").status_code == 200
    _policy(hub, pid, eligible_effect_kinds=["apply_proposal_effects"])
    delta = hub.root.project_steward_service._delta
    real = delta.decide_proposal
    first_done, go_on = threading.Event(), threading.Event()
    decided: list[str] = []

    def decide(principal: Any, project_id: str, proposal_id: str, verb: str, **kwargs: Any) -> Any:
        result = real(principal, project_id, proposal_id, verb, **kwargs)
        decided.append(proposal_id)
        if len(decided) == 1:
            first_done.set()
            assert go_on.wait(20)
        return result

    monkeypatch.setattr(delta, "decide_proposal", decide)
    started = _start(hub, pid).json()
    assert first_done.wait(20)
    assert hub.client.post(f"/api/steward/runs/{started['run_id']}/stop", json={}).status_code == 200
    go_on.set()
    run = _ended(hub, started["run_id"])
    assert len(decided) == 1, decided
    children = [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]]
    assert [(o["name"], o["state"]) for o in children if o["name"] == "project.decide_proposal"] == [
        ("project.decide_proposal", "succeeded")]
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"]) == ("interrupted", "cancelled", "stop_requested")


# ── L7 / F20: the review COMPARE opened ──────────────────────────────────


def test_l7_compare_and_proposal_creation_record_the_review_open_review_returned(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["create_proposals"])
    delta = hub.root.project_steward_service._delta
    real = delta.open_review
    returned: list[str] = []

    def recorded(principal: Any, project_id: str) -> Any:
        review = real(principal, project_id)
        returned.append(review["review_id"])  # the REAL producer's answer, recorded
        return review

    monkeypatch.setattr(delta, "open_review", recorded)
    started = _start(hub, pid).json()
    deadline = time.monotonic() + 30  # the run's own end (this fence reads no operation: it runs on main)
    while _run_row(hub, started["run_id"]).get("state") not in TERMINAL_RUN and time.monotonic() < deadline:
        time.sleep(0.05)
    steps = hub.client.get(f"/api/steward/runs/{started['run_id']}").json()["steps"]
    compare = next(s for s in steps if s["phase"] == "compare")
    assert returned and compare["observed"]["review_id"] == returned[0], (returned, compare["observed"])
    created = next(s for s in steps if s["effect_kind"] == "create_proposals")
    assert created["observed"]["review_id"] == returned[1]


# ── A1: each executed effect is a child of the run ───────────────────────


def test_a1_each_executed_effect_is_a_child_with_the_runs_actor_and_frozen_authority(hub: Hub) -> None:
    pid = _project(hub)
    meeting = _meeting(hub, "m-a1", overdue=1)
    assert hub.client.post(f"/api/projects/{pid}/meetings/{meeting}").status_code == 200
    policy = _policy(hub, pid, eligible_effect_kinds=["create_proposals", "apply_proposal_effects", "draft_update"])
    started = _start(hub, pid).json()
    run = _ended(hub, started["run_id"])
    authority = json.loads(run["authority_json"])
    children = [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]]
    assert sorted(o["name"] for o in children) == ["project.decide_proposal", "project.steward.effect",
                                                   "project.steward.effect"], children
    for child in children:
        assert (child["principal_kind"], child["principal_identity"]) == ("owner", "owner-session")
        assert child["authority_basis"] == f"project-steward:{run['id']}:{authority['authority_sha256']}"
        assert child["state"] == "succeeded"
    assert authority["policy_id"] == policy["policy"]["id"]
    assert authority["configure_operation_id"] == policy["operation_id"]
    read = hub.mcp("kernel.receipt", {"operation_id": children[0]["operation_id"]})[1]
    details = read["objects"][0]["native_receipts"][0]
    assert details["kind"] == "authority_details" and details["run_id"] == run["id"]
    assert details["policy_id"] == policy["policy"]["id"] and details["configure_operation_id"] == policy["operation_id"]
    assert details["delegator_identity"] == "owner-session" and details["grant_id"] is None


def test_a1_a_forged_child_is_refused_with_a_receipt(hub: Hub) -> None:
    pid = _project(hub)
    started = _start(hub, pid).json()
    _ended(hub, started["run_id"])
    forged = hub.client.post("/api/kernel/submit", json={
        "request_schema": 1, "request_id": "forged-1", "idempotency_key": "forged-1",
        "operation": {"name": "project.steward.effect", "version": 1}, "target": {"ref": f"steward_run:{started['run_id']}"},
        "arguments": {"native_id": "3b241101-e2bb-4255-8caf-4136c566a962", "payload": {"effect_kind": "draft_update"}},
        "placement": "node:hub-project-writer", "parent_operation_id": started["operation_id"],
    })
    assert forged.status_code in (200, 202), forged.text
    body = forged.json()
    assert body["state"] == "refused" and body["receipt"]["outcome"] in {
        "project_operation_service_required", "parent_operation_not_running"}, body


# ── A4: the policy cuts a run off at its next child ──────────────────────


def test_a4_a_changed_policy_refuses_the_next_child_and_the_run_ends_refused(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["create_proposals", "draft_update"])
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    _policy(hub, pid, max_actions_per_run=3)  # the terms changed mid-run
    hold.release.set()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["state"], op["outcome"]) == ("interrupted", "refused", "steward_policy_changed")
    assert [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]] == []


def test_a4_an_identical_re_save_does_not_stop_the_run(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])  # the same terms, a new owner operation
    hold.release.set()
    run = _ended(hub, started["run_id"])
    assert run["state"] == "completed" and _op(hub, started["operation_id"])["outcome"] == "completed"


def test_a4_a_first_policy_saved_during_a_no_policy_owner_run_does_not_stop_it(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    hold.release.set()
    run = _ended(hub, started["run_id"])
    assert run["state"] == "completed", run
    assert json.loads(run["authority_json"])["policy_sha256"] == ""
    assert [o for o in _ops(hub) if o["parent_operation_id"] == started["operation_id"]] == []  # no effect enlarged


def test_a4_a_disabled_policy_cuts_the_run_off(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    pid = _project(hub)
    _policy(hub, pid, eligible_effect_kinds=["draft_update"])
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    _policy(hub, pid, enabled=False)
    hold.release.set()
    run = _ended(hub, started["run_id"])
    op = _op(hub, started["operation_id"])
    assert (run["state"], op["outcome"]) == ("interrupted", "steward_disabled")


# ── A6: the scheduler and the trigger ────────────────────────────────────


def _due_effect(hub: Hub, pid: str, suffix: str = "1") -> None:
    """A pending steward run effect, as a watch evaluation records it."""
    with hub.db._connection() as conn:
        conn.execute("INSERT INTO connector_watches (id, connector_id, query_kind, name, query_json, enabled, project_id,"
                     " state) VALUES (?, 'gh', 'pull_requests', 'PRs', '{}', 1, ?, 'active')", (f"w-{suffix}", pid))
        conn.execute("INSERT INTO watch_rules (id, watch_id, ordinal, condition_schema, condition_json, action_schema,"
                     " action_json, enabled, revision) VALUES (?, ?, 0, 'WatchCondition@1', '{}', 'WatchAction@1', '[]',"
                     " 1, 0)", (f"r-{suffix}", f"w-{suffix}"))
        conn.execute("INSERT INTO watch_evaluations (id, watch_id, watch_revision, source_revision, trigger_kind, state)"
                     " VALUES (?, ?, 0, ?, 'scheduled', 'completed')", (f"e-{suffix}", f"w-{suffix}", f"rev-{suffix}"))
        conn.execute("INSERT INTO watch_effects (id, evaluation_id, rule_id, action_kind, idempotency_key, state)"
                     " VALUES (?, ?, ?, 'project.steward.run_once', ?, 'pending')",
                     (f"eff-{suffix}", f"e-{suffix}", f"r-{suffix}", f"idem-{suffix}"))


def test_a6_a_scheduled_run_acts_as_the_scheduler_under_the_recorded_policy(hub: Hub) -> None:
    from holdspeak.principals import Principal, PrincipalKind

    pid = _project(hub)
    policy = _policy(hub, pid, unattended_enabled=True, eligible_effect_kinds=["draft_update"])
    _due_effect(hub, pid)
    outcomes = hub.root.project_steward_service.run_due(Principal(PrincipalKind.SCHEDULER, "local-steward-conductor"))
    assert [o["outcome"] for o in outcomes] == ["run_started"], outcomes
    run = _ended(hub, outcomes[0]["run_id"])
    op = _op(hub, run["operation_id"])
    assert (op["principal_kind"], op["principal_identity"]) == ("scheduler", "local-steward-conductor")
    assert op["authority_basis"].startswith(f"project-steward-policy:{policy['policy']['id']}:")
    assert (op["delegator_kind"], op["delegator_identity"]) == ("owner", "owner-session")
    assert (run["state"], op["state"]) == ("completed", "succeeded")
    children = [o for o in _ops(hub) if o["parent_operation_id"] == op["operation_id"]]
    assert [(c["name"], c["principal_kind"], c["state"]) for c in children] == [
        ("project.steward.effect", "scheduler", "succeeded")]


def test_a6_a_scheduled_run_without_a_recorded_policy_is_refused_steward_policy_required(hub: Hub) -> None:
    from holdspeak.principals import Principal, PrincipalKind

    pid = _project(hub)
    with hub.db._connection() as conn:  # a policy no owner operation recorded (from before this story)
        conn.execute("INSERT INTO steward_policies (id, project_id, enabled, unattended_enabled) VALUES ('pol-old', ?, 1, 1)",
                     (pid,))
    _due_effect(hub, pid)
    outcomes = hub.root.project_steward_service.run_due(Principal(PrincipalKind.SCHEDULER, "local-steward-conductor"))
    assert [(o["outcome"], o["code"]) for o in outcomes] == [("refused", "steward_policy_required")], outcomes
    op = _op(hub, outcomes[0]["operation_id"])
    assert (op["principal_kind"], op["state"], op["outcome"]) == ("scheduler", "refused", "steward_policy_required")
    assert hub.db.steward_runs.list_runs(pid) == []


def test_a6_the_trigger_returns_its_pending_handle_and_its_runs_are_its_children(hub: Hub) -> None:
    import holdspeak.workbench_conductor as conductor

    pid = _project(hub)
    _policy(hub, pid, unattended_enabled=True)
    _due_effect(hub, pid)
    conductor.set_scheduler_services(hub.root.watch_service, hub.root.project_steward_service)
    resp = hub.client.post("/api/steward/trigger", json={})
    assert resp.status_code == 200, resp.text
    handle = resp.json()
    assert handle["operation_id"] and handle["state"] in {"claimed", "succeeded"}
    deadline = time.monotonic() + 30
    while _op(hub, handle["operation_id"])["receipt_state"] is None and time.monotonic() < deadline:
        time.sleep(0.05)
    trigger = _op(hub, handle["operation_id"])
    assert trigger["state"] == "succeeded" and json.loads(trigger["outcome"])["runs"] == ["run_started"]
    runs = [o for o in _ops(hub, "project.run_steward") if o["parent_operation_id"] == handle["operation_id"]]
    assert [(r["principal_kind"], r["state"]) for r in runs] == [("owner", "succeeded")]


# ── R4-1: stop is bound to the stored run's requester ────────────────────


def test_r4_1_an_agents_stop_of_the_owners_run_is_refused_with_a_receipt(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    pid = _project(hub)
    hold = Hold(hub, monkeypatch)
    started = _start(hub, pid).json()
    assert hold.entered.wait(10)
    agent = _agent(hub)
    is_error, refused = _tool(agent, "project.stop_steward", {"run_id": started["run_id"]})
    assert is_error is True and refused["code"] == "steward_run_owner_required", refused
    assert _op(hub, refused["operation_id"])["outcome"] == "steward_run_owner_required"
    http = agent.post(f"/api/steward/runs/{started['run_id']}/stop", json={})
    assert http.status_code == 403 and http.json()["code"] == "steward_run_owner_required", http.text
    assert _run_row(hub, started["run_id"])["stop_requested_at"] is None
    hold.release.set()
    assert _ended(hub, started["run_id"])["state"] == "completed"
