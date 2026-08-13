"""Performing a cancellation: the admitted ``inference.cancel`` signal.

Lifted out of :mod:`.inference_runner` verbatim (HS-131-10 round 2) so the
runner module stays inside the kernel's 300-line file budget while round 2's
logical cancellation fence, retry publication rebinding, and engine-context
guard are added to it. The behaviour is unchanged: same states, same election
point, same receipts, same dispositions. ``InferenceRunner._perform_cancel``
still exists and still delegates here, so instance-level monkeypatching in the
runner's own suite keeps working.

Requesting a cancellation and PERFORMING it are deliberately separate: either
the public caller or ``invoke()`` may reach the election point first, but only
the winner touches the adapter.
"""

from __future__ import annotations

import threading
import uuid
from typing import Any


def perform_cancel(runner: Any, iid: str, active: Any, principal: Any) -> str:
    """Win the election, submit the admitted cancel signal, and close out."""
    with active.condition:
        # This is the election point.  A request is deliberately separate
        # from performing it: either the public caller or invoke() may get
        # here first, but only the winner may touch the adapter.
        dispatching = active.state == "DISPATCHING"
        if active.state == "CANCEL_REQUESTED":
            active.state = "CANCELLING"
        elif active.state == "CANCELLING":
            while active.state == "CANCELLING": active.condition.wait()
            return runner._terminal_disposition(active)
        elif not dispatching:
            return runner._terminal_disposition(active)
    sid = "cancel_" + uuid.uuid4().hex
    raw = {"request_schema": 1, "request_id": sid, "idempotency_key": sid, "operation": {"name": "inference.cancel", "version": 1}, "target": {}, "parent_operation_id": active.operation_id, "arguments": {"invocation_id": iid, "signal_id": sid, "reason": "cancelled"}}
    acknowledged = False; disposition_known = False; cancel_operation_id = ""
    try:
        signal = runner._broker.submit(raw, principal)
        if signal["state"] == "refused": return runner._cancel_refused(active, "refused")
        approved = runner._broker.decide(signal["operation_id"], "approve", signal["revision"], principal)
        cancel_operation_id = approved["operation_id"]
        if not runner._broker.claim(active.node, sid).get("operations"): return runner._cancel_refused(active, "refused")
        cancel_result: list[object] = []
        cancel_error: list[BaseException] = []
        def run_cancel():
            try: cancel_result.append(active.adapter.cancel())
            except BaseException as exc: cancel_error.append(exc)
        cancel_thread = threading.Thread(target=run_cancel, daemon=True)
        cancel_thread.start()
        cancel_thread.join(runner._cancel_timeout)
        if cancel_thread.is_alive():
            disposition = "unknown"; acknowledged = True; disposition_known = True
            with active.condition: active.closing = True
            runner._persist_receipt(active, cancel_operation_id, "indeterminate", "cancel-disposition:unknown")
            with active.condition:
                active.closing = False; active.disposition = disposition; active.cancelled.set(); active.condition.notify_all()
            runner._finish(active, iid, "indeterminate", cancellation_owner=True)
            return "unknown"
        if cancel_error: raise cancel_error[0]
        disposition = str(cancel_result[0]); acknowledged = disposition != "completed"; disposition_known = True
        child_outcome = {"cancelled": "succeeded", "completed": "refused", "unknown": "indeterminate"}.get(disposition, "indeterminate")
        child_ref = f"invocation:{iid}" if disposition == "cancelled" else f"cancel-disposition:{disposition}"
        with active.condition: active.closing = True
        runner._persist_receipt(active, cancel_operation_id, child_outcome, child_ref)
        with active.condition: active.closing = False; active.condition.notify_all()
        if dispatching:
            # DISPATCHING is cooperative: except for unknown, the dispatcher
            # elects invocation closure only after adapter.dispatch returns.
            if acknowledged: active.cancelled.set()
            with active.condition: active.disposition = disposition; active.condition.notify_all()
            if disposition == "unknown":
                runner._finish(active, iid, "indeterminate", cancellation_owner=True)
                return "unknown"
            with active.condition:
                while active.state == "DISPATCHING": active.condition.wait()
            return runner._terminal_disposition(active)
        if acknowledged:
            active.cancelled.set()
            with active.condition: active.closing = True
            runner._persist_receipt(active, active.operation_id, "indeterminate" if disposition == "unknown" else "cancelled", "")
        with active.condition: active.disposition = disposition; active.state = "RUNNING" if disposition == "completed" else "CANCELLED"; active.closing = False; active.condition.notify_all()
        return disposition
    except BaseException as exc:
        if disposition_known:
            with active.condition:
                if active.state == "CLOSURE_FAILED": raise active.closure_error
            raise
        if cancel_operation_id:
            with active.condition: active.closing = True
            runner._persist_receipt(active, cancel_operation_id, "failed", "cancel-disposition:failed")
            with active.condition: active.closing = False; active.condition.notify_all()
        runner._cancel_refused(active, "refused")
        if not isinstance(exc, Exception): raise
        return "refused"


__all__ = ["perform_cancel"]
