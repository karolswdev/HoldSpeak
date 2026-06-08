"""Local activity-intelligence ledger.

Extracted verbatim from core.py in Phase 31 (HS-31-03).
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    ActivityRecord,
    ActivityImportCheckpoint,
    ActivityProjectRule,
    ActivityEnrichmentConnectorState,
    ConnectorRun,
    ActivityAnnotation,
    ActivityMeetingCandidate,
    VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES,
)

log = get_logger("db.activity")


class ActivityRepository(BaseRepository):
    """Local activity-intelligence ledger."""

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

    def set_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
        last_visit_raw: Optional[str] = None,
        last_imported_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
        enabled: bool = True,
    ) -> ActivityImportCheckpoint:
        """Create or update a browser history import checkpoint."""
        clean_browser = str(source_browser or "").strip().lower()
        if not clean_browser:
            raise ValueError("source_browser is required")
        clean_profile = str(source_profile or "").strip()
        clean_path_hash = str(source_path_hash or "").strip()
        now_iso = datetime.now().isoformat()
        imported_iso = (
            last_imported_at.isoformat()
            if isinstance(last_imported_at, datetime)
            else now_iso
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_import_checkpoints (
                    source_browser, source_profile, source_path_hash,
                    last_visit_raw, last_imported_at, last_error, enabled,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_browser, source_profile, source_path_hash)
                DO UPDATE SET
                    last_visit_raw = excluded.last_visit_raw,
                    last_imported_at = excluded.last_imported_at,
                    last_error = excluded.last_error,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_browser,
                    clean_profile,
                    clean_path_hash,
                    str(last_visit_raw) if last_visit_raw not in (None, "") else None,
                    imported_iso,
                    str(last_error) if last_error not in (None, "") else None,
                    int(bool(enabled)),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (clean_browser, clean_profile, clean_path_hash),
            ).fetchone()
            return self._row_to_activity_checkpoint(row)

    def list_activity_import_checkpoints(self) -> list[ActivityImportCheckpoint]:
        """List all browser history import checkpoints."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                ORDER BY source_browser ASC, source_profile ASC, source_path_hash ASC
                """
            ).fetchall()
            return [self._row_to_activity_checkpoint(row) for row in rows]

    def get_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
    ) -> Optional[ActivityImportCheckpoint]:
        """Load one browser history import checkpoint."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (
                    str(source_browser or "").strip().lower(),
                    str(source_profile or "").strip(),
                    str(source_path_hash or "").strip(),
                ),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_checkpoint(row)

    def get_activity_privacy_settings(self) -> dict[str, Any]:
        """Return activity ingestion privacy settings with defaults."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT enabled, retention_days, updated_at
                FROM activity_privacy_settings
                WHERE id = 1
                """
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO activity_privacy_settings
                        (id, enabled, retention_days, updated_at)
                    VALUES (1, 1, 30, ?)
                    """,
                    (datetime.now().isoformat(),),
                )
                row = conn.execute(
                    """
                    SELECT enabled, retention_days, updated_at
                    FROM activity_privacy_settings
                    WHERE id = 1
                    """
                ).fetchone()
            return {
                "enabled": bool(row["enabled"]),
                "paused": not bool(row["enabled"]),
                "retention_days": int(row["retention_days"] or 30),
                "updated_at": str(row["updated_at"]),
            }

    def update_activity_privacy_settings(
        self,
        *,
        enabled: Optional[bool] = None,
        retention_days: Optional[int] = None,
    ) -> dict[str, Any]:
        """Update activity ingestion privacy settings."""
        current = self.get_activity_privacy_settings()
        next_enabled = current["enabled"] if enabled is None else bool(enabled)
        next_retention = current["retention_days"]
        if retention_days is not None:
            next_retention = max(1, min(int(retention_days), 3650))
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_privacy_settings
                    (id, enabled, retention_days, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    retention_days = excluded.retention_days,
                    updated_at = excluded.updated_at
                """,
                (int(next_enabled), int(next_retention), datetime.now().isoformat()),
            )
        return self.get_activity_privacy_settings()

    def list_dismissed_nudge_keys(self) -> set[str]:
        """Phase 53: persisted nudge dismissals (HS-53-01)."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT nudge_key FROM activity_nudge_dismissals"
            ).fetchall()
            return {str(row["nudge_key"]) for row in rows}

    def dismiss_nudge(self, nudge_key: str) -> None:
        """Phase 53: persist a nudge dismissal so it stays dismissed (HS-53-01)."""
        clean = str(nudge_key or "").strip()
        if not clean:
            raise ValueError("nudge_key is required")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_nudge_dismissals (nudge_key, dismissed_at)
                VALUES (?, ?)
                ON CONFLICT(nudge_key) DO UPDATE SET dismissed_at = excluded.dismissed_at
                """,
                (clean, datetime.now().isoformat()),
            )

    def list_activity_domain_rules(self) -> list[dict[str, str]]:
        """List domain allow/deny rules for activity ingestion."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT domain, action, created_at, updated_at
                FROM activity_domain_rules
                ORDER BY domain ASC
                """
            ).fetchall()
            return [
                {
                    "domain": str(row["domain"]),
                    "action": str(row["action"] or "exclude"),
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                }
                for row in rows
            ]

    def upsert_activity_domain_rule(
        self,
        *,
        domain: str,
        action: str = "exclude",
    ) -> dict[str, str]:
        """Create or update one activity domain privacy rule."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            raise ValueError("domain is required")
        clean_action = str(action or "exclude").strip().lower()
        if clean_action not in {"exclude", "allow"}:
            raise ValueError("activity domain action must be 'exclude' or 'allow'")
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_domain_rules (domain, action, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    action = excluded.action,
                    updated_at = excluded.updated_at
                """,
                (clean_domain, clean_action, now_iso, now_iso),
            )
        return next(
            rule for rule in self.list_activity_domain_rules()
            if rule["domain"] == clean_domain
        )

    def delete_activity_domain_rule(self, domain: str) -> bool:
        """Delete one activity domain privacy rule."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            return False
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM activity_domain_rules WHERE domain = ?",
                (clean_domain,),
            )
            return bool(cursor.rowcount)

    def is_activity_domain_excluded(self, domain: str) -> bool:
        """Return true if a domain or one of its parents is excluded."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            return False
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT domain, action
                FROM activity_domain_rules
                WHERE action = 'exclude'
                """
            ).fetchall()
        for row in rows:
            rule_domain = str(row["domain"] or "").lower()
            if clean_domain == rule_domain or clean_domain.endswith(f".{rule_domain}"):
                return True
        return False

    def create_activity_project_rule(
        self,
        *,
        project_id: str,
        name: str = "",
        match_type: str,
        pattern: str,
        entity_type: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True,
        rule_id: Optional[str] = None,
    ) -> ActivityProjectRule:
        """Create a deterministic rule that maps activity records to a project."""
        clean_project_id = str(project_id or "").strip()
        if not clean_project_id:
            raise ValueError("project_id is required")
        if self._db.projects.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=match_type,
            pattern=pattern,
            entity_type=entity_type,
        )
        clean_id = str(rule_id or f"apr-{uuid.uuid4().hex[:12]}").strip()
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_project_rules (
                    id, project_id, name, enabled, priority, match_type,
                    pattern, entity_type, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_project_id,
                    str(name or "").strip(),
                    int(bool(enabled)),
                    int(priority),
                    clean_match_type,
                    clean_pattern,
                    clean_entity_type,
                    now_iso,
                    now_iso,
                ),
            )
        rule = self.get_activity_project_rule(clean_id)
        if rule is None:
            raise RuntimeError("activity project rule was not created")
        return rule

    def get_activity_project_rule(self, rule_id: str) -> Optional[ActivityProjectRule]:
        """Load one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT apr.*, p.name AS project_name
                FROM activity_project_rules apr
                LEFT JOIN projects p ON p.id = apr.project_id
                WHERE apr.id = ?
                """,
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_project_rule(row)

    def update_activity_project_rule(
        self,
        rule_id: str,
        **fields: Any,
    ) -> Optional[ActivityProjectRule]:
        """Update one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return None
        allowed = {
            "project_id",
            "name",
            "enabled",
            "priority",
            "match_type",
            "pattern",
            "entity_type",
        }
        current = self.get_activity_project_rule(clean_id)
        if current is None:
            return None

        next_match_type = fields.get("match_type", current.match_type)
        next_pattern = fields.get("pattern", current.pattern)
        next_entity_type = fields.get("entity_type", current.entity_type)
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=next_match_type,
            pattern=next_pattern,
            entity_type=next_entity_type,
        )

        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "project_id":
                clean_project_id = str(value or "").strip()
                if not clean_project_id:
                    raise ValueError("project_id is required")
                if self._db.projects.get_project(clean_project_id) is None:
                    raise ValueError(f"project not found: {clean_project_id}")
                updates.append("project_id = ?")
                params.append(clean_project_id)
            elif key == "name":
                updates.append("name = ?")
                params.append(str(value or "").strip())
            elif key == "enabled":
                updates.append("enabled = ?")
                params.append(int(bool(value)))
            elif key == "priority":
                updates.append("priority = ?")
                params.append(int(value))
            elif key == "match_type":
                updates.append("match_type = ?")
                params.append(clean_match_type)
            elif key == "pattern":
                updates.append("pattern = ?")
                params.append(clean_pattern)
            elif key == "entity_type":
                updates.append("entity_type = ?")
                params.append(clean_entity_type)
        if not updates:
            return current
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(clean_id)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE activity_project_rules SET {', '.join(updates)} WHERE id = ?",
                params,
            )
        return self.get_activity_project_rule(clean_id)

    def delete_activity_project_rule(self, rule_id: str) -> bool:
        """Delete one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return False
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM activity_project_rules WHERE id = ?",
                (clean_id,),
            )
            return bool(cursor.rowcount)

    def list_activity_project_rules(
        self,
        *,
        include_disabled: bool = False,
    ) -> list[ActivityProjectRule]:
        """List activity project rules in deterministic matching order."""
        query = """
            SELECT apr.*, p.name AS project_name
            FROM activity_project_rules apr
            LEFT JOIN projects p ON p.id = apr.project_id
        """
        params: list[Any] = []
        if not include_disabled:
            query += " WHERE apr.enabled = 1"
        query += " ORDER BY apr.priority DESC, apr.created_at ASC, apr.id ASC"
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_project_rule(row) for row in rows]

    def preview_activity_project_rule(
        self,
        *,
        project_id: str,
        match_type: str,
        pattern: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[ActivityRecord]:
        """Preview existing records that would match a proposed rule."""
        from ..activity_mapping import first_matching_rule

        clean_project_id = str(project_id or "").strip()
        if not clean_project_id:
            raise ValueError("project_id is required")
        if self._db.projects.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=match_type,
            pattern=pattern,
            entity_type=entity_type,
        )
        now = datetime.now()
        rule = ActivityProjectRule(
            id="preview",
            project_id=clean_project_id,
            project_name=None,
            name="",
            enabled=True,
            priority=0,
            match_type=clean_match_type,
            pattern=clean_pattern,
            entity_type=clean_entity_type,
            created_at=now,
            updated_at=now,
        )
        matches: list[ActivityRecord] = []
        for record in self._iter_activity_records():
            if first_matching_rule(record, [rule]) is not None:
                matches.append(record)
            if len(matches) >= max(1, min(int(limit), 500)):
                break
        return matches

    def apply_activity_project_rules(self, *, limit: Optional[int] = None) -> int:
        """Backfill existing activity records from enabled project mapping rules."""
        from ..activity_mapping import project_id_for_record

        rules = self.list_activity_project_rules(include_disabled=False)
        if not rules:
            return 0
        updated = 0
        cap = None if limit is None else max(1, int(limit))
        for record in self._iter_activity_records():
            project_id = project_id_for_record(record, rules)
            if project_id and project_id != record.project_id:
                self.assign_activity_record_project(record.id, project_id)
                updated += 1
                if cap is not None and updated >= cap:
                    break
        return updated

    def assign_activity_record_project(self, record_id: int, project_id: Optional[str]) -> bool:
        """Assign or clear a project ID on one existing activity record."""
        clean_project_id = (
            str(project_id).strip()
            if project_id is not None and str(project_id).strip()
            else None
        )
        if clean_project_id is not None and self._db.projects.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE activity_records
                SET project_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_project_id, datetime.now().isoformat(), int(record_id)),
            )
            return bool(cursor.rowcount)

    def match_activity_project_rule(
        self,
        record: ActivityRecord,
        rules: Optional[list[ActivityProjectRule]] = None,
    ) -> Optional[ActivityProjectRule]:
        """Return the first enabled mapping rule for an activity record."""
        from ..activity_mapping import first_matching_rule

        return first_matching_rule(
            record,
            rules if rules is not None else self.list_activity_project_rules(include_disabled=False),
        )

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

    def _normalize_activity_project_rule_fields(
        self,
        *,
        match_type: object,
        pattern: object,
        entity_type: Optional[object] = None,
    ) -> tuple[str, str, Optional[str]]:
        from ..activity_mapping import normalize_match_type

        clean_match_type = normalize_match_type(match_type)
        clean_pattern = str(pattern or "").strip()
        if not clean_pattern:
            raise ValueError("pattern is required")
        clean_entity_type = (
            str(entity_type).strip().lower()
            if entity_type is not None and str(entity_type).strip()
            else None
        )
        if clean_match_type == "entity_type":
            clean_pattern = clean_pattern.lower()
            clean_entity_type = None
        elif clean_match_type in {"domain", "url_contains", "title_contains", "github_repo", "source_browser"}:
            clean_pattern = clean_pattern.lower()
        return clean_match_type, clean_pattern, clean_entity_type

    def upsert_activity_enrichment_connector(
        self,
        *,
        connector_id: str,
        enabled: Optional[bool] = None,
        settings: Optional[dict[str, Any]] = None,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Create or update persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            raise ValueError("connector_id is required")
        current = self.get_activity_enrichment_connector(clean_id)
        next_enabled = bool(enabled) if enabled is not None else (current.enabled if current else False)
        next_settings = settings if settings is not None else (current.settings if current else {})
        now_iso = datetime.now().isoformat()
        last_run_iso = (
            last_run_at.isoformat()
            if isinstance(last_run_at, datetime)
            else (current.last_run_at.isoformat() if current and current.last_run_at else None)
        )
        clean_error = (
            str(last_error)
            if last_error not in (None, "")
            else (current.last_error if current and last_error is None else None)
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_enrichment_connectors (
                    id, enabled, settings_json, last_run_at, last_error,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    settings_json = excluded.settings_json,
                    last_run_at = excluded.last_run_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_id,
                    int(next_enabled),
                    self._json_dumps(next_settings or {}, fallback="{}"),
                    last_run_iso,
                    clean_error,
                    now_iso,
                    now_iso,
                ),
            )
        state = self.get_activity_enrichment_connector(clean_id)
        if state is None:
            raise RuntimeError("activity enrichment connector was not created")
        return state

    def get_activity_enrichment_connector(
        self,
        connector_id: str,
    ) -> Optional[ActivityEnrichmentConnectorState]:
        """Load persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                WHERE id = ?
                """,
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_enrichment_connector(row)

    def list_activity_enrichment_connectors(self) -> list[ActivityEnrichmentConnectorState]:
        """List persisted enrichment connector states."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                ORDER BY id ASC
                """
            ).fetchall()
            return [self._row_to_activity_enrichment_connector(row) for row in rows]

    def record_activity_enrichment_run(
        self,
        *,
        connector_id: str,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Persist the latest run result for one enrichment connector."""
        state = self.get_activity_enrichment_connector(connector_id)
        return self.upsert_activity_enrichment_connector(
            connector_id=connector_id,
            enabled=state.enabled if state else False,
            settings=state.settings if state else {},
            last_run_at=last_run_at or datetime.now(),
            last_error=last_error if last_error is not None else "",
        )

    def record_connector_run(
        self,
        *,
        connector_id: str,
        started_at: datetime,
        finished_at: datetime,
        succeeded: bool,
        error: Optional[str] = None,
        output_bytes: int = 0,
        annotation_count: int = 0,
        candidate_count: int = 0,
        command_count: int = 0,
    ) -> ConnectorRun:
        """Persist one row to `connector_runs`. HS-13-05.

        Every code path that exercises a pack — gh / jira CLI
        runs, calendar previews on enable, extension event
        ingestion — calls this at completion (success *or*
        failure). The single-row `last_run_at` / `last_error`
        on `activity_enrichment_connectors` remains the
        "what happened most recently" fast-path; this table
        is the over-time signal.
        """
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            raise ValueError("connector_id is required")
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO connector_runs (
                    connector_id, started_at, finished_at,
                    succeeded, error, output_bytes,
                    annotation_count, candidate_count, command_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    started_at.isoformat(),
                    finished_at.isoformat(),
                    1 if succeeded else 0,
                    (error or None),
                    int(output_bytes),
                    int(annotation_count),
                    int(candidate_count),
                    int(command_count),
                ),
            )
            row_id = int(cursor.lastrowid or 0)
        return ConnectorRun(
            id=row_id,
            connector_id=clean_id,
            started_at=started_at,
            finished_at=finished_at,
            succeeded=bool(succeeded),
            error=(error or None),
            output_bytes=int(output_bytes),
            annotation_count=int(annotation_count),
            candidate_count=int(candidate_count),
            command_count=int(command_count),
        )

    def list_connector_runs(
        self,
        *,
        connector_id: str,
        limit: int = 10,
    ) -> list[ConnectorRun]:
        """Return the N most recent runs for one connector."""
        clean_id = str(connector_id or "").strip()
        capped = max(1, min(int(limit), 200))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, connector_id, started_at, finished_at,
                       succeeded, error, output_bytes,
                       annotation_count, candidate_count, command_count
                FROM connector_runs
                WHERE connector_id = ?
                ORDER BY started_at DESC, id DESC
                LIMIT ?
                """,
                (clean_id, capped),
            ).fetchall()
        return [self._row_to_connector_run(row) for row in rows]

    def delete_connector_runs(self, *, connector_id: str) -> int:
        """Drop every run row for one connector. Returns the row
        count deleted. Called by the per-pack "Clear annotations" /
        "Clear candidates" surfaces — run history is part of the
        connector's output."""
        clean_id = str(connector_id or "").strip()
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM connector_runs WHERE connector_id = ?",
                (clean_id,),
            )
            return int(cursor.rowcount or 0)

    def _row_to_connector_run(self, row: Any) -> ConnectorRun:
        return ConnectorRun(
            id=int(row[0]),
            connector_id=str(row[1]),
            started_at=datetime.fromisoformat(str(row[2])),
            finished_at=datetime.fromisoformat(str(row[3])),
            succeeded=bool(row[4]),
            error=(str(row[5]) if row[5] is not None else None),
            output_bytes=int(row[6] or 0),
            annotation_count=int(row[7] or 0),
            candidate_count=int(row[8] or 0),
            command_count=int(row[9] or 0),
        )

    def create_activity_annotation(
        self,
        *,
        source_connector_id: str,
        annotation_type: str,
        title: str = "",
        value: Optional[dict[str, Any]] = None,
        confidence: float = 0.0,
        activity_record_id: Optional[int] = None,
        annotation_id: Optional[str] = None,
    ) -> ActivityAnnotation:
        """Persist one local enrichment annotation."""
        clean_connector = str(source_connector_id or "").strip()
        if not clean_connector:
            raise ValueError("source_connector_id is required")
        clean_type = str(annotation_type or "").strip().lower()
        if not clean_type:
            raise ValueError("annotation_type is required")
        clean_id = str(annotation_id or f"ann-{uuid.uuid4().hex[:12]}").strip()
        record_id = int(activity_record_id) if activity_record_id is not None else None
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            if record_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM activity_records WHERE id = ?",
                    (record_id,),
                ).fetchone()
                if exists is None:
                    raise ValueError(f"activity record not found: {record_id}")
            conn.execute(
                """
                INSERT INTO activity_annotations (
                    id, activity_record_id, source_connector_id, annotation_type,
                    title, value_json, confidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    record_id,
                    clean_connector,
                    clean_type,
                    str(title or "").strip(),
                    self._json_dumps(value or {}, fallback="{}"),
                    max(0.0, min(1.0, float(confidence))),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                "SELECT * FROM activity_annotations WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_annotation(row)

    def list_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[ActivityAnnotation]:
        """List local enrichment annotations."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "SELECT * FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_annotation(row) for row in rows]

    def delete_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
    ) -> int:
        """Delete local enrichment annotations by connector, record, or type."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "DELETE FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

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

    def _row_to_activity_enrichment_connector(
        self,
        row: sqlite3.Row,
    ) -> ActivityEnrichmentConnectorState:
        return ActivityEnrichmentConnectorState(
            id=str(row["id"]),
            enabled=bool(row["enabled"]),
            settings=self._json_loads_dict(row["settings_json"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
            last_error=row["last_error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_annotation(self, row: sqlite3.Row) -> ActivityAnnotation:
        return ActivityAnnotation(
            id=str(row["id"]),
            activity_record_id=int(row["activity_record_id"]) if row["activity_record_id"] is not None else None,
            source_connector_id=str(row["source_connector_id"]),
            annotation_type=str(row["annotation_type"]),
            title=str(row["title"] or ""),
            value=self._json_loads_dict(row["value_json"]),
            confidence=float(row["confidence"] or 0),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_project_rule(self, row: sqlite3.Row) -> ActivityProjectRule:
        return ActivityProjectRule(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            project_name=row["project_name"],
            name=str(row["name"] or ""),
            enabled=bool(row["enabled"]),
            priority=int(row["priority"] or 0),
            match_type=str(row["match_type"]),
            pattern=str(row["pattern"]),
            entity_type=row["entity_type"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_checkpoint(self, row: sqlite3.Row) -> ActivityImportCheckpoint:
        return ActivityImportCheckpoint(
            source_browser=str(row["source_browser"]),
            source_profile=str(row["source_profile"] or ""),
            source_path_hash=str(row["source_path_hash"] or ""),
            last_visit_raw=row["last_visit_raw"],
            last_imported_at=(
                datetime.fromisoformat(row["last_imported_at"])
                if row["last_imported_at"]
                else None
            ),
            last_error=row["last_error"],
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
