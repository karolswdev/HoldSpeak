"""The activity ledger: normalize, upsert, read, delete, and the record row mapper.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional, Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ...logging_config import get_logger
from ..models import ActivityRecord

log = get_logger("db.activity")


class ActivityRecordsMixin:
    def _normalize_activity_url(self, url: object) -> str:
        clean = str(url or "").strip()
        if not clean:
            raise ValueError("url is required")
        parsed = urlsplit(clean)
        if not parsed.scheme or not parsed.netloc:
            return clean

        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/")
        query_pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True))
        query = urlencode(query_pairs, doseq=True)
        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                path,
                query,
                "",
            )
        )

    def _activity_domain(self, normalized_url: str, domain: Optional[str]) -> str:
        clean_domain = str(domain or "").strip().lower()
        if clean_domain:
            return clean_domain
        parsed = urlsplit(normalized_url)
        return (parsed.hostname or "").lower()

    def _activity_time_to_iso(self, value: object) -> Optional[str]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def upsert_activity_record(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
        url: str,
        title: Optional[str] = None,
        domain: Optional[str] = None,
        visit_count: int = 1,
        first_seen_at: Optional[datetime] = None,
        last_seen_at: Optional[datetime] = None,
        last_visit_raw: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ActivityRecord:
        """Insert or merge one normalized browser activity record."""
        clean_browser = str(source_browser or "").strip().lower()
        if not clean_browser:
            raise ValueError("source_browser is required")
        clean_profile = str(source_profile or "").strip()
        clean_path_hash = str(source_path_hash or "").strip()
        clean_url = str(url or "").strip()
        normalized_url = self._normalize_activity_url(clean_url)
        clean_domain = self._activity_domain(normalized_url, domain)
        clean_entity_type = (
            str(entity_type).strip().lower()
            if entity_type is not None and str(entity_type).strip()
            else None
        )
        clean_entity_id = (
            str(entity_id).strip()
            if entity_id is not None and str(entity_id).strip()
            else None
        )
        clean_project_id = (
            str(project_id).strip()
            if project_id is not None and str(project_id).strip()
            else None
        )
        now_iso = datetime.now().isoformat()
        first_seen_iso = self._activity_time_to_iso(first_seen_at) or self._activity_time_to_iso(last_seen_at)
        last_seen_iso = self._activity_time_to_iso(last_seen_at) or first_seen_iso
        raw_timestamp = str(last_visit_raw) if last_visit_raw not in (None, "") else None

        with self._connection() as conn:
            existing = conn.execute(
                """
                SELECT *
                FROM activity_records
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND (
                    normalized_url = ?
                    OR (
                        ? IS NOT NULL
                        AND ? IS NOT NULL
                        AND entity_type = ?
                        AND entity_id = ?
                    )
                  )
                ORDER BY
                    CASE WHEN normalized_url = ? THEN 0 ELSE 1 END,
                    updated_at DESC
                LIMIT 1
                """,
                (
                    clean_browser,
                    clean_profile,
                    normalized_url,
                    clean_entity_type,
                    clean_entity_id,
                    clean_entity_type,
                    clean_entity_id,
                    normalized_url,
                ),
            ).fetchone()

            if existing is None:
                cursor = conn.execute(
                    """
                    INSERT INTO activity_records (
                        source_browser, source_profile, source_path_hash, url,
                        normalized_url, title, domain, visit_count, first_seen_at,
                        last_seen_at, last_visit_raw, entity_type, entity_id,
                        project_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_browser,
                        clean_profile,
                        clean_path_hash,
                        clean_url,
                        normalized_url,
                        title,
                        clean_domain,
                        max(0, int(visit_count)),
                        first_seen_iso,
                        last_seen_iso,
                        raw_timestamp,
                        clean_entity_type,
                        clean_entity_id,
                        clean_project_id,
                        now_iso,
                        now_iso,
                    ),
                )
                record_id = int(cursor.lastrowid)
            else:
                record_id = int(existing["id"])
                existing_first = existing["first_seen_at"]
                existing_last = existing["last_seen_at"]
                merged_first = min(
                    [value for value in (existing_first, first_seen_iso) if value],
                    default=None,
                )
                merged_last = max(
                    [value for value in (existing_last, last_seen_iso) if value],
                    default=None,
                )
                conn.execute(
                    """
                    UPDATE activity_records
                    SET source_path_hash = COALESCE(NULLIF(?, ''), source_path_hash),
                        url = ?,
                        normalized_url = ?,
                        title = COALESCE(?, title),
                        domain = ?,
                        visit_count = MAX(visit_count, ?),
                        first_seen_at = ?,
                        last_seen_at = ?,
                        last_visit_raw = COALESCE(?, last_visit_raw),
                        entity_type = COALESCE(?, entity_type),
                        entity_id = COALESCE(?, entity_id),
                        project_id = COALESCE(?, project_id),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        clean_path_hash,
                        clean_url,
                        normalized_url,
                        title,
                        clean_domain,
                        max(0, int(visit_count)),
                        merged_first,
                        merged_last,
                        raw_timestamp,
                        clean_entity_type,
                        clean_entity_id,
                        clean_project_id,
                        now_iso,
                        record_id,
                    ),
                )

            row = conn.execute(
                "SELECT * FROM activity_records WHERE id = ?",
                (record_id,),
            ).fetchone()
            return self._row_to_activity_record(row)

    def list_activity_records(
        self,
        *,
        source_browser: Optional[str] = None,
        source_profile: Optional[str] = None,
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        entity_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[ActivityRecord]:
        """List normalized activity records for recent-context surfaces."""
        where: list[str] = []
        params: list[Any] = []
        if source_browser:
            where.append("source_browser = ?")
            params.append(str(source_browser).strip().lower())
        if source_profile is not None:
            where.append("source_profile = ?")
            params.append(str(source_profile).strip())
        if project_id:
            where.append("project_id = ?")
            params.append(str(project_id).strip())
        if domain:
            where.append("domain = ?")
            params.append(str(domain).strip().lower())
        if entity_type:
            where.append("entity_type = ?")
            params.append(str(entity_type).strip().lower())
        if since is not None:
            where.append("last_seen_at >= ?")
            params.append(since.isoformat())

        query = "SELECT * FROM activity_records"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY last_seen_at DESC, updated_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_record(row) for row in rows]

    def delete_activity_records(
        self,
        *,
        source_browser: Optional[str] = None,
        source_profile: Optional[str] = None,
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        older_than: Optional[datetime] = None,
    ) -> int:
        """Delete imported activity records for clear/retention controls."""
        where: list[str] = []
        params: list[Any] = []
        if source_browser:
            where.append("source_browser = ?")
            params.append(str(source_browser).strip().lower())
        if source_profile is not None:
            where.append("source_profile = ?")
            params.append(str(source_profile).strip())
        if project_id:
            where.append("project_id = ?")
            params.append(str(project_id).strip())
        if domain:
            where.append("domain = ?")
            params.append(str(domain).strip().lower())
        if older_than is not None:
            where.append("last_seen_at < ?")
            params.append(older_than.isoformat())
        query = "DELETE FROM activity_records"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def get_activity_record(self, record_id: int) -> Optional[ActivityRecord]:
        """Phase 53 (HS-53-03): fetch a single activity record by id.

        Used by the dictation-context override so a nudge-selected record can be
        pinned without re-importing browser history. Returns ``None`` for an
        unknown id.
        """
        try:
            clean_id = int(record_id)
        except (TypeError, ValueError):
            return None
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM activity_records WHERE id = ?",
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_record(row)

    def _iter_activity_records(self) -> Iterator[ActivityRecord]:
        """Iterate all activity records in recent-first order without the public cap."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_records
                ORDER BY last_seen_at DESC, updated_at DESC, id DESC
                """
            ).fetchall()
            return iter([self._row_to_activity_record(row) for row in rows])

    def _row_to_activity_record(self, row: sqlite3.Row) -> ActivityRecord:
        return ActivityRecord(
            id=int(row["id"]),
            source_browser=str(row["source_browser"]),
            source_profile=str(row["source_profile"] or ""),
            source_path_hash=str(row["source_path_hash"] or ""),
            url=str(row["url"]),
            normalized_url=str(row["normalized_url"]),
            title=row["title"],
            domain=str(row["domain"] or ""),
            visit_count=int(row["visit_count"] or 0),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]) if row["first_seen_at"] else None,
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]) if row["last_seen_at"] else None,
            last_visit_raw=row["last_visit_raw"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            project_id=row["project_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

