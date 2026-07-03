"""Meeting candidates surfaced from the ledger.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Any

from ..models import (
    ActivityMeetingCandidate,
    VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES,
)


class ActivityCandidatesMixin:
    def create_activity_meeting_candidate(
        self,
        *,
        source_connector_id: str,
        title: str,
        source_activity_record_id: Optional[int] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        meeting_url: Optional[str] = None,
        confidence: float = 0.0,
        status: str = "candidate",
        candidate_id: Optional[str] = None,
    ) -> ActivityMeetingCandidate:
        """Persist one local meeting candidate from an enrichment connector."""
        clean_connector = str(source_connector_id or "").strip()
        if not clean_connector:
            raise ValueError("source_connector_id is required")
        clean_title = str(title or "").strip()
        if not clean_title:
            raise ValueError("title is required")
        clean_status = self._normalize_activity_meeting_candidate_status(status)
        record_id = int(source_activity_record_id) if source_activity_record_id is not None else None
        clean_id = str(candidate_id or f"amc-{uuid.uuid4().hex[:12]}").strip()
        clean_meeting_url = str(meeting_url).strip() if meeting_url not in (None, "") else None
        dedupe_key = self._activity_meeting_candidate_dedupe_key(
            source_connector_id=clean_connector,
            source_activity_record_id=record_id,
            meeting_url=clean_meeting_url,
            title=clean_title,
        )
        now_iso = datetime.now().isoformat()
        starts_iso = self._activity_time_to_iso(starts_at)
        ends_iso = self._activity_time_to_iso(ends_at)
        clean_confidence = max(0.0, min(1.0, float(confidence)))
        with self._connection() as conn:
            if record_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM activity_records WHERE id = ?",
                    (record_id,),
                ).fetchone()
                if exists is None:
                    raise ValueError(f"activity record not found: {record_id}")
            existing = conn.execute(
                """
                SELECT *
                FROM activity_meeting_candidates
                WHERE dedupe_key = ?
                  AND dedupe_key != ''
                """,
                (dedupe_key,),
            ).fetchone()
            if existing is not None:
                next_status = clean_status if clean_status != "candidate" else str(existing["status"])
                conn.execute(
                    """
                    UPDATE activity_meeting_candidates
                    SET source_activity_record_id = COALESCE(?, source_activity_record_id),
                        title = ?,
                        starts_at = COALESCE(?, starts_at),
                        ends_at = COALESCE(?, ends_at),
                        meeting_url = COALESCE(?, meeting_url),
                        confidence = MAX(confidence, ?),
                        status = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        record_id,
                        clean_title,
                        starts_iso,
                        ends_iso,
                        clean_meeting_url,
                        clean_confidence,
                        next_status,
                        now_iso,
                        str(existing["id"]),
                    ),
                )
                row = conn.execute(
                    "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                    (str(existing["id"]),),
                ).fetchone()
                return self._row_to_activity_meeting_candidate(row)
            conn.execute(
                """
                INSERT INTO activity_meeting_candidates (
                    id, source_connector_id, source_activity_record_id, dedupe_key, title,
                    starts_at, ends_at, meeting_url, started_meeting_id, confidence, status,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_connector,
                    record_id,
                    dedupe_key,
                    clean_title,
                    starts_iso,
                    ends_iso,
                    clean_meeting_url,
                    None,
                    clean_confidence,
                    clean_status,
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row)

    def get_activity_meeting_candidate(
        self,
        candidate_id: str,
    ) -> Optional[ActivityMeetingCandidate]:
        """Fetch one local meeting candidate by ID."""
        clean_id = str(candidate_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row) if row is not None else None

    def list_activity_meeting_candidates(
        self,
        *,
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[ActivityMeetingCandidate]:
        """List local meeting candidates."""
        where: list[str] = []
        params: list[Any] = []
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if status:
            where.append("status = ?")
            params.append(self._normalize_activity_meeting_candidate_status(status))
        query = "SELECT * FROM activity_meeting_candidates"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY starts_at ASC, created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_meeting_candidate(row) for row in rows]

    def update_activity_meeting_candidate_status(
        self,
        candidate_id: str,
        status: str,
    ) -> Optional[ActivityMeetingCandidate]:
        """Update one meeting candidate status."""
        clean_id = str(candidate_id or "").strip()
        if not clean_id:
            return None
        clean_status = self._normalize_activity_meeting_candidate_status(status)
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE activity_meeting_candidates
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_status, datetime.now().isoformat(), clean_id),
            )
            if not cursor.rowcount:
                return None
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row)

    def mark_activity_meeting_candidate_started(
        self,
        candidate_id: str,
        *,
        meeting_id: Optional[str] = None,
    ) -> Optional[ActivityMeetingCandidate]:
        """Mark a candidate as manually started and persist the started meeting ID."""
        clean_id = str(candidate_id or "").strip()
        if not clean_id:
            return None
        clean_meeting_id = str(meeting_id).strip() if meeting_id not in (None, "") else None
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE activity_meeting_candidates
                SET status = 'started',
                    started_meeting_id = COALESCE(?, started_meeting_id),
                    updated_at = ?
                WHERE id = ?
                """,
                (clean_meeting_id, datetime.now().isoformat(), clean_id),
            )
            if not cursor.rowcount:
                return None
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row)

    def delete_activity_meeting_candidates(
        self,
        *,
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Delete local meeting candidates by connector or status."""
        where: list[str] = []
        params: list[Any] = []
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if status:
            where.append("status = ?")
            params.append(self._normalize_activity_meeting_candidate_status(status))
        query = "DELETE FROM activity_meeting_candidates"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def _normalize_activity_meeting_candidate_status(self, status: object) -> str:
        clean_status = str(status or "").strip().lower()
        if clean_status not in VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES:
            raise ValueError(
                "activity meeting candidate status must be one of "
                f"{sorted(VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES)}"
            )
        return clean_status

    def _activity_meeting_candidate_dedupe_key(
        self,
        *,
        source_connector_id: str,
        source_activity_record_id: Optional[int],
        meeting_url: Optional[str],
        title: str,
    ) -> str:
        clean_connector = str(source_connector_id or "").strip().lower()
        if source_activity_record_id is not None:
            return f"{clean_connector}:record:{int(source_activity_record_id)}"
        if meeting_url:
            try:
                clean_url = self._normalize_activity_url(meeting_url)
            except ValueError:
                clean_url = str(meeting_url).strip().lower()
            return f"{clean_connector}:url:{clean_url}"
        return f"{clean_connector}:title:{str(title or '').strip().lower()}"

    def _row_to_activity_meeting_candidate(
        self,
        row: sqlite3.Row,
    ) -> ActivityMeetingCandidate:
        return ActivityMeetingCandidate(
            id=str(row["id"]),
            source_connector_id=str(row["source_connector_id"]),
            source_activity_record_id=(
                int(row["source_activity_record_id"])
                if row["source_activity_record_id"] is not None
                else None
            ),
            dedupe_key=str(row["dedupe_key"] or ""),
            title=str(row["title"]),
            starts_at=datetime.fromisoformat(row["starts_at"]) if row["starts_at"] else None,
            ends_at=datetime.fromisoformat(row["ends_at"]) if row["ends_at"] else None,
            meeting_url=row["meeting_url"],
            started_meeting_id=row["started_meeting_id"],
            confidence=float(row["confidence"] or 0),
            status=str(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

