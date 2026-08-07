"""Transport-neutral mesh inbox and relay operations."""
from __future__ import annotations

from typing import Any

from ..db.core import Database
from ..principals import Principal
from .errors import ConflictError, ValidationError


class MeshService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def list_inbox(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        from ..intel_queue import build_runtime_queue_frame
        from ..operation_policy import commitment_labels, operation_for_proposal

        jobs: list[dict[str, Any]] = []
        intel_frame = build_runtime_queue_frame(self._db)
        for job in intel_frame["jobs"]:
            if str(job.get("status") or "") in ("queued", "running"):
                jobs.append({
                    "kind": "intel", "id": str(job.get("id") or ""),
                    "label": str(job.get("label") or ""),
                    "status": str(job.get("status") or "queued"),
                    "meeting_id": job.get("meeting_id"), "attempts": int(job.get("attempts") or 0),
                })
        for job in self._db.plugins.list_plugin_run_jobs(status="queued", limit=20):
            jobs.append({
                "kind": "plugin", "id": f"plugin:{job.id}", "label": job.plugin_id,
                "status": job.status, "meeting_id": job.meeting_id, "attempts": int(job.attempts or 0),
            })
        proposals = []
        for proposal in self._db.actuators.list_pending_proposals(limit=50):
            operation = operation_for_proposal(proposal)
            policy = dict(getattr(proposal, "policy_snapshot", {}) or {})
            if policy.get("outcome") == "refused":
                continue
            proposals.append({
                "id": proposal.id, "origin": proposal.origin, "meeting_id": proposal.meeting_id,
                "target": proposal.target, "action": proposal.action, "preview": proposal.preview,
                "status": proposal.status, "review_decision": proposal.review_decision,
                "authorization_state": proposal.authorization_state,
                "execution_state": proposal.execution_state, "operation": operation.to_dict(),
                "policy_snapshot": policy, "commitment": commitment_labels(operation),
                "created_at": proposal.created_at,
            })
        return {"jobs": jobs, "proposals": proposals, "counts": {
            "queued": int(intel_frame.get("queued") or 0),
            "running": int(intel_frame.get("running") or 0),
            "failed": int(intel_frame.get("failed") or 0),
            "pending_approvals": len(proposals),
        }}

    def claim_relay(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        node = str(payload.get("node") or "").strip()
        if not node:
            raise ValidationError("node must be a non-empty string")
        job = self._db.mesh_relay.claim_next(node)
        return {"job": job.to_dict() if job is not None else None}

    def complete_relay(self, principal: Principal, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        result = payload.get("result")
        if not isinstance(result, str) or not result.strip():
            raise ValidationError("result must be a non-empty string")
        if not self._db.mesh_relay.complete(job_id, result=result):
            raise ConflictError(
                f"relay job {job_id} is not completable (expired, failed, or unknown)",
                code="relay_not_completable",
            )
        return {"success": True}

    def fail_relay(self, principal: Principal, job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        error = str(payload.get("error") or "").strip()
        if not error:
            raise ValidationError("error must be a non-empty string")
        if not self._db.mesh_relay.fail(job_id, error=error):
            raise ConflictError(
                f"relay job {job_id} is not failable (already terminal or unknown)",
                code="relay_not_failable",
            )
        return {"success": True}
