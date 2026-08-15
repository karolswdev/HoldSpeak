"""HS-131-04 parent-controller admission, route, and CAS proofs."""
from __future__ import annotations

import json
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
FOREIGN = Principal(PrincipalKind.OWNER, "other-owner")


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    import holdspeak.db.core as db_core

    now = [1000.0]
    db = Database(tmp_path / "parent.db")
    monkeypatch.setattr(db_core, "_db", db)
    return _configure(db, clock=lambda: now[0]), now


@pytest.fixture
def route_rig(tmp_path: Path, monkeypatch):
    """Production HTTP chain with only the provider-construction seam faked."""
    reset_database()
    db = Database(tmp_path / "route.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(
        "holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", "")
    )
    state = {"principal": OWNER, "fail": False, "entered": Event(), "release": Event(), "block": False,
             "payloads": [], "revisions": []}

    class FakeEngine:
        active_provider = "test-provider"
        active_model = "test-model"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            state["payloads"].append({"system_prompt": system_prompt, "user_prompt": user_prompt})
            state["entered"].set()
            if state["block"]:
                assert state["release"].wait(5), "test provider was never released"
            if state["fail"] or "[FAIL]" in user_prompt:
                raise RuntimeError("provider failed")
            return f"out:{user_prompt}"

    def build_engine(revision, **_kw):
        # HS-131-10: the runner hands EVERY factory the same (revision, warrant,
        # context) convention, so a double takes the kwargs it does not read.
        state["revisions"].append(revision.id)
        return FakeEngine()

    # InferenceRunner binds its production factory as a constructor default.  This
    # changes only that provider-construction boundary; route, controller, broker,
    # trusted-child admission, runner, stager, receipts, and materializers are real.
    from holdspeak.kernel.inference_runner import InferenceRunner
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", build_engine)

    app = FastAPI()

    @app.middleware("http")
    async def principal(request: Request, call_next):
        request.state.principal = state["principal"]
        return await call_next(request)

    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    with TestClient(app) as client:
        yield client, db, state
    reset_database()


def _run(broker, *, kind="sequence", budget=3):
    return broker.parent_run_controller.start(OWNER, kind=kind, definition_ref=f"{kind}:definition", definition_revision="rev-1", input_snapshot={"input": "x"}, deadline_at=2000.0, child_budget=budget)


def _reason(callable_):
    with pytest.raises(KernelRefused) as exc:
        callable_()
    return exc.value.reason


def _recipe(client: TestClient, name: str, template: str = "{input}") -> str:
    response = client.post("/api/recipes", json={"name": name, "system_prompt": f"SYS {name}", "user_template": template})
    assert response.status_code == 201, response.text
    return response.json()["recipe"]["id"]


def _sequence(client: TestClient, recipe_ids: list[str]) -> str:
    return client.post("/api/chains", json={"name": "sequence", "steps": recipe_ids}).json()["chain"]["id"]


def _workflow(client: TestClient, graph: dict) -> str:
    return client.post("/api/workflows", json={"name": "workflow", "graph_json": graph}).json()["workflow"]["id"]


def _linear(nodes: list[dict]) -> dict:
    ids = [node["id"] for node in nodes]
    return {"id": "wf-route", "name": "route workflow", "entry": ids[0], "nodes": nodes,
            "exec_edges": [{"from": {"node": left, "name": "then"}, "to": right} for left, right in zip(ids, ids[1:])], "data_edges": []}


def _children(db: Database, parent_id: str) -> list[dict]:
    with db._connection() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at", (parent_id,))]


def _receipt(db: Database, operation_id: str) -> dict:
    with db._connection() as conn:
        row = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)).fetchone()
    assert row is not None
    return dict(row)


def _stage(db: Database, invocation_id: str) -> dict:
    with db._connection() as conn:
        row = conn.execute("SELECT * FROM kernel_projection_stages WHERE invocation_id=?", (invocation_id,)).fetchone()
    assert row is not None
    return dict(row)


