"""Stale-loop escalation + the end-of-day closure ritual (CAD-6).

Escalation: a loop that has survived several nudges or several days gets a louder
severity, so it stops being ignorable. Closeout: at end of day, group the open loops
and recommend a cheap decision for each (close / file / snooze / kill / delegate), so
clearing the board is a batch of one-taps rather than a chore. All deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .models import OpenLoop

# Escalation thresholds (nudges survived, days old).
_PERSISTENT_NUDGES = 3
_ESCALATED_NUDGES = 6
_PERSISTENT_DAYS = 2.0
_ESCALATED_DAYS = 4.0


def _age_days(loop: OpenLoop, now: datetime) -> float:
    if not loop.created_at:
        return 0.0
    try:
        return max(0.0, (now - datetime.fromisoformat(loop.created_at)).total_seconds() / 86400.0)
    except ValueError:
        return 0.0


def escalation_severity(loop: OpenLoop, *, now: datetime) -> str:
    """quiet | normal | persistent | escalated — how loudly to push this loop."""
    if loop.needs_review:
        return "quiet"
    age = _age_days(loop, now)
    if loop.nudge_count >= _ESCALATED_NUDGES or age >= _ESCALATED_DAYS:
        return "escalated"
    if loop.nudge_count >= _PERSISTENT_NUDGES or age >= _PERSISTENT_DAYS:
        return "persistent"
    return "normal"


# The deterministic recommendation for a loop at closeout.
@dataclass
class CloseoutRec:
    loop: OpenLoop
    severity: str
    action: str       # close | file | snooze | kill | delegate | reply | approve | review
    reason: str


@dataclass
class Closeout:
    date: str
    recs: list[CloseoutRec] = field(default_factory=list)
    open_count: int = 0

    @property
    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.recs:
            out[r.action] = out.get(r.action, 0) + 1
        return out

    @property
    def is_empty(self) -> bool:
        return not self.recs


def _recommend(loop: OpenLoop, severity: str, *, now: datetime) -> CloseoutRec:
    age = _age_days(loop, now)
    if loop.needs_review:
        return CloseoutRec(loop, severity, "review", "Low-confidence — confirm or dismiss.")
    if loop.source_type == "agent_question":
        return CloseoutRec(loop, severity, "reply", "An agent is waiting — answer it.")
    if loop.source_type == "proposal":
        return CloseoutRec(loop, severity, "approve", "A proposal is ready for your approval.")
    unowned = not (loop.owner and loop.owner.strip())
    if severity == "escalated" and unowned:
        return CloseoutRec(loop, severity, "kill", "Open for days, still unowned — kill it or own it.")
    if unowned:
        return CloseoutRec(loop, severity, "delegate", "No owner — assign it or delegate it.")
    if age >= _ESCALATED_DAYS:
        return CloseoutRec(loop, severity, "file", "Owned but stale — file it as an issue now.")
    if severity in ("persistent", "escalated"):
        return CloseoutRec(loop, severity, "file", "It keeps resurfacing — file it and move on.")
    return CloseoutRec(loop, severity, "snooze", "Not today — snooze until it matters.")


def build_closeout(db, *, now: Optional[datetime] = None) -> Closeout:
    """Group the open loops with a recommended decision for each (deterministic)."""
    now = now or datetime.now()
    loops = db.cadence.list_loops()  # ordered by stale_score desc
    recs = [
        _recommend(loop, escalation_severity(loop, now=now), now=now)
        for loop in loops
    ]
    return Closeout(date=now.strftime("%Y-%m-%d"), recs=recs, open_count=len(loops))


# Which closeout/decision actions are legal to apply in a batch (lifecycle only —
# 'file'/'reply'/'approve' open a draft elsewhere, they are not batch-applied here).
APPLYABLE = {"snooze", "kill", "close", "done", "delegate"}


def apply_decision(db, loop_id: str, action: str, *, now: Optional[datetime] = None,
                   owner: Optional[str] = None) -> bool:
    """Apply one lifecycle decision. Returns True if applied. No external side effect."""
    now = now or datetime.now()
    loop = db.cadence.get_loop(loop_id)
    if loop is None or action not in APPLYABLE:
        return False
    if action == "snooze":
        from datetime import timedelta
        db.cadence.snooze(loop_id, (now + timedelta(days=1)).isoformat())
    elif action == "kill":
        db.cadence.set_status(loop_id, "killed")
    elif action in ("close", "done"):
        db.cadence.set_status(loop_id, "closed")
    elif action == "delegate":
        db.cadence.set_status(loop_id, "delegated")
    return True


def render_closeout_text(closeout: Closeout) -> str:
    lines = [f"End-of-day closeout — {closeout.date}", ""]
    if closeout.is_empty:
        lines.append("Your loops are clear. Nice.")
        return "\n".join(lines)
    summary = ", ".join(f"{k}×{v}" for k, v in sorted(closeout.summary.items()))
    lines.append(f"{closeout.open_count} open · recommended: {summary}")
    lines.append("")
    for r in closeout.recs:
        tag = f"[{r.severity[0].upper()}]" if r.severity in ("persistent", "escalated") else "   "
        lines.append(f"  {tag} {r.action:8s} {r.loop.title}  — {r.reason}")
    return "\n".join(lines)
