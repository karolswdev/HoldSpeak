"""Repositories for the Workbench primitive (HS-116-01).

A Workbench is a DeskPrimitive: one agent (recipe), one inference target
(profile), one schedule, N items. The agent works through items and
produces receipts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    VALID_SKILL_SOURCES,
    VALID_SKILL_STATUSES,
    VALID_WORKBENCH_ITEM_STATUSES,
    SkillRecord,
    WorkbenchItemRecord,
    WorkbenchRecord,
    WorkbenchRunRecord,
)

log = get_logger("db.workbenches")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class WorkbenchRepository(BaseRepository):

    def upsert(
        self,
        *,
        workbench_id: str,
        name: str = "",
        recipe_id: Optional[str] = None,
        profile_id: Optional[str] = None,
        schedule: Optional[str] = None,
        schedule_enabled: bool = False,
        item_order: Optional[list[str]] = None,
        last_modified: Optional[str] = None,
        deleted: bool = False,
        created_at: Optional[str] = None,
    ) -> WorkbenchRecord:
        clean_id = str(workbench_id or "").strip()
        if not clean_id:
            raise ValueError("workbench id is required")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM workbenches WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO workbenches (id, name, recipe_id, profile_id, schedule,
                                        schedule_enabled, item_order_json,
                                        created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    recipe_id = excluded.recipe_id,
                    profile_id = excluded.profile_id,
                    schedule = excluded.schedule,
                    schedule_enabled = excluded.schedule_enabled,
                    item_order_json = excluded.item_order_json,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(name or ""),
                    str(recipe_id).strip() if recipe_id else None,
                    str(profile_id).strip() if profile_id else None,
                    str(schedule).strip() if schedule else None,
                    1 if schedule_enabled else 0,
                    self._json_dumps(item_order or [], fallback="[]"),
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, workbench_id: str, *, include_deleted: bool = False) -> Optional[WorkbenchRecord]:
        clean_id = str(workbench_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM workbenches WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._row(row)

    def list(self, *, include_deleted: bool = False, limit: int = 500) -> list[WorkbenchRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if include_deleted:
                rows = conn.execute(
                    "SELECT * FROM workbenches ORDER BY name ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM workbenches WHERE deleted = 0 ORDER BY name ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, workbench_id: str) -> bool:
        clean_id = str(workbench_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE workbenches SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0",
                (now, clean_id),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def purge(self, workbench_id: str) -> bool:
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM workbenches WHERE id = ?", (str(workbench_id).strip(),))
            return bool(cur.rowcount and cur.rowcount > 0)

    def _row(self, row: Any) -> WorkbenchRecord:
        return WorkbenchRecord(
            id=row["id"],
            name=row["name"],
            recipe_id=row["recipe_id"],
            profile_id=row["profile_id"],
            schedule=row["schedule"],
            schedule_enabled=bool(row["schedule_enabled"]),
            item_order_json=row["item_order_json"] or "[]",
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )


class WorkbenchItemRepository(BaseRepository):

    def upsert(
        self,
        *,
        item_id: str,
        workbench_id: str,
        title: str = "",
        body: str = "",
        priority: int = 3,
        status: str = "pending",
        grounding: Optional[dict] = None,
        context: Optional[dict] = None,
        result: Optional[str] = None,
        result_egress: Optional[dict] = None,
        tokens_consumed: int = 0,
        last_modified: Optional[str] = None,
        created_at: Optional[str] = None,
        claimed_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> WorkbenchItemRecord:
        clean_id = str(item_id or "").strip()
        if not clean_id:
            raise ValueError("item id is required")
        if status not in VALID_WORKBENCH_ITEM_STATUSES:
            raise ValueError(f"invalid item status: {status}")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at FROM workbench_items WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            conn.execute(
                """
                INSERT INTO workbench_items (id, workbench_id, title, body, priority, status,
                                            grounding_json, context_json, result, result_egress_json,
                                            tokens_consumed, created_at, last_modified,
                                            claimed_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    workbench_id = excluded.workbench_id,
                    title = excluded.title,
                    body = excluded.body,
                    priority = excluded.priority,
                    status = excluded.status,
                    grounding_json = excluded.grounding_json,
                    context_json = excluded.context_json,
                    result = excluded.result,
                    result_egress_json = excluded.result_egress_json,
                    tokens_consumed = excluded.tokens_consumed,
                    last_modified = excluded.last_modified,
                    claimed_at = excluded.claimed_at,
                    completed_at = excluded.completed_at
                """,
                (
                    clean_id,
                    str(workbench_id).strip(),
                    str(title or ""),
                    str(body or ""),
                    max(1, min(int(priority), 5)),
                    status,
                    self._json_dumps(grounding or {}, fallback="{}"),
                    self._json_dumps(context or {}, fallback="{}"),
                    result,
                    self._json_dumps(result_egress, fallback=None) if result_egress else None,
                    int(tokens_consumed),
                    created,
                    last_modified or now,
                    claimed_at,
                    completed_at,
                ),
            )
        return self.get(clean_id)  # type: ignore[return-value]

    def get(self, item_id: str) -> Optional[WorkbenchItemRecord]:
        clean_id = str(item_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM workbench_items WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        return self._row(row)

    def list_for_workbench(
        self, workbench_id: str, *, status: Optional[str] = None, limit: int = 500
    ) -> list[WorkbenchItemRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM workbench_items WHERE workbench_id = ? AND status = ? ORDER BY priority ASC, created_at ASC LIMIT ?",
                    (workbench_id, status, bounded),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM workbench_items WHERE workbench_id = ? ORDER BY priority ASC, created_at ASC LIMIT ?",
                    (workbench_id, bounded),
                ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, item_id: str) -> bool:
        clean_id = str(item_id or "").strip()
        if not clean_id:
            return False
        with self._connection() as conn:
            cur = conn.execute("DELETE FROM workbench_items WHERE id = ?", (clean_id,))
            return bool(cur.rowcount and cur.rowcount > 0)

    def has_active_items(self, workbench_id: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM workbench_items WHERE workbench_id = ? AND status IN ('claimed', 'running')",
                (workbench_id,),
            ).fetchone()
            return bool(row and row["cnt"] > 0)

    def _row(self, row: Any) -> WorkbenchItemRecord:
        return WorkbenchItemRecord(
            id=row["id"],
            workbench_id=row["workbench_id"],
            title=row["title"],
            body=row["body"],
            priority=row["priority"],
            status=row["status"],
            grounding_json=row["grounding_json"] or "{}",
            context_json=row["context_json"] or "{}",
            result=row["result"],
            result_egress_json=row["result_egress_json"],
            tokens_consumed=row["tokens_consumed"] or 0,
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            claimed_at=row["claimed_at"],
            completed_at=row["completed_at"],
        )


class WorkbenchRunRepository(BaseRepository):

    def create(
        self,
        *,
        run_id: str,
        workbench_id: str,
        started_at: Optional[str] = None,
    ) -> WorkbenchRunRecord:
        clean_id = str(run_id or "").strip()
        if not clean_id:
            raise ValueError("run id is required")
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO workbench_runs (id, workbench_id, started_at)
                VALUES (?, ?, ?)
                """,
                (clean_id, str(workbench_id).strip(), started_at or now),
            )
        return self.get(clean_id)  # type: ignore[return-value]

    def complete(
        self,
        run_id: str,
        *,
        items_attempted: int = 0,
        items_completed: int = 0,
        items_failed: int = 0,
        total_tokens: int = 0,
        egress_boundary: str = "",
        model: str = "",
        constitutional_context_revision: int = 0,
        constitutional_context_hash: str = "",
        skills_injected: Optional[list[str]] = None,
        status: str = "completed",
    ) -> Optional[WorkbenchRunRecord]:
        clean_id = str(run_id or "").strip()
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE workbench_runs SET
                    completed_at = ?,
                    items_attempted = ?,
                    items_completed = ?,
                    items_failed = ?,
                    total_tokens = ?,
                    egress_boundary = ?,
                    model = ?,
                    constitutional_context_revision = ?,
                    constitutional_context_hash = ?,
                    skills_injected_json = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    now,
                    items_attempted,
                    items_completed,
                    items_failed,
                    total_tokens,
                    egress_boundary,
                    model,
                    constitutional_context_revision,
                    constitutional_context_hash,
                    self._json_dumps(skills_injected or [], fallback="[]"),
                    status,
                    clean_id,
                ),
            )
        return self.get(clean_id)

    def get(self, run_id: str) -> Optional[WorkbenchRunRecord]:
        clean_id = str(run_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM workbench_runs WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        return self._row(row)

    def list_for_workbench(self, workbench_id: str, *, limit: int = 20) -> list[WorkbenchRunRecord]:
        bounded = max(1, min(int(limit), 100))
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM workbench_runs WHERE workbench_id = ? ORDER BY started_at DESC LIMIT ?",
                (workbench_id, bounded),
            ).fetchall()
        return [self._row(r) for r in rows]

    def _row(self, row: Any) -> WorkbenchRunRecord:
        return WorkbenchRunRecord(
            id=row["id"],
            workbench_id=row["workbench_id"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            items_attempted=row["items_attempted"] or 0,
            items_completed=row["items_completed"] or 0,
            items_failed=row["items_failed"] or 0,
            total_tokens=row["total_tokens"] or 0,
            egress_boundary=row["egress_boundary"] or "",
            model=row["model"] or "",
            constitutional_context_revision=row["constitutional_context_revision"] or 0,
            constitutional_context_hash=row["constitutional_context_hash"] or "",
            skills_injected_json=row["skills_injected_json"] or "[]",
            status=row["status"] or "running",
        )


class SkillRepository(BaseRepository):

    def upsert(
        self,
        *,
        skill_id: str,
        title: str = "",
        body: str = "",
        source: str = "owner-authored",
        status: str = "active",
        recipe_ids: Optional[list[str]] = None,
        created_by: str = "",
        version: Optional[int] = None,
        last_modified: Optional[str] = None,
        created_at: Optional[str] = None,
        deleted: bool = False,
    ) -> SkillRecord:
        clean_id = str(skill_id or "").strip()
        if not clean_id:
            raise ValueError("skill id is required")
        if source not in VALID_SKILL_SOURCES:
            raise ValueError(f"invalid skill source: {source}")
        if status not in VALID_SKILL_STATUSES:
            raise ValueError(f"invalid skill status: {status}")
        now = _now_iso()
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT created_at, version FROM skills WHERE id = ?", (clean_id,)
            ).fetchone()
            created = created_at or (existing["created_at"] if existing else now)
            ver = version if version is not None else (
                (existing["version"] + 1) if existing else 1
            )
            conn.execute(
                """
                INSERT INTO skills (id, title, body, source, status, recipe_ids_json,
                                    created_by, version, created_at, last_modified, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    body = excluded.body,
                    source = excluded.source,
                    status = excluded.status,
                    recipe_ids_json = excluded.recipe_ids_json,
                    created_by = excluded.created_by,
                    version = excluded.version,
                    last_modified = excluded.last_modified,
                    deleted = excluded.deleted
                """,
                (
                    clean_id,
                    str(title or ""),
                    str(body or ""),
                    source,
                    status,
                    self._json_dumps(recipe_ids or [], fallback="[]"),
                    str(created_by or ""),
                    ver,
                    created,
                    last_modified or now,
                    1 if deleted else 0,
                ),
            )
        return self.get(clean_id, include_deleted=True)  # type: ignore[return-value]

    def get(self, skill_id: str, *, include_deleted: bool = False) -> Optional[SkillRecord]:
        clean_id = str(skill_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM skills WHERE id = ?", (clean_id,)).fetchone()
        if not row:
            return None
        if row["deleted"] and not include_deleted:
            return None
        return self._skill_row(row)

    def list(self, *, status: Optional[str] = None, include_deleted: bool = False, limit: int = 500) -> list[SkillRecord]:
        bounded = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM skills WHERE status = ? AND deleted = 0 ORDER BY title ASC LIMIT ?",
                    (status, bounded),
                ).fetchall()
            elif include_deleted:
                rows = conn.execute(
                    "SELECT * FROM skills ORDER BY title ASC LIMIT ?", (bounded,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM skills WHERE deleted = 0 ORDER BY title ASC LIMIT ?",
                    (bounded,),
                ).fetchall()
        return [self._skill_row(r) for r in rows]

    def list_for_recipe(self, recipe_id: str, *, active_only: bool = True) -> list[SkillRecord]:
        all_skills = self.list(status="active" if active_only else None)
        return [
            s for s in all_skills
            if recipe_id in (s.to_dict().get("recipe_ids") or [])
        ]

    def delete(self, skill_id: str) -> bool:
        clean_id = str(skill_id or "").strip()
        if not clean_id:
            return False
        now = _now_iso()
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE skills SET deleted = 1, last_modified = ? WHERE id = ? AND deleted = 0",
                (now, clean_id),
            )
            return bool(cur.rowcount and cur.rowcount > 0)

    def _skill_row(self, row: Any) -> SkillRecord:
        return SkillRecord(
            id=row["id"],
            title=row["title"],
            body=row["body"],
            source=row["source"],
            status=row["status"],
            recipe_ids_json=row["recipe_ids_json"] or "[]",
            created_by=row["created_by"] or "",
            version=row["version"] or 1,
            created_at=row["created_at"],
            last_modified=row["last_modified"],
            deleted=bool(row["deleted"]),
        )
