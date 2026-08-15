"""The worker-local replay reservation ledger (HS-131-16, design §4.1).

This table lives in the WORKER's own database, never the hub's. One row elects the
single executor of one signed dispatch offer, and the election is the primary-key
conflict itself: ``INSERT … ON CONFLICT DO NOTHING`` is atomic across threads,
across concurrent worker processes, and across a restart, so "has this offer
already been executed here?" is never a check-then-run race.

Reservation happens BEFORE the execution revision is persisted, before the local
runner is constructed, before any engine exists, and before any provider is
reached. A duplicate therefore refuses having done no physical work at all.

Residue is reconciled, not retried. A worker that dies holding a reservation left
a physical attempt whose outcome nobody can honestly name, so startup marks it
``indeterminate`` — Article VI.2's named failure — rather than silently running the
model a second time under authority that was only ever good for once.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

from .base import BaseRepository

#: A reservation this process won and still owns.
RESERVED = "reserved"
#: The cohort finished and every local receipt is durable.
SETTLED = "settled"
#: Nobody can honestly say whether the physical attempt happened.
INDETERMINATE = "indeterminate"

#: The sibling file whose OS lock names the one live owner of a worker database.
OWNER_LOCK_SUFFIX = ".mesh-owner"


def _iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).isoformat()


class MeshWorkerRepository(BaseRepository):
    """At-most-once execution of one hub offer on THIS node."""

    table = "mesh_worker"

    # ── the one live owner (repair R7) ───────────────────────────────

    def owner_lock_path(self) -> Path:
        """The sibling file whose OS lock this worker database's owner holds."""
        return Path(str(getattr(self._db, "db_path", "mesh_worker")) + OWNER_LOCK_SUFFIX)

    @contextmanager
    def owner_lock(self) -> Iterator[None]:
        """Hold this worker database for one serving lifetime, or refuse.

        Startup reconciliation rewrites every reservation a previous life left
        open, so it may only run when this process is the ONLY live owner — a
        second ``mesh serve`` over the same database would otherwise declare a
        running worker's in-flight attempt indeterminate.

        The lock is an OS lock on a sibling file: it releases on close and on
        process exit of any kind, so a crashed worker leaves no stale claim and
        the next owner reconciles its residue honestly. It is narrow on purpose —
        one worker database, for as long as it is being served, and nothing else.
        """
        # Imported here, not at module scope: persistence does not depend on the
        # protocol vocabulary just to name one refusal.
        from ..mesh_authority.refusals import MeshAuthorityRefused, WORKER_OWNER_LOCKED

        path = self.owner_lock_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            try:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except ImportError:  # pragma: no cover - platform fallback
                pass
            except OSError:
                # Another live process owns this worker database. Refusing HERE
                # is what keeps a second worker away from the reservation ledger.
                raise MeshAuthorityRefused(WORKER_OWNER_LOCKED) from None
            yield
        finally:
            os.close(handle)

    def reserve(
        self,
        *,
        hub_key_id: str,
        hub_operation_id: str,
        first_ordinal: int,
        offer_id: str = "",
        job_id: str = "",
        now: Optional[datetime] = None,
    ) -> bool:
        """Elect this process as the executor. ``False`` means someone already was.

        The tuple is deliberately ``(hub key, hub operation, first ordinal)``:
        the key id scopes it to one pairing, the operation id is the hub's own
        logical attempt, and the first ordinal keeps a legitimate product retry —
        which arrives as a NEW hub operation — from colliding with this one.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO mesh_worker_reservations
                    (hub_key_id, hub_operation_id, first_ordinal, offer_id, job_id,
                     state, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (hub_key_id, hub_operation_id, first_ordinal) DO NOTHING
                """,
                (
                    str(hub_key_id), str(hub_operation_id), int(first_ordinal),
                    str(offer_id), str(job_id), RESERVED, _iso(now),
                ),
            )
        return cursor.rowcount > 0

    def get(
        self, *, hub_key_id: str, hub_operation_id: str, first_ordinal: int
    ) -> Optional[dict[str, Any]]:
        """The reservation row, or ``None``."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM mesh_worker_reservations
                WHERE hub_key_id = ? AND hub_operation_id = ? AND first_ordinal = ?
                """,
                (str(hub_key_id), str(hub_operation_id), int(first_ordinal)),
            ).fetchone()
        return dict(row) if row is not None else None

    def settle(
        self,
        *,
        hub_key_id: str,
        hub_operation_id: str,
        first_ordinal: int,
        terminal_outcome: str,
        now: Optional[datetime] = None,
    ) -> bool:
        """Close the reservation this process owns. ``False`` means it lost it.

        Sol's round-four ruling 8: a failed CAS is not a cosmetic detail. The
        worker no longer owns the reservation, so it may not report the cohort as
        recorded — the caller halts rather than continuing to claim work under a
        ledger it does not own.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE mesh_worker_reservations
                SET state = ?, terminal_outcome = ?, settled_at = ?
                WHERE hub_key_id = ? AND hub_operation_id = ? AND first_ordinal = ?
                  AND state = ?
                """,
                (
                    SETTLED, str(terminal_outcome), _iso(now),
                    str(hub_key_id), str(hub_operation_id), int(first_ordinal), RESERVED,
                ),
            )
        return cursor.rowcount > 0

    def reconcile_abandoned(self, *, now: Optional[datetime] = None) -> int:
        """Mark every reservation left open by a previous life indeterminate.

        Called once at worker startup. Never a retry: an abandoned reservation may
        have reached the provider, so the honest terminal state is "unknown", and
        the hub's own deadline is what closes the job.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE mesh_worker_reservations
                SET state = ?, terminal_outcome = ?, settled_at = ?
                WHERE state = ?
                """,
                (INDETERMINATE, INDETERMINATE, _iso(now), RESERVED),
            )
        return int(cursor.rowcount or 0)


__all__ = [
    "INDETERMINATE",
    "MeshWorkerRepository",
    "OWNER_LOCK_SUFFIX",
    "RESERVED",
    "SETTLED",
]
