"""Parked 2026-11-08 (Lane I, engine door): the Cadence draft's parent-run
mechanics (frozen bundle, parent cancellation, stage recovery, crash close).
The draft is one root invoke through the engine door now. Kept, not run
(tests/_parked/conftest.py)."""
from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

import pytest

from tests.unit.test_residual_service_admission import (  # noqa: F401
    CALLER, _children, _parents, _receipt, _rig, _rows,
)


def test_assignment_edit_after_bundle_freeze_cannot_retarget_cadence(
    tmp_path, monkeypatch
) -> None:
    """The exact OWNER assignment is frozen before the provider can run."""
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    _profile(db, "cadence-edited")
    real_admit = broker.inference_adoption_service.admit_on_frozen_route

    def admit_after_assignment_edit(*args: Any, **kwargs: Any):
        InferenceAssignmentService(db).set_assignment(
            ASSIGNMENT_OWNER,
            {
                "command_id": "replace-cadence-route",
                "expected_revision": 1,
                "scope": {"kind": "capability", "capability_id": "background.cadence_draft"},
                "entries": [{"profile_id": "cadence-edited", "profile_revision": 1}],
            },
        )
        return real_admit(*args, **kwargs)

    monkeypatch.setattr(
        broker.inference_adoption_service, "admit_on_frozen_route", admit_after_assignment_edit
    )
    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "llm"
    assert leaf.attempts == 1
    with db._connection() as conn:
        profile_ids = [row[0] for row in conn.execute(
            "SELECT profile_id FROM inference_route_plan_entries ORDER BY route_leg_ordinal"
        ).fetchall()]
    assert profile_ids == ["cadence-route"]
    assert InferenceAssignmentService(db).get_assignment(
        ASSIGNMENT_OWNER, {"kind": "capability", "capability_id": "background.cadence_draft"}
    )["entries"][0]["profile_id"] == "cadence-edited"