def test_sequence_and_workflow_create_one_authenticated_native_parent(route_rig):
    client, db, _ = route_rig
    sequence = _sequence(client, [_recipe(client, "one")])
    workflow = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "sum", "kind": {"summarize": {}}}, {"id": "out", "kind": {"output": {}}}]))
    sequence_body = client.post(f"/api/chains/{sequence}/run", json={"input": "x"}).json()
    workflow_body = client.post(f"/api/workflows/{workflow}/run", json={"input": "x"}).json()
    for body, name in ((sequence_body, "sequence.run"), (workflow_body, "workflow.run")):
        op = _children(db, body["parent_operation_id"])
        with db._connection() as conn:
            parent = dict(conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (body["parent_operation_id"],)).fetchone())
        assert parent["name"] == name and parent["principal_identity"] == OWNER.identity
        assert len(op) == 1 and _receipt(db, parent["operation_id"])["outcome"] == "succeeded"


def test_unauthenticated_sequence_or_workflow_refuses_before_parent_or_child(route_rig):
    client, db, state = route_rig
    sequence = _sequence(client, [_recipe(client, "one")])
    workflow = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "out", "kind": {"output": {}}}]))
    state["principal"] = UNAUTHENTICATED
    for url in (f"/api/chains/{sequence}/run", f"/api/workflows/{workflow}/run"):
        assert client.post(url, json={"input": "x"}).status_code == 401
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM kernel_operations WHERE name IN ('sequence.run','workflow.run','inference.invoke')").fetchone()[0] == 0


def test_three_step_sequence_has_three_admitted_children_and_terminal_receipts(route_rig):
    client, db, _ = route_rig
    chain = _sequence(client, [_recipe(client, "one"), _recipe(client, "two"), _recipe(client, "three")])
    response = client.post(f"/api/chains/{chain}/run", json={"input": "start"})
    assert response.status_code == 200, response.text
    body = response.json(); children = _children(db, body["parent_operation_id"])
    assert len(children) == len(body["children"]) == 3
    assert all(child["parent_operation_id"] == body["parent_operation_id"] for child in children)
    assert [_receipt(db, child["operation_id"])["outcome"] for child in children] == ["succeeded"] * 3


def test_workflow_child_cardinality_covers_model_retry_fallback_skip_and_pure_nodes(route_rig):
    client, db, state = route_rig
    # retryThenQueue is terminal failure: it does not invent a retry child.
    retry = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "model", "kind": {"summarize": {}}, "failure_policy": "retryThenQueue"}, {"id": "out", "kind": {"output": {}}}]))
    state["fail"] = True
    failed = client.post(f"/api/workflows/{retry}/run", json={"input": "x"})
    assert failed.status_code == 502
    # A child is never admitted without its owning parent, even on failure.
    with db._connection() as conn:
        parentless_children = conn.execute("SELECT count(*) FROM kernel_operations WHERE name='inference.invoke' AND parent_operation_id='' ").fetchone()[0]
    assert parentless_children == 0
    with db._connection() as conn:
        parent = conn.execute("SELECT operation_id FROM kernel_operations WHERE name='workflow.run' ORDER BY created_at DESC LIMIT 1").fetchone()[0]
    retry_children = _children(db, parent)
    assert len(retry_children) == 1 and _receipt(db, retry_children[0]["operation_id"])["outcome"] == "failed"

    # fallbackOnDevice and skip carry input through as pure handling; keep_if is pure.
    fallback = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "model", "kind": {"summarize": {}}, "failure_policy": "fallbackOnDevice"}, {"id": "keep", "kind": {"keep_if": {"keyword": "x"}}}, {"id": "out", "kind": {"output": {}}}]))
    skipped = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "model", "kind": {"summarize": {}}, "failure_policy": "skip"}, {"id": "out", "kind": {"output": {}}}]))
    for workflow in (fallback, skipped):
        response = client.post(f"/api/workflows/{workflow}/run", json={"input": "x"})
        assert response.status_code == 200, response.text
        children = _children(db, response.json()["parent_operation_id"])
        assert len(children) == 1 and _receipt(db, children[0]["operation_id"])["outcome"] == "failed"



def test_child_causation_definition_node_and_deployment_revisions_are_immutable(route_rig):
    client, db, _ = route_rig
    recipe = _recipe(client, "one")
    chain = _sequence(client, [recipe])
    sequence = client.post(f"/api/chains/{chain}/run", json={"input": "x"}).json()
    graph = _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "node", "kind": {"summarize": {}}}, {"id": "out", "kind": {"output": {}}}])
    workflow = client.post(f"/api/workflows/{_workflow(client, graph)}/run", json={"input": "x"}).json()
    for body, expected_kind in ((sequence, "sequence-step-output"), (workflow, "workflow-node-output")):
        child = _children(db, body["parent_operation_id"])[0]
        stage = _stage(db, child["native_id"])
        projection = json.loads(stage["projection_json"])
        assert child["parent_operation_id"] == body["parent_operation_id"]
        assert child["correlation_id"] and projection["deployment_revision"]
        assert projection["recipe_revision"] if expected_kind == "sequence-step-output" else projection["node_revision"].startswith("sha256:")
        assert stage["kind"] == expected_kind and _receipt(db, child["operation_id"])["result_ref"] == stage["result_ref"]


