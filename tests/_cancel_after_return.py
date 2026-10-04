"""One deterministic order for the "cancel after provider return" tests.

A parent cancel that lands while a child's provider call is in flight starts a
daemon thread that sends the physical cancel signal to the child
(``holdspeak/kernel/parent_terminal.py``, ``cancel_parent``). That thread races
the caller, which closes the parent:

* the parent closes first (the usual order on an idle machine): the signal is
  refused, the provider returns, the child keeps its earned ``succeeded``
  receipt, and publication is fenced;
* the signal thread is first (a loaded machine): the child is cancelled
  mid-flight and its receipt is ``cancelled``.

The two orders are lawful product behaviour, but these tests name the first
one: the provider returned, the child earned its receipt, nothing publishes.
They got it only from thread timing, so they failed in full runs under load.

``hold_child_cancel_until_provider_returns`` makes the order a fact: the
signal thread waits on an event that is set when the child's own terminal
receipt is durable. No wall-clock budget decides the result. The deadline on
the wait is only a guard against a hung test.
"""
from __future__ import annotations

import threading
from typing import Any

_GUARD_SECONDS = 120.0


def hold_child_cancel_until_provider_returns(monkeypatch: Any) -> threading.Event:
    """Hold the child cancel signal until the child's receipt is durable.

    Returns the event that is set when the child's terminal receipt is
    written. Every other part of the path is the real product code.
    """
    from holdspeak.kernel.inference_runner import InferenceRunner

    child_receipt_durable = threading.Event()
    real_persist = InferenceRunner._persist_receipt
    real_cancel = InferenceRunner._cancel_internal

    def persist(self: Any, active: Any, operation_id: str, *args: Any, **kwargs: Any) -> Any:
        try:
            return real_persist(self, active, operation_id, *args, **kwargs)
        finally:
            if operation_id == active.operation_id:
                child_receipt_durable.set()

    def cancel_internal(self: Any, invocation_id: str, principal: Any) -> str:
        child_receipt_durable.wait(_GUARD_SECONDS)
        return real_cancel(self, invocation_id, principal)

    monkeypatch.setattr(InferenceRunner, "_persist_receipt", persist)
    monkeypatch.setattr(InferenceRunner, "_cancel_internal", cancel_internal)
    return child_receipt_durable