@pytest.mark.parametrize("order", ["parent_closes_first", "signal_first"])
def test_a_cancelled_cadence_parent_never_publishes_its_late_draft(
    tmp_path, monkeypatch, order
) -> None:
    """Cancellation lands while the provider is in flight: nothing publishes.

    The child EARNED its receipt and keeps it — the provider really did answer, and
    rewriting that row would be the dishonest fix. What is fenced is PUBLICATION:
    the stage is discarded, the caller receives the deterministic action, and no
    drafted text reaches the surface.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    from tests._cancel_after_return import force_cancel_order

    force_cancel_order(monkeypatch, order)

    class CancellingIntel:
        active_provider = "local"

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            parent_id = _parents(db)[0]["operation_id"]
            broker.parent_run_controller.cancel_by_operation_id(CALLER, parent_id)
            return DRAFT

    broker.inference_runner._engine_factory = lambda _revision, **_: CancellingIntel()

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    assert "Watchdog the intel queue" not in str(detail["next_action"])
    assert leaf.attempts == 1
    children = _children(db)
    assert len(children) == 1
    from tests._cancel_after_return import assert_provider_return_on_record

    # The provider returned in both orders: the receipt keeps that fact.
    assert_provider_return_on_record(
        db, children[0]["operation_id"], fenced=order == "signal_first"
    )
    assert _receipt(db, _parents(db)[0]["operation_id"])["outcome"] == "cancelled"
    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    # Parent closes first: the child staged its draft and the cancelled parent
    # discarded it. Signal first: the fenced result was never staged.
    assert [(row["kind"], row["state"]) for row in stages] == (
        [("cadence-next-action", "DISCARDED")] if order == "parent_closes_first" else []
    ), stages


def _wait(predicate, *, timeout: float = 5.0) -> bool:
    """Bounded poll — no sleeps in the assertion path, no unbounded waits."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_cancelling_the_request_task_cancels_the_parent_and_publishes_nothing(
    tmp_path, monkeypatch
) -> None:
    """The realistic disconnect: the REQUEST goes away, the provider does not.

    Cancelling the awaiting coroutine cancels nothing inside ``asyncio.to_thread``
    — the provider thread runs to completion regardless. The pre-fix service
    caught that ``CancelledError`` in its generic arm and closed the parent
    ``failed``, which is both a lie (nobody failed; the caller left) and unsafe:
    ``FAILED`` is not one of the states the projection stager fences on, so the
    surviving thread's output published through the next recovery pass.

    A durable CANCELLED parent is what makes late output unpublishable, so that is
    what this asserts — together with the child keeping whatever terminal receipt
    it honestly earned.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()

    class BlockingIntel:
        active_provider = "local"

        def run_prompt(self, **_: Any) -> str:
            leaf.hit()
            entered.set()
            release.wait(5.0)
            return DRAFT

    broker.inference_runner._engine_factory = lambda _revision, **_: BlockingIntel()

    async def drive() -> None:
        task = asyncio.create_task(service.get_loop(CALLER, loop.id))
        while not entered.is_set():
            await asyncio.sleep(0.01)
        # The client is gone. Nothing has told the provider thread yet.
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # Only now does the provider answer -- into a request that no longer exists.
        release.set()

    asyncio.run(drive())

    assert leaf.attempts == 1
    parents = _parents(db)
    assert len(parents) == 1
    parent_receipt = _receipt(db, parents[0]["operation_id"])
    assert parent_receipt is not None, "the cancelled parent must still terminalize"
    assert parent_receipt["outcome"] == "cancelled", parent_receipt["outcome"]

    children = _children(db)
    assert len(children) == 1
    assert _wait(lambda: _receipt(db, children[0]["operation_id"]) is not None), (
        "the admitted child never reached a terminal receipt"
    )
    # Recovery is the pass that used to turn the survivor's output into PUBLISHED.
    broker.projection_stager.recover()
    published = [
        row for row in _rows(db, "SELECT * FROM kernel_projection_stages")
        if row["state"] == "PUBLISHED"
    ]
    assert published == [], f"late output published after cancellation: {published}"


def test_recovery_discards_a_cadence_stage_left_by_a_cancelled_request(
    tmp_path, monkeypatch
) -> None:
    """The other ordering: the provider WON the race and already staged.

    Here the child completes and stages its projection before the cancellation
    lands, so a stage row genuinely exists — this is the exact shape the HS-131-13
    audit reproduced, where ``ProjectionStager.recover`` finalized the survivor
    into ``PUBLISHED``. With the parent durably CANCELLED the discard rule
    registered for ``cadence-next-action`` fires instead, so the row ends
    ``DISCARDED`` and no drafted text is ever materialized.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)
    staged = threading.Event()
    release = threading.Event()
    real_stage = broker.projection_stager.stage

    def blocking_stage(*args: Any, **kwargs: Any):
        # Stage for real (the row becomes durable), then hold the worker thread
        # right there so the cancellation is guaranteed to land AFTER staging.
        result = real_stage(*args, **kwargs)
        staged.set()
        release.wait(5.0)
        return result

    monkeypatch.setattr(broker.projection_stager, "stage", blocking_stage)

    async def drive() -> None:
        task = asyncio.create_task(service.get_loop(CALLER, loop.id))
        while not staged.is_set():
            await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()

    asyncio.run(drive())

    assert leaf.attempts == 1
    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [row["kind"] for row in stages] == ["cadence-next-action"], stages
    assert _receipt(db, _parents(db)[0]["operation_id"])["outcome"] == "cancelled"
    children = _children(db)
    assert len(children) == 1
    assert _wait(lambda: _receipt(db, children[0]["operation_id"]) is not None)

    # The pass that used to publish it.
    broker.projection_stager.recover()

    stages = _rows(db, "SELECT * FROM kernel_projection_stages")
    assert [(row["kind"], row["state"]) for row in stages] == [
        ("cadence-next-action", "DISCARDED")
    ], stages


def test_an_unexpected_crash_still_terminalizes_the_cadence_parent(
    tmp_path, monkeypatch
) -> None:
    """No OPEN parent is left behind waiting for the lease reaper.

    ``get_loop`` is fail-closed by charter, so a crash inside the draft is
    invisible to the caller — which is exactly how a parent operation ends up with
    no terminal receipt for a lease window. Article XI.2 admits no such gap: the
    parent closes ``failed`` on the way out, in the same request.
    """
    db, broker, service, loop, leaf, _revisions = _rig(tmp_path, monkeypatch)

    def exploding_finalize(*_args: Any, **_kwargs: Any):
        raise RuntimeError("projection store went away")

    monkeypatch.setattr(broker.projection_stager, "finalize", exploding_finalize)

    detail = asyncio.run(service.get_loop(CALLER, loop.id))

    assert detail["next_action"]["generated_by"] == "deterministic"
    parents = _parents(db)
    assert len(parents) == 1
    receipt = _receipt(db, parents[0]["operation_id"])
    assert receipt is not None and receipt["outcome"] == "failed"
    # The child that really ran keeps its own honest, separate receipt.
    children = _children(db)
    assert len(children) == 1
    assert _receipt(db, children[0]["operation_id"])["outcome"] == "succeeded"


# ================================================= 5. The deletions, pinned