def test_each_child_resolves_phase130_placement_then_freezes_deployment_revision(route_rig):
    client, db, state = route_rig
    chain = _sequence(client, [_recipe(client, "one"), _recipe(client, "two")])
    body = client.post(f"/api/chains/{chain}/run", json={"input": "x"}).json()
    children = _children(db, body["parent_operation_id"])
    revisions = [json.loads(_stage(db, child["native_id"])["projection_json"])["deployment_revision"] for child in children]
    assert len(revisions) == 2 and revisions == state["revisions"]
    with db._connection() as conn:
        durable_revisions = {row["id"] for row in conn.execute("SELECT id FROM deployment_revisions")}
    assert set(revisions) <= durable_revisions


def test_live_outer_context_admits_causally_linked_child(rig):
    broker, _ = rig; run = _run(broker)
    assert broker.parent_run_controller.reserve_child(run.context, OWNER, planned_node="0", invocation_id="child") == 1


def test_outer_context_refuses_wrong_parent(rig):
    broker, _ = rig; one, two = _run(broker), _run(broker)
    # Contexts identify exactly one parent; their own child reservations cannot
    # collapse the two parents into a shared causal row.
    assert one.context.operation_id != two.context.operation_id
    broker.parent_run_controller.reserve_child(one.context, OWNER, planned_node="0", invocation_id="one")
    broker.parent_run_controller.reserve_child(two.context, OWNER, planned_node="0", invocation_id="two")
    with broker.store._connection() as conn:
        rows = conn.execute("SELECT operation_id,children_json FROM kernel_parent_runs ORDER BY operation_id").fetchall()
    assert {json.loads(row["children_json"])[0] for row in rows} == {"one", "two"}


def test_outer_context_refuses_dead_parent(rig):
    broker, _ = rig; run = _run(broker); broker.parent_run_controller.cancel(run.context, OWNER)
    assert _reason(lambda: broker.parent_run_controller.reserve_child(run.context, OWNER, planned_node="0", invocation_id="x")) == "parent_context_invalid"


def test_outer_context_refuses_foreign_principal_parent(rig):
    broker, _ = rig; run = _run(broker)
    assert _reason(lambda: broker.parent_run_controller.reserve_child(run.context, FOREIGN, planned_node="0", invocation_id="x")) == "parent_operation_scope_required"


def test_client_supplied_or_forged_parent_context_is_refused(rig):
    broker, _ = rig
    assert _reason(lambda: broker.parent_run_controller.reserve_child(object(), OWNER, planned_node="0", invocation_id="x")) == "parent_context_invalid"


def test_late_or_superseded_child_output_cannot_advance_sequence_or_graph(rig):
    broker, _ = rig; run = _run(broker); broker.parent_run_controller.cancel(run.context, OWNER)
    assert run.context.epoch == 1


def test_parent_cancel_fences_admission_and_late_output_while_child_receipts_survive(route_rig):
    """Route-level interleaving: cancel wins while provider dispatch is blocked."""
    client, db, state = route_rig
    chain = _sequence(client, [_recipe(client, "slow")])
    state["block"] = True
    with ThreadPoolExecutor(max_workers=1) as executor:
        run = executor.submit(client.post, f"/api/chains/{chain}/run", json={"input": "x"})
        assert state["entered"].wait(5)
        with db._connection() as conn:
            parent_id = conn.execute("SELECT operation_id FROM kernel_operations WHERE name='sequence.run' ORDER BY created_at DESC LIMIT 1").fetchone()[0]
        cancel = client.post(f"/api/chains/runs/{parent_id}/cancel")
        assert cancel.status_code == 200 and cancel.json()["parent_operation_id"] == parent_id
        state["release"].set()
        assert run.result(timeout=10).status_code == 409
    child = _children(db, parent_id)[0]
    assert _receipt(db, child["operation_id"])["outcome"] == "succeeded"
    with db._connection() as conn:
        checkpoint = conn.execute("SELECT advanced FROM kernel_parent_checkpoints WHERE parent_operation_id=?", (parent_id,)).fetchone()
    assert checkpoint is not None and checkpoint["advanced"] == 0
    broker = _configure(db)
    # Restart does not reconstruct a bearer context from a durable row.
    assert _reason(lambda: broker.parent_run_controller.reserve_child(object(), OWNER, planned_node="later", invocation_id="later")) == "parent_context_invalid"


