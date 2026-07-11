"""Durable, local-only first-value journey state (HS-92-03).

The repository intentionally has no phrase/text/blob column: it records only
journey mechanics and outcomes, never what the owner dictated.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from .base import BaseRepository

ONBOARDING_DISPOSITIONS = {"completed", "dismissed", "needs_help"}
FIRST_VALUE_DESTINATIONS = {"this_machine", "paired_desktop"}
FIRST_VALUE_FAILURES = {
    "permission_denied",
    "missing_model",
    "rejected_token",
    "unreachable_hub",
    "delivery_conflict",
    "transcription_failed",
    "no_speech",
    "unknown",
}


class OnboardingRepository(BaseRepository):
    def disposition(self) -> Optional[dict[str, str]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT disposition, updated_at FROM onboarding_state WHERE id = 1"
            ).fetchone()
        if row is None:
            return None
        return {"disposition": row["disposition"], "updated_at": row["updated_at"]}

    def set_disposition(self, disposition: str) -> dict[str, str]:
        clean = str(disposition or "").strip().lower()
        if clean not in ONBOARDING_DISPOSITIONS:
            raise ValueError(f"invalid onboarding disposition: {disposition!r}")
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO onboarding_state (id, disposition, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    disposition = excluded.disposition,
                    updated_at = excluded.updated_at
                """,
                (clean, now),
            )
        return {"disposition": clean, "updated_at": now}

    def start_attempt(self, *, destination: str) -> dict[str, Any]:
        clean_destination = str(destination or "").strip().lower()
        if clean_destination not in FIRST_VALUE_DESTINATIONS:
            raise ValueError(f"invalid first-value destination: {destination!r}")
        attempt_id = uuid.uuid4().hex
        started_at = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO first_value_attempts (id, started_at, destination)
                VALUES (?, ?, ?)
                """,
                (attempt_id, started_at, clean_destination),
            )
        return {
            "id": attempt_id,
            "started_at": started_at,
            "succeeded_at": None,
            "steps": 0,
            "decisions": 0,
            "destination": clean_destination,
            "failure_category": None,
        }

    def finish_attempt(
        self,
        attempt_id: str,
        *,
        outcome: str,
        steps: int,
        decisions: int,
        destination: str,
        failure_category: Optional[str] = None,
    ) -> dict[str, Any]:
        clean_outcome = str(outcome or "").strip().lower()
        if clean_outcome not in {"success", "failure"}:
            raise ValueError("outcome must be success or failure")
        clean_destination = str(destination or "").strip().lower()
        if clean_destination not in FIRST_VALUE_DESTINATIONS:
            raise ValueError(f"invalid first-value destination: {destination!r}")
        clean_failure = str(failure_category or "").strip().lower() or None
        if clean_outcome == "failure" and clean_failure not in FIRST_VALUE_FAILURES:
            raise ValueError("a recognized failure_category is required on failure")
        if clean_outcome == "success":
            clean_failure = None
        bounded_steps = int(steps)
        bounded_decisions = int(decisions)
        if not 1 <= bounded_steps <= 20 or not 0 <= bounded_decisions <= 20:
            raise ValueError("steps must be 1..20 and decisions must be 0..20")
        finished_at = datetime.now().isoformat()
        pid = str(attempt_id or "").strip()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT id, started_at, succeeded_at, steps, decisions,
                       destination, failure_category, finished_at
                FROM first_value_attempts WHERE id = ?
                """,
                (pid,),
            ).fetchone()
            if row is None:
                raise KeyError(f"unknown first-value attempt: {attempt_id}")
            if row["finished_at"] is not None:
                return {
                    "id": row["id"],
                    "started_at": row["started_at"],
                    "succeeded_at": row["succeeded_at"],
                    "steps": int(row["steps"]),
                    "decisions": int(row["decisions"]),
                    "destination": row["destination"],
                    "failure_category": row["failure_category"],
                }
            conn.execute(
                """
                UPDATE first_value_attempts
                SET succeeded_at = ?, steps = ?, decisions = ?, destination = ?,
                    failure_category = ?, finished_at = ?
                WHERE id = ?
                """,
                (
                    finished_at if clean_outcome == "success" else None,
                    bounded_steps,
                    bounded_decisions,
                    clean_destination,
                    clean_failure,
                    finished_at,
                    pid,
                ),
            )
        return {
            "id": pid,
            "started_at": row["started_at"],
            "succeeded_at": finished_at if clean_outcome == "success" else None,
            "steps": bounded_steps,
            "decisions": bounded_decisions,
            "destination": clean_destination,
            "failure_category": clean_failure,
        }

    def latest_attempt(self) -> Optional[dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT id, started_at, succeeded_at, steps, decisions,
                       destination, failure_category, finished_at
                FROM first_value_attempts
                ORDER BY started_at DESC, id DESC LIMIT 1
                """
            ).fetchone()
        return dict(row) if row is not None else None


__all__ = [
    "FIRST_VALUE_DESTINATIONS",
    "FIRST_VALUE_FAILURES",
    "ONBOARDING_DISPOSITIONS",
    "OnboardingRepository",
]
