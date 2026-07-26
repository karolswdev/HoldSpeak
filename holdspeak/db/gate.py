"""Gate proposal repository (HS-104-02).

The tool-call gate's persistence: a held proposal is a RECORD, never
authority — nothing in these rows can cause execution; only a live
hook waiting on a decision can proceed. Every state transition passes
through ONE chokepoint (:meth:`GateProposalRepository._transition`),
and every transition writes a ``gate_audit`` row in the
``steering_audit`` shape: who/when/session/tool/hash, decision,
reason. Arguments are redacted at the edge — sha256 + first 120
characters, never the full payload (the council's redaction demand).

States: ``held | approved | denied | expired | invalidated``. Held is
the only non-terminal state. Restart honesty: on hub startup every
``held`` row flips ``invalidated`` (revalidate-or-expire, never
resume). Expiry is a deny — there is no timeout-auto-allow anywhere.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from .base import BaseRepository

ARGS_HEAD_CHARS = 120

HELD = "held"
APPROVED = "approved"
DENIED = "denied"
EXPIRED = "expired"
INVALIDATED = "invalidated"

TERMINAL_STATES = frozenset({APPROVED, DENIED, EXPIRED, INVALIDATED})
ALL_STATES = TERMINAL_STATES | {HELD}

#: The only legal transitions. Everything else is refused by the state
#: machine with a typed error — never lost, never silently absorbed.
_LEGAL = frozenset(
    (HELD, target) for target in (APPROVED, DENIED, EXPIRED, INVALIDATED)
)


class GateStateError(Exception):
    """An illegal transition, refused by name with the standing state."""

    def __init__(self, proposal_id: str, current: str, requested: str) -> None:
        self.proposal_id = proposal_id
        self.current = current
        self.requested = requested
        super().__init__(
            f"proposal {proposal_id!r} is {current!r}; cannot become {requested!r}"
        )


class GateArgsMismatchError(Exception):
    """The TOCTOU refusal: same idempotency key, different args hash."""

    def __init__(self, proposal_id: str) -> None:
        self.proposal_id = proposal_id
        super().__init__(f"args_mismatch: proposal {proposal_id!r} re-posted with different arguments")


@dataclass(frozen=True)
class GateProposal:
    id: str
    session_key: str
    agent: str
    tool: str
    args_sha256: str
    args_head: str
    cwd: str
    operation: dict[str, Any]
    policy_snapshot: dict[str, Any]
    created_at: float
    expires_at: float
    state: str
    decided_by: Optional[str]
    decided_at: Optional[float]
    reason: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_key": self.session_key,
            "agent": self.agent,
            "tool": self.tool,
            "args_sha256": self.args_sha256,
            "args_head": self.args_head,
            "cwd": self.cwd,
            "operation": dict(self.operation),
            "policy_snapshot": dict(self.policy_snapshot),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "state": self.state,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "reason": self.reason,
        }


class GateProposalRepository(BaseRepository):
    """Proposals + their audit trail. `now_fn` is injectable (the
    grant-store clock pattern) so expiry races are testable without
    sleeps."""

    def __init__(self, connection, container=None, *, now_fn: Callable[[], float] = time.time):
        super().__init__(connection, container)
        self._now = now_fn

    # -- arrival -----------------------------------------------------------

    def propose(
        self,
        *,
        proposal_id: str,
        session_key: str,
        agent: str,
        tool: str,
        args_sha256: str,
        args_head: str,
        cwd: str,
        ttl_seconds: float,
        operation: Optional[dict[str, Any]] = None,
        policy_snapshot: Optional[dict[str, Any]] = None,
    ) -> GateProposal:
        """Idempotent arrival.

        - New key → a ``held`` row (audit: ``proposed``).
        - Same key, same args hash → the standing row, whatever its
          state (audit: ``re_arrival`` — one decision, two arrivals).
        - Same key, DIFFERENT args hash → :class:`GateArgsMismatchError`
          AND the original (if still held) is ``invalidated`` — the
          Phase-87 refuse-and-revoke reflex, so a human's Approve can
          never land on a payload the human never saw.
        """
        args_head = args_head[:ARGS_HEAD_CHARS]
        existing = self.get(proposal_id)
        if existing is not None:
            if existing.args_sha256 != args_sha256:
                if existing.state == HELD:
                    self._transition(
                        proposal_id,
                        INVALIDATED,
                        decided_by="gate",
                        reason="args_mismatch: a re-arrival changed the arguments",
                    )
                self._audit(
                    proposal_id=proposal_id,
                    session_key=session_key,
                    tool=tool,
                    args_sha256=args_sha256,
                    event="args_mismatch",
                    detail="re-POST with a different args hash refused",
                    decided_by=None,
                )
                raise GateArgsMismatchError(proposal_id)
            self._audit(
                proposal_id=proposal_id,
                session_key=existing.session_key,
                tool=existing.tool,
                args_sha256=existing.args_sha256,
                event="re_arrival",
                detail=f"standing state {existing.state}",
                decided_by=None,
            )
            return self.get(proposal_id)  # re-read: mismatch path may have invalidated

        now = self._now()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO gate_proposals (
                    id, session_key, agent, tool, args_sha256, args_head, cwd,
                    operation_json, policy_snapshot_json,
                    created_at, expires_at, state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proposal_id,
                    session_key,
                    agent,
                    tool,
                    args_sha256,
                    args_head,
                    cwd,
                    self._json_dumps(operation or {}, fallback="{}"),
                    self._json_dumps(policy_snapshot or {}, fallback="{}"),
                    now,
                    now + max(ttl_seconds, 0.0),
                    HELD,
                ),
            )
        self._audit(
            proposal_id=proposal_id,
            session_key=session_key,
            tool=tool,
            args_sha256=args_sha256,
            event="proposed",
            detail=f"held for {ttl_seconds:.0f}s",
            decided_by=None,
        )
        return self.get(proposal_id)

    # -- the ONE decision chokepoint --------------------------------------

    def _transition(
        self,
        proposal_id: str,
        target: str,
        *,
        decided_by: str,
        reason: Optional[str],
    ) -> GateProposal:
        """Every state flip in the system lands here — the census pins
        it. First write wins: the UPDATE is guarded on the current
        state, so a racing second decision refuses with the standing
        decision instead of overwriting it."""
        if target not in TERMINAL_STATES:
            raise GateStateError(proposal_id, "?", target)
        current = self.get(proposal_id)
        if current is None:
            raise KeyError(proposal_id)
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE gate_proposals
                SET state = ?, decided_by = ?, decided_at = ?, reason = ?
                WHERE id = ? AND state = ?
                """,
                (target, decided_by, self._now(), reason, proposal_id, HELD),
            )
            won = cursor.rowcount == 1
        if not won:
            standing = self.get(proposal_id)
            raise GateStateError(proposal_id, standing.state, target)
        after = self.get(proposal_id)
        self._audit(
            proposal_id=proposal_id,
            session_key=after.session_key,
            tool=after.tool,
            args_sha256=after.args_sha256,
            event=target,
            detail=reason,
            decided_by=decided_by,
        )
        return after

    def decide(
        self, proposal_id: str, *, decision: str, decided_by: str, reason: Optional[str] = None
    ) -> GateProposal:
        """Approve or deny a HELD proposal (expiry checked first: a
        decision arriving after expiry loses to ``expired``)."""
        if decision not in (APPROVED, DENIED):
            raise ValueError(f"decision must be approved|denied, not {decision!r}")
        self.expire_due()
        return self._transition(proposal_id, decision, decided_by=decided_by, reason=reason)

    def expire_due(self) -> list[str]:
        """Flip every overdue ``held`` row to ``expired`` (a deny with
        the named reason, never an allow)."""
        now = self._now()
        overdue = [
            row.id
            for row in self.list_state(HELD)
            if row.expires_at <= now
        ]
        expired: list[str] = []
        for proposal_id in overdue:
            try:
                self._transition(
                    proposal_id,
                    EXPIRED,
                    decided_by="gate",
                    reason="expired: no decision arrived before the hold ran out",
                )
                expired.append(proposal_id)
            except GateStateError:
                pass  # a decision won the race; its state stands
        return expired

    def invalidate_all_held(self, *, reason: str) -> list[str]:
        """Restart honesty: nothing held pre-restart is decidable
        post-restart without the agent proposing again."""
        flipped: list[str] = []
        for row in self.list_state(HELD):
            try:
                self._transition(row.id, INVALIDATED, decided_by="gate", reason=reason)
                flipped.append(row.id)
            except GateStateError:
                pass
        return flipped

    # -- reads -------------------------------------------------------------

    def get(self, proposal_id: str) -> Optional[GateProposal]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM gate_proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
        return self._to_proposal(row) if row is not None else None

    def list_state(self, state: str, *, limit: int = 100) -> list[GateProposal]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM gate_proposals WHERE state = ? ORDER BY created_at ASC LIMIT ?",
                (state, limit),
            ).fetchall()
        return [self._to_proposal(row) for row in rows]

    def audit_entries(self, *, limit: int = 200) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM gate_audit ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                "id": row["id"],
                "ts": row["ts"],
                "proposal_id": row["proposal_id"],
                "session_key": row["session_key"],
                "tool": row["tool"],
                "args_sha256": row["args_sha256"],
                "event": row["event"],
                "detail": row["detail"],
                "decided_by": row["decided_by"],
            }
            for row in rows
        ]

    # -- reported usage (HS-104-05) ----------------------------------------

    def report_usage(
        self,
        *,
        session_key: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int,
        cache_creation_tokens: int,
    ) -> None:
        """Replace the session's reported figures (the hook reports
        session totals, not deltas). Cache figures stay separate."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO session_usage (
                    session_key, model, input_tokens, output_tokens,
                    cache_read_tokens, cache_creation_tokens, reported_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(session_key) DO UPDATE SET
                    model = excluded.model,
                    input_tokens = excluded.input_tokens,
                    output_tokens = excluded.output_tokens,
                    cache_read_tokens = excluded.cache_read_tokens,
                    cache_creation_tokens = excluded.cache_creation_tokens,
                    reported_at = excluded.reported_at
                """,
                (
                    session_key,
                    model,
                    max(0, int(input_tokens)),
                    max(0, int(output_tokens)),
                    max(0, int(cache_read_tokens)),
                    max(0, int(cache_creation_tokens)),
                ),
            )

    def usage_for(self, session_key: str) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM session_usage WHERE session_key = ?",
                (session_key,),
            ).fetchone()
        if row is None:
            return None
        return {
            "session_key": row["session_key"],
            "model": row["model"],
            "input_tokens": row["input_tokens"],
            "output_tokens": row["output_tokens"],
            "cache_read_tokens": row["cache_read_tokens"],
            "cache_creation_tokens": row["cache_creation_tokens"],
            "reported_at": row["reported_at"],
        }

    def proposals_for_session(self, session_key: str, *, limit: int = 500) -> list[GateProposal]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM gate_proposals WHERE session_key = ? "
                "ORDER BY created_at ASC LIMIT ?",
                (session_key, limit),
            ).fetchall()
        return [self._to_proposal(row) for row in rows]

    # -- internals ---------------------------------------------------------

    def _audit(
        self,
        *,
        proposal_id: str,
        session_key: str,
        tool: str,
        args_sha256: str,
        event: str,
        detail: Optional[str],
        decided_by: Optional[str],
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO gate_audit (
                    proposal_id, session_key, tool, args_sha256, event, detail, decided_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (proposal_id, session_key, tool, args_sha256, event, detail, decided_by),
            )

    def _to_proposal(self, row: Any) -> GateProposal:
        return GateProposal(
            id=row["id"],
            session_key=row["session_key"],
            agent=row["agent"],
            tool=row["tool"],
            args_sha256=row["args_sha256"],
            args_head=row["args_head"],
            cwd=row["cwd"],
            operation=self._json_loads_dict(row["operation_json"]),
            policy_snapshot=self._json_loads_dict(row["policy_snapshot_json"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            state=row["state"],
            decided_by=row["decided_by"],
            decided_at=row["decided_at"],
            reason=row["reason"],
        )
