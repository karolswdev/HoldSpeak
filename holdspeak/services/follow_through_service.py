"""Unified read model for work that must follow a meeting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service


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


@dataclass(frozen=True)
class FollowThroughBoard:
    now: list[FollowThroughCard]
    waiting: list[FollowThroughCard]
    unassigned: list[FollowThroughCard]
    overdue: list[FollowThroughCard]


_TERMINAL_STATES = {"done", "dismissed", "closed", "killed"}
_LANES = ("now", "waiting", "unassigned", "overdue")


@observe_service
class FollowThroughService:
    """Project action items and their cadence signals into execution lanes."""

    def __init__(self, db: Any, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

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
            card = FollowThroughCard(
                id=str(action["id"]),
                text=str(action["task"]),
                owner=action["owner"],
                due=self._date_text(action["due"]),
                status=status,
                meeting_id=action["meeting_id"],
                decision_id=None,
                stale_score=float(loop["stale_score"]) if loop is not None else None,
                source="action_item",
                lane=self._lane(action["owner"], action["due"], status, today),
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
            )
            lanes[card.lane].append(card)

        if state is not None:
            for lane in _LANES:
                if lane != state:
                    lanes[lane] = []
        return FollowThroughBoard(**lanes)

    @staticmethod
    def _action_rows(conn: Any, *, project_id: str | None, owner: str | None) -> list[Any]:
        query = "SELECT a.* FROM action_items a"
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
    def _lane(cls, owner: Any, due: Any, status: str, today: date) -> str:
        if not owner or not str(owner).strip():
            return "unassigned"
        due_text = cls._date_text(due)
        if due_text is None:
            return "waiting"
        try:
            due_date = date.fromisoformat(due_text)
        except ValueError:
            return "waiting"
        if due_date < today and status.lower() == "open":
            return "overdue"
        if due_date <= today + timedelta(days=2):
            return "now"
        return "waiting"
