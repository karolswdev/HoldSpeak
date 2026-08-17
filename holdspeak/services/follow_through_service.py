"""Unified read model for work that must follow a meeting."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any, Protocol

from holdspeak.services.observer import (
    NullObserver,
    PipelineEvent,
    PipelineObserver,
    current_correlation_id,
    observe_service,
)
from holdspeak.services.service_event_ledger import ServiceEventLedger


class _FollowThroughObserver:
    """Keep decrypted People cards out of generic durable observation.

    The board is a mixed read model. Once it can contain an encrypted People
    projection, serializing its result would copy confidential text into the
    plaintext ``pipeline_events`` table. Observation retains timing/outcome but
    replaces the entire board result—not merely matching or truncating text.
    """

    def __init__(self, delegate: PipelineObserver) -> None:
        self._delegate = delegate

    def on_event(self, event: PipelineEvent) -> None:
        if event.service == "FollowThroughService" and event.method == "board":
            event = replace(event, result_summary='{"board":"redacted"}')
        elif event.service == "FollowThroughService" and event.method == "complete":
            try:
                arguments = json.loads(event.args_summary)
            except (TypeError, json.JSONDecodeError):
                arguments = {}
            if str(arguments.get("card_id") or "").startswith("people:"):
                event = replace(
                    event,
                    args_summary='{"people_transition":"redacted"}',
                    result_summary='{"people_transition":"redacted"}',
                    error="people_transition_failed" if event.error else None,
                    error_code="people_transition_failed" if event.error else None,
                )
        self._delegate.on_event(event)


@dataclass(frozen=True)
class CardProvenance:
    """The verified meeting moment from which a follow-through card derives."""

    meeting_id: str | None
    segment_text: str | None
    segment_speaker: str | None
    segment_start: float | None
    moment: dict[str, Any] | None
    available: bool


@dataclass(frozen=True)
class FollowThroughCard:
    id: str
    text: str
    owner: str | None
    due: str | None
    status: str
    meeting_id: str | None
    decision_id: str | None
    stale_score: float | None
    source: str
    lane: str
    provenance: CardProvenance | None
    # A source-owned deep link.  Only People currently needs it: it is an
    # in-memory opaque record reference, never persisted on a Cadence/action row.
    target_ref: str | None = None


@dataclass(frozen=True)
class FollowThroughBoard:
    now: list[FollowThroughCard]
    waiting: list[FollowThroughCard]
    unassigned: list[FollowThroughCard]
    overdue: list[FollowThroughCard]


class PeopleCommitmentProjection(Protocol):
    """Read/mutate the encrypted People authority without retaining a copy here.

    The projection is deliberately a tiny capability rather than a repository.  The
    normal HoldSpeak database, its action items, and Cadence must never receive a
    People commitment.  An implementation decrypts only while producing this
    request's cards and owns the corresponding encrypted lifecycle transition.
    """

    def list_cards(self, principal: Any, *, owner: str | None = None) -> list[FollowThroughCard]: ...

    def transition(self, principal: Any, card_id: str, verb: str) -> dict[str, Any]: ...


_TERMINAL_STATES = {"done", "dismissed", "closed", "killed"}
_LANES = ("now", "waiting", "unassigned", "overdue")


@observe_service
class FollowThroughService:
    """Project action items and their cadence signals into execution lanes."""

    def __init__(
        self,
        db: Any,
        *,
        observer: PipelineObserver | None = None,
        people_projection: PeopleCommitmentProjection | None = None,
    ) -> None:
        self._db = db
        self._observer = _FollowThroughObserver(observer or NullObserver())
        self._people_projection = people_projection

    def board(
        self,
        principal: Any,
        *,
        project_id: str | None = None,
        owner: str | None = None,
        state: str | None = None,
    ) -> FollowThroughBoard:
        """Return the follow-through board, optionally narrowed to one lane."""
        if state is not None and state not in _LANES:
            raise ValueError(f"Unknown follow-through lane: {state}")

        today = date.today()
        lanes: dict[str, list[FollowThroughCard]] = {lane: [] for lane in _LANES}
        with self._db._connection() as conn:
            actions = self._action_rows(conn, project_id=project_id, owner=owner)
            loops = self._loop_rows(conn, project_id=project_id, owner=owner)
            decisions = self._decision_rows(conn, project_id=project_id)

        # A cadence loop whose source is an action enriches the action card;
        # it is not a second card for the same obligation.
        action_loops = {
            str(row["source_id"]): row
            for row in loops
            if row["source_type"] == "meeting_action"
        }
        action_ids = {str(row["id"]) for row in actions}

        for action in actions:
            status = str(action["status"])
            if status.lower() in _TERMINAL_STATES:
                continue
            loop = action_loops.get(str(action["id"]))
            if loop is not None and self._is_snoozed(loop["snoozed_until"], today):
                continue
            card = FollowThroughCard(
                id=str(action["id"]),
                text=str(action["task"]),
                owner=action["owner"],
                due=self._date_text(action["due"]),
                status=status,
                meeting_id=action["meeting_id"],
                decision_id=action["decision_id"],
                stale_score=float(loop["stale_score"]) if loop is not None else None,
                source="action_item",
                lane=self._lane(
                    action["owner"],
                    action["due"],
                    status,
                    today,
                    review_state=action["review_state"],
                ),
                provenance=self._provenance_for(
                    meeting_id=action["meeting_id"],
                    source_timestamp=action["source_timestamp"],
                    decision_id=action["decision_id"],
                ),
            )
            lanes[card.lane].append(card)

        # Non-action loops are independently actionable.  A meeting-decision
        # loop retains decision provenance when its source still exists.
        for loop in loops:
            if loop["source_type"] == "meeting_action" and str(loop["source_id"]) in action_ids:
                continue
            status = str(loop["status"])
            if status.lower() in _TERMINAL_STATES:
                continue
            if self._is_snoozed(loop["snoozed_until"], today):
                continue
            decision = decisions.get(str(loop["source_id"])) if loop["source_type"] == "meeting_decision" else None
            source = "decision" if decision is not None else "cadence_loop"
            card = FollowThroughCard(
                id=str(loop["id"]),
                text=str(loop["title"]),
                owner=loop["owner"],
                due=self._date_text(loop["due_at"]),
                status=status,
                meeting_id=decision["source_meeting_id"] if decision is not None else None,
                decision_id=decision["id"] if decision is not None else None,
                stale_score=float(loop["stale_score"]),
                source=source,
                lane=self._lane(loop["owner"], loop["due_at"], status, today),
                provenance=self._provenance_for(
                    meeting_id=decision["source_meeting_id"] if decision is not None else None,
                    source_timestamp=None,
                    decision_id=decision["id"] if decision is not None else None,
                ),
            )
            lanes[card.lane].append(card)

        # People cards are a synchronous, in-memory overlay.  They intentionally
        # do not enter action_items, cadence_*, the audit export, or any cache.
        # A project filter has no honest People mapping in PR1, so it excludes the
        # overlay rather than implying a relationship/project association.
        if self._people_projection is not None and project_id is None:
            try:
                people_cards = self._people_projection.list_cards(principal, owner=owner)
            except Exception:
                # Never turn a locked encrypted sidecar into a false empty roster
                # or break ordinary Follow-through.  The specific store reason is
                # deliberately not returned because it can become an oracle.
                people_cards = []
            for card in people_cards:
                if card.source != "people_commitment":
                    raise ValueError("invalid people follow-through projection")
                if card.lane not in lanes:
                    raise ValueError("invalid people follow-through lane")
                lanes[card.lane].append(card)

        if state is not None:
            for lane in _LANES:
                if lane != state:
                    lanes[lane] = []
        return FollowThroughBoard(**lanes)

    def commit_decision(
        self,
        principal: Any,
        decision_id: str,
        owner: str | None = None,
        due_at: str | None = None,
    ) -> dict[str, Any]:
        """Create an accountable action from an accepted decision."""
        now = datetime.now().isoformat()
        action_item_id = f"action-{uuid.uuid4().hex}"
        commitment_id = f"commitment-{uuid.uuid4().hex}"

        with self._db._connection() as conn:
            decision = conn.execute(
                """SELECT id, text, source_meeting_id, lifecycle
                   FROM decisions WHERE id = ? AND deleted = 0""",
                (decision_id,),
            ).fetchone()
            if decision is None:
                raise ValueError(f"Decision not found: {decision_id}")
            if decision["lifecycle"] != "accepted":
                raise ValueError("Only accepted decisions can be committed")

            conn.execute(
                """INSERT INTO action_items
                   (id, meeting_id, task, owner, due, status, review_state, created_at)
                   VALUES (?, ?, ?, ?, ?, 'open', 'accepted', ?)""",
                (
                    action_item_id,
                    decision["source_meeting_id"],
                    str(decision["text"]),
                    owner,
                    due_at,
                    now,
                ),
            )
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="decision.committed",
                producer=type(self).__name__,
                subject_ref=f'decision:{decision["id"]}',
                source_revision=commitment_id,
                facts={
                    "entity_title": str(decision["text"]),
                    "commitment_id": commitment_id,
                    "action_item_id": action_item_id,
                    "owner": owner,
                    "due_at": due_at,
                },
                refs=[f'decision:{decision["id"]}', f"action_item:{action_item_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f'decision:{decision["id"]}',
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'open', ?, ?)""",
                (
                    commitment_id,
                    decision["id"],
                    action_item_id,
                    owner,
                    due_at,
                    now,
                    now,
                ),
            )

        return {
            "id": commitment_id,
            "decision_id": str(decision["id"]),
            "action_item_id": action_item_id,
            "owner": owner,
            "due_at": due_at,
            "status": "open",
            "created_at": now,
            "updated_at": now,
        }

    def complete(
        self,
        principal: Any,
        card_id: str,
        verb: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Apply a write-through verb to an action card and its linked records.

        ``card_id`` is an ``action_items.id``.  The action, every cadence loop
        sourced from it, and every associated decision commitment are changed in
        one SQLite transaction so board reads cannot observe a partial result.
        """
        normalized_verb = str(verb).strip().lower()
        if normalized_verb not in {"done", "dismiss", "snooze", "delegate", "reopen"}:
            raise ValueError(f"Unknown follow-through verb: {verb}")
        if str(card_id).startswith("people:"):
            if self._people_projection is None:
                # Do not disclose whether a guessed opaque People id exists.
                raise ValueError("people_commitment_unavailable")
            if normalized_verb in {"snooze", "delegate"}:
                raise ValueError("people_commitment_verb_unsupported")
            return self._people_projection.transition(principal, str(card_id), normalized_verb)

        del principal  # The caller's authority is enforced by the transport.
        data = payload or {}
        now = datetime.now().isoformat()

        with self._db._connection() as conn:
            action = conn.execute(
                "SELECT id FROM action_items WHERE id = ?", (card_id,)
            ).fetchone()
            if action is None:
                raise ValueError(f"Action item not found: {card_id}")

            loop_rows = conn.execute(
                "SELECT id FROM cadence_loops WHERE source_id = ?", (card_id,)
            ).fetchall()
            commitment_rows = conn.execute(
                "SELECT id FROM decision_commitments WHERE action_item_id = ?", (card_id,)
            ).fetchall()
            loop_ids = [str(row["id"]) for row in loop_rows]
            commitment_ids = [str(row["id"]) for row in commitment_rows]

            if normalized_verb in {"done", "dismiss"}:
                action_status = "done" if normalized_verb == "done" else "dismissed"
                conn.execute(
                    "UPDATE action_items SET status = ?, completed_at = ? WHERE id = ?",
                    (action_status, now, card_id),
                )
                conn.execute(
                    "UPDATE cadence_loops SET status = 'closed', updated_at = ? WHERE source_id = ?",
                    (now, card_id),
                )
                conn.execute(
                    "UPDATE decision_commitments SET status = 'closed', updated_at = ? WHERE action_item_id = ?",
                    (now, card_id),
                )
            elif normalized_verb == "snooze":
                until = data.get("until")
                if not isinstance(until, str) or not until.strip():
                    raise ValueError("snooze requires payload['until']")
                conn.execute(
                    """UPDATE cadence_loops
                       SET status = 'snoozed', snoozed_until = ?, updated_at = ?
                       WHERE source_id = ?""",
                    (until.strip(), now, card_id),
                )
            elif normalized_verb == "delegate":
                owner = data.get("to")
                if not isinstance(owner, str) or not owner.strip():
                    raise ValueError("delegate requires payload['to']")
                owner = owner.strip()
                conn.execute("UPDATE action_items SET owner = ? WHERE id = ?", (owner, card_id))
                conn.execute(
                    "UPDATE decision_commitments SET owner = ?, updated_at = ? WHERE action_item_id = ?",
                    (owner, now, card_id),
                )
            else:  # reopen
                conn.execute(
                    "UPDATE action_items SET status = 'open', completed_at = NULL WHERE id = ?",
                    (card_id,),
                )
                conn.execute(
                    """UPDATE cadence_loops
                       SET status = 'open', snoozed_until = NULL, updated_at = ?
                       WHERE source_id = ?""",
                    (now, card_id),
                )
                conn.execute(
                    "UPDATE decision_commitments SET status = 'open', updated_at = ? WHERE action_item_id = ?",
                    (now, card_id),
                )

        return {
            "card_id": card_id,
            "verb": normalized_verb,
            "loop_ids": loop_ids,
            "commitment_ids": commitment_ids,
        }

    def _provenance_for(
        self,
        *,
        meeting_id: Any,
        source_timestamp: Any,
        decision_id: Any,
    ) -> CardProvenance:
        """Return only a repository-verified source moment for a board card.

        A missing, stale, or malformed source is deliberately represented as
        unavailable rather than inferred from neighbouring meeting data.
        """
        unavailable = CardProvenance(
            meeting_id=str(meeting_id) if meeting_id else None,
            segment_text=None,
            segment_speaker=None,
            segment_start=None,
            moment=None,
            available=False,
        )
        try:
            if decision_id:
                moment = self._db.decisions.resolve_decision_moment(str(decision_id))
                if moment is None:
                    return unavailable
                return CardProvenance(
                    meeting_id=moment.meeting_id,
                    segment_text=moment.text,
                    segment_speaker=moment.speaker,
                    segment_start=moment.segment_start,
                    moment=moment.to_dict(),
                    available=True,
                )
            if not meeting_id or source_timestamp is None:
                return unavailable
            moment = self._db.decisions.resolve_segment(meeting_id, source_timestamp)
            if moment is None:
                return unavailable
            return CardProvenance(
                meeting_id=moment.meeting_id,
                segment_text=moment.text,
                segment_speaker=moment.speaker,
                segment_start=moment.segment_start,
                moment=None,
                available=True,
            )
        except Exception:
            return unavailable

    @staticmethod
    def _action_rows(conn: Any, *, project_id: str | None, owner: str | None) -> list[Any]:
        query = "SELECT a.*, dc.decision_id FROM action_items a LEFT JOIN decision_commitments dc ON dc.action_item_id = a.id"
        clauses: list[str] = []
        params: list[str] = []
        if project_id:
            query += " JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id"
            clauses.append("mp.project_id = ?")
            params.append(project_id)
        if owner:
            clauses.append("a.owner = ?")
            params.append(owner)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        return list(conn.execute(query + " ORDER BY a.created_at DESC", params))

    @staticmethod
    def _loop_rows(conn: Any, *, project_id: str | None, owner: str | None) -> list[Any]:
        query = "SELECT * FROM cadence_loops"
        clauses: list[str] = []
        params: list[str] = []
        if project_id:
            # Project association for meeting actions is determined by the
            # canonical meeting_projects relation, not cadence's display label.
            clauses.append(
                "(source_type = 'meeting_action' AND source_id IN "
                "(SELECT a.id FROM action_items a JOIN meeting_projects mp "
                "ON mp.meeting_id = a.meeting_id WHERE mp.project_id = ?))"
            )
            params.append(project_id)
        if owner:
            clauses.append("owner = ?")
            params.append(owner)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        return list(conn.execute(query, params))

    @staticmethod
    def _decision_rows(conn: Any, *, project_id: str | None) -> dict[str, Any]:
        query = "SELECT id, source_meeting_id FROM decisions WHERE deleted = 0"
        params: list[str] = []
        if project_id:
            query += " AND (project_key = ? OR source_meeting_id IN " \
                "(SELECT meeting_id FROM meeting_projects WHERE project_id = ?))"
            params.extend((project_id, project_id))
        return {str(row["id"]): row for row in conn.execute(query, params)}

    @staticmethod
    def _date_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text[:10] if text else None

    @classmethod
    def _is_snoozed(cls, snoozed_until: Any, today: date) -> bool:
        snooze_text = cls._date_text(snoozed_until)
        if snooze_text is None:
            return False
        try:
            return date.fromisoformat(snooze_text) > today
        except ValueError:
            return False

    @classmethod
    def _lane(
        cls,
        owner: Any,
        due: Any,
        status: str,
        today: date,
        *,
        review_state: Any = None,
    ) -> str:
        if str(review_state or "").lower() == "pending":
            return "unassigned"
        if not owner or not str(owner).strip():
            return "unassigned"
        due_text = cls._date_text(due)
        if due_text is None:
            return "waiting"
        try:
            due_date = date.fromisoformat(due_text)
        except ValueError:
            return "waiting"
        # HS-132-14 walk finding: pipeline-persisted action items carry
        # "pending" (db/meetings.py constrains to pending/done/dismissed);
        # only commit_decision writes "open". Both vocabularies mean live
        # work — gating overdue on "open" alone silently under-reported the
        # lane, the drill, and the dock badge for every meeting-born item.
        if due_date < today and status.lower() in ("open", "pending"):
            return "overdue"
        if due_date <= today + timedelta(days=2):
            return "now"
        return "waiting"
