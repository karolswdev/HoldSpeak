"""Kernel-operation transitions serialized against parent publication claims."""
from __future__ import annotations

import sqlite3
import time
from typing import Any

from .journal_txn import json_encode as _json
from .model import KernelRefused


def transition(
    store: Any,
    operation_id: str,
    expected_revision: int,
    state: str,
    **changes: Any,
) -> dict[str, Any]:
    assignments = ["state=?", "revision=revision+1", "updated_at=?"]
    values: list[Any] = [state, store._clock()]
    allowed = {"decision", "warrant_json", "warrant_revoked", "claimed_by"}
    for key, value in changes.items():
        if key not in allowed:
            raise KernelRefused("operation_mutation_not_allowed", key)
        assignments.append(f"{key}=?")
        values.append(_json(value) if key == "warrant_json" else value)
    values.extend((operation_id, expected_revision))
    wait_until = time.monotonic() + store._publication_wait_seconds
    while True:
        try:
            with store._connection() as conn:
                result = conn.execute(
                    f"UPDATE kernel_operations SET {','.join(assignments)} "
                    "WHERE operation_id=? AND revision=?",
                    values,
                )
                if result.rowcount != 1:
                    raise KernelRefused(
                        "operation_revision_conflict", operation_id=operation_id
                    )
        except sqlite3.IntegrityError as exc:
            if "kernel_parent_publication_in_progress" not in str(exc):
                raise
            if time.monotonic() >= wait_until:
                raise KernelRefused(
                    "parent_publication_in_progress", operation_id=operation_id
                ) from exc
            time.sleep(store._publication_poll_seconds)
            continue
        return store.operation(operation_id) or {}


__all__ = ["transition"]
