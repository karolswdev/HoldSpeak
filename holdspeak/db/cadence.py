"""CadenceRepository — persistence for the Cadence Engine (CAD-1-01).

Stores Open Loops and their evidence / next-actions / nudges / policies. Loops
are source-PROJECTED: `upsert_loop` is idempotent on (source_type, source_id) and
PRESERVES the user's lifecycle decisions (status/snoozed_until/nudge_count/score)
across re-collection — so a killed loop stays killed and a snoozed loop stays
snoozed. This repo only reads + writes cadence_* rows; it performs no external
side effect (those go through the actuator path in later phases).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from ..cadence.models import (
    CadencePolicy,
    EvidenceRef,
    NextBestAction,
    Nudge,
    OpenLoop,
)
from .base import BaseRepository

# Statuses the user has explicitly decided — never overwritten by re-projection.
_USER_DECIDED = {"killed", "snoozed", "delegated"}


def _now() -> str:
    return datetime.now().isoformat()


class CadenceRepository(BaseRepository):
    """Durable home for cadence loops/evidence/next-actions/nudges/policies."""

    # ── loops ──────────────────────────────────────────────────────────────
    def upsert_loop(self, loop: OpenLoop) -> OpenLoop:
        """Idempotently project a loop from its source.

        Insert when new (status defaults to the loop's, usually 'open'); on an
        existing (source_type, source_id) update only the SOURCE-derived fields
        (title/summary/project/owner/priority/needs_review/due_at) and leave the
        user's lifecycle state untouched. Evidence is replaced to mirror the source.
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM cadence_loops WHERE source_type = ? AND source_id = ?",
                (loop.source_type, loop.source_id),
            ).fetchone()
            now = _now()
            if row is None:
                loop_id = loop.id or uuid.uuid4().hex
                conn.execute(
                    """
                    INSERT INTO cadence_loops
                        (id, source_type, source_id, project, title, summary, status,
                         priority, needs_review, owner, created_at, updated_at, due_at,
                         snoozed_until, stale_score, last_nudged_at, nudge_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        loop_id, loop.source_type, loop.source_id, loop.project,
                        loop.title, loop.summary, loop.status, loop.priority,
                        1 if loop.needs_review else 0, loop.owner, now, now,
                        loop.due_at, loop.snoozed_until, loop.stale_score,
                        loop.last_nudged_at, loop.nudge_count,
                    ),
                )
            else:
                loop_id = row["id"]
                conn.execute(
                    """
                    UPDATE cadence_loops
                       SET project = ?, title = ?, summary = ?, priority = ?,
                           needs_review = ?, owner = ?, due_at = ?, updated_at = ?
                     WHERE id = ?
                    """,
                    (
                        loop.project, loop.title, loop.summary, loop.priority,
                        1 if loop.needs_review else 0, loop.owner, loop.due_at,
                        now, loop_id,
                    ),
                )
            # mirror evidence (cheap; source-derived)
            conn.execute("DELETE FROM cadence_evidence_refs WHERE loop_id = ?", (loop_id,))
            for ev in loop.evidence:
                conn.execute(
                    """
                    INSERT INTO cadence_evidence_refs
                        (id, loop_id, kind, ref_id, label, timestamp, deep_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (uuid.uuid4().hex, loop_id, ev.kind, ev.ref_id, ev.label,
                     ev.timestamp, ev.deep_link),
                )
        return self.get_loop(loop_id)  # type: ignore[return-value]

    def get_loop(self, loop_id: str) -> Optional[OpenLoop]:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM cadence_loops WHERE id = ?", (loop_id,)).fetchone()
            if row is None:
                return None
            ev = conn.execute(
                "SELECT * FROM cadence_evidence_refs WHERE loop_id = ? ORDER BY id", (loop_id,)
            ).fetchall()
        return _row_to_loop(row, ev)

    def get_loop_by_source(self, source_type: str, source_id: str) -> Optional[OpenLoop]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id FROM cadence_loops WHERE source_type = ? AND source_id = ?",
                (source_type, source_id),
            ).fetchone()
        return self.get_loop(row["id"]) if row else None

    def list_loops(
        self, *, status: Optional[str] = None, include_terminal: bool = False
    ) -> list[OpenLoop]:
        """Open loops ordered by staleness desc. By default excludes closed/killed."""
        clauses, params = [], []
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        elif not include_terminal:
            clauses.append("status NOT IN ('closed', 'killed')")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM cadence_loops{where} ORDER BY stale_score DESC, updated_at DESC",
                params,
            ).fetchall()
            out = []
            for row in rows:
                ev = conn.execute(
                    "SELECT * FROM cadence_evidence_refs WHERE loop_id = ? ORDER BY id",
                    (row["id"],),
                ).fetchall()
                out.append(_row_to_loop(row, ev))
        return out

    def set_status(self, loop_id: str, status: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE cadence_loops SET status = ?, updated_at = ? WHERE id = ?",
                (status, _now(), loop_id),
            )

    def snooze(self, loop_id: str, until: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE cadence_loops SET status = 'snoozed', snoozed_until = ?, updated_at = ? WHERE id = ?",
                (until, _now(), loop_id),
            )

    def set_stale_score(self, loop_id: str, score: float) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE cadence_loops SET stale_score = ? WHERE id = ?", (score, loop_id)
            )

    def bump_nudge(self, loop_id: str, at: Optional[str] = None) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE cadence_loops SET nudge_count = nudge_count + 1, last_nudged_at = ? WHERE id = ?",
                (at or _now(), loop_id),
            )

    def close_missing(self, source_type: str, present_source_ids: list[str]) -> int:
        """Close loops of `source_type` whose source vanished (audit, not delete).

        Never touches user-decided (killed/snoozed/delegated) loops. Returns count.
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, source_id, status FROM cadence_loops WHERE source_type = ?",
                (source_type,),
            ).fetchall()
            present = set(present_source_ids)
            closed = 0
            for row in rows:
                if (
                    row["source_id"] not in present
                    and row["status"] not in _USER_DECIDED
                    and row["status"] != "closed"
                ):
                    conn.execute(
                        "UPDATE cadence_loops SET status = 'closed', updated_at = ? WHERE id = ?",
                        (_now(), row["id"]),
                    )
                    closed += 1
        return closed

    # ── next actions ───────────────────────────────────────────────────────
    def add_next_action(self, action: NextBestAction) -> str:
        action_id = action.id or uuid.uuid4().hex
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cadence_next_actions
                    (id, loop_id, kind, title, body_markdown, confidence, reversible,
                     proposal_id, generated_by, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (action_id, action.loop_id, action.kind, action.title, action.body_markdown,
                 action.confidence, 1 if action.reversible else 0, action.proposal_id,
                 action.generated_by, action.generated_at or _now()),
            )
        return action_id

    # ── nudges ─────────────────────────────────────────────────────────────
    def record_nudge(self, nudge: Nudge) -> str:
        nudge_id = nudge.id or uuid.uuid4().hex
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cadence_nudges
                    (id, loop_id, next_action_id, surface, severity, title,
                     message_markdown, status, created_at, shown_at, acted_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nudge_id, nudge.loop_id, nudge.next_action_id, nudge.surface, nudge.severity,
                 nudge.title, nudge.message_markdown, nudge.status, nudge.created_at or _now(),
                 nudge.shown_at, nudge.acted_at, nudge.expires_at),
            )
        return nudge_id

    # ── policies ───────────────────────────────────────────────────────────
    def upsert_policy(self, policy: CadencePolicy) -> str:
        policy_id = policy.id or policy.name
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cadence_policies (id, name, enabled, config_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name, enabled = excluded.enabled,
                    config_json = excluded.config_json, updated_at = excluded.updated_at
                """,
                (policy_id, policy.name, 1 if policy.enabled else 0,
                 self._json_dumps(policy.config, fallback="{}"), _now()),
            )
        return policy_id

    def get_policy(self, policy_id: str) -> Optional[CadencePolicy]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM cadence_policies WHERE id = ?", (policy_id,)
            ).fetchone()
        return _row_to_policy(row, self) if row else None

    def list_policies(self) -> list[CadencePolicy]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM cadence_policies ORDER BY id").fetchall()
        return [_row_to_policy(row, self) for row in rows]


def _row_to_loop(row, evidence_rows) -> OpenLoop:
    return OpenLoop(
        id=row["id"],
        source_type=row["source_type"],
        source_id=row["source_id"],
        project=row["project"],
        title=row["title"],
        summary=row["summary"],
        status=row["status"],
        priority=row["priority"],
        needs_review=bool(row["needs_review"]),
        owner=row["owner"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        due_at=row["due_at"],
        snoozed_until=row["snoozed_until"],
        stale_score=row["stale_score"],
        last_nudged_at=row["last_nudged_at"],
        nudge_count=row["nudge_count"],
        evidence=[
            EvidenceRef(
                id=e["id"], kind=e["kind"], ref_id=e["ref_id"], label=e["label"],
                timestamp=e["timestamp"], deep_link=e["deep_link"],
            )
            for e in evidence_rows
        ],
    )


def _row_to_policy(row, repo: BaseRepository) -> CadencePolicy:
    return CadencePolicy(
        id=row["id"],
        name=row["name"],
        enabled=bool(row["enabled"]),
        config=repo._json_loads_dict(row["config_json"]),
        updated_at=row["updated_at"],
    )
