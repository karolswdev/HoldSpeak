"""HS-131-03 projection-stage protocol seams."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner")


class Adapter:
    def dispatch(self, engine, payload, cancellation):
        return "answer"

    def cancel(self):
        return "cancelled"


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "projection.db")
    db.profiles.upsert(profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf")
    revision = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    broker = _configure(db)
    with db._connection() as conn:
        conn.execute("CREATE TABLE materialized_projection (projection_stage_id TEXT PRIMARY KEY, answer TEXT NOT NULL)")
    return db, broker, revision


def _request(revision, invocation_id="projection_test"):
    payload = {"question": "hello", "schema_version": 1, "deployment_revision": revision.id}
    return InvocationRequest(revision.id, ServiceContract.for_payload("holdspeak.ask", "1", payload), time.time() + 30, payload, invocation_id)


def _materializer(stager):
    def materialize(conn, stage, permit):
        stager.require_permit(permit, conn)
        conn.execute("INSERT INTO materialized_projection(projection_stage_id,answer) VALUES(?,?)", (stage.stage_id, stage.projection["answer"]))
        return {"answer": stage.projection["answer"], "projection_stage_id": stage.stage_id}
    return materialize


def test_projection_stage_precedes_success_receipt_and_finalizes_once(rig):
    db, broker, revision = rig
    stager = broker.projection_stager
    stager.register("test-result", _materializer(stager))
    runner = InferenceRunner(broker, db, engine_factory=lambda _revision, **_kw: object(), principal_provider=lambda: OWNER)
    seen = []

    def encode(answer):
        stage = stager.get("projection_test")
        assert stage is None  # encoder has no publication privileges
        return {"answer": answer}

    callback = stager.publisher("projection_test", "test-result", encode)
    original = broker.receipt

    def receipt(operation_id, outcome, result_ref, node, **_kwargs):
        stage = stager.get("projection_test")
        assert stage is not None and stage.state == "STAGED"
        assert result_ref == stage.result_ref
        seen.append(result_ref)
        return original(operation_id, outcome, result_ref, node, **_kwargs)

    broker.receipt = receipt
    outcome = runner.invoke(_request(revision), Adapter(), publish=callback)
    assert outcome.outcome == "succeeded"
    assert outcome.result_ref == seen[0]
    final = stager.finalize("projection_test")
    assert final["answer"] == "answer"
    assert stager.finalize("projection_test") == final
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM materialized_projection").fetchone()[0] == 1


def test_stage_payload_conflict_and_permit_are_fenced(rig):
    db, broker, revision = rig
    stager = broker.projection_stager
    runner = InferenceRunner(broker, db, engine_factory=lambda _revision, **_kw: object(), principal_provider=lambda: OWNER)
    outcome = runner.invoke(_request(revision), Adapter(), publish=stager.publisher("projection_test", "fenced", lambda answer: {"answer": answer}))
    assert outcome.outcome == "succeeded"
    with pytest.raises(KernelRefused, match="projection_stage_payload_conflict"):
        stager.stage("projection_test", "fenced", {"answer": "changed"})

    def forged(conn, stage, permit):
        with pytest.raises(KernelRefused, match="projection_publication_permit_invalid"):
            stager.require_permit(object(), conn)
        return {"answer": "never"}

    stager.register("fenced", forged)
    with pytest.raises(KernelRefused, match="projection_permit_not_used"):
        stager.finalize("projection_test")
    assert stager.get("projection_test").state == "STAGED"


def test_absent_receipt_stays_invisible_until_liveness_terminalizes(rig):
    db, broker, revision = rig
    stager = broker.projection_stager
    # Stage against an admitted invocation without closing its receipt.
    submitted = broker.submit({
        "request_schema": 1, "request_id": "raw-stage", "idempotency_key": "raw-stage",
        "operation": {"name": "inference.invoke", "version": 1}, "target": {},
        "arguments": {"invocation_id": "raw_stage", "deployment_revision": revision.id,
                      "definition_origin": {"kind": "service", "contract": "holdspeak.ask", "revision": "1", "payload_hash": "sha256:" + "0" * 64},
                      "deadline_at": time.time() + 30, "attempt_ordinal": 1},
    }, OWNER)
    approved = broker.decide(submitted["operation_id"], "approve", submitted["revision"], OWNER)
    node = Principal(PrincipalKind.NODE, broker.store.operation(approved["operation_id"])["placement"].removeprefix("node:"))
    assert broker.claim(node, "raw_stage")["operations"]
    stage = stager.stage("raw_stage", "absent", {"answer": "invisible"})
    assert stager.recover()["healthy"]
    assert stager.get("raw_stage").state == "STAGED"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM materialized_projection").fetchone()[0] == 0


# ==================================== ROUND 2: the terminal receipt is immutable


def test_schedule_drift_discards_the_projection_without_touching_the_receipt(tmp_path):
    """Terra blocker 8: the stager REWROTE a succeeded child receipt.

    When a scheduled run's terms changed while the provider was answering, the
    stager did this inside the materialization transaction::

        UPDATE kernel_operations SET state='refused' ... WHERE state='succeeded'
        UPDATE kernel_receipts  SET state='refused',outcome=<drift>,result_ref=''

    That is a mutation of an already-terminal invocation receipt — the exact
    thing this story's acceptance criterion forbids, and the thing
    ``ExecutorPlane.receipt`` itself refuses by name (``receipt_immutable``). The
    provider DID run and DID answer; the schedule going stale afterwards is a
    fact about the delegation, not a reason to rewrite history.

    The fence therefore lives entirely on the projection now. This reads the
    child's receipt row BYTE FOR BYTE before and after the drifted finalization.
    """
    import json

    from holdspeak.services.schedule_delegation import ScheduleDelegationService
    from holdspeak.services.workbench_runner import WorkbenchRunner
    from tests.unit.test_schedule_delegations import OWNER as SCHEDULE_OWNER
    from tests.unit.test_schedule_delegations import SCHEDULER, _rig as _schedule_rig

    import asyncio

    db, service, workbench_id = _schedule_rig(tmp_path)
    db.workbench_items.upsert(
        item_id="byte-for-byte", workbench_id=workbench_id, title="byte for byte"
    )
    service.update_workbench(SCHEDULE_OWNER, workbench_id, schedule_enabled=True)
    delegation_id = ScheduleDelegationService(db).live(workbench_id)["id"]

    class _EditsTheRecipeMidCall:
        def run_prompt(self, **_):
            # A real durable edit while the provider call is in flight.
            with db._connection() as conn:
                conn.execute(
                    "UPDATE recipes SET last_modified='edited-during-provider' WHERE id='r'"
                )
            return "the provider really did answer"

    import holdspeak.intel.providers as providers

    original = providers.build_meeting_intel_for_profile
    providers.build_meeting_intel_for_profile = lambda **_: _EditsTheRecipeMidCall()
    try:
        broker = _configure(db)
        # Capture the child's receipt the instant the RUNNER made it terminal.
        snapshots: list[str] = []
        persist = broker.inference_runner._persist_receipt

        def capture(active, operation_id, outcome, result_ref, **kwargs):
            receipt = persist(active, operation_id, outcome, result_ref, **kwargs)
            operation = broker.store.operation(operation_id)
            if operation and operation["name"] == "inference.invoke":
                snapshots.append(json.dumps(dict(receipt), sort_keys=True))
            return receipt

        broker.inference_runner._persist_receipt = capture
        result = asyncio.run(
            WorkbenchRunner(db, broker).run_scheduled(
                SCHEDULER, workbench_id, due_minute=424242
            )
        )
    finally:
        providers.build_meeting_intel_for_profile = original

    with db._connection() as conn:
        child_id = conn.execute(
            "SELECT operation_id FROM kernel_operations"
            " WHERE parent_operation_id=? AND name='inference.invoke'",
            (result["parent_operation_id"],),
        ).fetchone()[0]
        stage = dict(
            conn.execute(
                "SELECT state,final_result_json FROM kernel_projection_stages"
                " WHERE operation_id=?",
                (child_id,),
            ).fetchone()
        )
        delegation = dict(
            conn.execute(
                "SELECT state,revocation_reason FROM kernel_schedule_delegations WHERE id=?",
                (delegation_id,),
            ).fetchone()
        )

    assert snapshots, "the runner never terminalized an invocation child"
    after = json.dumps(dict(broker.store.receipt(child_id)), sort_keys=True)
    # BYTE FOR BYTE: not merely the same outcome — the same row.
    assert after == snapshots[-1]
    assert json.loads(after)["outcome"] == "succeeded"
    assert broker.store.operation(child_id)["state"] == "succeeded"

    # The projection is what carries the refusal, and nothing was published.
    assert stage["state"] == "DISCARDED"
    assert json.loads(stage["final_result_json"] or "{}") == {
        "discarded": "delegation_stale_work"
    }
    item = db.workbench_items.get("byte-for-byte")
    assert item.status != "done" and item.result in (None, "")
    assert delegation == {
        "state": "REVOKED", "revocation_reason": "delegation_stale_work"
    }

    # And a second finalization cannot resurrect it (no late publication).
    assert broker.projection_stager.finalize(
        broker.store.operation(child_id)["native_id"]
    ) is None
    assert json.dumps(dict(broker.store.receipt(child_id)), sort_keys=True) == after
