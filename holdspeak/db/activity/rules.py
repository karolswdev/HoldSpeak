"""Domain exclusion rules and project-assignment rules.

Bodies moved verbatim from db/activity.py (HS-79-01, the Phase-63 discipline).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, Any

from ..models import ActivityProjectRule


class ActivityRulesMixin:
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
        from ...activity_mapping import first_matching_rule

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
        from ...activity_mapping import project_id_for_record

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
        from ...activity_mapping import first_matching_rule

        return first_matching_rule(
            record,
            rules if rules is not None else self.list_activity_project_rules(include_disabled=False),
        )

    def _normalize_activity_project_rule_fields(
        self,
        *,
        match_type: object,
        pattern: object,
        entity_type: Optional[object] = None,
    ) -> tuple[str, str, Optional[str]]:
        from ...activity_mapping import normalize_match_type

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