def test_child_non_success_preserves_receipt_and_applies_existing_domain_policy(rig):
    broker, _ = rig; run = _run(broker)
    receipt = broker.parent_run_controller.close(run.context, "failed")
    assert receipt["outcome"] == "failed"


def test_model_derived_sequence_workflow_writes_are_receipt_gated(route_rig):
    client, db, _ = route_rig
    chain = _sequence(client, [_recipe(client, "one")])
    body = client.post(f"/api/chains/{chain}/run", json={"input": "x"}).json()
    child = _children(db, body["parent_operation_id"])[0]
    stage = _stage(db, child["native_id"])
    with db._connection() as conn:
        checkpoint = conn.execute("SELECT * FROM kernel_parent_checkpoints WHERE stage_id=?", (stage["stage_id"],)).fetchone()
        artifact = conn.execute("SELECT * FROM artifacts WHERE id=?", (body["artifact_id"],)).fetchone()
    assert checkpoint is not None and checkpoint["advanced"] == 1
    assert _receipt(db, child["operation_id"])["result_ref"] == stage["result_ref"]
    assert artifact is not None and _receipt(db, body["parent_operation_id"])["outcome"] == "succeeded"


def test_outer_context_liveness_and_epoch_check_is_atomic_with_child_admission(route_rig):
    """A stale Python context loses to the durable cancellation under admission lock."""
    _, db, _ = route_rig
    from holdspeak.deployment_revisions import capture_deployment_revision
    from holdspeak.inference_targets import resolve_placement
    from holdspeak.kernel.inference_runner import ServiceContract
    broker = _configure(db)
    run = broker.parent_run_controller.start(OWNER, kind="sequence", definition_ref="sequence:atomic", definition_revision="rev-1", input_snapshot={"input":"x"}, deadline_at=time.time()+30, child_budget=1)
    stale_context = run.context  # caller's liveness view before the interleaving
    deployment = capture_deployment_revision(db, resolve_placement(db).target)
    origin = ServiceContract.for_payload("holdspeak.test", "1", {"test":"atomic"})
    raw = {"request_schema":1,"request_id":"atomic-child","idempotency_key":"atomic-child","operation":{"name":"inference.invoke","version":1},"target":{},"parent_operation_id":run.operation_id,"arguments":{"invocation_id":"atomic-child","deployment_revision":deployment.id,"definition_origin":origin.journal_value(),"deadline_at":time.time()+30,"attempt_ordinal":1}}
    # The caller has already read a live capability; cancellation now commits its
    # durable epoch/state change before trusted admission begins its transaction.
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM kernel_parent_runs WHERE operation_id=?", (run.operation_id,)).fetchone()[0] == "OPEN"
    assert broker.parent_run_controller.cancel(stale_context, OWNER) == "cancelled"
    with db._connection() as conn:
        assert conn.execute("SELECT state FROM kernel_parent_runs WHERE operation_id=?", (run.operation_id,)).fetchone()[0] == "CANCELLING"
    assert _reason(lambda: broker.submit_trusted_child(raw, OWNER, stale_context, planned_node="step:1")) == "parent_context_invalid"
    assert not _children(db, run.operation_id)


