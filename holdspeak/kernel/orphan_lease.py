"""The orphan-lease decision: when a claimed parent shell with no run row is dead.

A ``ParentRunController.start(..., _defer_persist=True)`` caller (the deferred
intel binder, ``services/meeting_deferred_queue_binding.py``) commits the
operation's claim first and writes the ``kernel_parent_runs`` row later, inside
its own queue-claim transaction.  Between the two commits a claimed operation
with no parent row is a LIVE shell, not an orphan.  The hub's one-second
kernel liveness tick (``web_server._kernel_liveness_loop`` ->
``reconcile_abandoned``) landing in that gap receipted the shell
``indeterminate``, and the executor's first child admission then met
``parent_operation_not_running`` -- a terminal ``refused`` at attempt 1 with
nothing run (HS-200-12, CI 2026-09-18).

A shell that lost its claim race is its binder's own ``discard()``.  Only a
shell unpersisted for a whole lease -- ``updated_at`` (stamped by the broker
clock at claim, ``kernel/journal.py``) older than ``lease_seconds`` on the same
clock -- is a dead context.
"""
from __future__ import annotations

from typing import Any, Iterable


def orphaned_claimed_shells(
    conn: Any, operation_names: Iterable[str], *, now: float, lease_seconds: float,
) -> list[Any]:
    """Claimed parent operations with no run row, older than one lease."""
    names = tuple(operation_names)
    placeholders = ",".join("?" for _ in names)
    return conn.execute(
        f"""SELECT o.operation_id FROM kernel_operations o
               LEFT JOIN kernel_parent_runs p ON p.operation_id=o.operation_id
              WHERE o.state='claimed' AND p.operation_id IS NULL
                AND o.name IN ({placeholders})
                AND o.updated_at < ?""",
        (*names, now - lease_seconds),
    ).fetchall()


__all__ = ["orphaned_claimed_shells"]
