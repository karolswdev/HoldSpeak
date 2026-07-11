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
    ) -> None:
        """Insert a new project knowledge base."""
        clean_id = str(project_id).strip()
        clean_name = str(name).strip()
        if not clean_id:
            raise ValueError("project_id is required")
        if not clean_name:
            raise ValueError("project name is required")
        threshold = max(0.0, min(1.0, float(detection_threshold)))
        now_iso = datetime.now().isoformat()
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
        params.append(datetime.now().isoformat())
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