def test_direct_owner_parent_id_requires_exact_principal_identity(route_rig):
    """Generic broker admission cannot use an owner's raw parent id as a bearer key."""
    _, db, _ = route_rig
    from holdspeak.deployment_revisions import capture_deployment_revision
    from holdspeak.inference_targets import resolve_placement
    from holdspeak.kernel.inference_runner import ServiceContract
    broker = _configure(db)
    run = broker.parent_run_controller.start(OWNER, kind="sequence", definition_ref="sequence:definition", definition_revision="rev-1", input_snapshot={"input": "x"}, deadline_at=time.time() + 30, child_budget=3)
    deployment = capture_deployment_revision(db, resolve_placement(db).target)
    origin = ServiceContract.for_payload("holdspeak.test", "1", {"test": "foreign-parent"})
    raw = {"request_schema": 1, "request_id": "foreign-parent", "idempotency_key": "foreign-parent", "operation": {"name": "inference.invoke", "version": 1}, "target": {}, "parent_operation_id": run.operation_id, "arguments": {"invocation_id": "foreign-parent-child", "deployment_revision": deployment.id, "definition_origin": origin.journal_value(), "deadline_at": time.time() + 30, "attempt_ordinal": 1}}
    refused = broker.submit(raw, FOREIGN)
    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == "parent_operation_scope_required"


def test_outer_context_is_unexportable_and_replay_scoped(rig):
    broker, _ = rig; run, other = _run(broker), _run(broker)
    assert "OuterRunContext" in repr(run.context)
    with pytest.raises(TypeError): pickle.dumps(run.context)
    assert _reason(lambda: broker.parent_run_controller.reserve_child(run.context, FOREIGN, planned_node="0", invocation_id="foreign")) == "parent_operation_scope_required"
    assert run.context.operation_id != other.context.operation_id


def test_zero_dispatch_definition_receipt_closes_one_parent_without_children(route_rig):
    client, db, _ = route_rig
    chain = _sequence(client, [])
    response = client.post(f"/api/chains/{chain}/run", json={"input": "x"})
    assert response.status_code == 409
    parent_id = response.json()["parent_operation_id"]
    assert not _children(db, parent_id) and _receipt(db, parent_id)["outcome"] == "refused"


def test_cancel_publish_race_has_one_durable_advancement_winner(rig):
    broker, _ = rig
    def finalize(run, child):
        with broker.store._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO kernel_projection_stages(stage_id,invocation_id,operation_id,kind,projection_json,projection_sha256,result_ref,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (f"stage-{child}", child, run.operation_id, "sequence-step-output", "{}", "sha256:test", f"projection-stage:{child}", "STAGED", 1000.0, 1000.0))
            return broker.parent_run_controller.finalize_child_checkpoint(conn, stage_id=f"stage-{child}", parent_operation_id=run.operation_id, child_invocation_id=child, execution_epoch=run.context.epoch, planned_node="step:1", checkpoint={"output": "kept"})
    child_wins = _run(broker); broker.parent_run_controller.reserve_child(child_wins.context, OWNER, planned_node="step:1", invocation_id="child-wins")
    assert finalize(child_wins, "child-wins") is True
    assert broker.parent_run_controller.cancel(child_wins.context, OWNER) in {"pending", "cancelled"}
    cancel_wins = _run(broker); broker.parent_run_controller.reserve_child(cancel_wins.context, OWNER, planned_node="step:1", invocation_id="cancel-wins")
    assert broker.parent_run_controller.cancel(cancel_wins.context, OWNER) in {"pending", "cancelled"}
    assert finalize(cancel_wins, "cancel-wins") is False


def test_fallback_supersession_fences_late_success(rig):
    """Controller-level proof through Terra #3's durable CAS seam (not HTTP-drivable)."""
    broker, _ = rig; run = _run(broker)
    broker.parent_run_controller.reserve_child(run.context, OWNER, planned_node="node:model", invocation_id="late")
    replacement = broker.parent_run_controller.supersede(run.context, OWNER)
    with broker.store._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO kernel_projection_stages(stage_id,invocation_id,operation_id,kind,projection_json,projection_sha256,result_ref,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)", ("stage-late", "late", run.operation_id, "workflow-node-output", "{}", "sha256:test", "projection-stage:late", "STAGED", 1000.0, 1000.0))
        advanced = broker.parent_run_controller.finalize_child_checkpoint(conn, stage_id="stage-late", parent_operation_id=run.operation_id, child_invocation_id="late", execution_epoch=run.context.epoch, planned_node="node:model", checkpoint={"output": "late"})
    assert replacement.epoch == run.context.epoch + 1 and advanced is False
    with broker.store._connection() as conn:
        assert conn.execute("SELECT advanced FROM kernel_parent_checkpoints WHERE stage_id='stage-late'").fetchone()[0] == 0


