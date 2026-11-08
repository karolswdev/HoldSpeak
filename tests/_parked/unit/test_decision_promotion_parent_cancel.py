"""Parked 2026-11-08 (Lane I, engine door): the decision promotion draft no
longer runs under a parent route bundle, so a parent cancellation has nothing
to cancel. Kept, not run (tests/_parked/conftest.py)."""
from __future__ import annotations

import asyncio

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.errors import ConflictError
from tests.unit.test_decision_record_service import _accepted_meeting_decision
from tests.unit.test_one_path_cardinality import (  # noqa: F401
    _Leaf, _assert_reconciled, _configure, _instrument, _operation, _receipt,
)
from typing import Any


@pytest.mark.parametrize("order", ["parent_closes_first", "signal_first"])
def test_promotion_cancellation_after_provider_return_never_publishes_artifact(tmp_path, monkeypatch, order):
    from tests._cancel_after_return import force_cancel_order

    force_cancel_order(monkeypatch, order)
    db = Database(tmp_path / "promotion.db")
    _accepted_meeting_decision(db, "dec-fence")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion", "profile_revision": 1}],
    })
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")

    class CancellingIntel:
        def run_prompt(self, **_):
            with db._connection() as conn:
                parent_id = conn.execute(
                    "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
                ).fetchone()[0]
            # The durable parent cancellation lands while the provider call is
            # in flight, before the runner can elect a successful child receipt.
            broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
            return "late draft that must not publish"

    broker.inference_runner._engine_factory = lambda _revision, **_kw: CancellingIntel()
    service = DecisionLifecycleService(db, kernel=broker)
    # The child's provider work completed, so its receipt is EARNED
    # (succeeded); the cancellation election fences PUBLICATION instead —
    # the finalize discard refuses the artifact by name.
    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(service.draft_promoted_with_model(owner, "dec-fence", "note", {}))

    with db._connection() as conn:
        parent_id = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
        ).fetchone()[0]
        child_id = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE parent_operation_id=? AND name='inference.invoke'",
            (parent_id,),
        ).fetchone()[0]
        artifact_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    parent_receipt = broker.store.receipt(parent_id)
    assert artifact_count == 0
    from tests._cancel_after_return import assert_provider_return_on_record

    assert_provider_return_on_record(db, child_id, fenced=order == "signal_first")
    assert parent_receipt is not None and parent_receipt["outcome"] == "cancelled"


def test_promotion_cancelled_after_child_is_eligible_discards_artifact(tmp_path):
    db = Database(tmp_path / "promotion-late.db")
    _accepted_meeting_decision(db, "dec-late")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion-late")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-late", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-late", "profile_revision": 1}],
    })
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db); owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    broker.inference_runner._engine_factory = lambda _revision, **_kw: type("Intel", (), {"run_prompt": lambda self, **_: "eligible draft"})()
    finalize = broker.projection_stager.finalize
    def cancel_before_finalize(invocation_id):
        parent_id = broker.store.operation(broker.projection_stager.get(invocation_id).operation_id)["parent_operation_id"]
        broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
        return finalize(invocation_id)
    broker.projection_stager.finalize = cancel_before_finalize
    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(owner, "dec-late", "note", {}))
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0




# From tests/unit/test_one_path_cardinality.py
@pytest.mark.parametrize("order", ["parent_closes_first", "signal_first"])
def test_cancellation_after_provider_return_is_one_child_one_receipt_one_physical_attempt(tmp_path, monkeypatch, order):
    """Scenario: cancellation (durable parent cancel lands while provider is in flight).

    Surface: Decision promotion. The child's provider work completed and EARNED
    a succeeded receipt; the parent cancellation elects PUBLICATION fencing
    instead. Reconciliation is at the child cohort: one admitted child, one
    (succeeded) terminal receipt, one physical attempt -- the parent's own
    ``cancelled`` receipt is a SEPARATE, non-child row.
    """
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.errors import ConflictError
    from tests._cancel_after_return import force_cancel_order

    force_cancel_order(monkeypatch, order)

    db = Database(tmp_path / "promotion-cardinality.db")
    _accepted_meeting_decision(db, "dec-cardinality")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion-cardinality")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-cardinality-promotion", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-cardinality", "profile_revision": 1}],
    })
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-cardinality-owner")

    leaf = _Leaf()

    class CancellingIntel:
        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            with db._connection() as conn:
                parent_id = conn.execute(
                    "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
                ).fetchone()[0]
            broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
            return "late draft that must not publish"

    broker.inference_runner._engine_factory = lambda _revision, **_: CancellingIntel()
    counts = _instrument(broker.inference_runner)
    service = DecisionLifecycleService(db, kernel=broker)

    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(service.draft_promoted_with_model(owner, "dec-cardinality", "note", {}))

    with db._connection() as conn:
        parent_id = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
        ).fetchone()[0]

    children = _assert_reconciled(
        db, parent_operation_id=parent_id, counts=counts, leaf=leaf, expect_children=1,
    )
    from tests._cancel_after_return import assert_provider_return_on_record

    # The provider returned in both orders and the receipt says so. With the
    # signal first, a cancel was requested for this child: its result is fenced.
    assert_provider_return_on_record(
        db, children[0]["operation_id"], fenced=order == "signal_first"
    )
    # The parent's OWN receipt is cancelled -- a separate row, never counted as
    # a child, and never conflated with the child's earned outcome.
    parent_receipt = _receipt(db, parent_id)
    assert parent_receipt is not None and parent_receipt["outcome"] == "cancelled"
    parent_row = _operation(db, parent_id)
    assert parent_row["name"] != "inference.invoke"


