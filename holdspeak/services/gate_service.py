"""Transport-neutral tool-call gate operations."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

from typing import Any

from ..db.core import Database
from ..db.gate import APPROVED, DENIED, HELD
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ServiceError, ValidationError


@observe_service
class GateService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def propose(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        from .. import kernel
        from ..coder_gate import DEFAULT_TTL_SECONDS
        from ..kernel.runtime import _as_principal

        proposal_id = str(payload.get("id") or "").strip()
        tool = str(payload.get("tool") or "").strip()
        args_sha256 = str(payload.get("args_sha256") or "").strip()
        if not proposal_id or not tool or not args_sha256:
            raise ValidationError("id, tool, and args_sha256 are required")
        try:
            ttl = float(payload.get("ttl_seconds") or 0.0)
        except (TypeError, ValueError):
            ttl = 0.0
        self._db.gate.expire_due()
        with _as_principal(principal):
            handle = kernel.submit({
                "request_schema": 1, "request_id": proposal_id,
                "idempotency_key": f"gate:{proposal_id}",
                "operation": {"name": "tool.call", "version": 1}, "subject_refs": [],
                "target": {"ref": f"gate:{proposal_id}"},
                "parent_operation_id": str(payload.get("parent_operation_id") or ""),
                "arguments": {
                    "proposal_id": proposal_id, "tool": tool, "args_sha256": args_sha256,
                    "args_head": str(payload.get("args_head") or ""), "cwd": str(payload.get("cwd") or ""),
                    "ttl_seconds": ttl if ttl > 0.0 else DEFAULT_TTL_SECONDS,
                }, "placement": "node:local",
            })
        if (handle.get("receipt") or {}).get("outcome") == "idempotency_payload_mismatch":
            raise ConflictError(
                "a re-arrival changed the arguments; the original hold was revoked",
                code="args_mismatch", context={"state": "invalidated"},
            )
        proposal = self._db.gate.get(proposal_id)
        if proposal is None:
            raise ServiceError("proposal_not_admitted", "proposal was not admitted", context={"handle": handle, "status": 409})
        return proposal.to_dict()

    def get_proposal(self, principal: Principal, proposal_id: str) -> dict[str, Any]:
        from ..kernel.model import KernelRefused
        from ..kernel.runtime import _service

        self._db.gate.expire_due()
        proposal = self._db.gate.get(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        if principal.name == "agent" and proposal.session_key != principal.identity:
            raise ServiceError("principal_scope_required", "principal scope required", context={
                "status": 403, "principal": principal.name, "principal_identity": principal.identity,
                "missing_right": "agent.read:other_session",
            })
        if proposal.state == APPROVED and principal.name == "agent":
            try:
                _service().claim(Principal(PrincipalKind.NODE, "local"), proposal_id)
            except KernelRefused as exc:
                if exc.reason != "no_claimable_operation":
                    raise ServiceError(exc.reason, exc.reason, context={"status": 409, "operation_id": exc.operation_id}) from exc
        return proposal.to_dict()

    def list_proposals(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        state = str((filters or {}).get("state") or HELD)
        self._db.gate.expire_due()
        return {"proposals": [proposal.to_dict() for proposal in self._db.gate.list_state(state)], "state": state}

    def decide(self, principal: Principal, proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from .. import kernel
        from ..kernel.model import KernelRefused
        from ..kernel.runtime import _as_principal, _service

        decision = str(payload.get("decision") or "").strip()
        if decision not in (APPROVED, DENIED):
            raise ValidationError(f"decision must be {APPROVED}|{DENIED}")
        proposal = self._db.gate.get(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        operation_id = str(proposal.operation.get("kernel_operation_id") or "")
        if not operation_id:
            raise ConflictError("proposal not kernel admitted", code="proposal_not_kernel_admitted")
        reason = str(payload.get("reason") or "").strip()[:200]
        try:
            with _as_principal(principal):
                projected = kernel.read([f"operation:{operation_id}"], "state", "committed")
                standing = projected["objects"][0]["operation"]
                _service().decide(operation_id, "approve" if decision == APPROVED else "reject", int(standing["revision"]), principal, reason=reason)
                if decision == APPROVED:
                    _service().claim(Principal(PrincipalKind.NODE, "local"), proposal_id)
        except (KernelRefused, IndexError) as exc:
            current = self._db.gate.get(proposal_id)
            raise ConflictError("proposal was already decided", code="already_decided", context={
                "state": current.state if current is not None else "unknown", "requested": decision,
            }) from exc
        current = self._db.gate.get(proposal_id)
        if current is None:
            raise NotFound("proposal", proposal_id)
        return current.to_dict()

    def record_receipt(self, principal: Principal, proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from ..kernel.model import KernelRefused
        from ..kernel.runtime import _service

        proposal = self._db.gate.get(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        if principal.name != "agent" or proposal.session_key != principal.identity:
            raise ServiceError("principal_scope_required", "principal scope required", context={"status": 403})
        operation_id = str(proposal.operation.get("kernel_operation_id") or "")
        if not operation_id:
            raise ConflictError("proposal not kernel admitted", code="proposal_not_kernel_admitted")
        try:
            return _service().receipt(operation_id, "succeeded" if str(payload.get("outcome") or "") == "succeeded" else "failed", f"gate:{proposal_id}", Principal(PrincipalKind.NODE, "local"))
        except KernelRefused as exc:
            raise ServiceError(exc.reason, exc.reason, context={"status": 403 if "principal" in exc.reason else 409, "operation_id": exc.operation_id}) from exc

    def record_usage(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self._db.gate.report_usage(session_key=principal.identity, model=str(payload.get("model") or ""), input_tokens=int(payload.get("input_tokens") or 0), output_tokens=int(payload.get("output_tokens") or 0), cache_read_tokens=int(payload.get("cache_read_tokens") or 0), cache_creation_tokens=int(payload.get("cache_creation_tokens") or 0))
        except (TypeError, ValueError) as exc:
            raise ValidationError("figures must be integers") from exc
        return {"success": True}

    def get_session_receipt(self, principal: Principal, session_key: str) -> dict[str, Any]:
        from ..session_receipts import build_receipt
        return build_receipt(session_key, db=self._db)

    def audit(self, principal: Principal, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        limit = max(1, min(int((filters or {}).get("limit") or 100), 500))
        return {"entries": self._db.gate.audit_entries(limit=limit)}

    def invalidate_held_on_startup(self) -> tuple[list[Any], int]:
        """Expire proposals a process restart can no longer honestly resume."""
        from ..kernel.runtime import _service

        flipped = self._db.gate.invalidate_all_held(
            reason="hub restarted while the proposal was held"
        )
        recovered = _service().recover_invalidated(flipped) if flipped else 0
        return flipped, recovered
