"""Durable, local-only first-value journey state (HS-92-03).

The repository intentionally has no phrase/text/blob column: it records only
journey mechanics and outcomes, never what the owner dictated.
"""
from __future__ import annotations

import uuid
from datetime import datetime
import re
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
    "timeout",
    "no_speech",
    "unknown",
}
FIRST_VALUE_EVENT_KINDS = {
    "dictation_requested",
    "capture_started",
    "capture_released",
    "transcript_received",
    "draft_edited",
    "copy_selected",
    "keep_selected",
    "setup_selected",
    "alternate_target_selected",
    "continue_later_selected",
}
# A step is an explicit user act. Capture lifecycle and transcript callbacks are
# still retained as mechanics, but do not inflate the owner-facing count.
FIRST_VALUE_STEP_EVENTS = {
    "dictation_requested",
    "copy_selected",
    "keep_selected",
    "setup_selected",
    "alternate_target_selected",
    "continue_later_selected",
}
FIRST_VALUE_DECISION_EVENTS = {
    "keep_selected",
    "setup_selected",
    "alternate_target_selected",
    "continue_later_selected",
}
_EVENT_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def _elapsed_ms(started_at: object, finished_at: object) -> Optional[int]:
    if not isinstance(started_at, str) or not isinstance(finished_at, str):
        return None
    try:
        started = datetime.fromisoformat(started_at)
        finished = datetime.fromisoformat(finished_at)
    except ValueError:
        return None
    return max(0, int(round((finished - started).total_seconds() * 1000)))


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
            # The start request is itself the first observed owner act. Keeping
            # it in the same transaction means an attempt can never exist with
            # a fabricated client-supplied step count.
            conn.execute(
                """
                INSERT INTO first_value_events
                    (event_id, attempt_id, kind, occurred_at)
                VALUES (?, ?, 'dictation_requested', ?)
                """,
                (f"start:{attempt_id}", attempt_id, started_at),
            )
        return {
            "id": attempt_id,
            "started_at": started_at,
            "succeeded_at": None,
            "steps": 1,
            "decisions": 0,
            "destination": clean_destination,
            "failure_category": None,
            "elapsed_ms": None,
            "event_count": 1,
        }

    def record_event(
        self,
        attempt_id: str,
        *,
        event_id: str,
        kind: str,
        now: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Record one bounded, content-free interaction event idempotently."""
        pid = str(attempt_id or "").strip()
        eid = str(event_id or "").strip()
        clean_kind = str(kind or "").strip().lower()
        if not _EVENT_ID.fullmatch(eid):
            raise ValueError("event_id must be 1..128 identifier characters")
        if clean_kind not in FIRST_VALUE_EVENT_KINDS:
            raise ValueError(f"invalid first-value event kind: {kind!r}")
        expected = re.compile(
            rf"^{re.escape(pid)}:[1-9][0-9]{{0,3}}:{re.escape(clean_kind)}$"
        )
        if not expected.fullmatch(eid):
            raise ValueError("event_id must contain only attempt, sequence, and kind")
        occurred_at = (now or datetime.now()).isoformat()
        with self._connection() as conn:
            attempt = conn.execute(
                "SELECT id, finished_at FROM first_value_attempts WHERE id = ?", (pid,)
            ).fetchone()
            if attempt is None:
                raise KeyError(f"unknown first-value attempt: {attempt_id}")
            if attempt["finished_at"] is not None:
                raise ValueError("first-value attempt is already finished")
            conn.execute(
                """
                INSERT INTO first_value_events
                    (event_id, attempt_id, kind, occurred_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(event_id) DO NOTHING
                """,
                (eid, pid, clean_kind, occurred_at),
            )
            row = conn.execute(
                "SELECT event_id, attempt_id, kind, occurred_at "
                "FROM first_value_events WHERE event_id = ?",
                (eid,),
            ).fetchone()
        if row is None or row["attempt_id"] != pid or row["kind"] != clean_kind:
            raise ValueError("event_id already belongs to another interaction")
        return dict(row)

    def mechanics(self, attempt_id: str) -> dict[str, int]:
        pid = str(attempt_id or "").strip()
        step_marks = ",".join("?" for _ in FIRST_VALUE_STEP_EVENTS)
        decision_marks = ",".join("?" for _ in FIRST_VALUE_DECISION_EVENTS)
        params = (
            *sorted(FIRST_VALUE_STEP_EVENTS),
            *sorted(FIRST_VALUE_DECISION_EVENTS),
            pid,
        )
        with self._connection() as conn:
            row = conn.execute(
                f"""
                SELECT COUNT(*) AS event_count,
                       SUM(CASE WHEN kind IN ({step_marks}) THEN 1 ELSE 0 END) AS steps,
                       SUM(CASE WHEN kind IN ({decision_marks}) THEN 1 ELSE 0 END) AS decisions
                FROM first_value_events WHERE attempt_id = ?
                """,
                params,
            ).fetchone()
        return {
            "event_count": int(row["event_count"] or 0),
            "steps": int(row["steps"] or 0),
            "decisions": int(row["decisions"] or 0),
        }

    def finish_attempt(
        self,
        attempt_id: str,
        *,
        outcome: str,
        steps: Optional[int],
        decisions: Optional[int],
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
        observed = self.mechanics(attempt_id)
        # Legacy databases/clients can only reach the fallback when an attempt
        # predates the event table. New attempts always carry the transactional
        # dictation_requested event and therefore ignore client counters.
        bounded_steps = (
            observed["steps"] if observed["event_count"] else int(steps or 1)
        )
        bounded_decisions = (
            observed["decisions"] if observed["event_count"] else int(decisions or 0)
        )
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
                    "elapsed_ms": _elapsed_ms(row["started_at"], row["finished_at"]),
                    "event_count": observed["event_count"],
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
            "elapsed_ms": _elapsed_ms(row["started_at"], finished_at),
            "event_count": observed["event_count"],
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
        if row is None:
            return None
        attempt = dict(row)
        attempt.update(self.mechanics(str(row["id"])))
        attempt["elapsed_ms"] = _elapsed_ms(row["started_at"], row["finished_at"])
        return attempt


__all__ = [
    "FIRST_VALUE_DESTINATIONS",
    "FIRST_VALUE_FAILURES",
    "FIRST_VALUE_EVENT_KINDS",
    "FIRST_VALUE_STEP_EVENTS",
    "FIRST_VALUE_DECISION_EVENTS",
    "ONBOARDING_DISPOSITIONS",
    "OnboardingRepository",
]
