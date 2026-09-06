"""Windowed, persistent generation model for the Monday Brief."""

from __future__ import annotations

import datetime
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service


_SECTIONS = ("this_week", "changed", "broke", "waiting", "decisions")
_PATH_FRAGMENT = re.compile(r'[/\\](?:\w+[/\\]){1,}[\w.]+')


def _sanitize_detail(args_summary: str) -> str | None:
    """Truncate raw args_summary to a summary-level detail.

    HS-150-03 D2: raw filesystem paths from observer arguments must never
    enter monday_brief_items.  The detail becomes the event/method name from
    the JSON keys, stripping path-valued fragments.
    """
    if args_summary == "{}":
        return None
    # Strip any string that looks like a filesystem path.
    cleaned = _PATH_FRAGMENT.sub("<path>", args_summary)
    # If everything was a path, collapse to None.
    if cleaned.strip() in ("{}", "", '{"": "<path>"}'):
        return None
    return cleaned


_CHANGE_METHOD_MARKERS = (
    "create",
    "update",
    "delete",
    "transition",
    "run",
    "commit",
    "complete",
)

# HS-171-06: services whose pipeline_events carry human-meaningful state
# changes (things with a title a person wrote or a state a person must
# act on).  Everything else is a kernel-level operation that goes into
# the ledger summary, not the item list.
_HUMAN_SERVICES: frozenset[str] = frozenset({
    "AskService",
    "CadenceService",
    "CoderService",
    "DecisionLifecycleService",
    "DecisionRecordService",
    "DeskService",
    "DictationService",
    "FollowThroughService",
    "MeetingService",
    "MeetingIntelService",
    "MeetingAftercareService",
    "MemoryService",
    "MondayBriefService",
    "NoteService",
    "PeopleService",
    "ProjectService",
    "ProjectDeltaService",
    "ProjectSetupService",
    "ProjectUpdateService",
    "ProjectStewardService",
    "ReactionService",
    "RefinementThoughtService",
    "ScheduledRecordingService",
    "SequenceWorkflowService",
    "SettingsService",
    "ThreadService",
    "ThoughtService",
    "WatchService",
    "WorkbenchService",
})
_CLOSE_HOUR = 17
_RETRY_WINDOW_SECONDS = 5 * 60
# HS-132-08: a recorded meeting is the most material thing a week contains, so
# it leads Changed ahead of the observer's method-level receipts (priority 0).
_MEETING_PRIORITY = 50
SHELF_STATES = ("acknowledged", "deferred")


@dataclass
class BriefItem:
    id: str
    section: str  # this_week, changed, broke, waiting, decisions
    text: str
    detail: str | None = None
    source_ref: str | None = None
    priority: int = 0


@dataclass
class LedgerSummary:
    """HS-171-06: kernel operation count kept separate from human items."""
    operations: int = 0
    since: str | None = None


