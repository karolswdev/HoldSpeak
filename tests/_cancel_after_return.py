"""Force each order of the cancel race, one at a time, and read the receipt.

A parent cancel that lands while a child's provider call is in flight starts a
daemon thread that sends the physical cancel signal to the child
(``holdspeak/kernel/parent_terminal.py``, ``cancel_parent``). That thread races
the caller, which closes the parent:

* ``PARENT_CLOSES_FIRST``: the signal arrives after the child is closed and
  does nothing. The child is ``succeeded / provider_returned``; the cancelled
  parent discards its stage.
* ``SIGNAL_FIRST``: a cancel is requested for the child while it is
  ``DISPATCHING``, and only then does the parent close.

The law (``cancelled_evidence`` in ``holdspeak/kernel/inference_cancel_signal.py``)
keeps two facts apart. What happened: a provider call that returned is recorded
as ``provider_returned`` with its result reference. Whether the result may be
used: never, when a cancel was requested for this child. The receipt state is
``cancelled`` with the signal ``cancel_fenced``; nothing is staged, published or
returned, whatever the adapter answered to the cancel.

Before the kernel fix, ``SIGNAL_FIRST`` wrote ``cancelled / dispatch_intent``
with no result reference: the record lost a provider return that was known.
Thread timing chose the order, so the tests were green on an idle machine and
red in full runs under load. ``force_cancel_order`` makes the order a fact:
each side waits on an event from the other. The deadline on a wait is only a
guard against a hung test.
"""
from __future__ import annotations

import threading
from typing import Any

PARENT_CLOSES_FIRST = "parent_closes_first"
SIGNAL_FIRST = "signal_first"
BOTH_ORDERS = (PARENT_CLOSES_FIRST, SIGNAL_FIRST)

_GUARD_SECONDS = 120.0


def force_cancel_order(monkeypatch: Any, order: str) -> threading.Event:
    """Make the child cancel signal and the parent close run in ``order``.

    Only the order is forced. The controller, the runner, the adapter and the
    receipts are the real product code. Returns the event that is set when the
    adapter has answered a cancel signal (for a test that cancels a child
    directly and must hold the provider's return until then).
    """
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.kernel.parent_run import ParentRunController

    assert order in BOTH_ORDERS, order
    child_receipt_durable = threading.Event()
    signal_settled = threading.Event()
    real_persist = InferenceRunner._persist_receipt
    real_cancel = InferenceRunner._cancel_internal
    real_close = ParentRunController.close

    def persist(self: Any, active: Any, operation_id: str, *args: Any, **kwargs: Any) -> Any:
        try:
            return real_persist(self, active, operation_id, *args, **kwargs)
        finally:
            # The child's own receipt, or the receipt of the cancel signal
            # (written when the adapter has answered).
            (child_receipt_durable if operation_id == active.operation_id else signal_settled).set()

    def cancel_internal(self: Any, invocation_id: str, principal: Any) -> str:
        if order == PARENT_CLOSES_FIRST:
            assert child_receipt_durable.wait(_GUARD_SECONDS), "the child never closed"
        return real_cancel(self, invocation_id, principal)

    def close(self: Any, context: Any, outcome: str, *args: Any, **kwargs: Any) -> Any:
        if order == SIGNAL_FIRST and outcome == "cancelled":
            assert signal_settled.wait(_GUARD_SECONDS), "the cancel signal never settled"
        return real_close(self, context, outcome, *args, **kwargs)

    monkeypatch.setattr(InferenceRunner, "_persist_receipt", persist)
    monkeypatch.setattr(InferenceRunner, "_cancel_internal", cancel_internal)
    monkeypatch.setattr(ParentRunController, "close", close)
    return signal_settled


def child_receipt_facts(db: Any, operation_id: str) -> dict[str, str]:
    """The durable receipt of one child: state, result reference, attested evidence."""
    import json

    with db._connection() as conn:
        receipt = conn.execute(
            "SELECT state,result_ref FROM kernel_receipts WHERE operation_id=?", (operation_id,)
        ).fetchone()
        attested = conn.execute(
            "SELECT material_json FROM kernel_inference_receipt_attestations WHERE operation_id=?",
            (operation_id,),
        ).fetchone()
    assert receipt is not None and attested is not None, "the child has no attested receipt"
    material = json.loads(attested[0])
    return {
        "state": str(receipt[0]), "result_ref": str(receipt[1]),
        "send_phase": str(material["send_phase"]), "runner_signal": str(material["runner_signal"]),
    }


def assert_provider_return_on_record(db: Any, operation_id: str, *, fenced: bool) -> None:
    """The provider returned, and the receipt says so. ``fenced``: a cancel was
    requested for this child, so its result is on the record but not for use."""
    facts = child_receipt_facts(db, operation_id)
    assert facts["send_phase"] == "provider_returned", facts
    assert facts["result_ref"], facts
    if fenced:
        assert (facts["state"], facts["runner_signal"]) == ("cancelled", "cancel_fenced"), facts
    else:
        assert (facts["state"], facts["runner_signal"]) == ("succeeded", "none"), facts


def cancel_child_in_flight(db: Any, signal_settled: threading.Event, cancel: Any) -> str:
    """Call from inside a fake provider: cancel the child that is in flight now.

    ``cancel(invocation_id)`` runs on its own thread (a real cancel waits for
    the dispatch to end). This returns when the adapter has answered the
    signal, so the provider's return is always after the cancel request.
    """
    with db._connection() as conn:
        invocation_id = str(conn.execute(
            "SELECT native_id FROM kernel_operations WHERE name='inference.invoke' "
            "ORDER BY created_at DESC LIMIT 1"
        ).fetchone()[0])
    threading.Thread(target=cancel, args=(invocation_id,), daemon=True).start()
    assert signal_settled.wait(_GUARD_SECONDS), "the cancel signal never settled"
    return invocation_id


def invoke_child_operation_id(db: Any, invocation_id: str) -> str:
    with db._connection() as conn:
        return str(conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE name='inference.invoke' AND native_id=?",
            (invocation_id,),
        ).fetchone()[0])
