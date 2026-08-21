"""Minimal serialized lease for newly activated local model artifacts.

This is the Slice-2 safety floor, not the later capacity scheduler: one v2
local artifact may cross the physical loading leaf at a time on a hub.  The
lease is durable, crash-reconciled, and bound to the admitted kernel operation.
"""
from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .model import KernelRefused


_PROCESS_EPOCH = f"{os.getpid()}:{uuid.uuid4().hex}"
_LEASE_SECONDS = 3600.0


@dataclass(frozen=True)
class LocalRuntimeLease:
    lease_id: str
    operation_id: str


def acquire_local_runtime_lease(
    db: Any, *, operation_id: str, deployment_revision_id: str,
    clock: Any = time.time,
) -> LocalRuntimeLease:
    now = float(clock())
    lease_id = "local_lease_" + uuid.uuid4().hex
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """UPDATE inference_runtime_leases
                  SET state='expired', updated_at=?
                WHERE state='active' AND process_id<>?""",
            (now, _PROCESS_EPOCH),
        )
        replay = conn.execute(
            """SELECT lease_id FROM inference_runtime_leases
                WHERE operation_id=? AND state='active'""",
            (operation_id,),
        ).fetchone()
        if replay is not None:
            conn.commit()
            return LocalRuntimeLease(str(replay["lease_id"]), operation_id)
        active = conn.execute(
            "SELECT operation_id FROM inference_runtime_leases WHERE state='active'"
        ).fetchone()
        if active is not None:
            conn.rollback()
            raise KernelRefused("inference_local_runtime_busy")
        conn.execute(
            """INSERT INTO inference_runtime_leases
               (lease_id,operation_id,deployment_revision_id,state,process_id,
                expires_at,created_at,updated_at)
               VALUES (?,?,?,'active',?,?,?,?)""",
            (
                lease_id, operation_id, deployment_revision_id,
                _PROCESS_EPOCH, now + _LEASE_SECONDS, now, now,
            ),
        )
        conn.commit()
    return LocalRuntimeLease(lease_id, operation_id)


def release_local_runtime_lease(
    db: Any, lease: LocalRuntimeLease, *, indeterminate: bool = False,
    clock: Any = time.time,
) -> None:
    with db._connection() as conn:
        conn.execute(
            """UPDATE inference_runtime_leases
                  SET state=?, updated_at=?
                WHERE lease_id=? AND operation_id=? AND state='active'""",
            (
                "indeterminate" if indeterminate else "released",
                float(clock()), lease.lease_id, lease.operation_id,
            ),
        )


__all__ = [
    "LocalRuntimeLease", "acquire_local_runtime_lease",
    "release_local_runtime_lease",
]
