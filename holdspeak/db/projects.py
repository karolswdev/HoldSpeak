"""Projects, associations, and detection log.

Extracted verbatim from core.py in Phase 31 (HS-31-03).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional, Any

from ..logging_config import get_logger
from .base import BaseRepository
from .models import (
    ActionItemSummary,
    ProjectSummary,
    ArtifactSummary,
)

log = get_logger("db.projects")


class ProjectRepository(BaseRepository):
    """Projects, associations, and detection log."""

    table = "projects"

    def create_project(
        self,
        *,
        project_id: str,
        name: str,
        description: str = "",
        keywords: Optional[list[str]] = None,
        team_members: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
        detection_threshold: float = 0.4,
        updated_at: Optional[str] = None,
    ) -> None:
        """Insert a new project knowledge base.

        ``updated_at`` preserves an INCOMING sync clock (the cross-device
        merge must keep clocks comparable — a destination that restamps
        arrival time can never see an equal-clock conflict again).
        """
        clean_id = str(project_id).strip()
        clean_name = str(name).strip()
        if not clean_id:
            raise ValueError("project_id is required")
        if not clean_name:
            raise ValueError("project name is required")
        threshold = max(0.0, min(1.0, float(detection_threshold)))
        now_iso = str(updated_at).strip() if updated_at else datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_name,
                    str(description or ""),
                    self._json_dumps(keywords or [], fallback="[]"),
                    self._json_dumps(team_members or [], fallback="[]"),
                    self._json_dumps(context or {}, fallback="{}"),
                    threshold,
                    now_iso,
                    now_iso,
                ),
            )

    def update_project(self, project_id: str, **fields: Any) -> None:
        """Update one or more project fields."""
        clean_id = str(project_id).strip()
        if not clean_id:
            raise ValueError("project_id is required")
        allowed = {
            "name", "description", "keywords", "team_members",
            "context", "detection_threshold", "is_archived",
        }
        # The sync merge passes the INCOMING clock through so cross-device
        # clocks stay comparable; every other caller stamps now.
        sync_clock = fields.pop("updated_at", None)
        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "name":
                clean = str(value).strip()
                if not clean:
                    raise ValueError("project name cannot be empty")
                updates.append("name = ?")
                params.append(clean)
            elif key == "description":
                updates.append("description = ?")
                params.append(str(value or ""))
            elif key == "keywords":
                updates.append("keywords_json = ?")
                params.append(self._json_dumps(value or [], fallback="[]"))
            elif key == "team_members":
                updates.append("team_members_json = ?")
                params.append(self._json_dumps(value or [], fallback="[]"))
            elif key == "context":
                updates.append("context_json = ?")
                params.append(self._json_dumps(value or {}, fallback="{}"))
            elif key == "detection_threshold":
                updates.append("detection_threshold = ?")
                params.append(max(0.0, min(1.0, float(value))))
            elif key == "is_archived":
                updates.append("is_archived = ?")
                params.append(1 if value else 0)
        if not updates:
            return
        updates.append("updated_at = ?")
        params.append(str(sync_clock).strip() if sync_clock else datetime.now().isoformat())
        params.append(clean_id)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                params,
            )

    def get_project(self, project_id: str) -> Optional[ProjectSummary]:
        """Load a single project by ID."""
        clean_id = str(project_id).strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT p.*,
                       (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                FROM projects p
                WHERE p.id = ?
                """,
                (clean_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_project(row)

    def list_projects(self, *, include_archived: bool = False) -> list[ProjectSummary]:
        """List all projects with meeting counts."""
        with self._connection() as conn:
            if include_archived:
                rows = conn.execute(
                    """
                    SELECT p.*,
                           (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                    FROM projects p
                    ORDER BY p.is_archived ASC, p.name ASC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT p.*,
                           (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                    FROM projects p
                    WHERE p.is_archived = 0
                    ORDER BY p.name ASC
                    """
                ).fetchall()
            return [self._row_to_project(row) for row in rows]

    def get_all_projects_for_detector(self) -> list[dict[str, Any]]:
        """Load lightweight project data for the project_detector plugin."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, keywords_json, team_members_json, detection_threshold
                FROM projects
                WHERE is_archived = 0
                """
            ).fetchall()
            results: list[dict[str, Any]] = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "name": row["name"],
                    "keywords": self._json_loads_list(row["keywords_json"]),
                    "team_members": self._json_loads_list(row["team_members_json"]),
                    "detection_threshold": float(row["detection_threshold"]),
                })
            return results

    def associate_meeting_project(
        self,
        *,
        meeting_id: str,
        project_id: str,
        source: str = "auto",
        confidence: float = 0.0,
    ) -> None:
        """Create or update a meeting-project association."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO meeting_projects (meeting_id, project_id, source, confidence, detected_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(meeting_id, project_id) DO UPDATE SET
                    source = excluded.source,
                    confidence = MAX(meeting_projects.confidence, excluded.confidence),
                    detected_at = excluded.detected_at
                """,
                (
                    str(meeting_id).strip(),
                    str(project_id).strip(),
                    str(source).strip().lower() or "auto",
                    max(0.0, min(1.0, float(confidence))),
                    now_iso,
                ),
            )
            conn.execute(
                """INSERT INTO project_resources
                   (project_id,resource_ref,relationship,source,confidence,
                    created_at,last_modified,deleted)
                   VALUES (?,?,'member',?,?,?,?,0)
                   ON CONFLICT(project_id,resource_ref) DO UPDATE SET
                     source=excluded.source,
                     confidence=MAX(project_resources.confidence,excluded.confidence),
                     last_modified=excluded.last_modified,deleted=0""",
                (
                    str(project_id).strip(), f"meeting:{str(meeting_id).strip()}",
                    str(source).strip().lower() or "auto",
                    max(0.0, min(1.0, float(confidence))), now_iso, now_iso,
                ),
            )

    def disassociate_meeting_project(self, *, meeting_id: str, project_id: str) -> None:
        """Remove a meeting-project association."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM meeting_projects WHERE meeting_id = ? AND project_id = ?",
                (str(meeting_id).strip(), str(project_id).strip()),
            )
            conn.execute(
                "UPDATE project_resources SET deleted=1,last_modified=? "
                "WHERE project_id=? AND resource_ref=?",
                (datetime.now().isoformat(), str(project_id).strip(),
                 f"meeting:{str(meeting_id).strip()}"),
            )

    def get_meeting_projects(self, meeting_id: str) -> list[dict[str, Any]]:
        """List projects associated with a meeting."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT mp.project_id, mp.source, mp.confidence, mp.detected_at,
                       p.name as project_name
                FROM meeting_projects mp
                JOIN projects p ON p.id = mp.project_id
                WHERE mp.meeting_id = ?
                ORDER BY mp.confidence DESC
                """,
                (str(meeting_id).strip(),),
            ).fetchall()
            return [
                {
                    "project_id": row["project_id"],
                    "project_name": row["project_name"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "detected_at": row["detected_at"],
                }
                for row in rows
            ]

    def get_project_meetings(
        self, project_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.title, m.started_at, m.duration_seconds,
                       m.intel_status, mp.source, mp.confidence
                FROM meeting_projects mp
                JOIN meetings m ON m.id = mp.meeting_id
                WHERE mp.project_id = ?
                ORDER BY m.started_at DESC
                LIMIT ? OFFSET ?
                """,
                (str(project_id).strip(), max(1, int(limit)), max(0, int(offset))),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "started_at": row["started_at"],
                    "duration_seconds": row["duration_seconds"],
                    "intel_status": row["intel_status"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                }
                for row in rows
            ]

    def get_project_action_items(self, project_id: str) -> list[ActionItemSummary]:
        """List action items from all meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT ai.id, ai.task, ai.owner, ai.due, ai.status, ai.review_state,
                       ai.source_timestamp,
                       ai.meeting_id, m.title as meeting_title, m.started_at as meeting_date,
                       ai.created_at, ai.completed_at, ai.reviewed_at
                FROM action_items ai
                JOIN meeting_projects mp ON mp.meeting_id = ai.meeting_id
                JOIN meetings m ON m.id = ai.meeting_id
                WHERE mp.project_id = ?
                ORDER BY ai.created_at DESC
                """,
                (str(project_id).strip(),),
            ).fetchall()
            return [
                ActionItemSummary(
                    id=row["id"],
                    task=row["task"],
                    owner=row["owner"],
                    due=row["due"],
                    status=row["status"],
                    review_state=row["review_state"],
                    meeting_id=row["meeting_id"],
                    meeting_title=row["meeting_title"],
                    meeting_date=datetime.fromisoformat(row["meeting_date"]),
                    source_timestamp=row["source_timestamp"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    reviewed_at=datetime.fromisoformat(row["reviewed_at"]) if row["reviewed_at"] else None,
                )
                for row in rows
            ]

    def get_project_artifacts(self, project_id: str) -> list[ArtifactSummary]:
        """List artifacts from all meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT a.*
                FROM artifacts a
                JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id
                WHERE mp.project_id = ?
                ORDER BY a.created_at DESC
                """,
                (str(project_id).strip(),),
            ).fetchall()
            results: list[ArtifactSummary] = []
            for row in rows:
                sources_rows = conn.execute(
                    "SELECT source_type, source_ref FROM artifact_sources WHERE artifact_id = ?",
                    (row["id"],),
                ).fetchall()
                sources = [
                    {"source_type": s["source_type"], "source_ref": s["source_ref"]}
                    for s in sources_rows
                ]
                results.append(
                    ArtifactSummary(
                        id=row["id"],
                        meeting_id=row["meeting_id"],
                        artifact_type=row["artifact_type"],
                        title=row["title"],
                        body_markdown=row["body_markdown"],
                        structured_json=self._json_loads_dict(row["structured_json"]),
                        confidence=float(row["confidence"]),
                        status=row["status"],
                        plugin_id=row["plugin_id"],
                        plugin_version=row["plugin_version"],
                        sources=sources,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return results

    def get_project_summary(self, project_id: str) -> dict[str, Any]:
        """Aggregated stats for a project: meeting count, action items by status, date range."""
        clean_id = str(project_id).strip()
        with self._connection() as conn:
            meeting_row = conn.execute(
                """
                SELECT COUNT(*) as meeting_count,
                       MIN(m.started_at) as first_meeting,
                       MAX(m.started_at) as last_meeting
                FROM meeting_projects mp
                JOIN meetings m ON m.id = mp.meeting_id
                WHERE mp.project_id = ?
                """,
                (clean_id,),
            ).fetchone()
            ai_rows = conn.execute(
                """
                SELECT ai.status, COUNT(*) as cnt
                FROM action_items ai
                JOIN meeting_projects mp ON mp.meeting_id = ai.meeting_id
                WHERE mp.project_id = ?
                GROUP BY ai.status
                """,
                (clean_id,),
            ).fetchall()
            artifact_count_row = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM artifacts a
                JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id
                WHERE mp.project_id = ?
                """,
                (clean_id,),
            ).fetchone()
            action_items_by_status = {row["status"]: row["cnt"] for row in ai_rows}
            return {
                "meeting_count": meeting_row["meeting_count"] or 0,
                "first_meeting": meeting_row["first_meeting"],
                "last_meeting": meeting_row["last_meeting"],
                "action_items_by_status": action_items_by_status,
                "artifact_count": artifact_count_row["cnt"] if artifact_count_row else 0,
            }

    def log_project_detection(
        self,
        *,
        meeting_id: str,
        project_id: str,
        window_id: str,
        score: float,
        keyword_hits: Optional[list[str]] = None,
        member_hits: Optional[list[str]] = None,
    ) -> None:
        """Record one project detection score for an intent window."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO project_detection_log
                    (meeting_id, project_id, window_id, score, keyword_hits_json, member_hits_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(meeting_id).strip(),
                    str(project_id).strip(),
                    str(window_id).strip(),
                    max(0.0, float(score)),
                    self._json_dumps(keyword_hits or [], fallback="[]"),
                    self._json_dumps(member_hits or [], fallback="[]"),
                ),
            )

    def get_project_detection_log(
        self, project_id: str, *, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Get recent detection audit entries for a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT pdl.*, m.title as meeting_title
                FROM project_detection_log pdl
                LEFT JOIN meetings m ON m.id = pdl.meeting_id
                WHERE pdl.project_id = ?
                ORDER BY pdl.created_at DESC
                LIMIT ?
                """,
                (str(project_id).strip(), max(1, int(limit))),
            ).fetchall()
            return [
                {
                    "meeting_id": row["meeting_id"],
                    "meeting_title": row["meeting_title"],
                    "window_id": row["window_id"],
                    "score": row["score"],
                    "keyword_hits": self._json_loads_list(row["keyword_hits_json"]),
                    "member_hits": self._json_loads_list(row["member_hits_json"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    # ── HS-158-01: Project Room aggregate CRUD ─────────────────────────

    def get_project_room_fields(self, project_id: str) -> Optional[dict[str, Any]]:
        """Load the Project Room columns for *project_id*.

        Returns None if the project does not exist.  Only the Room-era
        columns are returned; callers wanting the full legacy shape use
        ``get_project()``.
        """
        clean_id = str(project_id).strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT purpose, outcome_text, owner_ref, lifecycle,
                       posture, posture_reason, start_at, target_at,
                       review_cadence_json, next_review_at, template_key,
                       modules_json, revision, last_review_id, last_review_at
                FROM projects WHERE id = ?
                """,
                (clean_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "purpose": row["purpose"],
                "outcome_text": row["outcome_text"],
                "owner_ref": row["owner_ref"],
                "lifecycle": row["lifecycle"],
                "posture": row["posture"],
                "posture_reason": row["posture_reason"],
                "start_at": row["start_at"],
                "target_at": row["target_at"],
                "review_cadence_json": row["review_cadence_json"],
                "next_review_at": row["next_review_at"],
                "template_key": row["template_key"],
                "modules_json": row["modules_json"],
                "revision": row["revision"],
                "last_review_id": row["last_review_id"],
                "last_review_at": row["last_review_at"],
            }

    def update_project_room_fields(
        self,
        project_id: str,
        *,
        expected_revision: Optional[int] = None,
        **fields: Any,
    ) -> int:
        """Update Project Room columns and return the new revision.

        If *expected_revision* is given and does not match the current
        revision, raises ``ValueError`` (optimistic concurrency).
        Only Room-era fields are accepted; unknown keys are silently
        ignored.
        """
        clean_id = str(project_id).strip()
        if not clean_id:
            raise ValueError("project_id is required")

        allowed = {
            "purpose", "outcome_text", "owner_ref", "lifecycle",
            "posture", "posture_reason", "start_at", "target_at",
            "review_cadence_json", "next_review_at", "template_key",
            "modules_json", "last_review_id", "last_review_at",
        }
        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            updates.append(f"{key} = ?")
            params.append(value)
        if not updates:
            raise ValueError("no updatable fields supplied")

        with self._connection() as conn:
            if expected_revision is not None:
                current = conn.execute(
                    "SELECT revision FROM projects WHERE id = ?",
                    (clean_id,),
                ).fetchone()
                if current is None:
                    raise ValueError(f"project {clean_id} not found")
                if current["revision"] != expected_revision:
                    raise ValueError(
                        f"stale revision: expected {expected_revision}, "
                        f"got {current['revision']}"
                    )
            updates.append("revision = revision + 1")
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(clean_id)
            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return int(row["revision"])

    # ── project_items CRUD ───────────────────────────────────────────

    def insert_project_item(
        self,
        *,
        item_id: str,
        project_id: str,
        item_type: str,
        title: str = "",
        summary: Optional[str] = None,
        lifecycle: str = "open",
        severity: Optional[str] = None,
        owner_ref: Optional[str] = None,
        due_at: Optional[str] = None,
        sort_key: Optional[float] = None,
        details_json: Optional[str] = None,
        provenance_kind: Optional[str] = None,
        source_observation_id: Optional[str] = None,
        created_by_ref: Optional[str] = None,
    ) -> None:
        """Insert a Project item (workstream, milestone, risk, etc.)."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO project_items (
                    id, project_id, item_type, title, summary, lifecycle,
                    severity, owner_ref, due_at, sort_key, details_json,
                    provenance_kind, source_observation_id, created_by_ref,
                    revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    str(item_id).strip(),
                    str(project_id).strip(),
                    str(item_type).strip(),
                    str(title).strip(),
                    summary,
                    str(lifecycle).strip(),
                    severity,
                    owner_ref,
                    due_at,
                    sort_key,
                    details_json,
                    provenance_kind,
                    source_observation_id,
                    created_by_ref,
                    now_iso,
                    now_iso,
                ),
            )

    def get_project_item(self, item_id: str) -> Optional[dict[str, Any]]:
        """Load a single project item by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_items WHERE id = ?",
                (str(item_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_project_items(
        self, project_id: str, *, item_type: Optional[str] = None, limit: int = 200
    ) -> list[dict[str, Any]]:
        """List items for a project, optionally filtered by type."""
        clean_id = str(project_id).strip()
        if item_type:
            rows = self._execute_read(
                "SELECT * FROM project_items WHERE project_id = ? AND item_type = ? "
                "ORDER BY sort_key, created_at LIMIT ?",
                (clean_id, str(item_type).strip(), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_items WHERE project_id = ? "
                "ORDER BY item_type, sort_key, created_at LIMIT ?",
                (clean_id, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    def update_project_item(self, item_id: str, **fields: Any) -> None:
        """Update mutable fields on a project item."""
        allowed = {
            "title", "summary", "lifecycle", "severity", "owner_ref",
            "due_at", "sort_key", "details_json", "provenance_kind",
            "source_observation_id",
        }
        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            updates.append(f"{key} = ?")
            params.append(value)
        if not updates:
            return
        updates.append("revision = revision + 1")
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(str(item_id).strip())
        with self._connection() as conn:
            conn.execute(
                f"UPDATE project_items SET {', '.join(updates)} WHERE id = ?",
                params,
            )

    # ── project_changes CRUD ─────────────────────────────────────────

    def insert_project_change(
        self,
        *,
        change_id: str,
        project_id: str,
        project_revision: int,
        change_kind: str,
        target_ref: Optional[str] = None,
        actor_ref: Optional[str] = None,
        command_id: Optional[str] = None,
        before_hash: Optional[str] = None,
        after_hash: Optional[str] = None,
        summary_json: Optional[str] = None,
    ) -> None:
        """Append a change-log entry (append-only by convention)."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(change_id).strip(),
                    str(project_id).strip(),
                    int(project_revision),
                    str(change_kind).strip(),
                    target_ref,
                    actor_ref,
                    command_id,
                    before_hash,
                    after_hash,
                    summary_json,
                    now_iso,
                ),
            )

    def list_project_changes(
        self,
        project_id: str,
        *,
        since_revision: Optional[int] = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List changes for a project, optionally since a revision."""
        clean_id = str(project_id).strip()
        if since_revision is not None:
            rows = self._execute_read(
                "SELECT * FROM project_changes "
                "WHERE project_id = ? AND project_revision >= ? "
                "ORDER BY project_revision, created_at LIMIT ?",
                (clean_id, int(since_revision), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_changes WHERE project_id = ? "
                "ORDER BY project_revision DESC, created_at DESC LIMIT ?",
                (clean_id, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    # ── project_commands CRUD ────────────────────────────────────────

    def insert_project_command(
        self,
        *,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: Optional[str] = None,
        status: str = "pending",
    ) -> None:
        """Insert a new command (idempotency ledger entry)."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO project_commands (
                    id, project_id, command_kind, request_hash,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(command_id).strip(),
                    str(project_id).strip(),
                    str(command_kind).strip(),
                    request_hash,
                    str(status).strip(),
                    now_iso,
                ),
            )

    def get_project_command(self, command_id: str) -> Optional[dict[str, Any]]:
        """Load a command by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_commands WHERE id = ?",
                (str(command_id).strip(),),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def complete_project_command(
        self,
        command_id: str,
        *,
        status: str,
        result_json: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        """Mark a command completed (succeeded/failed)."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE project_commands
                SET status = ?, result_json = ?, error_code = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    str(status).strip(),
                    result_json,
                    error_code,
                    now_iso,
                    str(command_id).strip(),
                ),
            )

    def list_project_commands(
        self, project_id: str, *, status: Optional[str] = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List commands for a project, optionally filtered by status."""
        clean_id = str(project_id).strip()
        if status:
            rows = self._execute_read(
                "SELECT * FROM project_commands "
                "WHERE project_id = ? AND status = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (clean_id, str(status).strip(), max(1, int(limit))),
            )
        else:
            rows = self._execute_read(
                "SELECT * FROM project_commands WHERE project_id = ? "
                "ORDER BY created_at DESC LIMIT ?",
                (clean_id, max(1, int(limit))),
            )
        return [dict(r) for r in rows]

    # ── project_resources Room extensions ─────────────────────────────

    def update_resource_room_fields(
        self,
        project_id: str,
        resource_ref: str,
        *,
        semantic_role: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> None:
        """Update the Room-era fields on a project resource."""
        updates: list[str] = []
        params: list[Any] = []
        if semantic_role is not None:
            updates.append("semantic_role = ?")
            params.append(semantic_role)
        if metadata_json is not None:
            updates.append("metadata_json = ?")
            params.append(metadata_json)
        if not updates:
            return
        updates.append("revision = revision + 1")
        updates.append("last_modified = ?")
        params.append(datetime.now().isoformat())
        params.extend([str(project_id).strip(), str(resource_ref).strip()])
        with self._connection() as conn:
            conn.execute(
                f"UPDATE project_resources SET {', '.join(updates)} "
                "WHERE project_id = ? AND resource_ref = ?",
                params,
            )

    # ── internal helpers ─────────────────────────────────────────────

    def _execute_read(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[sqlite3.Row]:
        """Convenience: execute a read query and return all rows."""
        with self._connection() as conn:
            return conn.execute(sql, params).fetchall()

    def _row_to_project(self, row: sqlite3.Row) -> ProjectSummary:
        """Convert a DB row to a ProjectSummary."""
        return ProjectSummary(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            keywords=self._json_loads_list(row["keywords_json"]),
            team_members=self._json_loads_list(row["team_members_json"]),
            context=self._json_loads_dict(row["context_json"]),
            detection_threshold=float(row["detection_threshold"]),
            is_archived=bool(row["is_archived"]),
            meeting_count=int(row["meeting_count"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