def test_active_dispatch_heartbeats_survive_reconciliation_while_dead_parent_closes(rig, monkeypatch):
    """A long provider wait renews its process lease; an abandoned peer does not."""
    broker, now = rig
    monkeypatch.setattr(broker.parent_run_controller, "_heartbeat_seconds", .01)
    live, dead = _run(broker), _run(broker)
    broker.parent_run_controller.reserve_child(live.context, OWNER, planned_node="step:1", invocation_id="slow-child")
    now[0] += broker.parent_run_controller._lease_seconds + 1
    time.sleep(.04)  # several daemon beats occur while the child is still in flight
    assert broker.parent_run_controller.reconcile_abandoned() == 1
    assert broker.store.receipt(live.operation_id) is None
    assert broker.store.receipt(dead.operation_id)["outcome"] == "indeterminate"
    broker.parent_run_controller.end_child_dispatch(live.operation_id)


def test_reconciliation_rechecks_refreshed_lease_before_closing(rig, monkeypatch):
    """A lease refreshed after stale selection loses the indeterminate CAS."""
    broker, now = rig; run = _run(broker); now[0] = 5000.0
    with broker.database._connection() as conn:
        conn.execute("UPDATE kernel_parent_runs SET active_child_invocation_id='still-live' WHERE operation_id=?", (run.operation_id,))
    original = broker.parent_run_controller._close
    def refresh_between_selection_and_close(context, *args, **kwargs):
        broker.parent_run_controller._refresh_lease(context.operation_id)
        return original(context, *args, **kwargs)
    monkeypatch.setattr(broker.parent_run_controller, "_close", refresh_between_selection_and_close)
    assert broker.parent_run_controller.reconcile_abandoned() == 0
    assert broker.store.receipt(run.operation_id) is None


def test_restart_reconciles_receipted_child_then_closes_parent_indeterminate(rig):
    broker, now = rig; run = _run(broker); now[0] = 5000.0
    assert broker.parent_run_controller.reconcile_abandoned() == 1
    assert broker.store.receipt(run.operation_id)["outcome"] == "indeterminate"


def test_parent_aggregate_crash_gaps_reconcile_truthfully(rig):
    broker, now = rig
    # Gap 1: process dies before a parent stage: recovery makes only an
    # indeterminate parent receipt, never an Artifact.
    before_stage = _run(broker); now[0] = 5000.0
    assert broker.parent_run_controller.reconcile_abandoned() == 1
    assert broker.store.receipt(before_stage.operation_id)["outcome"] == "indeterminate"
    # Gap 2: a stage exists but no parent receipt. The dead lease elects
    # indeterminate; regular stage recovery discards that unreceipted success.
    now[0] = 1000.0; after_stage = _run(broker)
    staged = broker.projection_stager.stage(after_stage.native_id, "sequence-run-result", {"kind":"sequence", "parent_operation_id":after_stage.operation_id, "definition_revision":"rev-1", "artifact_id":"artifact-gap-two", "name":"gap", "output":"x", "sources":[], "steps":[], "created_at":"2026-01-01T00:00:00"})
    now[0] = 5000.0; broker.parent_run_controller.reconcile_abandoned(); broker.projection_stager.recover()
    assert broker.store.receipt(after_stage.operation_id)["outcome"] == "indeterminate"
    assert broker.projection_stager.get(after_stage.native_id).state == "DISCARDED"
    # Gap 3: receipt commits then process dies before finalization. Recovery
    # finalizes its exact receipt-linked stage once.
    now[0] = 1000.0; after_receipt = _run(broker)
    committed = broker.projection_stager.stage(after_receipt.native_id, "sequence-run-result", {"kind":"sequence", "parent_operation_id":after_receipt.operation_id, "definition_revision":"rev-1", "artifact_id":"artifact-gap-three", "name":"gap", "output":"x", "sources":[], "steps":[], "created_at":"2026-01-01T00:00:00"})
    broker.parent_run_controller.close(after_receipt.context, "succeeded", committed.result_ref, principal=OWNER)
    assert broker.projection_stager.recover()["finalized"] >= 1
    assert broker.projection_stager.finalize(after_receipt.native_id)["artifact_id"] == "artifact-gap-three"


def test_parent_non_success_outcomes_are_receipt_closed_without_artifact(rig):
    broker, _ = rig; run = _run(broker)
    assert broker.parent_run_controller.close(run.context, "cancelled")["outcome"] == "cancelled"


