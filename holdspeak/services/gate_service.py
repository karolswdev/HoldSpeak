"""Transport-neutral tool-call gate operations."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import os
from typing import Any, Callable, Mapping, Optional

from ..db.core import Database
from ..db.gate import APPROVED, DENIED, HELD
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ServiceError, ValidationError


#: Launch states whose agent may still run (Conductor K2 ledger).
_LIVE_LAUNCH_STATES = frozenset({"launched", "registered"})

#: The principal that records a Control-mode decision on a held call. It
#: decides only what ``resolve_policy`` (family ``tool_gate``) allowed.
CONTROL_MODE_IDENTITY = "control-mode"


@observe_service
class GateService:
    def __init__(
        self,
        db: Database,
        *,
        observer: PipelineObserver | None = None,
        launches: Callable[[], Any] | None = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        # Conductor K5: the launch driver whose ledger names each agent's own
        # worktree and branch (``default_launch_service`` in production).
        self._launches = launches

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
        standing = self._db.gate.get(proposal_id)
        if (
            standing is not None and principal.kind is PrincipalKind.AGENT
            and standing.session_key != principal.identity
        ):
            # A proposal id is one session's: another session never re-arrives
            # on it (and never reads its decision), as get_proposal holds.
            raise ServiceError("principal_scope_required", "principal scope required", context={
                "status": 403, "principal": principal.name, "principal_identity": principal.identity,
                "missing_right": "agent.submit:other_session",
            })
        verdict = self._checked_verdict(principal, payload)
        parent = str(payload.get("parent_operation_id") or "")
        if parent and self._launch_operation(parent):
            # A launched agent's hook names its launch's process.spawn
            # operation. The kernel admits a child of it only for the owner
            # who pressed the launch, so as a parent it refused every call of
            # the agent (parent_operation_scope_required). The link to the
            # launch rides the verdict (launch_id) instead.
            parent = ""
        with _as_principal(principal):
            handle = kernel.submit({
                "request_schema": 1, "request_id": proposal_id,
                "idempotency_key": f"gate:{proposal_id}",
                "operation": {"name": "tool.call", "version": 1}, "subject_refs": [],
                "target": {"ref": f"gate:{proposal_id}"},
                "parent_operation_id": parent,
                "arguments": {
                    "proposal_id": proposal_id, "tool": tool, "args_sha256": args_sha256,
                    "args_head": str(payload.get("args_head") or ""), "cwd": str(payload.get("cwd") or ""),
                    "ttl_seconds": ttl if ttl > 0.0 else DEFAULT_TTL_SECONDS,
                    "classification": verdict,
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
        if proposal.state == HELD and (proposal.policy_snapshot or {}).get("outcome") == "allowed":
            proposal = self._decide_by_mode(proposal)
        return proposal.to_dict()

    # ── Conductor K5: the Control-mode decision ──────────────────────

    def _decide_by_mode(self, proposal: Any) -> Any:
        """Approve a held call the Control mode allows, as the
        ``control-mode`` principal; the reason names the mode and the rule
        (the gate audit row and the kernel journal keep it)."""
        from ..operation_policy import MODE_LABELS

        policy = proposal.policy_snapshot or {}
        verdict = (proposal.operation or {}).get("tool_call") or {}
        mode = str(policy.get("mode") or "")
        reason = (
            f"{MODE_LABELS.get(mode, mode)}: {policy.get('reason_code') or 'allowed'}; "
            f"rule {verdict.get('rule') or 'none'}"
            + (f" ({verdict['read_rule']})" if verdict.get("read_rule") else "")
        )[:200]
        try:
            self.decide(
                Principal(PrincipalKind.OWNER, CONTROL_MODE_IDENTITY),
                proposal.id, {"decision": APPROVED, "reason": reason},
            )
        except ConflictError:
            pass  # decided in the meantime: the standing state answers
        return self._db.gate.get(proposal.id) or proposal

    def _checked_verdict(self, principal: Principal, payload: Mapping[str, Any]) -> dict[str, str]:
        """The hook's verdict, checked against the caller's OWN launch: the
        armed root must be that launch's worktree, the working folder must be
        in it, and a ``git push`` must name its branch. A call from no
        HoldSpeak launch carries no launch id (its hold stays)."""
        from ..tool_gate_rules import INSIDE, OUTSIDE, UNPARSED, classification_from_wire

        raw = classification_from_wire(payload.get("classification"))
        if raw is None:
            return {"launch_id": "", "scope": UNPARSED, "rule": "no_verdict", "read_rule": ""}
        if (raw["proposal_id"], raw["args_sha256"]) != (
            str(payload.get("id") or ""), str(payload.get("args_sha256") or "")
        ):
            # The verdict names the call it was read for; a verdict copied
            # from another call (another id or another args hash) waits.
            return {"launch_id": "", "scope": UNPARSED, "rule": "verdict_not_bound", "read_rule": ""}
        scope, rule = raw["scope"], raw["rule"]
        found = self._own_launch(principal)
        if found is None:
            return {"launch_id": "", "scope": scope, "rule": rule, "read_rule": raw["read_rule"]}
        launch_id, worktree, branch = found
        if scope == INSIDE:
            cwd = os.path.realpath(str(payload.get("cwd") or "/"))
            root = os.path.realpath(raw["root"]) if raw["root"] else ""
            if not worktree or root != worktree or not (
                cwd == worktree or cwd.startswith(worktree.rstrip(os.sep) + os.sep)
            ):
                scope, rule = OUTSIDE, "not_own_worktree"
            elif raw["push_branch"] and raw["push_branch"] != branch:
                scope, rule = OUTSIDE, "git_push_other_branch"
        return {
            "launch_id": launch_id, "scope": scope, "rule": rule,
            "read_rule": raw["read_rule"] if scope == INSIDE else "",
        }

    def _launch_records(self) -> tuple[Any, list[dict[str, Any]]]:
        service = self._launches() if self._launches is not None else _default_launches(self._db)
        return service, service._ledger.list()

    def _launch_operation(self, operation_id: str) -> bool:
        """True when ``operation_id`` is the process.spawn of a launch."""
        try:
            _service, records = self._launch_records()
        except Exception:
            return False
        return any(r.get("operation_id") == operation_id for r in records)

    def _own_launch(self, principal: Principal) -> Optional[tuple[str, str, str]]:
        """``(launch_id, worktree_path, branch)`` of the live launch whose
        registered session IS this principal, or whose launch-bound credential
        (``agent:launch:<id>``) the principal holds; ``None`` otherwise. A
        session credential is the launch's only once the rider registers the
        session: the parent operation id the hook names is a claim any session
        could copy."""
        if principal.kind is not PrincipalKind.AGENT:
            return None
        try:
            service, records = self._launch_records()
        except Exception:
            return None
        live = [r for r in reversed(records) if str(r.get("state") or "") in _LIVE_LAUNCH_STATES]
        # Conductor R3: inside a launch the hook authenticates with the
        # launch-bound credential its tmux session carries (K6,
        # ``agent:launch:<launch_id>``), not a ``<agent>:<session>`` one: that
        # credential IS the launch's (issued into its session only).
        from ..coder_factory import launch_identity

        record = next(
            (
                r for r in live
                if r.get("session_key") == principal.identity
                or (r.get("launch_id") and launch_identity(str(r["launch_id"])) == principal.identity)
            ),
            None,
        )
        if record is None:
            return None
        path = service._worktree_path(record)
        if not path and callable(getattr(service._registry, "reload", None)):
            service._registry.reload()
            path = service._worktree_path(record)
        branch = str(record.get("branch") or "")
        if not branch:
            # A launch made before K5 kept no branch: the registry's worktree has it.
            source = service._registry.get(str(record.get("source_id") or ""))
            worktree = next(
                (wt for wt in getattr(source, "worktrees", ()) if wt.worktree_id == record.get("worktree_id")),
                None,
            )
            branch = str(getattr(worktree, "branch", "") or "")
        return str(record.get("launch_id") or ""), os.path.realpath(path) if path else "", branch

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

        from ..coder_gate import RESTART_INVALIDATION_REASON

        flipped = self._db.gate.invalidate_all_held(reason=RESTART_INVALIDATION_REASON)
        recovered = _service().recover_invalidated(flipped) if flipped else 0
        return flipped, recovered


def _default_launches(db: Database) -> Any:
    from ..delivery.factory_launch import default_launch_service

    return default_launch_service(db)
