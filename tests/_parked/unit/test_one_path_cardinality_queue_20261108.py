"""PARKED 20261108 (Lane S2): cases of ``tests/unit/test_one_path_cardinality.py`` that drove the item queue.

The item queue is parked (holdspeak/services/_parked/workbench_runner_queue_20261108.py);
an automation's run is a Program of one prompt step. Not collected; they import the
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_one_path_cardinality import *  # noqa: F401,F403


def test_success_workbench_one_item_is_one_child_one_receipt_one_physical_attempt(tmp_path, monkeypatch):
    """Scenario: success. Surface: manual Workbench."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "workbench.db")
    profile = db.profiles.upsert(
        profile_id="wb-profile", name="Profile", kind="openAICompatible",
        base_url="http://wb-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(item_id="wb-item-1", workbench_id=workbench.id, title="Item 1", body="input 1")
    broker = _configure(db)

    leaf = _Leaf()
    broker.inference_runner._engine_factory = lambda _revision, **_: _LeafEngine(leaf, "provider output")
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    # The parent itself is typed OUT of the child cohort by name.
    parent_row = _operation(db, result["parent_operation_id"])
    assert parent_row["name"] == "workbench.run" != "inference.invoke"
    # HS-143-10: the one physical attempt carries the parent's immutable route,
    # rather than an item-local target lookup selected after parent admission.
    with db._connection() as conn:
        frozen = conn.execute(
            """SELECT member.route_plan_id frozen_route_id, operation.route_plan_id operation_route_id
                 FROM inference_route_attempts attempt
                 JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                 JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                 JOIN inference_parent_route_bundles bundle ON bundle.parent_operation_id=?
                 JOIN inference_parent_route_bundle_members member ON member.bundle_id=bundle.id
                WHERE attempt.child_operation_id=?""",
            (result["parent_operation_id"], children[0]["operation_id"]),
        ).fetchone()
    assert frozen is not None
    assert frozen["frozen_route_id"] == frozen["operation_route_id"]


# =========================================================== PRE-DISPATCH REFUSAL
# Surface: bare runner rig (cheapest rig for a claim-time refusal).


def test_provider_failure_workbench_is_one_child_one_failed_receipt_one_physical_attempt(tmp_path):
    """Scenario: provider failure. Surface: manual Workbench."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "workbench-fail.db")
    profile = db.profiles.upsert(
        profile_id="wb-fail-profile", name="Profile", kind="openAICompatible",
        base_url="http://wb-fail-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb-fail-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb-fail-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(item_id="wb-fail-item-1", workbench_id=workbench.id, title="Item 1", body="input 1")
    broker = _configure(db)

    leaf = _Leaf()
    broker.inference_runner._engine_factory = lambda _revision, **_: _LeafEngine(
        leaf, error=RuntimeError("provider said no")
    )
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "failed"
    assert counts == {"engine_factory": 1, "dispatch": 1}
    assert leaf.attempts == 1  # the request reached the provider and it refused


# ==================================================================== CANCELLATION
# Surface: Decision promotion (named product surface: cancellation-after-provider-return).


def test_the_dispatch_context_is_minted_from_the_CHILD_claim_not_a_parent(tmp_path):
    """The witness proof, end to end, plus the child-warrant fix (Terra finding A).

    Two things are true here and neither was before:

    * the context the factory receives was minted from a witness that
      ``ExecutorPlane.claim`` issued — there is no other way to obtain one, so
      every green run of this suite is also a proof that admission happened;
    * its authenticated basis is THIS CHILD's warrant. The claim's ancestor walk
      used to assign through the same local name, so a claimed child was handed
      back its last PARENT's warrant, and everything downstream (the mesh
      envelope, the context basis) was bound to the wrong operation.
    """
    from holdspeak.kernel.claim_witness import ClaimWitness
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "witness.db")
    profile = db.profiles.upsert(
        profile_id="witness-profile", name="Profile", kind="openAICompatible",
        base_url="http://witness-profile", model="wb-model",
    )
    recipe = db.recipes.upsert(
        recipe_id="witness-recipe", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="witness-run", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    db.workbench_items.upsert(
        item_id="witness-item-1", workbench_id=workbench.id, title="Item 1", body="input 1",
    )
    broker = _configure(db)
    leaf = _Leaf()
    seen: dict[str, Any] = {}

    def factory(_revision: Any, *, warrant: Any = None, context: Any = None) -> Any:
        seen["context"], seen["warrant"] = context, dict(warrant or {})
        return _LeafEngine(leaf, "provider output")

    broker.inference_runner._engine_factory = factory
    counts = _instrument(broker.inference_runner)

    result = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False))

    children = _assert_reconciled(
        db, parent_operation_id=result["parent_operation_id"], counts=counts, leaf=leaf,
        expect_children=1,
    )
    child_id = children[0]["operation_id"]
    child_warrant = broker.store.operation(child_id)["warrant"]
    parent_warrant = broker.store.operation(result["parent_operation_id"])["warrant"]

    assert seen["context"].operation_id == child_id  # the CHILD it just claimed
    assert seen["warrant"] == dict(child_warrant)
    assert seen["context"].warrant_basis == str(child_warrant["signature"])
    assert str(child_warrant["signature"]) != str(parent_warrant["signature"])
    # The witness itself is spent: one claim mints exactly one context.
    from holdspeak.kernel.claim_witness import consume_claim_witness
    from holdspeak.kernel.model import KernelRefused as _Refused

    stale = ClaimWitness.__new__(ClaimWitness)
    with pytest.raises(_Refused):
        consume_claim_witness(stale)


# ======================================================= ROUND 2: THE REPAIRS
# Six defects Terra's hostile pass found in the first repair round. Each test
# below is the probe that found one, made permanent.