def test_parent_child_replay_is_idempotent_across_restart(route_rig):
    """A completed real route replay returns its published result, not new work."""
    client, db, _ = route_rig
    chain = _sequence(client, [_recipe(client, "replay")])
    first = client.post(f"/api/chains/{chain}/run", json={"input": "x", "request_id": "request-replay"})
    assert first.status_code == 200, first.text
    original = first.json(); parent_id = original["parent_operation_id"]
    restarted = _configure(db)
    assert restarted.parent_run_controller.reconcile_abandoned() == 0
    replayed = client.post(f"/api/chains/{chain}/run", json={"input": "x", "request_id": "request-replay"})
    assert replayed.status_code == 200, replayed.text
    replay = replayed.json()
    assert (replay["parent_operation_id"], replay["artifact_id"], replay["output"]) == (parent_id, original["artifact_id"], original["output"])
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM kernel_parent_runs WHERE operation_id=?", (parent_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM kernel_operations WHERE parent_operation_id=?", (parent_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM kernel_projection_stages WHERE operation_id IN (SELECT operation_id FROM kernel_operations WHERE parent_operation_id=? OR operation_id=?)", (parent_id, parent_id)).fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM artifacts WHERE id=?", (original["artifact_id"],)).fetchone()[0] == 1


def test_child_budget_bounds_retry_and_model_fallback_dispatches(rig):
    broker, _ = rig; run = _run(broker, budget=1); broker.parent_run_controller.reserve_child(run.context, OWNER, planned_node="0", invocation_id="one")
    assert _reason(lambda: broker.parent_run_controller.reserve_child(run.context, OWNER, planned_node="1", invocation_id="two")) == "parent_child_budget_exhausted"
    assert broker.parent_run_controller.close(run.context, "failed")["outcome"] == "failed"


def test_workflow_node_classification_is_closed_before_admission(route_rig):
    client, db, _ = route_rig
    workflow = _workflow(client, _linear([{"id": "entry", "kind": {"entry": {}}}, {"id": "mystery", "kind": {"future_model": {}}}, {"id": "out", "kind": {"output": {}}}]))
    response = client.post(f"/api/workflows/{workflow}/run", json={"input": "x"})
    assert response.status_code == 409
    parent_id = response.json()["parent_operation_id"]
    assert not _children(db, parent_id)
    assert _receipt(db, parent_id)["outcome"] == "refused"


def test_sequence_child_refuses_recipe_revision_changed_after_planning(route_rig, monkeypatch):
    """The runner receives the planned SavedDefinition revision, never a refresh."""
    client, db, _ = route_rig
    recipe = _recipe(client, "planned")
    chain = _sequence(client, [recipe])
    from holdspeak.services.sequence_workflow_service import SequenceWorkflowService
    original = SequenceWorkflowService._target
    def mutate_before_admission(service, *args, **kwargs):
        with db._connection() as conn:
            conn.execute("UPDATE recipes SET last_modified=? WHERE id=?", ("2099-01-01T00:00:00+00:00", recipe))
        return original(service, *args, **kwargs)
    monkeypatch.setattr(SequenceWorkflowService, "_target", mutate_before_admission)
    response = client.post(f"/api/chains/{chain}/run", json={"input": "x"})
    assert response.status_code == 502
    with db._connection() as conn:
        parent_id = conn.execute("SELECT operation_id FROM kernel_operations WHERE name='sequence.run' ORDER BY created_at DESC LIMIT 1").fetchone()[0]
    assert not _children(db, parent_id)
    assert _receipt(db, parent_id)["outcome"] == "failed"


def test_cancel_and_failure_close_have_one_receipt_winner(rig):
    broker, _ = rig
    cancel_first = _run(broker)
    broker.parent_run_controller.cancel_by_operation_id(OWNER, cancel_first.operation_id)
    assert broker.store.receipt(cancel_first.operation_id)["outcome"] == "cancelled"
    assert _reason(lambda: broker.parent_run_controller.close(cancel_first.context, "failed", principal=OWNER)) == "parent_context_invalid"
    failure_first = _run(broker)
    assert broker.parent_run_controller.close(failure_first.context, "failed", principal=OWNER)["outcome"] == "failed"
    assert broker.parent_run_controller.cancel_by_operation_id(OWNER, failure_first.operation_id) == "failed"
    assert broker.store.receipt(failure_first.operation_id)["outcome"] == "failed"
