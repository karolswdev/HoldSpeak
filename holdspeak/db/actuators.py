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
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from ..actuator_authority import authority_binding
from ..operation_policy import describe_operation, normalize_control_mode, resolve_policy
from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    AuthorityGrantRecord,
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
        meeting_id: Optional[str],
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
        origin: str = "meeting",
        control_mode: str = "neutral",
        policy_source: str = "config",
        fixed_destination: Optional[bool] = None,
    ) -> ActuatorProposalRecord:
        """Persist a `proposed` proposal (idempotent on `idempotency_key`).

        Re-proposing the same action for the same meeting/window returns the
        existing row unchanged (no duplicate, no extra audit entry). A fresh
        insert writes the opening `-> proposed` audit entry.

        A proposal is owner-typed (v5, Phase 72): `origin='meeting'` requires
        a real `meeting_id`; `origin='desk'` (the iPad desk relay) carries
        `meeting_id=None` — the old hidden sentinel meeting is gone.
        """
        clean_origin = str(origin or "meeting").strip().lower()
        if clean_origin not in ("meeting", "desk"):
            raise ValueError(f"invalid proposal origin: {origin!r}")
        clean_meeting_id = str(meeting_id).strip() if meeting_id is not None else None
        clean_plugin_id = str(plugin_id).strip()
        clean_key = str(idempotency_key).strip()
        clean_target = str(target).strip()
        clean_action = str(action).strip()
        clean_preview = str(preview).strip()
        if clean_origin == "meeting" and not clean_meeting_id:
            raise ValueError("meeting_id is required for origin='meeting'")
        if clean_origin == "desk":
            clean_meeting_id = None
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
        destination_is_fixed = (
            bool(fixed_destination)
            if fixed_destination is not None
            else clean_target.lower() in {"slack", "webhook", "github"}
        )
        operation = describe_operation(
            operation_id=f"actuator:{proposal_id}",
            family="external_write",
            effect_class=f"{clean_target.lower()}/{clean_action.lower()}",
            actor="owner",
            destination=authority_binding(
                target=clean_target, action=clean_action, preview=clean_preview,
                payload=payload or {},
            ).normalized_destination,
            data_classes=("proposed_content", "connector_metadata"),
            project_scope=str((payload or {}).get("project") or (payload or {}).get("repo") or "") or None,
            resource_scope=clean_meeting_id or str(window_id).strip() or None,
            fixed_destination=destination_is_fixed,
            consequence=(
                "execute_now" if clean_target.lower() in {"slack", "webhook", "github"}
                else "queue_executor"
            ),
        )
        operation_json = self._json_dumps(operation.to_dict(), fallback="{}")
        policy = resolve_policy(
            operation,
            mode=control_mode,
            source=str(policy_source or "config"),
        )
        policy_snapshot_json = self._json_dumps(policy.to_dict(), fallback="{}")

        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO actuator_proposals (
                    id, meeting_id, origin, window_id, plugin_id, plugin_version,
                    idempotency_key, status, review_decision, authorization_state,
                    execution_state, target, action, preview,
                    payload_json, reversible, required_capabilities_json,
                    operation_json, policy_snapshot_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'proposed', 'unreviewed', 'proposed',
                        'not_started', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO NOTHING
                """,
                (
                    proposal_id,
                    clean_meeting_id,
                    clean_origin,
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
                    operation_json,
                    policy_snapshot_json,
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
                    (
                        proposal_id,
                        (
                            "proposal recorded; "
                            f"policy={policy.policy_version} mode={policy.mode} "
                            f"outcome={policy.outcome}"
                        ),
                        now,
                    ),
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

    def list_pending_proposals(self, *, limit: int = 50) -> list[ActuatorProposalRecord]:
        """Every proposal awaiting the human nod, ACROSS meetings + desk origins.

        The mesh inbox's approval lane (HSM-15-03): `list_proposals` is
        meeting-scoped, so device-initiated (`origin='desk'`, `meeting_id`
        NULL) rows were reachable only by id. One query, newest first.
        """
        bounded = max(1, min(int(limit), 200))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM actuator_proposals
                WHERE status = 'proposed'
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (bounded,),
            ).fetchall()
        return [self._row_to_proposal(row) for row in rows]

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
        policy_snapshot: Optional[dict[str, Any]] = None,
        grant_id: Optional[str] = None,
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
            review_decision = row["review_decision"]
            authorization_state = row["authorization_state"]
            execution_state = row["execution_state"]
            if target_status in ("approved", "rejected"):
                decided_at = now
                decided_by = actor
                authorization_state = "approved" if target_status == "approved" else "rejected"
            if target_status in ("executed", "failed"):
                executed_at = now
                execution_state = "succeeded" if target_status == "executed" else "failed"
            elif target_status == "approved":
                execution_state = "not_started"

            result_json = (
                self._json_dumps(result, fallback="null")
                if result is not None
                else row["result_json"]
            )
            new_error = error if error is not None else row["error"]

            binding = None
            if target_status == "approved":
                binding = authority_binding(
                    target=row["target"],
                    action=row["action"],
                    preview=row["preview"],
                    payload=self._json_loads_dict(row["payload_json"]),
                )
                binding_detail = (
                    "authority bound: "
                    f"payload={binding.payload_hash[:12]} "
                    f"destination={binding.normalized_destination} "
                    f"preview={binding.preview_hash[:12]} "
                    f"renderer={binding.preview_renderer_version} "
                    f"effect={binding.effect_class} policy={binding.policy_version}"
                )
                detail = f"{detail}; {binding_detail}" if detail else binding_detail

            approved_payload_hash = (
                binding.payload_hash if binding else row["approved_payload_hash"]
            )
            approved_destination = (
                binding.normalized_destination if binding else row["approved_destination"]
            )
            approved_preview_hash = (
                binding.preview_hash if binding else row["approved_preview_hash"]
            )
            preview_renderer_version = (
                binding.preview_renderer_version if binding else row["preview_renderer_version"]
            )
            approved_effect_class = binding.effect_class if binding else row["effect_class"]
            policy_version = binding.policy_version if binding else row["policy_version"]
            policy_snapshot_json = (
                self._json_dumps(policy_snapshot, fallback="{}")
                if policy_snapshot is not None else row["policy_snapshot_json"]
            )
            selected_grant_id = grant_id if grant_id is not None else row["grant_id"]

            conn.execute(
                """
                UPDATE actuator_proposals
                SET status = ?, review_decision = ?, authorization_state = ?,
                    execution_state = ?, decided_by = ?, decided_at = ?, executed_at = ?,
                    approved_payload_hash = ?, approved_destination = ?,
                    approved_preview_hash = ?, preview_renderer_version = ?,
                    effect_class = ?, policy_version = ?,
                    policy_snapshot_json = ?, grant_id = ?,
                    result_json = ?, error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    target_status, review_decision, authorization_state, execution_state,
                    decided_by, decided_at, executed_at,
                    approved_payload_hash, approved_destination, approved_preview_hash,
                    preview_renderer_version, approved_effect_class, policy_version,
                    policy_snapshot_json, selected_grant_id,
                    result_json, new_error, now, pid,
                ),
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

    def record_review_decision(
        self, proposal_id: str, decision: str, *, actor: str = "reviewer"
    ) -> ActuatorProposalRecord:
        """Change content review only; never imply effect authorization."""
        clean = str(decision).strip().lower()
        if clean not in {"accepted", "dismissed"}:
            raise ValueError("review decision must be accepted or dismissed")
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT status FROM actuator_proposals WHERE id=?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown proposal: {proposal_id}")
            conn.execute(
                "UPDATE actuator_proposals SET review_decision=?,updated_at=? WHERE id=?",
                (clean, now, proposal_id),
            )
            conn.execute(
                """INSERT INTO actuator_proposal_audit
                   (proposal_id,actor,from_status,to_status,detail,created_at)
                   VALUES (?,?,?,?,?,?)""",
                (proposal_id, actor, row["status"], row["status"],
                 f"review_decision={clean}; authority unchanged", now),
            )
            updated = conn.execute(
                "SELECT * FROM actuator_proposals WHERE id=?", (proposal_id,)
            ).fetchone()
        return self._row_to_proposal(updated)

    def mark_execution_state(self, proposal_id: str, state: str) -> ActuatorProposalRecord:
        """Update the independent execution axis without forging legacy status."""
        allowed = {"not_started", "queued", "running", "succeeded", "failed", "cancelled", "unavailable"}
        clean = str(state).strip().lower()
        if clean not in allowed:
            raise ValueError(f"invalid execution state: {state!r}")
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute("SELECT status FROM actuator_proposals WHERE id=?", (proposal_id,)).fetchone()
            if row is None:
                raise KeyError(f"unknown proposal: {proposal_id}")
            conn.execute(
                "UPDATE actuator_proposals SET execution_state=?,updated_at=? WHERE id=?",
                (clean, now, proposal_id),
            )
            updated = conn.execute("SELECT * FROM actuator_proposals WHERE id=?", (proposal_id,)).fetchone()
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

    def last_execution_receipt(self, target: str) -> Optional[str]:
        """Latest durable successful receipt time for one egress target."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT executed_at FROM actuator_proposals
                WHERE target = ? AND status = 'executed' AND executed_at IS NOT NULL
                ORDER BY executed_at DESC, id DESC LIMIT 1
                """,
                (str(target).strip(),),
            ).fetchone()
        return str(row["executed_at"]) if row is not None else None

    def issue_grant(
        self,
        *,
        actor: str,
        operation_family: str,
        effect_class: str,
        destination: str,
        data_classes: list[str],
        ttl_seconds: int,
        max_uses: int = 1,
        project_scope: Optional[str] = None,
        resource_scope: Optional[str] = None,
        control_mode: str = "neutral",
    ) -> AuthorityGrantRecord:
        """Issue a durable, bounded grant. No secret or payload is accepted."""
        clean_actor = str(actor or "").strip()
        clean_family = str(operation_family or "").strip().lower()
        clean_effect = str(effect_class or "").strip().lower()
        clean_destination = str(destination or "").strip().lower()
        clean_data = list(dict.fromkeys(str(item).strip().lower() for item in data_classes if str(item).strip()))
        if not all((clean_actor, clean_family, clean_effect, clean_destination, clean_data)):
            raise ValueError("grant requires actor, operation family, effect, destination, and data classes")
        ttl = max(10, min(int(ttl_seconds), 30 * 24 * 60 * 60))
        uses = max(1, min(int(max_uses), 10_000))
        issued = datetime.now()
        expires = issued + timedelta(seconds=ttl)
        grant_id = f"grant_{uuid.uuid4().hex[:16]}"
        bound = {
            "actor": clean_actor, "operation_family": clean_family,
            "effect_class": clean_effect, "destination": clean_destination,
            "data_classes": clean_data, "project_scope": project_scope,
            "resource_scope": resource_scope,
        }
        binding_hash = hashlib.sha256(
            json.dumps(bound, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO authority_grants
                   (id,actor,operation_family,effect_class,destination,data_classes_json,
                    project_scope,resource_scope,issued_at,expires_at,max_uses,
                    remaining_uses,binding_hash,control_mode)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    grant_id, clean_actor, clean_family, clean_effect, clean_destination,
                    self._json_dumps(clean_data, fallback="[]"), project_scope,
                    resource_scope, issued.isoformat(), expires.isoformat(), uses,
                    uses, binding_hash, normalize_control_mode(control_mode),
                ),
            )
        return self.get_grant(grant_id)  # type: ignore[return-value]

    def get_grant(self, grant_id: str) -> Optional[AuthorityGrantRecord]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM authority_grants WHERE id=?", (grant_id,)).fetchone()
        return self._row_to_grant(row) if row is not None else None

    def list_grants(self, *, actor: Optional[str] = None, include_inactive: bool = True) -> list[AuthorityGrantRecord]:
        with self._connection() as conn:
            if actor:
                rows = conn.execute(
                    "SELECT * FROM authority_grants WHERE actor=? ORDER BY issued_at DESC", (actor,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM authority_grants ORDER BY issued_at DESC").fetchall()
        grants = [self._row_to_grant(row) for row in rows]
        return grants if include_inactive else [grant for grant in grants if grant.state == "active"]

    def revoke_grant(self, grant_id: str, *, reason: str = "owner_revoked") -> bool:
        with self._connection() as conn:
            cursor = conn.execute(
                """UPDATE authority_grants SET revoked_at=?,revoke_reason=?
                   WHERE id=? AND revoked_at IS NULL""",
                (datetime.now().isoformat(), str(reason or "owner_revoked"), grant_id),
            )
        return bool(cursor.rowcount)

    def revoke_active_grants(self, *, reason: str) -> int:
        """Fail closed after a policy/destination configuration mutation."""
        with self._connection() as conn:
            cursor = conn.execute(
                """UPDATE authority_grants SET revoked_at=?,revoke_reason=?
                   WHERE revoked_at IS NULL AND remaining_uses>0""",
                (datetime.now().isoformat(), str(reason or "configuration_changed")),
            )
        return int(cursor.rowcount)

    def consume_grant(
        self, grant_id: str, *, operation_id: str = "unknown"
    ) -> AuthorityGrantRecord:
        """Atomically burn one use and append a queryable use receipt."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM authority_grants WHERE id=?", (grant_id,)).fetchone()
            if row is None:
                raise KeyError(f"unknown grant: {grant_id}")
            grant = self._row_to_grant(row)
            if grant.state != "active":
                raise PermissionError(f"grant {grant_id} is {grant.state}")
            cursor = conn.execute(
                """UPDATE authority_grants
                   SET remaining_uses=remaining_uses-1,
                       revoked_at=CASE WHEN remaining_uses=1 THEN ? ELSE revoked_at END,
                       revoke_reason=CASE WHEN remaining_uses=1 THEN 'count_exhausted' ELSE revoke_reason END
                   WHERE id=? AND revoked_at IS NULL AND remaining_uses>0 AND expires_at>?""",
                (now, grant_id, now),
            )
            if cursor.rowcount != 1:
                raise PermissionError(f"grant {grant_id} is no longer active")
            conn.execute(
                """INSERT INTO authority_grant_uses
                   (id,grant_id,operation_id,actor,effect_class,destination,outcome,used_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    f"use_{uuid.uuid4().hex[:16]}", grant_id,
                    str(operation_id or "unknown"), grant.actor, grant.effect_class,
                    grant.destination, "consumed", now,
                ),
            )
        return self.get_grant(grant_id)  # type: ignore[return-value]

    def list_grant_uses(self, grant_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT id,grant_id,operation_id,actor,effect_class,destination,outcome,used_at
                   FROM authority_grant_uses WHERE grant_id=? ORDER BY used_at DESC,id DESC""",
                (grant_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _row_to_grant(self, row: Any) -> AuthorityGrantRecord:
        return AuthorityGrantRecord(
            id=row["id"], actor=row["actor"], operation_family=row["operation_family"],
            effect_class=row["effect_class"], destination=row["destination"],
            data_classes=[str(item) for item in self._json_loads_list(row["data_classes_json"])],
            project_scope=row["project_scope"], resource_scope=row["resource_scope"],
            issued_at=row["issued_at"], expires_at=row["expires_at"],
            max_uses=int(row["max_uses"]), remaining_uses=int(row["remaining_uses"]),
            revoked_at=row["revoked_at"], revoke_reason=row["revoke_reason"],
            binding_hash=row["binding_hash"], control_mode=row["control_mode"],
        )

    def _row_to_proposal(self, row: Any) -> ActuatorProposalRecord:
        return ActuatorProposalRecord(
            id=row["id"],
            meeting_id=row["meeting_id"],
            origin=row["origin"] if "origin" in row.keys() else "meeting",
            window_id=row["window_id"],
            plugin_id=row["plugin_id"],
            plugin_version=row["plugin_version"],
            idempotency_key=row["idempotency_key"],
            status=row["status"],
            review_decision=row["review_decision"],
            authorization_state=row["authorization_state"],
            execution_state=row["execution_state"],
            target=row["target"],
            action=row["action"],
            preview=row["preview"],
            payload=self._json_loads_dict(row["payload_json"]),
            reversible=bool(row["reversible"]),
            required_capabilities=[str(c) for c in self._json_loads_list(row["required_capabilities_json"])],
            decided_by=row["decided_by"],
            approved_payload_hash=row["approved_payload_hash"],
            approved_destination=row["approved_destination"],
            approved_preview_hash=row["approved_preview_hash"],
            preview_renderer_version=row["preview_renderer_version"],
            effect_class=row["effect_class"],
            policy_version=row["policy_version"],
            operation=self._json_loads_dict(row["operation_json"]),
            policy_snapshot=self._json_loads_dict(row["policy_snapshot_json"]),
            grant_id=row["grant_id"],
            result=self._json_loads_dict(row["result_json"]) if row["result_json"] else None,
            error=row["error"],
            created_at=row["created_at"],
            decided_at=row["decided_at"],
            executed_at=row["executed_at"],
            updated_at=row["updated_at"],
        )
