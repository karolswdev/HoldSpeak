"""Device-local bounded authority for Workbench schedules (HS-131-06)."""
from __future__ import annotations
import hashlib
import json
import time
import uuid
from typing import Any
from ..deployment_revisions import capture_deployment_revision
from ..inference_targets import resolve_placement
from ..principals import Principal, PrincipalKind
from .errors import ServiceError


def _terms(db: Any, wb: Any, *, conn: Any | None = None) -> dict[str, Any]:
    recipe = db.recipes.get(wb.recipe_id) if wb.recipe_id else None
    if recipe is None:
        raise ServiceError("delegation_stale_work", "Workbench has no recipe", context={"status": 409})
    target = resolve_placement(db, invocation=None, workbench=wb.profile_id, agent=recipe.profile_id).target
    if not target.ready:
        raise ServiceError("delegation_target_changed", target.readiness_reason, context={"status": 409})
    deployment = capture_deployment_revision(db, target, conn=conn)
    return {"recipe_id": recipe.id, "recipe_revision": str(recipe.last_modified),
            "workbench_revision": str(wb.last_modified), "schedule_revision": str(wb.schedule_revision),
            "cadence": str(wb.schedule or ""), "deployment_revision_id": deployment.id}


def _hash(terms: dict[str, Any], expires_at: float | None) -> str:
    payload = {**terms, "expires_at": expires_at}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ScheduleDelegationService:
    def __init__(self, db: Any) -> None: self.db = db

    def live(self, workbench_id: str) -> dict[str, Any] | None:
        with self.db._connection() as conn:
            row = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE workbench_id=? AND state='LIVE'", (workbench_id,)).fetchone()
        return dict(row) if row else None

    def enable_from_owner_in_transaction(self, principal: Principal, wb: Any, conn: Any, *, terms: dict[str, Any] | None = None, expires_at: float | None = None) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        terms = terms or _terms(self.db, wb, conn=conn); now = time.time(); delegation_id = "scheddeleg_" + uuid.uuid4().hex
        digest = _hash(terms, expires_at)
        conn.execute("UPDATE kernel_schedule_delegations SET state='REVOKED',revoked_at=?,revocation_reason='reapproved',updated_at=? WHERE workbench_id=? AND state='LIVE'", (now, now, wb.id))
        conn.execute("INSERT INTO kernel_schedule_delegations(id,workbench_id,delegator_kind,delegator_identity,recipe_id,recipe_revision,workbench_revision,schedule_revision,cadence,deployment_revision_id,terms_sha256,expires_at,state,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'LIVE',?,?)", (delegation_id,wb.id,principal.name,principal.identity,terms['recipe_id'],terms['recipe_revision'],terms['workbench_revision'],terms['schedule_revision'],terms['cadence'],terms['deployment_revision_id'],digest,expires_at,now,now))
        return {"id": delegation_id, **terms, "terms_sha256": digest, "expires_at": expires_at, "state": "LIVE"}

    def enable_from_owner(self, principal: Principal, wb: Any, *, expires_at: float | None = None) -> dict[str, Any]:
        """INTERNAL compatibility helper; WorkbenchService owns the atomic gesture."""
        # Capturing a deployment revision writes its immutable row, so resolve it
        # before taking the owner transaction's write lock.
        terms = _terms(self.db, wb)
        with self.db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return self.enable_from_owner_in_transaction(principal, wb, conn, terms=terms, expires_at=expires_at)

    def revoke_in_transaction(self, conn: Any, workbench_id: str, reason: str) -> list[tuple[str, str]]:
        """Revoke and epoch-fence matching parents before the owner transaction commits."""
        now = time.time()
        rows = conn.execute("SELECT id FROM kernel_schedule_delegations WHERE workbench_id=? AND state='LIVE'", (workbench_id,)).fetchall()
        ids = [str(row['id']) for row in rows]
        conn.execute("UPDATE kernel_schedule_delegations SET state='REVOKED',revoked_at=?,revocation_reason=?,updated_at=? WHERE workbench_id=? AND state='LIVE'", (now,reason,now,workbench_id))
        fenced: list[tuple[str, str]] = []
        for delegation_id in ids:
            parents = conn.execute("SELECT operation_id,active_child_invocation_id FROM kernel_parent_runs WHERE state='OPEN' AND input_json LIKE ?", (f'%\"delegation_id\":\"{delegation_id}\"%',)).fetchall()
            for parent in parents:
                if conn.execute("UPDATE kernel_parent_runs SET state='CANCELLING',execution_epoch=execution_epoch+1,active_child_invocation_id='',updated_at=? WHERE operation_id=? AND state='OPEN'", (now,parent['operation_id'])).rowcount:
                    fenced.append((str(parent['operation_id']), str(parent['active_child_invocation_id'] or '')))
        return fenced

    def revoke(self, workbench_id: str, reason: str) -> list[str]:
        with self.db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            fenced = self.revoke_in_transaction(conn, workbench_id, reason)
        self.complete_fenced(fenced)
        return [operation_id for operation_id, _ in fenced]

    def complete_fenced(self, fenced: list[tuple[str, str]]) -> None:
        """After commit, signal any provider and elect the durable cancellation receipt."""
        if not fenced:
            return
        try:
            from ..kernel.runtime import _configure
            from ..principals import Principal, PrincipalKind
            # Use the affected database's existing broker. _service() resolves
            # the ambient application database and can dispose this run's
            # controller, invalidating its in-flight parent context.
            broker = _configure(self.db); scheduler = Principal(PrincipalKind.SCHEDULER, 'local-workbench-conductor')
            for operation_id, _invocation_id in fenced:
                # cancel_by_operation_id owns the durable parent election and
                # signals its active child after fencing it. Calling the child
                # cancellation first can race the receipt winner we must adopt.
                broker.parent_run_controller.cancel_by_operation_id(scheduler, operation_id)
        except Exception:
            # The durable epoch fence was committed; normal recovery completes a
            # receipt if this process dies before provider signalling.
            pass

    def validate(self, workbench_id: str) -> dict[str, Any]:
        wb=self.db.workbenches.get(workbench_id)
        if wb is None or not wb.schedule_enabled: raise ServiceError("schedule_disabled", "Schedule is disabled", context={"status":409})
        row=self.live(workbench_id)
        if row is None:
            with self.db._connection() as conn:
                prior = conn.execute("SELECT state FROM kernel_schedule_delegations WHERE workbench_id=? ORDER BY updated_at DESC LIMIT 1", (workbench_id,)).fetchone()
            if prior is not None and str(prior['state']) == 'REVOKED':
                raise ServiceError("delegation_revoked", "Delegation revoked", context={"status":409})
            raise ServiceError("delegation_missing", "No local owner delegation", context={"status":409})
        if row['expires_at'] is not None and float(row['expires_at']) <= time.time():
            self.revoke(workbench_id, "expired"); raise ServiceError("delegation_expired", "Delegation expired", context={"status":409})
        current=_terms(self.db, wb)
        if current['cadence'] != row['cadence']:
            self.revoke(workbench_id, "delegation_cadence_changed")
            raise ServiceError("delegation_cadence_changed", "Cadence changed", context={"status":409})
        if current['deployment_revision_id'] != row['deployment_revision_id']:
            self.revoke(workbench_id, "delegation_target_changed")
            raise ServiceError("delegation_target_changed", "Target changed", context={"status":409})
        if any(str(current[k]) != str(row[k]) for k in ('recipe_id','recipe_revision','workbench_revision','schedule_revision')):
            self.revoke(workbench_id, "delegation_stale_work")
            raise ServiceError("delegation_stale_work", "Bound work changed", context={"status":409})
        return row
