"""Shared actuator-lifecycle helpers (Phase 72).

The propose→approve→execute helpers that both the meeting proposal routes
(`meetings.py`) and the desk actuator relay (`desk_actuators.py`) call. They
were closures inside ``build_meetings_router`` until the desk relay moved to
its own router; promoting them here keeps ONE implementation of the
execute-on-approve leg (the full unification of the lifecycle is the next
story's job — this module is its seam).

Behavior is byte-identical to the closures it replaces; ``ctx`` (the
broadcast seam) is passed explicitly instead of closed over.
"""
from __future__ import annotations

from typing import Any

from ..context import WebContext

# The gh runner override for the GitHub-issue connector (tests patch this).
_GITHUB_RUNNER = None


def proposal_to_dict(proposal: Any) -> dict[str, Any]:
    return {
        "id": proposal.id,
        "origin": getattr(proposal, "origin", "meeting"),
        "meeting_id": proposal.meeting_id,
        "window_id": proposal.window_id,
        "plugin_id": proposal.plugin_id,
        "plugin_version": proposal.plugin_version,
        "status": proposal.status,
        "target": proposal.target,
        "action": proposal.action,
        "preview": proposal.preview,
        "payload": proposal.payload,
        "reversible": proposal.reversible,
        "required_capabilities": proposal.required_capabilities,
        "decided_by": proposal.decided_by,
        "authority": {
            "payload_hash": proposal.approved_payload_hash,
            "destination": proposal.approved_destination,
            "preview_hash": proposal.approved_preview_hash,
            "preview_renderer_version": proposal.preview_renderer_version,
            "effect_class": proposal.effect_class,
            "policy_version": proposal.policy_version,
        } if proposal.approved_payload_hash else None,
        "result": proposal.result,
        "error": proposal.error,
        "created_at": proposal.created_at,
        "decided_at": proposal.decided_at,
        "executed_at": proposal.executed_at,
    }


def actuator_result_event(proposal: Any) -> dict[str, Any]:
    """The wire-safe `actuator_result` payload (preview only, never the
    machine payload — the Phase-56 lock)."""
    return {
        "id": getattr(proposal, "id", ""),
        "meeting_id": getattr(proposal, "meeting_id", ""),
        "status": getattr(proposal, "status", ""),
        "target": getattr(proposal, "target", ""),
        "action": getattr(proposal, "action", ""),
        "preview": getattr(proposal, "preview", ""),
        "reversible": bool(getattr(proposal, "reversible", False)),
        "error": getattr(proposal, "error", None),
    }


def decide_proposal(
    ctx: WebContext,
    db: Any,
    proposal_id: str,
    *,
    decision: str,
    actor: str,
    belongs: Any,
    executors: dict[str, Any],
) -> tuple[Any, str | None, int]:
    """ONE propose→approve→execute decision lifecycle (Phase 72).

    The four decision routes (the meeting proposal route and the three desk
    relay routes) used to carry four copies of the same skeleton: validate
    the decision → fetch + scope-check → transition (audited) → broadcast a
    terminal rejection → execute-on-approve for the targets whose approval
    IS the send. This is that skeleton, once.

    - ``belongs(existing) -> bool`` is the caller's scoping rule (the meeting
      route checks the meeting id; the desk routes check origin + target).
    - ``executors`` maps a target to its execute leg
      (``fn(ctx, db, proposal, *, actor)``); targets absent from the map keep
      the Phase-37 behavior — approval flips state only.

    Returns ``(proposal, error, http_status)`` — exactly one of
    proposal/error is set.
    """
    clean = str(decision or "").strip().lower()
    if clean not in ("approved", "rejected"):
        return None, f"Invalid decision: {decision!r}", 400
    existing = db.actuators.get_proposal(proposal_id)
    if existing is None or not belongs(existing):
        return None, "Proposal not found", 404
    try:
        updated = db.actuators.transition_proposal(
            proposal_id, to_status=clean, actor=actor
        )
    except ValueError as ve:
        # Illegal lifecycle transition (e.g. already executed/rejected).
        return None, str(ve), 400
    if clean == "rejected":
        # A rejection is a terminal result presence can reflect (HS-56-03).
        # Wire-safe: preview only, never the machine payload.
        ctx.broadcast("actuator_result", actuator_result_event(updated))
    if clean == "approved":
        execute = executors.get(updated.target)
        if execute is not None:
            updated = execute(ctx, db, updated, actor=actor)
    return updated, None, 200


