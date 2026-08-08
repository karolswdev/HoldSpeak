"""Windowed, persistent generation model for the Monday Brief."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Any

from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service


_SECTIONS = ("changed", "broke", "waiting", "decisions")
_CHANGE_METHOD_MARKERS = (
    "create",
    "update",
    "delete",
    "transition",
    "run",
    "commit",
    "complete",
)
_CLOSE_HOUR = 17
_RETRY_WINDOW_SECONDS = 5 * 60


@dataclass
class BriefItem:
    id: str
    section: str  # changed, broke, waiting, decisions
    text: str
    detail: str | None = None
    source_ref: str | None = None
    priority: int = 0


@dataclass
class MondayBrief:
    id: str
    period_start: str
    period_end: str
    headline: str
    sections: dict[str, list[BriefItem]]
    generated_at: str
    is_empty: bool = False


@observe_service
class MondayBriefService:
    """Create one durable brief per local calendar day.

    The supplied datetime's timezone (when it has one) is retained while
    calculating the local 17:00 close. Naive datetimes retain the application's
    existing local-time convention.
    """

    def __init__(self, db: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def compute_window(
        self, now: datetime.datetime | None = None
    ) -> tuple[datetime.datetime, datetime.datetime]:
        """Compute the local brief window, from the preceding close to *now*."""
        period_end = now or datetime.datetime.now()
        weekday = period_end.weekday()
        if weekday == 0:  # Monday starts from the preceding Friday close.
            days_back = 3
        elif weekday < 5:  # Tuesday through Friday starts yesterday.
            days_back = 1
        else:  # Weekend briefs continue from Friday close.
            days_back = weekday - 4

        start_date = (period_end - datetime.timedelta(days=days_back)).date()
        period_start = datetime.datetime.combine(
            start_date,
            datetime.time(hour=_CLOSE_HOUR),
            tzinfo=period_end.tzinfo,
        )
        return period_start, period_end

    def generate(
        self, principal: Any, *, now: datetime.datetime | None = None
    ) -> MondayBrief:
        """Generate or return the existing brief for the current local date."""
        period_start, period_end = self.compute_window(now)
        date_key = period_end.date().isoformat()
        waiting_items = self._collect_waiting(principal)

        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT * FROM monday_briefs
                   WHERE substr(period_end, 1, 10) = ?
                   ORDER BY generated_at DESC, id DESC LIMIT 1""",
                (date_key,),
            ).fetchone()
            if row is not None:
                return self._load_brief(conn, row)

            brief_id = f"brief-{uuid.uuid4().hex}"
            generated_at = period_end.isoformat()
            conn.execute(
                """INSERT INTO monday_briefs
                   (id, period_start, period_end, headline, generated_at)
                   VALUES (?, ?, ?, '', ?)""",
                (
                    brief_id,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    generated_at,
                ),
            )
            items = [
                *self._collect_changes(
                    period_start.isoformat(), period_end.isoformat()
                ),
                *self._collect_breakage(
                    period_start.isoformat(), period_end.isoformat()
                ),
                *waiting_items,
                *self._collect_decisions(principal),
            ]
            for item in items:
                conn.execute(
                    """INSERT INTO monday_brief_items
                       (id, brief_id, section, text, detail, source_ref, priority)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.id,
                        brief_id,
                        item.section,
                        item.text,
                        item.detail,
                        item.source_ref,
                        item.priority,
                    ),
                )
            row = conn.execute(
                "SELECT * FROM monday_briefs WHERE id = ?", (brief_id,)
            ).fetchone()
            assert row is not None
            return self._load_brief(conn, row)

    def _collect_changes(self, window_start: str, window_end: str) -> list[BriefItem]:
        """Reduce pipeline events in the window to material state changes."""
        start_timestamp = self._window_timestamp(window_start)
        end_timestamp = self._window_timestamp(window_end)
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT event_id, timestamp, service, method, args_summary,
                          correlation_id, error
                   FROM pipeline_events
                   WHERE timestamp BETWEEN ? AND ?
                   ORDER BY timestamp ASC, id ASC""",
                (start_timestamp, end_timestamp),
            ).fetchall()

        groups: dict[str, list[Any]] = {}
        uncorrelated_retries: dict[tuple[str, str, str], tuple[str, Any]] = {}
        for row in rows:
            method = str(row["method"])
            if not any(marker in method.lower() for marker in _CHANGE_METHOD_MARKERS):
                continue
            correlation_id = str(row["correlation_id"])
            if correlation_id:
                groups.setdefault(correlation_id, []).append(row)
                continue

            # Observer calls without a correlation are independent unless they
            # look like an immediate retry of the same failed invocation.
            signature = (str(row["service"]), method, str(row["args_summary"]))
            previous = uncorrelated_retries.get(signature)
            if (
                previous is not None
                and float(row["timestamp"]) - float(previous[1]["timestamp"])
                <= _RETRY_WINDOW_SECONDS
                and (previous[1]["error"] is not None or row["error"] is not None)
            ):
                group_key = previous[0]
                groups[group_key].append(row)
            else:
                group_key = f"event:{row['event_id']}"
                groups[group_key] = [row]
            uncorrelated_retries[signature] = (group_key, row)

        items: list[BriefItem] = []
        for events in groups.values():
            first = events[0]
            args_summary = str(first["args_summary"])
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="changed",
                    text=f"{first['service']}.{first['method']}",
                    detail=args_summary if args_summary != "{}" else None,
                    source_ref=(
                        f"pipeline:{first['correlation_id']}"
                        if first["correlation_id"]
                        else f"pipeline-event:{first['event_id']}"
                    ),
                )
            )
        return items

    def _collect_breakage(self, window_start: str, window_end: str) -> list[BriefItem]:
        """Gather errors and failures from the requested brief window."""
        start_timestamp = self._window_timestamp(window_start)
        end_timestamp = self._window_timestamp(window_end)
        items: list[BriefItem] = []

        with self._db._connection() as conn:
            event_rows = conn.execute(
                """SELECT event_id, timestamp, service, method, error, error_code
                   FROM pipeline_events
                   WHERE error IS NOT NULL AND timestamp BETWEEN ? AND ?
                   ORDER BY timestamp DESC, id DESC""",
                (start_timestamp, end_timestamp),
            ).fetchall()

            # The observer may record retries separately. Keep the most recent
            # receipt for each failing service method, which is the useful repair
            # path without inflating the Monday Brief.
            seen_methods: set[tuple[str, str]] = set()
            for row in event_rows:
                service = str(row["service"])
                method = str(row["method"])
                if (service, method) in seen_methods:
                    continue
                seen_methods.add((service, method))
                error = str(row["error"])
                error_code = row["error_code"]
                detail = f"{error_code}: {error}" if error_code else error
                items.append(
                    BriefItem(
                        id=f"brief-break-pipeline-{row['event_id']}",
                        section="broke",
                        text=f"{service}.{method} failed",
                        detail=detail,
                        source_ref=f"pipeline-event:{row['event_id']}",
                        priority=2,
                    )
                )

            connector_table = conn.execute(
                """SELECT 1 FROM sqlite_master
                   WHERE type = 'table' AND name = 'connector_runs'"""
            ).fetchone()
            if connector_table is not None:
                connector_rows = conn.execute(
                    """SELECT id, connector_id, started_at, error
                       FROM connector_runs
                       WHERE succeeded = 0 AND started_at BETWEEN ? AND ?
                       ORDER BY started_at DESC, id DESC""",
                    (window_start, window_end),
                ).fetchall()
                seen_connectors: set[str] = set()
                for row in connector_rows:
                    connector_id = str(row["connector_id"])
                    if connector_id in seen_connectors:
                        continue
                    seen_connectors.add(connector_id)
                    items.append(
                        BriefItem(
                            id=f"brief-break-connector-{row['id']}",
                            section="broke",
                            text=f"Connector {connector_id} failed",
                            detail=str(row["error"] or "No error detail recorded."),
                            source_ref=f"connector-run:{row['id']}",
                            priority=2,
                        )
                    )

        return items

    def _collect_waiting(self, principal: Any) -> list[BriefItem]:
        """Gather pending work: overdue follow-through, high-priority loops, pending proposals."""
        board = FollowThroughService(self._db).board(principal)
        items: list[BriefItem] = []
        seen_loop_ids: set[str] = set()
        seen_action_ids: set[str] = set()

        for lane, priority, label in (
            (board.overdue, 300, "Overdue"),
            (board.unassigned, 200, "Unassigned"),
        ):
            for card in lane:
                if card.source == "cadence_loop":
                    seen_loop_ids.add(card.id)
                elif card.source == "action_item":
                    seen_action_ids.add(card.id)
                detail = f"Due {card.due}" if card.due else "Needs an owner"
                items.append(
                    BriefItem(
                        id=f"brief-item-{uuid.uuid4().hex}",
                        section="waiting",
                        text=f"{label}: {card.text}",
                        detail=detail,
                        source_ref=f"{card.source}:{card.id}",
                        priority=priority,
                    )
                )

        with self._db._connection() as conn:
            loop_rows = conn.execute(
                """SELECT id, source_type, source_id, title, priority, due_at
                   FROM cadence_loops
                   WHERE status = 'open' AND priority IN ('high', 'urgent')
                   ORDER BY CASE priority WHEN 'urgent' THEN 1 ELSE 0 END DESC,
                            due_at ASC, id ASC"""
            ).fetchall()
            proposal_rows = []
            proposal_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'actuator_proposals'"
            ).fetchone()
            if proposal_table is not None:
                proposal_rows = conn.execute(
                    """SELECT id, preview, target, action
                       FROM actuator_proposals
                       WHERE status = 'proposed' AND review_decision = 'unreviewed'
                       ORDER BY created_at ASC, id ASC"""
                ).fetchall()

        for loop in loop_rows:
            loop_id = str(loop["id"])
            if loop_id in seen_loop_ids or (
                loop["source_type"] == "meeting_action"
                and str(loop["source_id"]) in seen_action_ids
            ):
                continue
            urgency = 120 if str(loop["priority"]) == "urgent" else 100
            due_at = str(loop["due_at"]) if loop["due_at"] else None
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    text=f"Open loop: {loop['title']}",
                    detail=f"Due {due_at[:10]}" if due_at else "High priority",
                    source_ref=f"cadence_loop:{loop_id}",
                    priority=urgency,
                )
            )

        for proposal in proposal_rows:
            preview = str(proposal["preview"]).strip()
            description = preview or f"{proposal['action']} on {proposal['target']}"
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="waiting",
                    text=f"Approval needed: {description}",
                    detail="Awaiting review",
                    source_ref=f"actuator_proposal:{proposal['id']}",
                    priority=150,
                )
            )

        return sorted(items, key=lambda item: (-item.priority, item.source_ref or ""))

    def _collect_decisions(self, principal: Any) -> list[BriefItem]:
        """Gather decisions requiring owner attention."""
        del principal
        items: list[BriefItem] = []

        # A proposed actuator cannot cross the egress boundary until its owner
        # grants authorization, so it always leads the decision queue.
        for proposal in self._db.actuators.list_pending_proposals():
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Authorize {proposal.target} {proposal.action}: {proposal.preview}",
                    source_ref=f"actuator_proposal:{proposal.id}",
                    priority=300,
                )
            )

        # Desk decisions carry an explicit proposed state. Meeting-derived
        # decisions are recorded until the owner accepts or rejects them.
        for decision in self._db.desk_decisions.list():
            if decision.status != "proposed":
                continue
            title = decision.title or decision.decision_markdown or decision.id
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Review decision: {title}",
                    source_ref=f"decision:{decision.id}",
                    priority=200,
                )
            )
        for decision in self._db.decisions.list(lifecycle="recorded"):
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Review decision: {decision.text}",
                    source_ref=f"decision:{decision.id}",
                    priority=200,
                )
            )

        # Open, due-soon commitments require attention, but they never outrank
        # an authorization or an unresolved decision review.
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=7)
        with self._db._connection() as conn:
            commitments = conn.execute(
                """SELECT dc.id, dc.decision_id, dc.due_at, d.text
                   FROM decision_commitments AS dc
                   JOIN decisions AS d ON d.id = dc.decision_id
                   WHERE dc.status = 'open' AND dc.due_at IS NOT NULL
                     AND d.deleted = 0
                   ORDER BY dc.due_at ASC, dc.id ASC"""
            ).fetchall()
        for commitment in commitments:
            try:
                due_date = datetime.datetime.fromisoformat(
                    str(commitment["due_at"]).replace("Z", "+00:00")
                ).date()
            except ValueError:
                continue
            if due_date > horizon:
                continue
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="decisions",
                    text=f"Commitment due {due_date.isoformat()}: {commitment['text']}",
                    source_ref=f"decision:{commitment['decision_id']}",
                    priority=120 if due_date <= today else 110,
                )
            )

        return sorted(items, key=lambda item: (-item.priority, item.source_ref or ""))

    @staticmethod
    def _window_timestamp(value: str) -> float:
        """Convert an ISO brief boundary to the event ledger's epoch timestamp."""
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()

    def get_latest(self, principal: Any) -> MondayBrief | None:
        """Return the most recently generated brief, if one exists."""
        del principal
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM monday_briefs ORDER BY generated_at DESC, id DESC LIMIT 1"
            ).fetchone()
            return self._load_brief(conn, row) if row is not None else None

    @staticmethod
    def _load_brief(conn: Any, row: Any) -> MondayBrief:
        sections: dict[str, list[BriefItem]] = {section: [] for section in _SECTIONS}
        for item in conn.execute(
            """SELECT id, section, text, detail, source_ref, priority
               FROM monday_brief_items WHERE brief_id = ?
               ORDER BY priority DESC, id ASC""",
            (row["id"],),
        ):
            section = str(item["section"])
            sections.setdefault(section, []).append(
                BriefItem(
                    id=str(item["id"]),
                    section=section,
                    text=str(item["text"]),
                    detail=item["detail"],
                    source_ref=item["source_ref"],
                    priority=int(item["priority"]),
                )
            )
        return MondayBrief(
            id=str(row["id"]),
            period_start=str(row["period_start"]),
            period_end=str(row["period_end"]),
            headline=str(row["headline"]),
            sections=sections,
            generated_at=str(row["generated_at"]),
            is_empty=not any(sections.values()),
        )
