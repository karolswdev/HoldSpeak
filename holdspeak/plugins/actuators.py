"""Actuator proposal contract — the plugin system's third kind (Phase 37).

HS-37-01. An *artifact generator* emits read-only structured data; an
**actuator** instead proposes an **external side effect** (file a ticket,
post a message, open a PR comment, …). The phase-wide safety invariant is:

    No external side effect occurs without an explicit, audited,
    per-action human approval — and what executes is exactly what was
    previewed.

So an actuator's `run()` never *acts*. It returns an `ActuatorProposal`: a
description of what *would* happen — the `target` system, the `action`
verb, a human-readable `preview`, the exact machine `payload`, and whether
the effect is `reversible`. The host records the proposal (status
`proposed`); persistence (HS-37-02), human approval (HS-37-03), and the
guarded executor (HS-37-04) come later. The `payload` captured here is the
**source of truth** for the parity check the executor makes before acting.

This module is deliberately tiny and dependency-light — it is the contract,
not the machinery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# The PluginRunResult.status the host assigns when an actuator proposes.
ACTUATOR_PROPOSAL_STATUS = "proposed"


class ActuatorProposalError(ValueError):
    """Raised when an actuator's `run()` output is not a valid proposal.

    A malformed proposal is the *actuator's* fault, not a host failure: the
    host surfaces it as a normal plugin `error` (no side effect), so a
    buggy actuator can never silently slip past the contract.
    """


@dataclass(frozen=True)
class ActuatorProposal:
    """A proposed external side effect, awaiting human approval.

    Fields:
      - `target`   — the system the effect lands on (e.g. ``github`` / ``jira`` / ``webhook``).
      - `action`   — the verb (e.g. ``create_issue`` / ``post_message``).
      - `preview`  — a human-readable description of exactly what will happen.
      - `payload`  — the machine representation of the side effect; the
                     **source of truth** for execution parity (HS-37-04).
      - `reversible` — whether the effect can be undone (informational for the approver).
      - `required_capabilities` — host capabilities the *execution* needs (may
                     differ from the capabilities required to *propose*).
    """

    target: str
    action: str
    preview: str
    payload: dict[str, Any] = field(default_factory=dict)
    reversible: bool = False
    required_capabilities: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, Any]:
        """Serialize to a plain dict (PluginRunResult.output + persistence)."""
        return {
            "target": self.target,
            "action": self.action,
            "preview": self.preview,
            "payload": dict(self.payload),
            "reversible": self.reversible,
            "required_capabilities": list(self.required_capabilities),
        }

    @classmethod
    def from_run_output(cls, raw: Any) -> "ActuatorProposal":
        """Parse + validate an actuator `run()` output into a proposal.

        Raises `ActuatorProposalError` listing every problem at once, so a
        plugin author fixes them in one pass. Strings are stripped;
        `target`/`action`/`preview` must be non-empty; `payload` must be a
        mapping (an empty payload is allowed but suspicious); `reversible`
        is coerced to bool; `required_capabilities` must be a list of
        non-empty strings.
        """
        if not isinstance(raw, Mapping):
            raise ActuatorProposalError(
                "actuator run() must return a proposal dict with "
                "target/action/preview/payload"
            )

        problems: list[str] = []

        def _require_str(key: str) -> str:
            value = raw.get(key)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"`{key}` must be a non-empty string")
                return ""
            return value.strip()

        target = _require_str("target")
        action = _require_str("action")
        preview = _require_str("preview")

        payload_raw = raw.get("payload", {})
        if not isinstance(payload_raw, Mapping):
            problems.append("`payload` must be an object")
            payload: dict[str, Any] = {}
        else:
            payload = dict(payload_raw)

        reversible = bool(raw.get("reversible", False))

        caps_raw = raw.get("required_capabilities", [])
        capabilities: tuple[str, ...] = ()
        if caps_raw:
            if not isinstance(caps_raw, (list, tuple)):
                problems.append("`required_capabilities`, when present, must be a list")
            else:
                capabilities = tuple(
                    str(c).strip().lower() for c in caps_raw if str(c).strip()
                )

        if problems:
            raise ActuatorProposalError("; ".join(problems))

        return cls(
            target=target,
            action=action,
            preview=preview,
            payload=payload,
            reversible=reversible,
            required_capabilities=capabilities,
        )


__all__ = [
    "ACTUATOR_PROPOSAL_STATUS",
    "ActuatorProposal",
    "ActuatorProposalError",
]
