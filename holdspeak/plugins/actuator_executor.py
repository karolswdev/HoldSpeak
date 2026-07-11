"""Guarded actuator executor (Phase 37, HS-37-04).

This is the one place an actuator's external side effect actually happens — so
it is where the phase invariant is enforced in code:

    No external side effect occurs without an explicit, audited, per-action
    human approval — and what executes is exactly what was previewed.

`ActuatorExecutor.execute(proposal_id)` acts on an **approved** proposal and,
before any outbound call:

  1. **status** — refuses anything that isn't `approved` (no execution).
  2. **policy gate** — the master `allow_actuators` switch must be on, and (if a
     per-project allow-list is supplied) the actuator id must be on it.
  3. **authority parity** — payload, normalized destination, material preview,
     renderer version, effect class, and policy version must all equal the
     durable binding captured at approval time. Any mismatch aborts to `failed`
     with **no** outbound call.
  4. **egress** — routes through the injected `connector` (HS-37-05 supplies one
     backed by the Phase-25-gated connector runtime; this module is
     connector-agnostic and never opens a socket itself).
  5. **audit** — every terminal transition (`executed`/`failed`) is recorded via
     `ActuatorRepository.transition_proposal`, which writes an audit row carrying
     the payload hash.

Policy/status refusals raise and **do not change state** (enable the gate / fix
the approval and retry); parity and connector failures transition the proposal to
`failed` (retryable via `failed -> approved`).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

from ..actuator_authority import AuthorityBinding, authority_binding, payload_hash
from ..logging_config import get_logger
from .actuators import ActuatorProposal

log = get_logger("plugins.actuator_executor")

# A connector performs the side effect for a proposal and returns a result dict
# (or raises). HS-37-05 supplies one backed by the connector runtime; tests pass
# a stub. The executor itself never egresses.
Connector = Callable[[Any], "dict[str, Any]"]


class ActuatorExecutionError(RuntimeError):
    """The proposal cannot be executed in its current state (not approved)."""


class ActuatorPolicyError(PermissionError):
    """Execution is refused by the governance gate (no state change)."""


class ActuatorExecutor:
    """Executes approved actuator proposals under the full guard stack."""

    def __init__(
        self,
        db: Any,
        *,
        connector: Connector,
        allow_actuators: bool = False,
        allowed_actuator_ids: Optional[Iterable[str]] = None,
        actor: str = "executor",
        on_result: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self._db = db
        self._connector = connector
        # HS-56-03: an optional observer for terminal outcomes (executed /
        # failed) so a host with a broadcast channel can reflect them (the
        # presence mascot's result cards). Wire-safe summary only — never the
        # machine payload. Purely observational: a callback failure never
        # affects the transition it reports on.
        self._on_result = on_result
        self._allow_actuators = bool(allow_actuators)
        # None => no allow-list enforcement (the master gate is the only gate);
        # a set (even empty) => the actuator id must be a member to execute.
        self._allowed = (
            {str(a).strip() for a in allowed_actuator_ids if str(a).strip()}
            if allowed_actuator_ids is not None
            else None
        )
        self._actor = str(actor).strip() or "executor"

    def execute(self, proposal_id: str) -> Any:
        """Execute an approved proposal; returns the updated proposal record.

        Raises `KeyError` (unknown), `ActuatorExecutionError` (not approved), or
        `ActuatorPolicyError` (gate/allow-list) **without** changing state. A
        parity or connector failure transitions the proposal to `failed`.
        """
        proposal = self._db.actuators.get_proposal(proposal_id)
        if proposal is None:
            raise KeyError(f"unknown proposal: {proposal_id}")

        # 1. status gate — only an approved proposal may execute.
        if proposal.status != "approved":
            raise ActuatorExecutionError(
                f"proposal {proposal_id} is '{proposal.status}', not 'approved' — refusing to execute"
            )

        # 2. policy gate — no state change on refusal (operator can enable + retry).
        if not self._allow_actuators:
            raise ActuatorPolicyError(
                "actuator execution is disabled (allow_actuators is off)"
            )
        if self._allowed is not None and proposal.plugin_id not in self._allowed:
            raise ActuatorPolicyError(
                f"actuator '{proposal.plugin_id}' is not on the project allow-list"
            )

        # 3. Mandatory material-authority parity (TOCTOU). The caller cannot
        # supply or bypass authority: approval persistence is the source of
        # truth, and every field is recomputed from the row immediately before
        # egress using the current renderer/policy versions.
        current_binding = authority_binding(
            target=proposal.target,
            action=proposal.action,
            preview=proposal.preview,
            payload=proposal.payload,
        )
        approved_binding = AuthorityBinding(
            payload_hash=proposal.approved_payload_hash or "",
            normalized_destination=proposal.approved_destination or "",
            preview_hash=proposal.approved_preview_hash or "",
            preview_renderer_version=proposal.preview_renderer_version or "",
            effect_class=proposal.effect_class or "",
            policy_version=proposal.policy_version or "",
        )
        mismatches = [
            name
            for name in AuthorityBinding.__dataclass_fields__
            if getattr(approved_binding, name) != getattr(current_binding, name)
        ]
        if mismatches:
            log.warning(
                "actuator authority mismatch for %s (%s)",
                proposal_id,
                ", ".join(mismatches),
            )
            updated = self._db.actuators.transition_proposal(
                proposal_id,
                to_status="failed",
                actor=self._actor,
                detail=f"authority mismatch: {', '.join(mismatches)}",
                error="approval authority check failed — execution aborted, no side effect performed",
            )
            self._notify_result(updated)
            return updated

        current_hash = current_binding.payload_hash

        # 4. egress via the injected connector (never a socket from here). The
        #    side effect is built from the stored payload, not any caller input.
        proposal_view = ActuatorProposal(
            target=proposal.target,
            action=proposal.action,
            preview=proposal.preview,
            payload=dict(proposal.payload),
            reversible=proposal.reversible,
            required_capabilities=tuple(proposal.required_capabilities),
        )
        try:
            result = self._connector(proposal_view)
        except Exception as exc:  # connector failure → failed (retryable) + audit
            log.error("actuator connector failed for %s: %s", proposal_id, exc)
            updated = self._db.actuators.transition_proposal(
                proposal_id,
                to_status="failed",
                actor=self._actor,
                detail=f"connector error; payload {current_hash[:12]}",
                error=f"{type(exc).__name__}: {exc}",
            )
            self._notify_result(updated)
            return updated

        # 5. success → executed + audit (result recorded; payload hash in detail).
        updated = self._db.actuators.transition_proposal(
            proposal_id,
            to_status="executed",
            actor=self._actor,
            detail=f"executed via connector; payload {current_hash[:12]}",
            result=result if isinstance(result, dict) else {"result": result},
        )
        self._notify_result(updated)
        return updated

    def _notify_result(self, proposal: Any) -> None:
        if self._on_result is None or proposal is None:
            return
        try:
            self._on_result(
                {
                    "id": getattr(proposal, "id", ""),
                    "meeting_id": getattr(proposal, "meeting_id", ""),
                    "status": getattr(proposal, "status", ""),
                    "target": getattr(proposal, "target", ""),
                    "action": getattr(proposal, "action", ""),
                    "preview": getattr(proposal, "preview", ""),
                    "reversible": bool(getattr(proposal, "reversible", False)),
                    "error": getattr(proposal, "error", None),
                }
            )
        except Exception as exc:  # observational only — never break the audit
            log.debug(f"actuator on_result observer failed: {exc}")


__all__ = [
    "ActuatorExecutor",
    "ActuatorExecutionError",
    "ActuatorPolicyError",
    "Connector",
    "payload_hash",
]
