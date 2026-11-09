"""PARKED 20261108 (Lane S2): cases of ``tests/unit/test_schedule_delegations.py`` that drove the item queue.

The item queue is parked (holdspeak/services/_parked/workbench_runner_queue_20261108.py);
an automation's run is a Program of one prompt step. Not collected; they import the
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_schedule_delegations import *  # noqa: F401,F403


def test_due_tick_uses_scheduler_parent_and_admitted_workbench_runner_children(tmp_path, monkeypatch):
    db, service, wid=_rig(tmp_path)
    db.workbench_items.upsert(item_id="i", workbench_id=wid, title="scheduled")
    service.update_workbench(OWNER,wid,schedule_enabled=True)
    class FakeIntel:
        def run_prompt(self, **_): return "scheduled output"
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner
    broker=_configure(db)
    result=asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=123456))
    parent=broker.store.operation(result["parent_operation_id"])
    with db._connection() as conn:
        child=dict(conn.execute("SELECT * FROM kernel_operations WHERE parent_operation_id=?",(parent["operation_id"],)).fetchone())
    basis=f"schedule-delegation:{ScheduleDelegationService(db).live(wid)['id']}:{ScheduleDelegationService(db).live(wid)['terms_sha256']}"
    assert (parent["principal_kind"], parent["principal_identity"], parent["delegator_kind"], parent["delegator_identity"], parent["authority_basis"]) == ("scheduler", "local-workbench-conductor", "owner", OWNER.identity, basis)
    assert (child["principal_kind"], child["delegator_kind"], child["delegator_identity"], child["authority_basis"]) == ("scheduler", "owner", OWNER.identity, basis)
    for operation_id in (parent["operation_id"], child["operation_id"]):
        receipt = broker.store.receipt(operation_id)
        assert (receipt["actor_kind"], receipt["actor_identity"], receipt["delegator_kind"], receipt["delegator_identity"], receipt["authority_basis"]) == ("scheduler", "local-workbench-conductor", "owner", OWNER.identity, basis)
    assert broker.store.receipt(parent["operation_id"])["target_ref"] == f"deployment:{ScheduleDelegationService(db).live(wid)['deployment_revision_id']}"


def test_disable_cancels_scheduler_parent_and_fences_late_output(tmp_path, monkeypatch):
    db, service, wid = _rig(tmp_path)
    db.workbench_items.upsert(item_id="active-item", workbench_id=wid, title="active scheduled work")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    delegation_id = ScheduleDelegationService(db).live(wid)["id"]

    class FakeIntel:
        calls = 0

        def run_prompt(self, **_):
            self.calls += 1
            if self.calls == 1:
                # The actual owner disable gesture must fence this parent while
                # its provider call is in flight; this is not a SQL simulation.
                service.update_workbench(OWNER, wid, schedule_enabled=False)
            return "late output"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel()
    )
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner

    broker = _configure(db)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=123457))
    with db._connection() as conn:
        delegation = dict(conn.execute(
            "SELECT state,revocation_reason FROM kernel_schedule_delegations WHERE id=?", (delegation_id,)
        ).fetchone())
    receipt = broker.store.receipt(result["parent_operation_id"])
    item = db.workbench_items.get("active-item")
    assert delegation == {"state": "REVOKED", "revocation_reason": "schedule_disabled"}
    assert result["terminal_disposition"] in {"cancelled", "indeterminate"}
    assert receipt is not None and receipt["outcome"] in {"cancelled", "indeterminate"}
    assert receipt["outcome"] != "succeeded"
    assert item.status in {"pending", "failed"}
    assert item.result in (None, "")
    with pytest.raises(ServiceError) as raised:
        asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=123458))
    assert raised.value.code == "delegation_revoked"


def test_disable_between_precheck_and_atomic_admission_leaves_tick_unconsumed(tmp_path, monkeypatch):
    db, service, wid = _rig(tmp_path)
    db.workbench_items.upsert(item_id="i", workbench_id=wid, title="race")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner
    broker = _configure(db)
    controller = broker.parent_run_controller
    original = controller._delegated_refusal
    calls = 0
    def gap(conn, snapshot, **kwargs):
        nonlocal calls
        calls += 1
        result = original(conn, snapshot, **kwargs)
        if calls == 1:
            service.update_workbench(OWNER, wid, schedule_enabled=False)
        return result
    monkeypatch.setattr(controller, "_delegated_refusal", gap)
    with pytest.raises(KernelRefused, match="delegation_revoked"):
        asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=888))
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_schedule_ticks WHERE workbench_id=? AND due_minute=888", (wid,)).fetchone()[0] == 0
    monkeypatch.setattr(controller, "_delegated_refusal", original)
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    class FakeIntel:
        def run_prompt(self, **_): return "admitted after race"
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=888))
    assert result["receipt_id"]


def test_raw_recipe_revision_edit_during_scheduled_provider_call_does_not_retarget_frozen_publication(tmp_path, monkeypatch):
    db, service, wid = _rig(tmp_path)
    db.workbench_items.upsert(item_id="in-flight", workbench_id=wid, title="in flight")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    delegation_id = ScheduleDelegationService(db).live(wid)["id"]
    class FakeIntel:
        def run_prompt(self, **_):
            # This is a real durable edit while the provider call is in flight.
            with db._connection() as conn:
                conn.execute("UPDATE recipes SET last_modified='edited-during-provider' WHERE id='r'")
            return "must never publish"
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner
    broker = _configure(db)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=890))
    with db._connection() as conn:
        child_id = conn.execute("SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?", (result["parent_operation_id"],)).fetchone()[0]
        delegation = dict(conn.execute("SELECT state,revocation_reason FROM kernel_schedule_delegations WHERE id=?", (delegation_id,)).fetchone())
    child_receipt = broker.store.receipt(child_id)
    parent_receipt = broker.store.receipt(result["parent_operation_id"])
    item = db.workbench_items.get("in-flight")
    # A raw record revision is not a fire-time selector. The route and terms
    # already frozen by the owner's delegation remain executable and publish.
    assert item.status == "done" and item.result == "must never publish"
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"
    assert child_receipt["state"] == "succeeded"
    assert stage_state(db, child_id)[0] == "PUBLISHED"
    assert delegation["state"] == "LIVE"
    assert parent_receipt is not None and parent_receipt["outcome"] == "succeeded"


def test_raw_profile_edit_during_scheduled_provider_call_does_not_retarget_frozen_publication(tmp_path, monkeypatch):
    db, service, wid = _rig(tmp_path)
    db.workbench_items.upsert(item_id="profile-in-flight", workbench_id=wid, title="profile in flight")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    delegation_id = ScheduleDelegationService(db).live(wid)["id"]
    class FakeIntel:
        def run_prompt(self, **_):
            with db._connection() as conn:
                conn.execute("UPDATE profiles SET model='changed-mid-call' WHERE id='p'")
            return "must never publish"
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner
    broker = _configure(db)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=891))
    with db._connection() as conn:
        child_id = conn.execute("SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?", (result["parent_operation_id"],)).fetchone()[0]
        delegation = dict(conn.execute("SELECT state,revocation_reason FROM kernel_schedule_delegations WHERE id=?", (delegation_id,)).fetchone())
    child_receipt = broker.store.receipt(child_id)
    parent_receipt = broker.store.receipt(result["parent_operation_id"])
    item = db.workbench_items.get("profile-in-flight")
    # A raw profile-row edit cannot replace the deployment revision already
    # frozen into the delegation route. It therefore cannot discard this output.
    assert item.status == "done" and item.result == "must never publish"
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"
    assert child_receipt["state"] == "succeeded"
    assert stage_state(db, child_id)[0] == "PUBLISHED"
    assert delegation["state"] == "LIVE"
    assert parent_receipt is not None and parent_receipt["outcome"] == "succeeded"


def test_raw_recipe_edit_after_first_scheduled_item_does_not_block_next_frozen_child(tmp_path, monkeypatch):
    db, service, wid = _rig(tmp_path)
    db.workbench_items.upsert(item_id="one", workbench_id=wid, title="one")
    db.workbench_items.upsert(item_id="two", workbench_id=wid, title="two")
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    class FakeIntel:
        calls = 0
        edit_before_next_admission = False
        def run_prompt(self, **_):
            self.calls += 1
            if self.calls == 1:
                self.edit_before_next_admission = True
            return "first only"
    intel = FakeIntel()
    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: intel)
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_runner import WorkbenchRunner
    broker = _configure(db)
    original_submit = broker.submit_trusted_child
    edited = False
    def edit_in_admission_gap(*args, **kwargs):
        nonlocal edited
        if intel.edit_before_next_admission and not edited:
            edited = True
            with db._connection() as conn:
                conn.execute("UPDATE recipes SET last_modified='edited-mid-run' WHERE id='r'")
        return original_submit(*args, **kwargs)
    monkeypatch.setattr(broker, "submit_trusted_child", edit_in_admission_gap)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=889))
    assert intel.calls == 4  # item + receipt-linked memory child for each item
    receipt = broker.store.receipt(result["parent_operation_id"])
    assert receipt is not None and receipt["outcome"] == "succeeded"