def execute_slack_proposal(ctx: WebContext, db: Any, proposal: Any, *, actor: str) -> Any:
    """HS-61-01: the execute leg for an approved Send-to-Slack proposal.

    The repo had no production execute path at all before this — the
    `ActuatorExecutor` was host-injected in dogfoods only. For `slack`
    proposals the approval IS the moment the user wants the send, so the
    decision route executes right here, through the full executor guard
    stack (status gate, payload parity, audit).

    On consent: the user configured `meeting.slack_webhook_url` (consent
    for exactly that host — the connector's manifest allow-lists it and
    nothing else) and just approved this very action. That pair is the
    Phase-52 "configuring is consent" model PLUS a per-action approval,
    so this executor instance runs with its master switch on rather than
    demanding a third toggle (`allow_actuators`) be flipped too.

    The webhook URL is a credential: it is read from config at execution
    time and injected by the connector in memory only — never stored on
    the proposal, never broadcast, never returned.
    """
    from ...config import Config
    from ...plugins.actuator_executor import ActuatorExecutor
    from ...slack_export import build_slack_connector

    url = Config.load().meeting.slack_webhook_url
    if not url:
        # Configured when proposed, unconfigured by execution time: an
        # honest terminal failure (retryable via failed -> approved once
        # the URL is back), never a silent drop.
        updated = db.actuators.transition_proposal(
            proposal.id,
            to_status="failed",
            actor=actor,
            detail="slack export: no webhook URL configured at execution time",
            error="Slack is not configured (meeting.slack_webhook_url is empty)",
        )
        ctx.broadcast("actuator_result", actuator_result_event(updated))
        return updated

    executor = ActuatorExecutor(
        db,
        connector=build_slack_connector(url),
        allow_actuators=True,
        actor=actor,
        on_result=lambda event: ctx.broadcast("actuator_result", event),
    )
    return executor.execute(proposal.id)


def execute_webhook_proposal(ctx: WebContext, db: Any, proposal: Any, *, actor: str) -> Any:
    """HSM-14: the execute leg for an approved desk Webhook proposal.

    The generic sibling of `execute_slack_proposal` — same consent model and
    guard stack, but the URL comes from `meeting.companion_webhook_url` and
    the host is allow-listed by `build_url_webhook_connector`. The credential
    is read from config at execution time and injected in memory only.
    """
    from ...config import Config
    from ...plugins.actuator_executor import ActuatorExecutor
    from ...slack_export import build_url_webhook_connector

    url = Config.load().meeting.companion_webhook_url
    if not url:
        updated = db.actuators.transition_proposal(
            proposal.id, to_status="failed", actor=actor,
            detail="companion webhook: no URL configured at execution time",
            error="Webhook is not configured (meeting.companion_webhook_url is empty)",
        )
        ctx.broadcast("actuator_result", actuator_result_event(updated))
        return updated
    executor = ActuatorExecutor(
        db, connector=build_url_webhook_connector(url), allow_actuators=True,
        actor=actor, on_result=lambda event: ctx.broadcast("actuator_result", event),
    )
    return executor.execute(proposal.id)


def execute_github_proposal(ctx: WebContext, db: Any, proposal: Any, *, actor: str) -> Any:
    """HSM-14: the execute leg for an approved desk GitHub-issue proposal.

    Files the issue via the Phase-38 `gh issue create` connector — auth is the
    host's local `gh`, no token is stored or crosses. The created issue URL is
    the result. The same guarded executor stack (status gate, payload parity).
    """
    from ...plugins.actuator_executor import ActuatorExecutor
    from ...plugins.builtin.github_issue_actuator import build_github_issue_connector

    executor = ActuatorExecutor(
        db, connector=build_github_issue_connector(runner=_GITHUB_RUNNER), allow_actuators=True,
        actor=actor, on_result=lambda event: ctx.broadcast("actuator_result", event),
    )
    return executor.execute(proposal.id)
