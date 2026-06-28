"""Deterministic Next-Best-Action generator (CAD-2-01).

Maps an Open Loop to the prepared move Qlippy wants the user to decide on — WITHOUT
an LLM (the LLM-drafted version is Phase 7). The point of the cadence engine is that
the next decision is cheap: a proposal awaiting approval becomes an `approve_proposal`,
an owned action becomes a `create_issue` DRAFT (a draft, not an execution — executing
goes through the actuator path), an unowned action becomes `assign_owner`, and a
low-confidence extraction becomes `review_draft`.
"""
from __future__ import annotations

from .models import NextBestAction, OpenLoop


def generate_next_action(loop: OpenLoop) -> NextBestAction:
    """The single best prepared move for this loop (deterministic)."""
    kind, title, body, reversible = _decide(loop)
    return NextBestAction(
        loop_id=loop.id or "",
        kind=kind,
        title=title,
        body_markdown=body,
        confidence=0.6,  # deterministic baseline; the LLM path (Phase 7) scores higher/lower
        reversible=reversible,
        generated_by="deterministic",
    )


def _decide(loop: OpenLoop):
    src = loop.source_type
    if loop.needs_review:
        return (
            "review_draft",
            f"Review: {loop.title}",
            "This was extracted with low confidence. Confirm it is a real, actionable "
            "item (then it can be filed), or dismiss it.",
            True,
        )
    if src == "proposal":
        return (
            "approve_proposal",
            f"Approve: {loop.title}",
            f"{loop.summary or 'A proposed action'} is ready for your approval. Approving runs it "
            "through the existing approve → execute path; nothing leaves your machine until you do.",
            False,
        )
    if src == "agent_question":
        where = loop.summary or loop.project or "your terminal"
        return (
            "reply_to_agent",
            f"Reply to the waiting agent: {loop.title}",
            f"A coding agent ({where}) is blocked on your answer:\n\n> {loop.title}\n\n"
            "Type your reply on the cadence page — it is sent into the agent's terminal pane. "
            "Never autonomous: nothing is sent until you press Send.",
            False,
        )
    if src in ("meeting_action", "manual"):
        if not (loop.owner and loop.owner.strip()):
            return (
                "assign_owner",
                f"Assign an owner: {loop.title}",
                "This action has no owner. Assign it (to you or someone else) so it can move, "
                "or kill the loop if it is not worth doing.",
                True,
            )
        return (
            "create_issue",
            f"File an issue: {loop.title}",
            _issue_body(loop),
            False,
        )
    if src == "meeting_decision":
        return (
            "schedule_followup",
            f"Schedule a follow-up: {loop.title}",
            "A decision was made that needs a follow-up. Schedule it or convert it to a tracked item.",
            True,
        )
    return ("review_draft", f"Review: {loop.title}", loop.summary or "", True)


def _issue_body(loop: OpenLoop) -> str:
    lines = [loop.title, ""]
    meta = []
    if loop.owner:
        meta.append(f"Owner: {loop.owner}")
    if loop.due_at:
        meta.append(f"Due: {loop.due_at}")
    if loop.project:
        meta.append(f"Project: {loop.project}")
    if meta:
        lines.append(" · ".join(meta))
    if loop.evidence:
        ev = loop.evidence[0]
        lines.append("")
        lines.append(f"Source: {ev.label or ev.kind}" + (f" ({ev.deep_link})" if ev.deep_link else ""))
    return "\n".join(lines)
