"""Durable additive envelopes for Persona, Sequence, and Workflow runs."""
from __future__ import annotations

from typing import Any, Optional

from .base import BaseRepository
from .models import (
    CapabilityAttemptRecord,
    CapabilityInvocationRecord,
    VALID_CAPABILITY_ATTEMPT_STATES,
    VALID_CAPABILITY_INVOCATION_STATES,
)
from .primitives import _now_iso


class CapabilityInvocationRepository(BaseRepository):
    """Cross-capability run receipts without replacing domain job tables."""

    def begin(
        self,
        *,
        invocation_id: str,
        definition_ref: str,
        initiator: str = "owner",
        grounding_refs: Optional[list[str]] = None,
        requested_placement: str = "this_machine",
        input_snapshot: Optional[dict[str, Any]] = None,
    ) -> CapabilityInvocationRecord:
        clean_id = str(invocation_id or "").strip()
        if not clean_id:
            raise ValueError("invocation id is required")
        if not str(definition_ref or "").strip():
            raise ValueError("definition ref is required")
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO capability_invocations
                   (id,correlation_id,definition_ref,initiator,grounding_refs_json,
                    requested_placement,input_snapshot_json,state,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    clean_id, clean_id, str(definition_ref).strip(),
                    str(initiator or "owner"),
                    self._json_dumps(grounding_refs or [], fallback="[]"),
                    str(requested_placement or "this_machine"),
                    self._json_dumps(input_snapshot or {}, fallback="{}"),
                    "running", now, now,
                ),
            )
        return self.get(clean_id)  # type: ignore[return-value]

    def start_attempt(
        self,
        *,
        invocation_id: str,
        attempt_id: str,
        destination: str,
        provider: Optional[str] = None,
    ) -> CapabilityAttemptRecord:
        now = _now_iso()
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(attempt_index),0)+1 AS n FROM capability_attempts WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            conn.execute(
                """INSERT INTO capability_attempts
                   (id,invocation_id,attempt_index,destination,provider,state,started_at)
                   VALUES (?,?,?,?,?,'running',?)""",
                (attempt_id, invocation_id, int(row["n"]), destination, provider, now),
            )
        return self._get_attempt(attempt_id)  # type: ignore[return-value]

    def finish_attempt(
        self,
        attempt_id: str,
        *,
        state: str,
        provider: Optional[str] = None,
        error: Optional[str] = None,
        result_ref: Optional[str] = None,
    ) -> CapabilityAttemptRecord:
        if state not in VALID_CAPABILITY_ATTEMPT_STATES - {"running"}:
            raise ValueError(f"invalid attempt state: {state}")
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """UPDATE capability_attempts
                   SET state=?,provider=COALESCE(?,provider),error=?,result_ref=?,completed_at=?
                   WHERE id=?""",
                (state, provider, error, result_ref, now, attempt_id),
            )
        row = self._get_attempt(attempt_id)
        if row is None:
            raise ValueError(f"unknown attempt: {attempt_id}")
        return row

    def finish(
        self,
        invocation_id: str,
        *,
        state: str,
        result_ref: Optional[str] = None,
        error: Optional[str] = None,
    ) -> CapabilityInvocationRecord:
        if state not in VALID_CAPABILITY_INVOCATION_STATES - {"running"}:
            raise ValueError(f"invalid invocation state: {state}")
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """UPDATE capability_invocations
                   SET state=?,result_ref=?,error=?,updated_at=?,completed_at=? WHERE id=?""",
                (state, result_ref, error, now, now, invocation_id),
            )
        row = self.get(invocation_id)
        if row is None:
            raise ValueError(f"unknown invocation: {invocation_id}")
        return row

    def get(self, invocation_id: str) -> Optional[CapabilityInvocationRecord]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM capability_invocations WHERE id=?", (invocation_id,)
            ).fetchone()
            attempts = conn.execute(
                "SELECT * FROM capability_attempts WHERE invocation_id=? ORDER BY attempt_index",
                (invocation_id,),
            ).fetchall()
        return self._row(row, attempts) if row else None

    def list(self, *, limit: int = 100) -> list[CapabilityInvocationRecord]:
        bounded = max(1, min(int(limit), 1000))
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id FROM capability_invocations ORDER BY created_at DESC LIMIT ?",
                (bounded,),
            ).fetchall()
        return [row for item in rows if (row := self.get(item["id"])) is not None]

    def _get_attempt(self, attempt_id: str) -> Optional[CapabilityAttemptRecord]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM capability_attempts WHERE id=?", (attempt_id,)
            ).fetchone()
        return self._attempt(row) if row else None

    def _attempt(self, row: Any) -> CapabilityAttemptRecord:
        return CapabilityAttemptRecord(
            id=row["id"], invocation_id=row["invocation_id"],
            attempt_index=int(row["attempt_index"]), destination=row["destination"],
            provider=row["provider"], state=row["state"], error=row["error"],
            result_ref=row["result_ref"], started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def _row(self, row: Any, attempts: list[Any]) -> CapabilityInvocationRecord:
        return CapabilityInvocationRecord(
            id=row["id"], correlation_id=row["correlation_id"],
            definition_ref=row["definition_ref"], initiator=row["initiator"],
            grounding_refs=[str(ref) for ref in self._json_loads_list(row["grounding_refs_json"])],
            requested_placement=row["requested_placement"],
            input_snapshot=self._json_loads_dict(row["input_snapshot_json"]),
            state=row["state"], result_ref=row["result_ref"], error=row["error"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            completed_at=row["completed_at"], attempts=[self._attempt(a) for a in attempts],
        )
