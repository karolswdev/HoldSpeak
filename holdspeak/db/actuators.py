"""ActuatorRepository — persistence for actuator proposals (Phase 37, HS-37-02).

An actuator (the plugin system's third kind, HS-37-01) proposes an external
side effect rather than acting. This repo is that proposal's durable home:
the lifecycle `proposed -> approved -> executed | rejected | failed` (a failed
proposal may be re-approved for a retry), an idempotency key (re-proposing the
same action for the same meeting/window does not duplicate), the proposal
fields, and a per-transition **audit trail** so "no silent egress" is provable
after the fact.

It stores + reads; it never executes. Approval (HS-37-03) flips state via
`transition_proposal`; the guarded executor (HS-37-04) reads the `payload` it
records here (the parity source-of-truth) before acting.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    VALID_ACTUATOR_PROPOSAL_STATUSES,
    ActuatorProposalAuditEntry,
    ActuatorProposalRecord,
)

log = get_logger("db.actuators")

# The lifecycle as an explicit transition map. `executed` and `rejected` are
# terminal; a `failed` proposal may be re-approved to retry execution.
_LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "proposed": {"approved", "rejected"},
    "approved": {"executed", "failed"},
    "failed": {"approved"},
    "executed": set(),
    "rejected": set(),
}


class ActuatorRepository(BaseRepository):
    """Persistence for actuator proposals (lifecycle + audit trail)."""

    def record_proposal(
        self,
        *,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        plugin_version: str,
        idempotency_key: str,
        target: str,
        action: str,
        preview: str,
        payload: Optional[dict[str, Any]] = None,
        reversible: bool = False,
        required_capabilities: Optional[list[str]] = None,
    ) -> ActuatorProposalRecord:
        """Persist a `proposed` proposal (idempotent on `idempotency_key`).

        Re-proposing the same action for the same meeting/window returns the
        existing row unchanged (no duplicate, no extra audit entry). A fresh
        insert writes the opening `-> proposed` audit entry.
        """
        clean_meeting_id = str(meeting_id).strip()
        clean_plugin_id = str(plugin_id).strip()
        clean_key = str(idempotency_key).strip()
        clean_target = str(target).strip()
        clean_action = str(action).strip()
        clean_preview = str(preview).strip()
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_plugin_id:
            raise ValueError("plugin_id is required")
        if not clean_key:
            raise ValueError("idempotency_key is required")
        if not clean_target:
            raise ValueError("target is required")
        if not clean_action:
            raise ValueError("action is required")
        if not clean_preview:
            raise ValueError("preview is required")

        proposal_id = uuid.uuid4().hex
        now = datetime.now().isoformat()
        payload_json = self._json_dumps(payload or {}, fallback="{}")
        caps_json = self._json_dumps(
            [str(c).strip().lower() for c in (required_capabilities or []) if str(c).strip()],
            fallback="[]",
        )

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO actuator_proposals (
                    id, meeting_id, window_id, plugin_id, plugin_version,
                    idempotency_key, status, target, action, preview,
                    payload_json, reversible, required_capabilities_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO NOTHING
                """,
                (
                    proposal_id,
                    clean_meeting_id,
                    str(window_id).strip(),
                    clean_plugin_id,
                    str(plugin_version).strip() or "unknown",
                    clean_key,
                    clean_target,
                    clean_action,
                    clean_preview,
                    payload_json,
                    int(bool(reversible)),
                    caps_json,
                    now,
                    now,
                ),
            )
            inserted = cursor.rowcount and cursor.rowcount > 0
            if inserted:
                conn.execute(
                    """
                    INSERT INTO actuator_proposal_audit (
                        proposal_id, actor, from_status, to_status, detail, created_at
                    )
                    VALUES (?, 'system', NULL, 'proposed', ?, ?)
                    """,
                    (proposal_id, "proposal recorded", now),
                )
            row = conn.execute(
                "SELECT * FROM actuator_proposals WHERE idempotency_key = ?",
                (clean_key,),
            ).fetchone()

        return self._row_to_proposal(row)

    def get_proposal(self, proposal_id: str) -> Optional[ActuatorProposalRecord]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM actuator_proposals WHERE id = ?",
                (str(proposal_id).strip(),),
            ).fetchone()
        return self._row_to_proposal(row) if row is not None else None

    def list_proposals(
        self, meeting_id: str, *, status: Optional[str] = None
    ) -> list[ActuatorProposalRecord]:
        clean_meeting_id = str(meeting_id).strip()
        with self._connection() as conn:
            if status is not None:
                rows = conn.execute(
                    """
                    SELECT * FROM actuator_proposals
                    WHERE meeting_id = ? AND status = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (clean_meeting_id, str(status).strip().lower()),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM actuator_proposals
                    WHERE meeting_id = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (clean_meeting_id,),
                ).fetchall()
        return [self._row_to_proposal(row) for row in rows]

    def transition_proposal(
        self,
        proposal_id: str,
        *,
        to_status: str,
        actor: str = "system",
        detail: Optional[str] = None,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> ActuatorProposalRecord:
        """Advance a proposal's status, enforcing the lifecycle + auditing it.

        Raises `KeyError` for an unknown proposal and `ValueError` for an
        unknown or illegal target status (e.g. `executed -> proposed`). Sets
        `decided_at`/`decided_by` on approve/reject and `executed_at` on
        execute/fail, and writes one audit entry per transition.
        """
        target_status = str(to_status).strip().lower()
        if target_status not in VALID_ACTUATOR_PROPOSAL_STATUSES:
            raise ValueError(f"unknown proposal status: {target_status!r}")

        pid = str(proposal_id).strip()
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM actuator_proposals WHERE id = ?", (pid,)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown proposal: {proposal_id}")

            from_status = row["status"]
            if target_status not in _LEGAL_TRANSITIONS.get(from_status, set()):
                raise ValueError(
                    f"illegal actuator proposal transition: {from_status} -> {target_status}"
                )

            decided_at = row["decided_at"]
            decided_by = row["decided_by"]
            executed_at = row["executed_at"]
            if target_status in ("approved", "rejected"):
                decided_at = now
                decided_by = actor
            if target_status in ("executed", "failed"):
                executed_at = now

            result_json = (
                self._json_dumps(result, fallback="null")
                if result is not None
                else row["result_json"]
            )
            new_error = error if error is not None else row["error"]

            conn.execute(
                """
                UPDATE actuator_proposals
                SET status = ?, decided_by = ?, decided_at = ?, executed_at = ?,
                    result_json = ?, error = ?, updated_at = ?
                WHERE id = ?
                """,
                (target_status, decided_by, decided_at, executed_at, result_json, new_error, now, pid),
            )
            conn.execute(
                """
                INSERT INTO actuator_proposal_audit (
                    proposal_id, actor, from_status, to_status, detail, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pid, str(actor).strip() or "system", from_status, target_status, detail, now),
            )
            updated = conn.execute(
                "SELECT * FROM actuator_proposals WHERE id = ?", (pid,)
            ).fetchone()

        return self._row_to_proposal(updated)

    def list_audit(self, proposal_id: str) -> list[ActuatorProposalAuditEntry]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM actuator_proposal_audit
                WHERE proposal_id = ?
                ORDER BY created_at ASC, id ASC
                """,
                (str(proposal_id).strip(),),
            ).fetchall()
        return [
            ActuatorProposalAuditEntry(
                id=int(row["id"]),
                proposal_id=row["proposal_id"],
                actor=row["actor"],
                from_status=row["from_status"],
                to_status=row["to_status"],
                detail=row["detail"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _row_to_proposal(self, row: Any) -> ActuatorProposalRecord:
        return ActuatorProposalRecord(
            id=row["id"],
            meeting_id=row["meeting_id"],
            window_id=row["window_id"],
            plugin_id=row["plugin_id"],
            plugin_version=row["plugin_version"],
            idempotency_key=row["idempotency_key"],
            status=row["status"],
            target=row["target"],
            action=row["action"],
            preview=row["preview"],
            payload=self._json_loads_dict(row["payload_json"]),
            reversible=bool(row["reversible"]),
            required_capabilities=[str(c) for c in self._json_loads_list(row["required_capabilities_json"])],
            decided_by=row["decided_by"],
            result=self._json_loads_dict(row["result_json"]) if row["result_json"] else None,
            error=row["error"],
            created_at=row["created_at"],
            decided_at=row["decided_at"],
            executed_at=row["executed_at"],
            updated_at=row["updated_at"],
        )
