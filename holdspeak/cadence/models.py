"""Cadence Engine data models (CAD-1-01).

Pure dataclasses — no I/O. The repository (`holdspeak/db/cadence.py`) converts
rows to/from these; the rest of the engine (collector, scoring, scheduler)
operates on them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

LoopStatus = Literal["open", "snoozed", "closed", "killed", "delegated"]
Priority = Literal["low", "normal", "high", "urgent"]
SourceType = Literal[
    "meeting_action",
    "meeting_decision",
    "agent_question",
    "activity_record",
    "proposal",
    "manual",
    "system",
]
EvidenceKind = Literal[
    "meeting_segment",
    "artifact",
    "action_item",
    "activity_record",
    "agent_session",
    "proposal",
    "dictation_journal",
]
NextActionKind = Literal[
    "review_draft",
    "approve_proposal",
    "reply_to_agent",
    "create_issue",
    "draft_slack_update",
    "mark_done",
    "assign_owner",
    "schedule_followup",
    "kill_loop",
    "snooze",
]
Surface = Literal["desktop", "telegram", "web", "cli", "ipad"]
Severity = Literal["quiet", "normal", "persistent", "escalated"]
NudgeStatus = Literal["pending", "shown", "acted", "dismissed", "expired"]


@dataclass
class EvidenceRef:
    """Why a loop exists — a citation the user can follow."""

    kind: EvidenceKind
    ref_id: str
    label: str = ""
    timestamp: Optional[str] = None
    deep_link: Optional[str] = None
    id: Optional[str] = None  # assigned by the store


@dataclass
class OpenLoop:
    """An unresolved item that may deserve future attention.

    Projected from a source by the collector; keyed by (source_type, source_id).
    The lifecycle fields (status/snoozed_until/nudge_count) are the user's, and
    survive re-collection.
    """

    source_type: SourceType
    source_id: str
    title: str
    summary: str = ""
    project: Optional[str] = None
    status: LoopStatus = "open"
    priority: Priority = "normal"
    needs_review: bool = False
    owner: Optional[str] = None
    due_at: Optional[str] = None
    snoozed_until: Optional[str] = None
    stale_score: float = 0.0
    last_nudged_at: Optional[str] = None
    nudge_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[str] = None  # assigned by the store
    evidence: list[EvidenceRef] = field(default_factory=list)


@dataclass
class NextBestAction:
    """The prepared thing Qlippy wants the user to decide on."""

    loop_id: str
    kind: NextActionKind
    title: str
    body_markdown: str = ""
    confidence: float = 0.0
    reversible: bool = True
    proposal_id: Optional[str] = None
    generated_by: str = "deterministic"
    generated_at: Optional[str] = None
    id: Optional[str] = None


@dataclass
class Nudge:
    """A surfaced recommendation at a specific time on a specific surface."""

    loop_id: str
    surface: Surface
    severity: Severity = "normal"
    next_action_id: Optional[str] = None
    title: str = ""
    message_markdown: str = ""
    status: NudgeStatus = "pending"
    created_at: Optional[str] = None
    shown_at: Optional[str] = None
    acted_at: Optional[str] = None
    expires_at: Optional[str] = None
    id: Optional[str] = None


@dataclass
class CadencePolicy:
    """How often Qlippy pushes for a given class of loop.

    `config` holds the tunable knobs (quiet hours, delays, escalation, caps,
    surfaces); persisted as JSON so policies are editable without a migration.
    """

    name: str
    enabled: bool = True
    config: dict = field(default_factory=dict)
    updated_at: Optional[str] = None
    id: Optional[str] = None


@dataclass(frozen=True)
class ScoreBreakdown:
    """The staleness total AND its per-signal contributions, so every nudge is
    explainable. Ephemeral (recomputed); only the total persists on the loop."""

    total: float
    contributions: dict  # signal name -> signed contribution

    def explain(self) -> str:
        parts = [f"{k}={v:+.1f}" for k, v in sorted(self.contributions.items())]
        return f"score={self.total:.1f} (" + ", ".join(parts) + ")"
