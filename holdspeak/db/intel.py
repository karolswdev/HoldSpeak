"""IntelRepository — the deferred-intel jobs/attempts queue.

Extracted verbatim from core.py in Phase 31 (HS-31-02). Intel *snapshots* live
with MeetingRepository (embedded in MeetingState); this repo owns the queue:
intel_jobs, intel_job_attempts, and meeting intel-status updates.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from ..logging_config import get_logger
from .base import BaseRepository
from .models import IntelJob, IntelQueueSummary, IntelJobAttempt

log = get_logger("db.intel")


class IntelRepository(BaseRepository):
    """Persistence for the deferred-intel queue (jobs, attempts, status)."""

    def enqueue_intel_job(
        self,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: Optional[str] = None,
    ) -> None:
        """Queue or refresh deferred intelligence processing for a meeting."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intel_jobs (
                    meeting_id, status, transcript_hash, requested_at, updated_at, attempts, last_error
                )
                VALUES (?, 'queued', ?, ?, ?, 0, ?)
                ON CONFLICT(meeting_id) DO UPDATE SET
                    status = 'queued',
                    transcript_hash = excluded.transcript_hash,
                    requested_at = excluded.requested_at,
                    updated_at = excluded.updated_at,
                    last_error = excluded.last_error
                """,
                (meeting_id, transcript_hash, now, now, reason),
            )

            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'queued',
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(intel_requested_at, ?),
                    intel_completed_at = NULL,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    reason or "Queued for later processing.",
                    now,
                    meeting_id,
                ),
            )

    def claim_next_intel_job(self, *, include_scheduled: bool = False) -> Optional[IntelJob]:
        """Claim the next queued intelligence job for processing."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            if include_scheduled:
                row = conn.execute(
                    """
                    SELECT * FROM intel_jobs
                    WHERE status = 'queued'
                    ORDER BY requested_at ASC
                    LIMIT 1
                    """
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT * FROM intel_jobs
                    WHERE status = 'queued'
                      AND requested_at <= ?
                    ORDER BY requested_at ASC
                    LIMIT 1
                    """,
                    (now_iso,),
                ).fetchone()
            if row is None:
                return None

            updated_at = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'running',
                    attempts = attempts + 1,
                    updated_at = ?,
                    last_error = NULL
                WHERE meeting_id = ?
                """,
                (updated_at, row["meeting_id"]),
            )

            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'running',
                    intel_status_detail = 'Processing queued meeting intelligence.',
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (row["meeting_id"],),
            )

            return IntelJob(
                meeting_id=row["meeting_id"],
                status="running",
                transcript_hash=row["transcript_hash"],
                requested_at=datetime.fromisoformat(row["requested_at"]),
                updated_at=datetime.fromisoformat(updated_at),
                attempts=int(row["attempts"]) + 1,
                last_error=None,
            )

    def retry_intel_job(
        self,
        meeting_id: str,
        error: str,
        *,
        retry_at: datetime,
        attempt: int,
        max_attempts: int,
    ) -> None:
        """Requeue a deferred intelligence job for a future retry."""
        now = datetime.now().isoformat()
        retry_at_iso = retry_at.isoformat()
        retry_label = retry_at.replace(microsecond=0).isoformat()
        detail = (
            f"Deferred intel attempt {attempt}/{max_attempts} failed: {error} "
            f"Retrying at {retry_label}."
        )
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'queued',
                    requested_at = ?,
                    updated_at = ?,
                    last_error = ?
                WHERE meeting_id = ?
                """,
                (retry_at_iso, now, error, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'queued',
                    intel_status_detail = ?,
                    intel_completed_at = NULL,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (detail, meeting_id),
            )

    def complete_intel_job(self, meeting_id: str) -> None:
        """Remove a completed deferred intelligence job."""
        with self._connection() as conn:
            conn.execute("DELETE FROM intel_jobs WHERE meeting_id = ?", (meeting_id,))

    def list_intel_jobs(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[IntelJob]:
        """List deferred intelligence jobs with meeting context."""
        with self._connection() as conn:
            query = """
                SELECT
                    j.*,
                    m.title AS meeting_title,
                    m.started_at AS meeting_started_at,
                    m.intel_status_detail AS intel_status_detail
                FROM intel_jobs j
                JOIN meetings m ON m.id = j.meeting_id
                WHERE 1=1
            """
            params: list[Any] = []

            if status and status != "all":
                query += " AND j.status = ?"
                params.append(status)

            query += """
                ORDER BY
                    CASE j.status
                        WHEN 'running' THEN 0
                        WHEN 'queued' THEN 1
                        WHEN 'failed' THEN 2
                        ELSE 3
                    END,
                    j.requested_at ASC
                LIMIT ?
            """
            params.append(limit)

            return [
                IntelJob(
                    meeting_id=row["meeting_id"],
                    status=row["status"],
                    transcript_hash=row["transcript_hash"],
                    requested_at=datetime.fromisoformat(row["requested_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    attempts=int(row["attempts"]),
                    last_error=row["last_error"],
                    meeting_title=row["meeting_title"],
                    started_at=(
                        datetime.fromisoformat(row["meeting_started_at"])
                        if row["meeting_started_at"]
                        else None
                    ),
                    intel_status_detail=row["intel_status_detail"],
                )
                for row in conn.execute(query, params)
            ]

    def get_intel_queue_summary(self) -> IntelQueueSummary:
        """Return aggregate telemetry for deferred-intel queue state."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM intel_jobs
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                """
                SELECT MIN(requested_at) AS next_retry_at
                FROM intel_jobs
                WHERE status = 'queued'
                  AND requested_at > ?
                  AND last_error IS NOT NULL
                """,
                (now_iso,),
            ).fetchone()

        next_retry_at = None
        if next_row is not None and next_row["next_retry_at"]:
            next_retry_at = datetime.fromisoformat(next_row["next_retry_at"])

        return IntelQueueSummary(
            total_jobs=int(row["total_jobs"] or 0),
            queued_jobs=int(row["queued_jobs"] or 0),
            running_jobs=int(row["running_jobs"] or 0),
            failed_jobs=int(row["failed_jobs"] or 0),
            queued_due_jobs=int(row["queued_due_jobs"] or 0),
            scheduled_retry_jobs=int(row["scheduled_retry_jobs"] or 0),
            next_retry_at=next_retry_at,
        )

    def record_intel_job_attempt(
        self,
        meeting_id: str,
        *,
        attempt: int,
        outcome: str,
        error: Optional[str] = None,
        retry_at: Optional[datetime] = None,
    ) -> None:
        """Append an intel-attempt history event."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intel_job_attempts (
                    meeting_id, attempt, outcome, error, retry_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    meeting_id,
                    int(attempt),
                    str(outcome),
                    error,
                    retry_at.isoformat() if retry_at else None,
                    now,
                ),
            )

    def list_intel_job_attempts(self, meeting_id: str, *, limit: int = 5) -> list[IntelJobAttempt]:
        """Return most recent deferred-intel attempt events for one meeting."""
        bounded_limit = max(1, min(int(limit), 50))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT meeting_id, attempt, outcome, error, retry_at, created_at
                FROM intel_job_attempts
                WHERE meeting_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (meeting_id, bounded_limit),
            ).fetchall()

        return [
            IntelJobAttempt(
                meeting_id=row["meeting_id"],
                attempt=int(row["attempt"]),
                outcome=row["outcome"],
                error=row["error"],
                retry_at=(datetime.fromisoformat(row["retry_at"]) if row["retry_at"] else None),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def fail_intel_job(self, meeting_id: str, error: str) -> None:
        """Mark a deferred intelligence job as failed."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'failed',
                    updated_at = ?,
                    last_error = ?
                WHERE meeting_id = ?
                """,
                (now, error, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'error',
                    intel_status_detail = ?,
                    intel_completed_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (error, now, meeting_id),
            )

    def requeue_intel_job(self, meeting_id: str, *, reason: Optional[str] = None) -> bool:
        """Requeue deferred intelligence processing for a meeting."""
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None or not meeting.segments:
            return False

        self.enqueue_intel_job(
            meeting_id,
            transcript_hash=meeting.transcript_hash(),
            reason=reason or "Manual retry requested.",
        )
        return True

    def update_meeting_intel_status(
        self,
        meeting_id: str,
        *,
        status: str,
        detail: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Update persisted intel status for a meeting."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = ?,
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(?, intel_requested_at),
                    intel_completed_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    status,
                    detail,
                    requested_at.isoformat() if requested_at else None,
                    completed_at.isoformat() if completed_at else None,
                    meeting_id,
                ),
            )
