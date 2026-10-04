"""Force each order of the parent-cancel race, one at a time.

A parent cancel that lands while a child's provider call is in flight starts a
daemon thread that sends the physical cancel signal to the child
(``holdspeak/kernel/parent_terminal.py``, ``cancel_parent``). That thread races
the caller, which closes the parent:

* ``PARENT_CLOSES_FIRST``: the signal arrives after the child is closed and
  does nothing;
* ``SIGNAL_FIRST``: the adapter answers the cancel while the child is
  ``DISPATCHING``, and only then does the parent close.

The law is the same in the two orders (``cancel_fences_child`` in
``holdspeak/kernel/inference_cancel_signal.py``): an adapter that answers
``not_supported`` did not stop the provider call, so a provider that then
returns earns ``succeeded / provider_returned`` with its result reference. A
confirmed abort (``cancelled``) closes the child as ``cancelled``. The parent
is ``cancelled`` and publication is fenced in every case.

Before the kernel fix, ``SIGNAL_FIRST`` wrote a ``cancelled`` child receipt
with no result reference for a provider call that had returned. Thread timing
chose the order, so the tests were green on an idle machine and red in full
runs under load. ``force_cancel_order`` makes the order a fact: each side
waits on an event from the other. The deadline on a wait is only a guard
against a hung test.
"""
from __future__ import annotations

import threading
from typing import Any

PARENT_CLOSES_FIRST = "parent_closes_first"
SIGNAL_FIRST = "signal_first"
BOTH_ORDERS = (PARENT_CLOSES_FIRST, SIGNAL_FIRST)

_GUARD_SECONDS = 120.0


def force_cancel_order(monkeypatch: Any, order: str) -> None:
    """Make the child cancel signal and the parent close run in ``order``.

    Only the order is forced. The controller, the runner, the adapter and the
    receipts are the real product code.
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
