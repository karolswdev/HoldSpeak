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

import os

from .models import EvidenceRef, OpenLoop
from .projects import resolve_project
from .scoring import LoopSignals, score_loop


def _first_line(text: str, *, limit: int = 120) -> str:
    line = (text or "").strip().splitlines()[0].strip() if (text or "").strip() else ""
    return line[:limit]


def _basename(path) -> str:
    return os.path.basename(str(path).rstrip("/")) if path else ""

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
        loops += self._collect_meeting_decisions(now)
        loops += self._collect_pending_proposals(now)
        loops += self._collect_agent_questions(now)
        return loops

    # ── awaiting coding-agent sessions (CAD-3-01) ───────────────────────────
    def _collect_agent_questions(self, now: datetime) -> list[OpenLoop]:
        """Mirror awaiting Claude/Codex sessions into top-scored agent_question loops.

        READ ONLY — reads the agent-session capture file; the reply DELIVERY is a
        route concern (`send_text_to_pane`), never this package.
        """
        try:
            from ..agent_context import list_recent_awaiting_agent_sessions
            sessions = list_recent_awaiting_agent_sessions()
        except Exception:
            return []
        present_ids: list[str] = []
        out = []
        for s in sessions:
            present_ids.append(s.session_id)
            question = (s.last_assistant_text or "").strip()
            loop = OpenLoop(
                source_type="agent_question",
                source_id=s.session_id,
                title=_first_line(question) or f"{s.agent} is waiting on you",
                summary=f"{s.agent} · {s.project_name or _basename(s.repo_root) or s.cwd}",
                project=resolve_project(explicit=s.project_name, repo_root=s.repo_root or s.cwd),
                priority="urgent",  # a blocked agent is the top signal
                owner="you",
                evidence=[
                    EvidenceRef(
                        kind="agent_session",
                        ref_id=s.session_id,
                        label=f"{s.agent} session",
                        timestamp=s.updated_at,
                        deep_link="/cadence",  # the reply composer lives on the coach page
                    )
                ],
            )
            saved = self._db.cadence.upsert_loop(loop)
            self._score(saved, now, LoopSignals())
            out.append(saved)
        self._db.cadence.close_missing("agent_question", present_ids)
        return out

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

    # ── meeting decisions with open commitments ─────────────────────────────
    def _collect_meeting_decisions(self, now: datetime) -> list[OpenLoop]:
        """Collect accepted decisions with open commitments into cadence loops."""
        with self._db._connection() as conn:
            rows = conn.execute(
                """
                SELECT dc.decision_id, dc.owner, dc.due_at, d.text,
                       d.project_key, d.source_meeting_id, m.title AS meeting_title
                  FROM decision_commitments AS dc
                  JOIN decisions AS d ON d.id = dc.decision_id
             LEFT JOIN meetings AS m ON m.id = d.source_meeting_id
                 WHERE dc.status = 'open'
                   AND d.deleted = 0
                   AND d.lifecycle = 'accepted'
                """
            ).fetchall()

        present_ids = [str(row["decision_id"]) for row in rows]
        out = []
        for row in rows:
            decision_id = str(row["decision_id"])
            owner = row["owner"]
            due_at = row["due_at"]
            unowned = not (owner and owner.strip())
            loop = OpenLoop(
                source_type="meeting_decision",
                source_id=decision_id,
                title=str(row["text"]),
                summary=f"Decision from {row['meeting_title'] or 'a meeting'}",
                project=resolve_project(
                    explicit=row["project_key"], meeting_label=row["meeting_title"]
                ),
                priority="high" if (due_at and not unowned) else "normal",
                owner=owner,
                due_at=due_at,
                evidence=[
                    EvidenceRef(
                        kind="decision",
                        ref_id=decision_id,
                        label=str(row["text"])[:80],
                        deep_link=f"/meetings/{row['source_meeting_id']}#decision-{decision_id}",
                    )
                ],
            )
            saved = self._db.cadence.upsert_loop(loop)
            self._score(saved, now, LoopSignals(unowned=unowned))
            out.append(saved)
        self._db.cadence.close_missing("meeting_decision", present_ids)
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
