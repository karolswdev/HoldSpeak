"""Durable Work attempt records (HS-94-04).

PLATFORM-CONTRACT §4.2: one attempt is one bounded undertaking of one
primary Story, bound to node + source + worktree + agent session +
terminal target. Association provenance is explicit (`launch`,
`rider_claim`, `manual`, `contract`, `heuristic`) and a heuristic row
is never exact. States move through an honest machine
(`starting` / `working` / `waiting` / `idle` / `ended` / `abandoned` /
`unknown`); every applied transition appends a replayable event row,
so history survives worktree removal, session end, and hub restarts.

Identity rules the shapes enforce:

- `attempt_id` is opaque and never reused — an agent moving to the
  next Story gets a NEW attempt (the old one ends first);
- at most ONE non-terminal exact attempt may pin a session
  (`idx_work_attempts_exact_session`, a partial unique index) — the
  repo-wide heuristic can put one session on several Story cards,
  but only as labeled, non-exact rows;
- wire projections (`to_wire`) carry labels and opaque IDs only:
  no filesystem path ever enters this table.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from .base import BaseRepository

ATTEMPTS_SCHEMA = 1

ASSOCIATION_KINDS = ("launch", "rider_claim", "manual", "contract", "heuristic")

ATTEMPT_STATES = (
    "starting",
    "working",
    "waiting",
    "idle",
    "ended",
    "abandoned",
    "unknown",
)

TERMINAL_STATES = frozenset({"ended", "abandoned"})

#: The honest transition table. `ended` / `abandoned` are sticky
#: tombstones; `unknown` (node offline) may recover into any live
#: state once the node reports again.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "starting": frozenset({"working", "waiting", "idle", "ended", "abandoned", "unknown"}),
    "working": frozenset({"waiting", "idle", "ended", "abandoned", "unknown"}),
    "waiting": frozenset({"working", "idle", "ended", "abandoned", "unknown"}),
    "idle": frozenset({"working", "waiting", "ended", "abandoned", "unknown"}),
    "unknown": frozenset({"working", "waiting", "idle", "ended", "abandoned"}),
    "ended": frozenset(),
    "abandoned": frozenset(),
}


class AttemptError(ValueError):
    """A typed refusal with a client-safe message (no paths, §12.3)."""


class AttemptConflict(AttemptError):
    """The session is already exactly pinned to a live attempt."""


class AttemptTransitionError(AttemptError):
    """The requested state change is not an honest transition."""


def _format_ts(value: Optional[datetime] = None) -> str:
    moment = value or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def new_attempt_id() -> str:
    return "att_" + uuid.uuid4().hex[:16]


@dataclass(frozen=True)
class WorkAttempt:
    attempt_id: str
    source_id: str
    project: str
    story_id: str
    worktree_id: str
    node_id: Optional[str]
    session_id: Optional[str]
    target_id: Optional[str]
    kind: str
    claimed_by: Optional[str]
    claimed_at: Optional[str]
    exact: bool
    state: str
    started_at: str
    updated_at: str
    ended_at: Optional[str]

    @property
    def terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def to_wire(self) -> dict[str, Any]:
        """The §4.2 wire record: opaque IDs, explicit provenance,
        no filesystem truth."""
        return {
            "attempt_id": self.attempt_id,
            "story_ref": {
                "source_id": self.source_id,
                "project": self.project,
                "story_id": self.story_id,
            },
            "node_id": self.node_id,
            "worktree_id": self.worktree_id,
            "session_id": self.session_id,
            "target_id": self.target_id,
            "association": {
                "kind": self.kind,
                "claimed_by": self.claimed_by,
                "claimed_at": self.claimed_at,
            },
            "exact": self.exact,
            "state": self.state,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "ended_at": self.ended_at,
        }


def _require(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise AttemptError(f"{field} is required")
    return text


def _optional(value: Any) -> Optional[str]:
    text = str(value).strip() if value is not None else ""
    return text or None


class WorkAttemptRepository(BaseRepository):
    """SQLite persistence for Work attempts + their transition events."""

    # ── creation ─────────────────────────────────────────────────

    def create(
        self,
        *,
        source_id: str,
        worktree_id: str,
        project: str,
        story_id: str,
        kind: str,
        exact: bool,
        node_id: Optional[str] = None,
        session_id: Optional[str] = None,
        target_id: Optional[str] = None,
        claimed_by: Optional[str] = None,
        claimed_at: Optional[str] = None,
        state: str = "starting",
        now: Optional[datetime] = None,
    ) -> WorkAttempt:
        source_id = _require(source_id, "source_id")
        worktree_id = _require(worktree_id, "worktree_id")
        project = _require(project, "project")
        story_id = _require(story_id, "story_id")
        if kind not in ASSOCIATION_KINDS:
            raise AttemptError(
                f"association kind must be one of: {', '.join(ASSOCIATION_KINDS)}"
            )
        if state not in ATTEMPT_STATES:
            raise AttemptError(f"state must be one of: {', '.join(ATTEMPT_STATES)}")
        if kind == "heuristic" and exact:
            raise AttemptError("a heuristic association is never exact")
        session_id = _optional(session_id)
        if exact and not session_id and kind == "rider_claim":
            raise AttemptError("a rider claim binds a session")
        timestamp = _format_ts(now)
        attempt = WorkAttempt(
            attempt_id=new_attempt_id(),
            source_id=source_id,
            project=project,
            story_id=story_id,
            worktree_id=worktree_id,
            node_id=_optional(node_id),
            session_id=session_id,
            target_id=_optional(target_id),
            kind=kind,
            claimed_by=_optional(claimed_by),
            claimed_at=_optional(claimed_at) or (timestamp if exact else None),
            exact=bool(exact),
            state=state,
            started_at=timestamp,
            updated_at=timestamp,
            ended_at=timestamp if state in TERMINAL_STATES else None,
        )
        try:
            with self._connection() as conn:
                conn.execute(
                    """
                    INSERT INTO work_attempts
                        (attempt_id, source_id, project, story_id, worktree_id,
                         node_id, session_id, target_id, association_kind,
                         claimed_by, claimed_at, exact, state, started_at,
                         updated_at, ended_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt.attempt_id,
                        attempt.source_id,
                        attempt.project,
                        attempt.story_id,
                        attempt.worktree_id,
                        attempt.node_id,
                        attempt.session_id,
                        attempt.target_id,
                        attempt.kind,
                        attempt.claimed_by,
                        attempt.claimed_at,
                        1 if attempt.exact else 0,
                        attempt.state,
                        attempt.started_at,
                        attempt.updated_at,
                        attempt.ended_at,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO work_attempt_events
                        (attempt_id, from_state, to_state, reason, occurred_at)
                    VALUES (?, NULL, ?, ?, ?)
                    """,
                    (attempt.attempt_id, attempt.state, f"created:{kind}", timestamp),
                )
        except sqlite3.IntegrityError as exc:
            raise AttemptConflict(
                "session is already exactly bound to a live attempt"
            ) from exc
        return attempt

    # ── reads ────────────────────────────────────────────────────

    def get(self, attempt_id: str) -> Optional[WorkAttempt]:
        with self._connection() as conn:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM work_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _from_row(row) if row else None

    def list(
        self,
        *,
        source_id: Optional[str] = None,
        project: Optional[str] = None,
        story_id: Optional[str] = None,
        session_id: Optional[str] = None,
        worktree_id: Optional[str] = None,
        node_id: Optional[str] = None,
        exact: Optional[bool] = None,
        active_only: bool = False,
        limit: int = 200,
    ) -> list[WorkAttempt]:
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("source_id", source_id),
            ("project", project),
            ("story_id", story_id),
            ("session_id", session_id),
            ("worktree_id", worktree_id),
            ("node_id", node_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        if exact is not None:
            clauses.append("exact = ?")
            params.append(1 if exact else 0)
        if active_only:
            placeholders = ", ".join("?" for _ in TERMINAL_STATES)
            clauses.append(f"state NOT IN ({placeholders})")
            params.extend(sorted(TERMINAL_STATES))
        where = f"WHERE {' AND '.join(clauses)} " if clauses else ""
        query = (
            f"SELECT {_COLUMNS} FROM work_attempts {where}"
            "ORDER BY started_at DESC, attempt_id LIMIT ?"
        )
        params.append(max(1, min(int(limit), 1000)))
        with self._connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [_from_row(row) for row in rows]

    def find_active(self, **filters: Any) -> list[WorkAttempt]:
        return self.list(active_only=True, **filters)

    def events(self, attempt_id: str) -> list[dict[str, Any]]:
        """The replayable transition history, oldest first."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT from_state, to_state, reason, occurred_at "
                "FROM work_attempt_events WHERE attempt_id = ? ORDER BY id",
                (attempt_id,),
            ).fetchall()
        return [
            {
                "from": row[0],
                "to": str(row[1]),
                "reason": str(row[2] or ""),
                "occurred_at": str(row[3]),
            }
            for row in rows
        ]

    # ── the state machine ────────────────────────────────────────

    def transition(
        self,
        attempt_id: str,
        to_state: str,
        *,
        reason: str = "",
        now: Optional[datetime] = None,
    ) -> WorkAttempt:
        """Apply one honest transition; a same-state call is a no-op
        that appends no event. Illegal moves refuse — terminal states
        are tombstones, never silently resurrected."""
        if to_state not in ATTEMPT_STATES:
            raise AttemptError(f"state must be one of: {', '.join(ATTEMPT_STATES)}")
        current = self.get(attempt_id)
        if current is None:
            raise AttemptError("unknown attempt")
        if current.state == to_state:
            return current
        if to_state not in ALLOWED_TRANSITIONS[current.state]:
            raise AttemptTransitionError(
                f"cannot move an attempt from {current.state} to {to_state}"
            )
        timestamp = _format_ts(now)
        ended_at = timestamp if to_state in TERMINAL_STATES else None
        with self._connection() as conn:
            conn.execute(
                "UPDATE work_attempts SET state = ?, updated_at = ?, "
                "ended_at = COALESCE(?, ended_at) WHERE attempt_id = ?",
                (to_state, timestamp, ended_at, attempt_id),
            )
            conn.execute(
                """
                INSERT INTO work_attempt_events
                    (attempt_id, from_state, to_state, reason, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (attempt_id, current.state, to_state, str(reason or ""), timestamp),
            )
        refreshed = self.get(attempt_id)
        assert refreshed is not None
        return refreshed


_COLUMNS = (
    "attempt_id, source_id, project, story_id, worktree_id, node_id, "
    "session_id, target_id, association_kind, claimed_by, claimed_at, "
    "exact, state, started_at, updated_at, ended_at"
)


def _from_row(row: Any) -> WorkAttempt:
    return WorkAttempt(
        attempt_id=str(row[0]),
        source_id=str(row[1]),
        project=str(row[2]),
        story_id=str(row[3]),
        worktree_id=str(row[4]),
        node_id=row[5],
        session_id=row[6],
        target_id=row[7],
        kind=str(row[8]),
        claimed_by=row[9],
        claimed_at=row[10],
        exact=bool(row[11]),
        state=str(row[12]),
        started_at=str(row[13]),
        updated_at=str(row[14]),
        ended_at=row[15],
    )


__all__ = [
    "ALLOWED_TRANSITIONS",
    "ASSOCIATION_KINDS",
    "ATTEMPTS_SCHEMA",
    "ATTEMPT_STATES",
    "AttemptConflict",
    "AttemptError",
    "AttemptTransitionError",
    "TERMINAL_STATES",
    "WorkAttempt",
    "WorkAttemptRepository",
    "new_attempt_id",
]