@dataclass
class MondayBrief:
    id: str
    period_start: str
    period_end: str
    headline: str
    sections: dict[str, list[BriefItem]]
    generated_at: str
    is_empty: bool = False
    # item_id -> "acknowledged" | "deferred". An absent key is untouched work.
    shelf: dict[str, str] = field(default_factory=dict)
    # HS-171-06: kernel operation ledger (not counted as items).
    ledger: LedgerSummary = field(default_factory=LedgerSummary)


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
        """Compute the local brief window, from the preceding close to *now*.

        The "what happened" lookback is UNCHANGED from Phase 132:
        Monday looks back to Friday 17:00, other weekdays to the
        preceding business day 17:00, weekends to Friday 17:00.

        HS-175-05: the forward-looking "THIS WEEK" section uses
        ``compute_lookahead`` separately; this function is not widened.
        """
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

    def compute_lookahead(
        self, now: datetime.datetime | None = None
    ) -> tuple[datetime.datetime, datetime.datetime]:
        """Compute the look-ahead window: *now* to Sunday 23:59.

        HS-175-05: used by the calendar-events and meeting-watch
        collectors for the "what is coming" half of the brief.
        """
        period_start = now or datetime.datetime.now().astimezone()
        days_since_monday = period_start.weekday()
        days_to_sunday = 6 - days_since_monday
        sunday = (period_start + datetime.timedelta(days=days_to_sunday)).date()
        period_end = datetime.datetime.combine(
            sunday,
            datetime.time(23, 59, 59),
            tzinfo=period_start.tzinfo,
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

            human_changes, ledger = self._collect_changes(
                period_start.isoformat(), period_end.isoformat()
            )

            # HS-175-05 / counsel C11: the THIS WEEK half is the ruled
            # forward window [now, Sunday 23:59] (Addendum 1, condition 2)
            # -- never from Monday 00:00, so it cannot overlap the SINCE
            # FRIDAY lookback.  ``compute_window`` is untouched.
            #
            # calendar_events.starts_at is stored as UTC ('...Z', see
            # calendar_ingest.py:407), so the boundaries are normalised to UTC
            # ISO before the string compare; a naive ``now`` (what the
            # cadence and the route pass) is read as local time, the same
            # convention compute_window keeps.  Dates (commitments' due_at)
            # are compared as the owner's local dates.
            ahead_start, ahead_end = self.compute_lookahead(period_end)
            ahead_start_iso = self._utc_iso(ahead_start)
            ahead_end_iso = self._utc_iso(ahead_end)
            local_start = ahead_start if ahead_start.tzinfo else ahead_start.astimezone()
            local_end = ahead_end if ahead_end.tzinfo else ahead_end.astimezone()
            clock_tz = local_start.tzinfo

            # Last brief generated_at for "since last brief" filtering
            last_brief_row = conn.execute(
                "SELECT MAX(generated_at) AS latest FROM monday_briefs"
            ).fetchone()
            last_brief_at = str(last_brief_row["latest"]) if (
                last_brief_row and last_brief_row["latest"]
            ) else None

            # C11: dedup against the lookback's "Meeting recorded" rows --
            # an occurrence already recorded is SINCE FRIDAY's, not THIS
            # WEEK's.
            recorded_event_ids = self._recorded_calendar_event_ids(
                period_start.isoformat(), period_end.isoformat()
            )

            # HS-175-05: new collectors (THIS WEEK section, forward-looking)
            calendar_items = self._collect_calendar_events(
                ahead_start_iso, ahead_end_iso, ahead_start_iso,
                exclude_event_ids=recorded_event_ids,
                clock_tz=clock_tz,
            )
            meeting_watch_items = self._collect_meeting_watch(
                ahead_start_iso, ahead_end_iso, last_brief_at,
                decisions_since=period_start.isoformat(),
                due_from=local_start.date().isoformat(),
                due_until=local_end.date().isoformat() + "T23:59:59",
            )

            sections = {
                "this_week": calendar_items + meeting_watch_items,
                "changed": human_changes
                + self._collect_meetings(
                    period_start.isoformat(), period_end.isoformat()
                ),
                "broke": self._collect_breakage(
                    period_start.isoformat(), period_end.isoformat()
                ),
                "waiting": waiting_items,
                # C11 follow-up: a commitment is said once -- the ids THIS
                # WEEK counts are dropped from the lookback's due items.
                "decisions": self._collect_decisions(
                    principal,
                    {
                        str(r["id"]) for r in self._commitments_due_rows(
                            conn,
                            local_start.date().isoformat(),
                            local_end.date().isoformat() + "T23:59:59",
                        )
                    },
                ),
            }
            headline, sections = self._compose(sections)
            brief_id = f"brief-{uuid.uuid4().hex}"
            generated_at = period_end.isoformat()
            conn.execute(
                """INSERT INTO monday_briefs
                   (id, period_start, period_end, headline, generated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    brief_id,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    headline,
                    generated_at,
                ),
            )
            items = [item for section in _SECTIONS for item in sections[section]]
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
            brief = self._load_brief(conn, row)
            brief.ledger = ledger
            return brief

    def _compose(
        self, sections: dict[str, list[BriefItem]]
    ) -> tuple[str, dict[str, list[BriefItem]]]:
        """Compose an honest, deterministic headline and ordered fixed sections."""
        finalized_sections = {
            section: sorted(
                sections.get(section, []),
                key=lambda item: (-item.priority, item.source_ref or "", item.id),
            )
            for section in _SECTIONS
        }
        counts = {section: len(items) for section, items in finalized_sections.items()}
        total_items = sum(counts.values())
        if total_items == 0:
            return "Nothing material changed.", finalized_sections

        def phrase(count: int, singular: str, plural: str) -> str:
            return f"{count} {singular if count == 1 else plural}"

        headline_parts = []
        if counts["this_week"]:
            # C11: calendar items are counted as what they are -- meetings,
            # armed recordings, commitments due, new decisions -- never as
            # "watch items".  The `Next:` row is detail, not a count.
            tw_items = finalized_sections["this_week"]
            meetings = self._leading_count(tw_items, "calendar:week")
            armed = self._leading_count(tw_items, "calendar:armed")
            due = self._leading_count(tw_items, "meeting_watch:commitments_due")
            decisions = self._leading_count(tw_items, "meeting_watch:decisions")
            known_refs = {
                "calendar:week", "calendar:armed",
                "meeting_watch:commitments_due", "meeting_watch:decisions",
            }
            # A `Next:` row is detail under its count; alone (never in the
            # product -- the collector emits the count first) it is an item.
            other_tw = sum(
                1 for item in tw_items
                if item.source_ref not in known_refs
                and (meetings == 0 or not str(item.source_ref or "").startswith("calendar_event:"))
            )
            if meetings:
                headline_parts.append(phrase(meetings, "meeting this week", "meetings this week"))
            if armed:
                headline_parts.append(phrase(armed, "armed", "armed"))
            if due:
                headline_parts.append(phrase(due, "commitment due", "commitments due"))
            if decisions:
                headline_parts.append(phrase(decisions, "new decision", "new decisions"))
            if other_tw:
                headline_parts.append(phrase(other_tw, "item this week", "items this week"))
        if counts["changed"]:
            headline_parts.append(phrase(counts["changed"], "thing changed", "things changed"))
        if counts["broke"]:
            headline_parts.append(phrase(counts["broke"], "thing broke", "things broke"))
        if counts["waiting"]:
            headline_parts.append(phrase(counts["waiting"], "thing waiting", "things waiting"))
        if counts["decisions"]:
            headline_parts.append(
                phrase(counts["decisions"], "decision waiting", "decisions waiting")
            )
        return ", ".join(headline_parts) + ".", finalized_sections

    def _collect_changes(
        self, window_start: str, window_end: str
    ) -> tuple[list[BriefItem], LedgerSummary]:
        """Reduce pipeline events in the window to material state changes.

        HS-171-06: returns ``(human_items, ledger)`` where *human_items*
        are things with a title a person wrote or a state a person must
        act on (_HUMAN_SERVICES), and *ledger* counts every other
        operation (kernel ops, primitives, recipes, gates, etc.) without
        surfacing them as items.
        """
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
        ledger_count = 0
        ledger_since: str | None = None
        for events in groups.values():
            first = events[0]
            service_name = str(first["service"])

            # HS-171-06: only human-meaningful services become items.
            if service_name not in _HUMAN_SERVICES:
                ledger_count += 1
                ts_str = str(first["timestamp"])
                if ledger_since is None or ts_str < ledger_since:
                    ledger_since = ts_str
                continue

            detail = _sanitize_detail(str(first["args_summary"]))
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="changed",
                    text=f"{service_name}.{first['method']}",
                    detail=detail,
                    source_ref=(
                        f"pipeline:{first['correlation_id']}"
                        if first["correlation_id"]
                        else f"pipeline-event:{first['event_id']}"
                    ),
                )
            )

        ledger = LedgerSummary(operations=ledger_count, since=ledger_since)
        return items, ledger

    def _collect_meetings(self, window_start: str, window_end: str) -> list[BriefItem]:
        """Gather meetings recorded inside the window.

        HS-132-08: the observer's method markers (create/update/delete/…) never
        match the meeting lifecycle, so a week full of recorded meetings used to
        read "Nothing material changed." Meetings are collected from their own
        durable rows rather than from pipeline receipts, which is the honest
        source: a meeting exists whether or not an observed method ran.
        """
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT m.id, m.title, m.started_at, m.ended_at, m.duration_seconds,
                          (SELECT COUNT(*) FROM action_items a
                            WHERE a.meeting_id = m.id) AS action_count
                   FROM meetings AS m
                   WHERE COALESCE(m.ended_at, m.started_at) BETWEEN ? AND ?
                     AND m.capture_status NOT IN ('recording', 'provisional')
                   ORDER BY COALESCE(m.ended_at, m.started_at) ASC, m.id ASC""",
                (window_start, window_end),
            ).fetchall()

        items: list[BriefItem] = []
        for row in rows:
            title = str(row["title"] or "").strip() or "Untitled meeting"
            parts: list[str] = []
            duration = row["duration_seconds"]
            if duration:
                parts.append(f"{max(1, round(float(duration) / 60))} min")
            actions = int(row["action_count"] or 0)
            if actions:
                parts.append(f"{actions} action item{'' if actions == 1 else 's'}")
            items.append(
                BriefItem(
                    id=f"brief-item-{uuid.uuid4().hex}",
                    section="changed",
                    text=f"Meeting recorded: {title}",
                    detail=" · ".join(parts) or None,
                    source_ref=f"meeting:{row['id']}",
                    priority=_MEETING_PRIORITY,
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

    def _collect_decisions(
        self, principal: Any, exclude_commitment_ids: set[str] | None = None,
    ) -> list[BriefItem]:
        """Gather decisions requiring owner attention.

        C11 follow-up: a commitment is said once.  ``exclude_commitment_ids``
        are the commitment ids THIS WEEK already counts (``N commitments
        due this week``); their lookback ``Commitment due`` items are
        dropped -- dedup by commitment id, never by text.
        """
        del principal
        items: list[BriefItem] = []
        excluded_commitments = exclude_commitment_ids or set()

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
            if str(commitment["id"]) in excluded_commitments:
                continue  # already said under THIS WEEK
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

    # ── HS-175-05: calendar events + meeting watch collectors ─────────

    def _collect_calendar_events(
        self, week_start: str, week_end: str, now_iso: str,
        *,
        exclude_event_ids: set[str] | None = None,
        clock_tz: datetime.tzinfo | None = None,
    ) -> list[BriefItem]:
        """Calendar events in the week range.

        HS-175-05: produces items for the ``this_week`` section
        (forward-looking calendar and armed-recording data):
        - ``N meetings`` (count of events in the week).
        - ``Next: [title] at [time]`` (next event after now).
        - ``N armed`` (events with linked armed recordings).

        C11: ``exclude_event_ids`` is the calendar_uid dedup against the
        lookback's "Meeting recorded" rows, keyed by the occurrence (the
        projection id hashes uid + starts_at) so a recurring series' next
        occurrence is never hidden by its last recording.  ``clock_tz``
        renders the ``Next:`` clock in the brief's own zone rather than
        the stored UTC.

        Returns an empty list when no calendar events exist (no
        calendar configured or no events in range).
        """
        items: list[BriefItem] = []
        excluded = exclude_event_ids or set()
        with self._db._connection() as conn:
            # Check that calendar_events table exists (belt -- fresh DBs)
            table_check = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='calendar_events'"
            ).fetchone()
            if table_check is None:
                return items

            event_rows = [
                row for row in conn.execute(
                    """SELECT id, uid, title, starts_at, meeting_url
                       FROM calendar_events
                       WHERE starts_at >= ? AND starts_at < ?
                       ORDER BY starts_at ASC, id ASC""",
                    (week_start, week_end),
                ).fetchall()
                if str(row["id"]) not in excluded
            ]
            if not event_rows:
                return items

            total = len(event_rows)
            items.append(
                BriefItem(
                    id=f"brief-cal-total-{uuid.uuid4().hex}",
                    section="this_week",
                    text=f"{total} meeting{'s' if total != 1 else ''} this week",
                    source_ref="calendar:week",
                    priority=_MEETING_PRIORITY + 10,
                )
            )

            # Next event after now
            for row in event_rows:
                if str(row["starts_at"]) > now_iso:
                    try:
                        next_dt = datetime.datetime.fromisoformat(
                            str(row["starts_at"]).replace("Z", "+00:00")
                        )
                        if clock_tz is not None and next_dt.tzinfo is not None:
                            next_dt = next_dt.astimezone(clock_tz)
                        time_str = next_dt.strftime("%H:%M")
                    except (ValueError, TypeError):
                        time_str = ""
                    title = str(row["title"] or "").strip() or "Untitled"
                    items.append(
                        BriefItem(
                            id=f"brief-cal-next-{uuid.uuid4().hex}",
                            section="this_week",
                            text=f"Next: {title} at {time_str}",
                            source_ref=f"calendar_event:{row['id']}",
                            priority=_MEETING_PRIORITY + 5,
                        )
                    )
                    break

            # Armed recordings count
            sched_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='scheduled_recordings'"
            ).fetchone()
            if sched_table is not None:
                event_ids = [str(r["id"]) for r in event_rows]
                placeholders = ",".join("?" * len(event_ids))
                armed_row = conn.execute(
                    f"""SELECT COUNT(*) AS cnt FROM scheduled_recordings
                        WHERE calendar_event_id IN ({placeholders})
                          AND enabled = 1""",
                    event_ids,
                ).fetchone()
                armed = int(armed_row["cnt"]) if armed_row else 0
                if armed:
                    items.append(
                        BriefItem(
                            id=f"brief-cal-armed-{uuid.uuid4().hex}",
                            section="this_week",
                            text=f"{armed} armed",
                            source_ref="calendar:armed",
                            priority=_MEETING_PRIORITY + 3,
                        )
                    )

        return items

    def _collect_meeting_watch(
        self, week_start: str, week_end: str, last_brief_at: str | None,
        *,
        decisions_since: str | None = None,
        due_from: str | None = None,
        due_until: str | None = None,
    ) -> list[BriefItem]:
        """Meeting watch items: new decisions and commitments.

        HS-175-05: reads decisions and commitments from meetings linked
        to any Room, filtered to the week window.

        - Meetings with new decisions since the last brief.
        - Meetings with new commitments.
        - Commitments due this week.

        C11: ``week_start`` is the forward window's start (``now``).  New
        decisions are a "since the last brief" fact, so their fallback
        floor is ``decisions_since`` (the lookback's start), not ``now``.
        Commitments carry due DATES, so they are bounded by the owner's
        local dates ``due_from`` (today) and ``due_until`` (Sunday), not by
        UTC instants.  The calendar_uid dedup lives in the calendar
        collector (``exclude_event_ids``); these items are counts over
        meeting data and name no event.
        """
        items: list[BriefItem] = []
        since = last_brief_at or decisions_since or week_start
        due_lo = due_from or week_start[:10]
        due_hi = due_until or week_end

        with self._db._connection() as conn:
            # Check tables exist
            for table in ("decision_records", "decision_record_sources",
                          "decision_commitments"):
                if conn.execute(
                    f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table}'"
                ).fetchone() is None:
                    return items

            # New decisions since last brief
            decision_rows = conn.execute(
                """SELECT r.id, r.decision_text, r.created_at,
                          s.source_ref AS meeting_id
                   FROM decision_records r
                   JOIN decision_record_sources s ON s.record_id = r.id
                   WHERE s.source_type = 'meeting'
                     AND r.created_at >= ? AND r.created_at < ?
                     AND r.deleted = 0
                   ORDER BY r.created_at DESC""",
                (since, week_end),
            ).fetchall()

            if decision_rows:
                count = len(decision_rows)
                items.append(
                    BriefItem(
                        id=f"brief-mtgwatch-decisions-{uuid.uuid4().hex}",
                        section="this_week",
                        text=f"{count} new decision{'s' if count != 1 else ''} from meetings",
                        source_ref="meeting_watch:decisions",
                        priority=_MEETING_PRIORITY + 2,
                    )
                )

            # Commitments due this week
            commitment_rows = self._commitments_due_rows(conn, due_lo, due_hi)

            if commitment_rows:
                count = len(commitment_rows)
                first = commitment_rows[0]
                first_due = str(first["due_at"] or "")[:10]
                first_text = None
                try:
                    d_row = conn.execute(
                        """SELECT d.text FROM decisions d
                           JOIN decision_commitments dc ON dc.decision_id = d.id
                           WHERE dc.id = ?""",
                        (str(first["id"]),),
                    ).fetchone()
                    if d_row and d_row["text"]:
                        first_text = str(d_row["text"]).strip()
                except Exception:
                    pass
                detail_parts = []
                if first_text:
                    detail_parts.append(first_text)
                if first_due:
                    detail_parts.append(first_due)
                detail = " | ".join(detail_parts) if detail_parts else None
                items.append(
                    BriefItem(
                        id=f"brief-mtgwatch-commitments-{uuid.uuid4().hex}",
                        section="this_week",
                        text=f"{count} commitment{'s' if count != 1 else ''} due this week",
                        detail=detail,
                        source_ref="meeting_watch:commitments_due",
                        priority=_MEETING_PRIORITY + 1,
                    )
                )

        return items

    @staticmethod
    def _window_timestamp(value: str) -> float:
        """Convert an ISO brief boundary to the event ledger's epoch timestamp."""
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()

    @staticmethod
    def _utc_iso(value: datetime.datetime) -> str:
        """C11: one boundary shape for the UTC-stored calendar projection.

        A naive value is read as local time (the convention the cadence
        and the route pass ``now`` in); an aware one keeps its zone.  Both
        land as ``YYYY-MM-DDTHH:MM:SS+00:00``, the exact shape
        ``calendar_ingest`` stores ``starts_at`` in, so the string compare
        in the collectors is a real instant compare.
        """
        aware = value if value.tzinfo is not None else value.astimezone()
        return aware.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _recorded_calendar_event_ids(
        self, window_start: str, window_end: str,
    ) -> set[str]:
        """C11: the calendar occurrences already recorded inside the lookback.

        Mirrors ``_collect_meetings``' predicate so an event that is a
        "Meeting recorded" row in SINCE FRIDAY is never also counted or
        named in THIS WEEK.
        """
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT DISTINCT m.calendar_event_id AS event_id
                   FROM meetings AS m
                   WHERE m.calendar_event_id IS NOT NULL
                     AND m.calendar_event_id != ''
                     AND COALESCE(m.ended_at, m.started_at) BETWEEN ? AND ?
                     AND m.capture_status NOT IN ('recording', 'provisional')""",
                (window_start, window_end),
            ).fetchall()
        return {str(r["event_id"]) for r in rows}

    @staticmethod
    def _commitments_due_rows(conn: Any, due_lo: str, due_hi: str) -> list[Any]:
        """Open commitments due in ``[due_lo, due_hi)`` -- the one query THIS
        WEEK counts and the lookback dedups against (by commitment id)."""
        try:
            return conn.execute(
                """SELECT dc.id, dc.due_at, dc.status, dc.owner
                   FROM decision_commitments dc
                   WHERE dc.status = 'open'
                     AND dc.due_at >= ? AND dc.due_at < ?
                   ORDER BY dc.due_at ASC""",
                (due_lo, due_hi),
            ).fetchall()
        except Exception:
            return []

    @staticmethod
    def _leading_count(items: list[BriefItem], source_ref: str) -> int:
        """The leading integer of the one count item carrying *source_ref*."""
        for item in items:
            if item.source_ref == source_ref:
                match = re.match(r"\s*(\d+)\b", item.text)
                if match:
                    return int(match.group(1))
        return 0

    def get_latest(self, principal: Any) -> MondayBrief | None:
        """Return the most recently generated brief, if one exists."""
        del principal
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM monday_briefs ORDER BY generated_at DESC, id DESC LIMIT 1"
            ).fetchone()
            return self._load_brief(conn, row) if row is not None else None

    # ── brief-item triage shelf (HS-132-08) ──────────────────────────────

    def shelve(self, principal: Any, item_id: str, state: str | None) -> dict[str, Any]:
        """Record (or clear) one owner triage verb against one brief item.

        *state* is ``acknowledged``, ``deferred``, or None to return the item to
        untouched. An unknown item or state is refused by name.
        """
        del principal
        if state is not None and state not in SHELF_STATES:
            raise ValueError(f"Unknown shelf state: {state}")
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT brief_id FROM monday_brief_items WHERE id = ?", (item_id,)
            ).fetchone()
            if row is None:
                raise LookupError(f"Unknown brief item: {item_id}")
            if state is None:
                conn.execute(
                    "DELETE FROM monday_brief_item_shelf WHERE item_id = ?", (item_id,)
                )
            else:
                conn.execute(
                    """INSERT INTO monday_brief_item_shelf
                       (item_id, brief_id, state, updated_at)
                       VALUES (?, ?, ?, datetime('now'))
                       ON CONFLICT(item_id) DO UPDATE SET
                           state = excluded.state,
                           updated_at = excluded.updated_at""",
                    (item_id, str(row["brief_id"]), state),
                )
        return {"item_id": item_id, "state": state}

    def shelf(self, principal: Any, brief_id: str | None = None) -> dict[str, str]:
        """Read the triage shelf for one brief, defaulting to the latest one."""
        del principal
        with self._db._connection() as conn:
            if brief_id is None:
                latest = conn.execute(
                    "SELECT id FROM monday_briefs ORDER BY generated_at DESC, id DESC LIMIT 1"
                ).fetchone()
                if latest is None:
                    return {}
                brief_id = str(latest["id"])
            return self._load_shelf(conn, brief_id)

    @staticmethod
    def _load_shelf(conn: Any, brief_id: str) -> dict[str, str]:
        rows = conn.execute(
            "SELECT item_id, state FROM monday_brief_item_shelf WHERE brief_id = ?",
            (brief_id,),
        ).fetchall()
        return {str(row["item_id"]): str(row["state"]) for row in rows}

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
            shelf=MondayBriefService._load_shelf(conn, str(row["id"])),
        )
