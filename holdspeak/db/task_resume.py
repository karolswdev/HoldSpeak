"""HS-200-41: persistence for a Room ask that outlived the tab.

`/api/ask` is one blocking request/response that persists nothing, and
``ask_results`` stores the answer without the question.  ``project_ask_tasks``
is therefore the only durable record of what was asked: purpose, Project,
state, why it stopped, and when it was saved.

Two reads live here besides the table's own CRUD, because both are about the
SAME identity and belong beside it:

- :meth:`ProjectAskTaskRepository.find_ask_result` — the answer half.  It is
  already durable and replayable (``ask_results.invocation_id`` is UNIQUE and
  the kernel's materializer publishes it after the receipt settles); what was
  missing was the key back to it.  Finding a row here is what lets a resume
  CLAIM a late answer instead of paying for it twice (ruling B3).
- :meth:`ProjectAskTaskRepository.reconcile_orphans` — startup recovery.  It
  reconciles from receipts only and never re-dispatches, copying the discipline
  of ``recover_refinements_on_startup``.

Every INSERT names its columns (the reconcile engine appends columns at the
end of a table, so a positional INSERT rots on a long-lived database).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository

# The states a row can hold.  The full posture-6 vocabulary is in the CHECK so
# the `TaskResume` species can draw rows from every owner (ruling B8); the
# writers in this repository reach only the honest subset for an ask.
ASK_TASK_STATES = (
    "saved", "running", "waiting", "failed", "incomplete", "accepted", "discarded",
)

# What "unfinished" means for the Resume projection: everything the owner has
# not finished with.  `discarded` is a state, not a DELETE (ruling B6), and it
# is excluded here; `accepted` is finished.
UNFINISHED_ASK_TASK_STATES = ("saved", "running", "waiting", "failed", "incomplete")

# The named reason a row carries when the process that was running it died.
# A code, not a composed sentence (ruling B5).
HOST_LOST_CODE = "ask_task_host_lost"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class ProjectAskTask:
    """One saved Room ask, exactly as the table holds it."""

    id: str
    project_id: str
    invocation_id: str
    purpose: str
    lens: str
    recipe_key: str
    grounding_json: str
    state: str
    stopped_reason: str
    stopped_code: str
    custody_host_id: str
    custody_lease_epoch: int
    dispatch_host_id: str
    dispatch_lease_epoch: int
    resume_order: int
    saved_at: str
    updated_at: str
    settled_at: Optional[str]

    @property
    def grounding(self) -> dict[str, Any]:
        try:
            parsed = json.loads(self.grounding_json or "{}")
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}


def _row_to_model(row: Any) -> ProjectAskTask:
    return ProjectAskTask(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        invocation_id=str(row["invocation_id"]),
        purpose=str(row["purpose"]),
        lens=str(row["lens"]),
        recipe_key=str(row["recipe_key"]),
        grounding_json=str(row["grounding_json"]),
        state=str(row["state"]),
        stopped_reason=str(row["stopped_reason"]),
        stopped_code=str(row["stopped_code"]),
        custody_host_id=str(row["custody_host_id"]),
        custody_lease_epoch=int(row["custody_lease_epoch"]),
        dispatch_host_id=str(row["dispatch_host_id"]),
        dispatch_lease_epoch=int(row["dispatch_lease_epoch"]),
        resume_order=int(row["resume_order"]),
        saved_at=str(row["saved_at"]),
        updated_at=str(row["updated_at"]),
        settled_at=None if row["settled_at"] is None else str(row["settled_at"]),
    )


class ProjectAskTaskRepository(BaseRepository):
    """Read/write authority for ``project_ask_tasks``."""

    table = "project_ask_tasks"

    # ── writes ───────────────────────────────────────────────────────

    def create(
        self,
        *,
        task_id: str,
        project_id: str,
        invocation_id: str,
        purpose: str,
        lens: str = "Project",
        recipe_key: str = "",
        grounding: Any = None,
        state: str = "saved",
        stopped_reason: str = "",
        stopped_code: str = "",
        custody_host_id: str = "",
        custody_lease_epoch: int = 0,
    ) -> ProjectAskTask:
        """Write the row BEFORE anything is dispatched.

        The invocation identity is pinned here so a late answer under the same
        id can be claimed after a restart.
        """
        grounding_json = self._json_dumps(grounding or {}, fallback="{}")
        now = _now()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            order_row = conn.execute(
                "SELECT COALESCE(MAX(resume_order), 0) AS high FROM project_ask_tasks"
            ).fetchone()
            resume_order = int(order_row["high"]) + 1
            conn.execute(
                """INSERT INTO project_ask_tasks
                   (id, project_id, invocation_id, purpose, lens, recipe_key,
                    grounding_json, state, stopped_reason, stopped_code,
                    custody_host_id, custody_lease_epoch,
                    dispatch_host_id, dispatch_lease_epoch,
                    resume_order, saved_at, updated_at, settled_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 0, ?, ?, ?, NULL)""",
                (
                    str(task_id), str(project_id), str(invocation_id), str(purpose),
                    str(lens), str(recipe_key), grounding_json, str(state),
                    str(stopped_reason), str(stopped_code),
                    str(custody_host_id), int(custody_lease_epoch),
                    resume_order, now, now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM project_ask_tasks WHERE id = ?", (str(task_id),)
            ).fetchone()
        return _row_to_model(row)

    def claim_dispatch(self, task_id: str, host_id: str, lease_epoch: int) -> bool:
        """Take the in-flight lease for one resume.

        Returns False when the row is already terminal or already leased —
        the caller must not dispatch.  No state is written: an ask has no job
        row and cannot honestly wear ``running`` (ruling B8); the lease itself
        is the in-flight fact, mirroring ``refinement_invocations``.
        """
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            changed = conn.execute(
                """UPDATE project_ask_tasks
                      SET dispatch_host_id = ?, dispatch_lease_epoch = ?, updated_at = ?
                    WHERE id = ?
                      AND state NOT IN ('accepted', 'discarded')
                      AND dispatch_host_id = ''""",
                (str(host_id), int(lease_epoch), _now(), str(task_id)),
            ).rowcount
        return changed == 1

    def release_dispatch(self, task_id: str) -> None:
        """Drop the in-flight lease without touching the state."""
        with self._connection() as conn:
            conn.execute(
                """UPDATE project_ask_tasks
                      SET dispatch_host_id = '', dispatch_lease_epoch = 0, updated_at = ?
                    WHERE id = ?""",
                (_now(), str(task_id)),
            )

    def settle(
        self,
        task_id: str,
        *,
        state: str,
        stopped_reason: str = "",
        stopped_code: str = "",
    ) -> Optional[ProjectAskTask]:
        """Move a row to a settled state, releasing any in-flight lease.

        ``stopped_reason`` is stored exactly as it was handed in — it is the
        target's own words (ruling B5).
        """
        if state not in ASK_TASK_STATES:
            raise ValueError(f"invalid ask task state: {state!r}")
        now = _now()
        settled = now if state in {"accepted", "discarded", "failed"} else None
        with self._connection() as conn:
            conn.execute(
                """UPDATE project_ask_tasks
                      SET state = ?, stopped_reason = ?, stopped_code = ?,
                          dispatch_host_id = '', dispatch_lease_epoch = 0,
                          updated_at = ?, settled_at = ?
                    WHERE id = ?""",
                (
                    str(state), str(stopped_reason), str(stopped_code),
                    now, settled, str(task_id),
                ),
            )
            row = conn.execute(
                "SELECT * FROM project_ask_tasks WHERE id = ?", (str(task_id),)
            ).fetchone()
        return None if row is None else _row_to_model(row)

    # ── reads ────────────────────────────────────────────────────────

    def get(self, task_id: str) -> Optional[ProjectAskTask]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_ask_tasks WHERE id = ?", (str(task_id),)
            ).fetchone()
        return None if row is None else _row_to_model(row)

    def get_by_invocation(self, invocation_id: str) -> Optional[ProjectAskTask]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_ask_tasks WHERE invocation_id = ?",
                (str(invocation_id),),
            ).fetchone()
        return None if row is None else _row_to_model(row)

    def high_water(self, *, project_id: str | None = None) -> int:
        """The top ``resume_order`` among unfinished rows — the paging anchor."""
        clauses, values = self._unfinished_clauses(project_id)
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(resume_order), 0) AS high FROM project_ask_tasks "
                "WHERE " + " AND ".join(clauses),
                values,
            ).fetchone()
        return int(row["high"])

    def page_unfinished(
        self,
        *,
        limit: int,
        high: int,
        after: tuple[int, str] | None = None,
        project_id: str | None = None,
    ) -> tuple[list[ProjectAskTask], bool]:
        """One keyset page of the Resume projection, newest saved first.

        Mirrors ``RefinementThoughtService.list_unfinished``: a high-water
        anchor plus ``(resume_order DESC, id DESC)``, so a row saved mid-page
        never shifts the page under the reader.  ``discarded`` is excluded.
        """
        clauses, values = self._unfinished_clauses(project_id)
        clauses.append("resume_order <= ?")
        values.append(int(high))
        if after is not None:
            clauses.append("(resume_order < ? OR (resume_order = ? AND id < ?))")
            values.extend([int(after[0]), int(after[0]), str(after[1])])
        values.append(int(limit) + 1)
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM project_ask_tasks WHERE " + " AND ".join(clauses)
                + " ORDER BY resume_order DESC, id DESC LIMIT ?",
                values,
            ).fetchall()
        page = [_row_to_model(row) for row in rows[: int(limit)]]
        return page, len(rows) > int(limit)

    @staticmethod
    def _unfinished_clauses(project_id: str | None) -> tuple[list[str], list[Any]]:
        placeholders = ", ".join("?" for _ in UNFINISHED_ASK_TASK_STATES)
        clauses = [f"state IN ({placeholders})"]
        values: list[Any] = list(UNFINISHED_ASK_TASK_STATES)
        if project_id:
            clauses.append("project_id = ?")
            values.append(str(project_id))
        return clauses, values

    def find_ask_result(self, invocation_id: str) -> Optional[dict[str, Any]]:
        """The durable answer for one invocation identity, or None.

        Two lookups, because an ask reaches ``ask_results`` under two different
        identities depending on the path it took:

        1. The classic path stages under the caller's own ``invocation_id``,
           so the direct read finds it.
        2. The routed path (an active ``…-route-assignments`` migration) stages
           under the WINNING CHILD's invocation, whose kernel operation carries
           the caller's operation as ``parent_operation_id``.  The join below
           follows that link so the same claim law holds on both paths.

        Nothing is dispatched, published or mutated here — this is a read of
        proof the kernel already settled.
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT payload_json FROM ask_results WHERE invocation_id = ?",
                (str(invocation_id),),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    """SELECT ar.payload_json
                         FROM ask_results ar
                         JOIN kernel_operations child
                           ON child.operation_id = ar.operation_id
                        WHERE child.parent_operation_id = ?
                        ORDER BY child.created_at DESC
                        LIMIT 1""",
                    (str(invocation_id),),
                ).fetchone()
        if row is None:
            return None
        try:
            payload = json.loads(str(row["payload_json"]))
        except (TypeError, ValueError):
            return None
        return payload if isinstance(payload, dict) else None

    # ── startup recovery ─────────────────────────────────────────────

    def reconcile_orphans(self) -> list[str]:
        """Settle rows whose dispatching process is gone. Never re-dispatches.

        A row holding a dispatch lease that no live ``refinement_hosts`` row
        still backs was in flight when the process died.  There is no receipt
        to read and no honest way to know what happened, so it settles to
        ``failed`` carrying the named code and nothing is sent anywhere —
        the discipline of ``recover_refinements_on_startup``.

        A lease that is still live is NOT abandonment and is left alone.
        """
        settled: list[str] = []
        now = _now()
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """SELECT id, dispatch_host_id, dispatch_lease_epoch
                     FROM project_ask_tasks
                    WHERE dispatch_host_id != ''
                      AND state NOT IN ('accepted', 'discarded')
                    ORDER BY resume_order, id"""
            ).fetchall()
            for row in rows:
                host = conn.execute(
                    "SELECT lease_epoch, expires_at FROM refinement_hosts WHERE host_id = ?",
                    (str(row["dispatch_host_id"]),),
                ).fetchone()
                if (
                    host is not None
                    and int(host["lease_epoch"]) == int(row["dispatch_lease_epoch"])
                    and str(host["expires_at"]) > now
                ):
                    continue
                conn.execute(
                    """UPDATE project_ask_tasks
                          SET state = 'failed', stopped_code = ?, stopped_reason = '',
                              dispatch_host_id = '', dispatch_lease_epoch = 0,
                              updated_at = ?, settled_at = ?
                        WHERE id = ?""",
                    (HOST_LOST_CODE, now, now, str(row["id"])),
                )
                settled.append(str(row["id"]))
        return settled
