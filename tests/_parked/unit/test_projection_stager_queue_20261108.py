"""PARKED 20261108 (Lane S2): cases of ``tests/unit/test_projection_stager.py`` that drove the item queue.

The item queue is parked (holdspeak/services/_parked/workbench_runner_queue_20261108.py);
an automation's run is a Program of one prompt step. Not collected; they import the
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_projection_stager import *  # noqa: F401,F403


def test_raw_schedule_record_edit_does_not_discard_a_frozen_projection_or_mutate_receipt(tmp_path):
    """A live delegation publishes its frozen route despite an unrelated raw edit."""
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
        # Capture each child receipt the instant the Runner makes it terminal.
        snapshots: dict[str, str] = {}
        persist = broker.inference_runner._persist_receipt

        def capture(active, operation_id, outcome, result_ref, **kwargs):
            receipt = persist(active, operation_id, outcome, result_ref, **kwargs)
            operation = broker.store.operation(operation_id)
            if operation and operation["name"] == "inference.invoke":
                snapshots[operation_id] = json.dumps(dict(receipt), sort_keys=True)
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
    # BYTE FOR BYTE: the frozen child's terminal receipt remains immutable.
    assert after == snapshots[child_id]
    assert json.loads(after)["outcome"] == "succeeded"
    assert broker.store.operation(child_id)["state"] == "succeeded"

    # The raw Recipe revision is not a schedule selector; publication remains
    # receipt-linked to the frozen route and the delegation stays authoritative.
    assert stage["state"] == "PUBLISHED"
    item = db.workbench_items.get("byte-for-byte")
    assert item.status == "done" and item.result == "the provider really did answer"
    assert delegation["state"] == "LIVE"
    assert json.dumps(dict(broker.store.receipt(child_id)), sort_keys=True) == after
