"""The LoopCollector (CAD-1-02) — projects Open Loops from real HoldSpeak state.

Phase 1 collects two source types: meeting action items and pending actuator
proposals. Projection is an idempotent upsert keyed (source_type, source_id), so
re-running never duplicates and never resurrects a user-decided loop; a source that
disappears is CLOSED (audit), not deleted. READ ONLY — the collector proposes and
executes nothing (that is Phase 6/7, always via the actuator path).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import EvidenceRef, OpenLoop
from .projects import resolve_project
from .scoring import LoopSignals, score_loop

# Below this review confidence an extracted action becomes a quiet `needs_review`
# loop (surfaced, never pushed) rather than a normal loop (chart §3.6). Phase 1
# proxy: an item still in review_state="pending" is treated as needs_review.
_REVIEW_PENDING = "pending"


class LoopCollector:
    def __init__(self, db, *, meeting_scan_limit: int = 50):
        self._db = db
        self._meeting_scan_limit = meeting_scan_limit

    def collect(self, *, now: Optional[datetime] = None) -> list[OpenLoop]:
        """Project + score loops from the current sources; return the live set."""
        now = now or datetime.now()
        loops: list[OpenLoop] = []
        loops += self._collect_meeting_actions(now)
        loops += self._collect_pending_proposals(now)
        return loops

    # ── meeting action items ────────────────────────────────────────────────
    def _collect_meeting_actions(self, now: datetime) -> list[OpenLoop]:
        items = self._db.meetings.list_action_items(include_completed=False)
        present_ids = [it.id for it in items]
        out = []
        for it in items:
            needs_review = (it.review_state or _REVIEW_PENDING) == _REVIEW_PENDING
            unowned = not (it.owner and it.owner.strip())
            loop = OpenLoop(
                source_type="meeting_action",
                source_id=it.id,
                title=it.task,
                summary=f"From {it.meeting_title or 'a meeting'}",
                project=resolve_project(meeting_label=it.meeting_title),
                priority="high" if (it.due and not unowned) else "normal",
                needs_review=needs_review,
                owner=it.owner,
                due_at=it.due,
                evidence=[
                    EvidenceRef(
                        kind="action_item",
                        ref_id=it.id,
                        label=it.task[:80],
                        timestamp=str(it.source_timestamp) if it.source_timestamp else None,
                        deep_link=f"/meetings/{it.meeting_id}#ai-{it.id}",
                    )
                ],
            )
            saved = self._db.cadence.upsert_loop(loop)
            self._score(saved, now, LoopSignals(unowned=unowned))
            out.append(saved)
        self._db.cadence.close_missing("meeting_action", present_ids)
        return out

    # ── pending actuator proposals (read only) ──────────────────────────────
    def _collect_pending_proposals(self, now: datetime) -> list[OpenLoop]:
        present_ids: list[str] = []
        out = []
        meetings = self._db.meetings.list_meetings(limit=self._meeting_scan_limit)
        for m in meetings:
            for p in self._db.actuators.list_proposals(m.id, status="proposed"):
                present_ids.append(p.id)
                loop = OpenLoop(
                    source_type="proposal",
                    source_id=p.id,
                    title=p.preview,
                    summary=f"{p.action} → {p.target}",
                    project=resolve_project(meeting_label=getattr(m, "title", None)),
                    priority="high",  # a proposal awaiting your approval is leverage
                    evidence=[
                        EvidenceRef(
                            kind="proposal",
                            ref_id=p.id,
                            label=p.preview[:80],
                            deep_link=f"/meetings/{p.meeting_id}#proposal-{p.id}",
                        )
                    ],
                )
                saved = self._db.cadence.upsert_loop(loop)
                self._score(saved, now, LoopSignals())
                out.append(saved)
        self._db.cadence.close_missing("proposal", present_ids)
        return out

    def _score(self, loop: OpenLoop, now: datetime, signals: LoopSignals) -> None:
        breakdown = score_loop(loop, now=now, signals=signals)
        loop.stale_score = breakdown.total
        self._db.cadence.set_stale_score(loop.id, breakdown.total)
