"""Transport-neutral project and relationship operations (HS-123-05).

HS-158-02 graduation: every accepted write increments projects.revision
exactly once, appends a project_changes row and a ServiceEventLedger event
in the same transaction (DOM-003, DOM-004, API-004).  Optional
expected_revision / command_id enforce optimistic concurrency (API-001)
and idempotent replay (API-002, DOM-010).  Absent params = legacy behavior
(API-006).
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from ..db.core import Database
from ..db.relationships import qualified_ref
from ..logging_config import get_logger
from ..meeting_aftercare import compute_project_since_last_meeting
from ..principals import Principal
from ..project_contracts import (
    CommandResultEnvelope,
    ProjectError,
    ProjectErrorCode,
    ResultKind,
    generate_pchg_id,
    generate_pcmd_id,
)
from ..refs import format as format_ref, parse as parse_ref
from .errors import ConflictError, NotFound, ValidationError
from .service_event_ledger import ServiceEventLedger

_log = get_logger("services.project_service")

# ── Room projection constants (HS-158-04, DB-005/NFR-001) ───────────────
# WEB-NOW-006 spirit: the focus block shows the top-N most urgent items.
ROOM_FOCUS_CAP: int = 5
# Recent changes shown in the room projection.
ROOM_CHANGES_CAP: int = 10

# Absent-section marker for domains not yet built (Art VI, NFR-006).
_ABSENT_SECTION: dict[str, str] = {"state": "absent", "reason": "not_yet_built"}


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash of a command's request payload (API-002)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _envelope_to_dict(env: CommandResultEnvelope) -> dict[str, Any]:
    """Serialize an envelope to a JSON-safe dict for storage/response."""
    return {
        "result_kind": env.result_kind.value,
        "project_id": env.project_id,
        "project_revision": env.project_revision,
        "changed_refs": [str(r) for r in env.changed_refs],
    }


@observe_service
class ProjectService:
    """The durable project boundary; routes only parse and serialize."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        self._ledger = ServiceEventLedger(db)

    # ── reads (unchanged) ────────────────────────────────────────────

    def list_projects(self, principal: Principal, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        return [self._project_payload(project) for project in self._db.projects.list_projects(
            include_archived=bool(filters.get("include_archived", False))
        )]

    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return self._project_payload(self._require_project(project_id))

    def list_briefings(self, principal: Principal, project_id: str, limit: int = 50) -> dict[str, Any]:
        self._require_project(project_id)
        clean_limit = max(1, min(int(limit), 200))
        annotations = self._db.activity.list_activity_annotations(
            source_connector_id="meeting_context", annotation_type="meeting_context_briefing",
            limit=max(clean_limit * 4, 100),
        )
        rows = [{"id": ann.id, "title": ann.title, "value": ann.value,
                 "created_at": ann.created_at.isoformat(), "updated_at": ann.updated_at.isoformat()}
                for ann in annotations if isinstance(ann.value, dict) and ann.value.get("project_id") == project_id]
        return {"project_id": project_id, "briefings": rows[:clean_limit]}

    def list_meetings(self, principal: Principal, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return self._db.projects.get_project_meetings(project_id, limit=limit, offset=offset)

    def list_resources(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [row.to_dict() for row in self._db.project_relationships.list_for_project(project_id)]

    def list_resource_relationships(self, principal: Principal, resource_ref: str) -> dict[str, Any]:
        ref = qualified_ref(resource_ref)
        placement = self._db.directory_memberships.get(ref)
        return {"resource_ref": ref, "zone": placement.to_dict() if placement else None,
                "knowledge": [row.to_dict() for row in self._db.knowledge_memberships.list_for_resource(ref)],
                "projects": [row.to_dict() for row in self._db.project_relationships.list_for_resource(ref)],
                "explanations": {"zone": "Where this object lives; exactly one Zone or the Desk root.",
                                 "knowledge": "Reusable collections this object informs; membership does not move it.",
                                 "projects": "Work this object supports; a relationship does not file or copy it."}}

    def list_meeting_projects(self, principal: Principal, meeting_id: str) -> list[dict[str, Any]]:
        self._require_meeting(meeting_id)
        return self._db.projects.get_meeting_projects(meeting_id)

    def since_last_meeting(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return compute_project_since_last_meeting(self._db, project_id) or {}

    def summary(self, principal: Principal, project_id: str) -> dict[str, Any]:
        self._require_project(project_id)
        return self._db.projects.get_project_summary(project_id)

    def list_action_items(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "task": item.task, "owner": item.owner, "due": item.due,
                 "status": item.status, "review_state": item.review_state,
                 "source_timestamp": item.source_timestamp, "meeting_id": item.meeting_id,
                 "meeting_title": item.meeting_title, "meeting_date": item.meeting_date.isoformat(),
                 "created_at": item.created_at.isoformat(),
                 "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                 "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None}
                for item in self._db.projects.get_project_action_items(project_id)]

    def list_artifacts(self, principal: Principal, project_id: str) -> list[dict[str, Any]]:
        self._require_project(project_id)
        return [{"id": item.id, "meeting_id": item.meeting_id, "artifact_type": item.artifact_type,
                 "title": item.title, "body_markdown": item.body_markdown, "confidence": item.confidence,
                 "status": item.status, "plugin_id": item.plugin_id, "created_at": item.created_at.isoformat()}
                for item in self._db.projects.get_project_artifacts(project_id)]

    # ── room projection (HS-158-04, SS6.2) ────────────────────────────

    def room(self, principal: Principal, project_id: str) -> dict[str, Any]:
        """Coherent, revision-stamped room projection (SS6.2, HS-158-04).

        Returns one dict with every section the first useful render needs.
        Per-section fault isolation (NFR-003): each sub-read is wrapped;
        a failure degrades that section without failing the response.
        404 only when the project itself is missing.

        observed_at is derived from project.updated_at (fully deterministic:
        two reads with no writes in between produce byte-identical payloads).

        Focus ordering (DB-005): severity DESC NULLS LAST, due_at ASC
        NULLS LAST, sort_key ASC NULLS LAST, created_at ASC, id ASC.
        """
        project = self._require_project(project_id)
        room_fields = self._db.projects.get_project_room_fields(project_id)

        # Orientation: identity + SS5.1 fields + revision + is_archived
        orientation = self._project_payload(project)
        revision = 0
        if room_fields:
            orientation["purpose"] = room_fields["purpose"]
            orientation["outcome_text"] = room_fields["outcome_text"]
            orientation["owner_ref"] = room_fields["owner_ref"]
            orientation["lifecycle"] = room_fields["lifecycle"]
            orientation["posture"] = room_fields["posture"]
            orientation["posture_reason"] = room_fields["posture_reason"]
            orientation["start_at"] = room_fields["start_at"]
            orientation["target_at"] = room_fields["target_at"]
            orientation["review_cadence_json"] = room_fields["review_cadence_json"]
            orientation["next_review_at"] = room_fields["next_review_at"]
            orientation["template_key"] = room_fields["template_key"]
            orientation["modules_json"] = room_fields["modules_json"]
            orientation["revision"] = room_fields["revision"]
            orientation["last_review_id"] = room_fields["last_review_id"]
            orientation["last_review_at"] = room_fields["last_review_at"]
            revision = room_fields["revision"] or 0

        # observed_at: derived from project.updated_at for full determinism
        observed_at = project.updated_at.isoformat()

        return {
            "project_id": project_id,
            "revision": revision,
            "observed_at": observed_at,
            "project": orientation,
            "items": self._room_section(
                "items", lambda: self._read_room_items(project_id)),
            "meetings": self._room_section(
                "meetings", lambda: self._read_room_meetings(
                    principal, project_id, project)),
            "resources": self._room_section(
                "resources", lambda: self._read_room_resources(project_id)),
            "changes": self._room_section(
                "changes", lambda: self._read_room_changes(project_id)),
            "review": dict(_ABSENT_SECTION),
            "sources": dict(_ABSENT_SECTION),
            "updates": dict(_ABSENT_SECTION),
            "steward": dict(_ABSENT_SECTION),
        }

    # ── room sub-readers (fault-isolated) ────────────────────────────

    @staticmethod
    def _room_section(name: str, fn: Any) -> dict[str, Any]:
        """Run *fn* and tag the result with state=ok, or return degraded."""
        try:
            result = fn()
            result["state"] = "ok"
            return result
        except Exception as exc:
            _log.warning("room section %s degraded: %s", name, exc)
            return {"state": "degraded", "error_code": f"{name}_read_failed"}

    def _read_room_items(self, project_id: str) -> dict[str, Any]:
        """Focus block: bounded top-N items + total counts per type."""
        with self._db._connection() as conn:
            count_rows = conn.execute(
                "SELECT item_type, COUNT(*) as cnt FROM project_items "
                "WHERE project_id = ? GROUP BY item_type",
                (project_id,),
            ).fetchall()
            totals_by_type = {row["item_type"]: row["cnt"] for row in count_rows}
            total = sum(totals_by_type.values())

            # Focus: bounded, deterministically ordered (DB-005)
            # Order: severity DESC NULLS LAST, due_at ASC NULLS LAST,
            #        sort_key ASC NULLS LAST, created_at ASC, id ASC
            focus_rows = conn.execute(
                """
                SELECT * FROM project_items WHERE project_id = ?
                ORDER BY
                    severity IS NULL, severity DESC,
                    due_at IS NULL, due_at ASC,
                    sort_key IS NULL, sort_key ASC,
                    created_at ASC,
                    id ASC
                LIMIT ?
                """,
                (project_id, ROOM_FOCUS_CAP),
            ).fetchall()
        return {
            "focus": [dict(r) for r in focus_rows],
            "totals_by_type": totals_by_type,
            "total": total,
        }

    def _read_room_meetings(
        self, principal: Principal, project_id: str, project: Any,
    ) -> dict[str, Any]:
        """Meetings summary: count + latest."""
        count = project.meeting_count
        latest_list = self.list_meetings(principal, project_id, limit=1)
        return {
            "count": count,
            "latest": latest_list[0] if latest_list else None,
        }

    def _read_room_resources(self, project_id: str) -> dict[str, Any]:
        """Resources summary: count + latest linked."""
        resource_objs = self._db.project_relationships.list_for_project(
            project_id)
        count = len(resource_objs)
        return {
            "count": count,
            "latest": resource_objs[0].to_dict() if resource_objs else None,
        }

    def _read_room_changes(self, project_id: str) -> dict[str, Any]:
        """Recent changes, bounded, newest first."""
        changes = self._db.projects.list_project_changes(
            project_id, limit=ROOM_CHANGES_CAP)
        return {"recent": changes}

    # ── writes (graduated to revision law) ───────────────────────────

    def create_project(
        self, principal: Principal, payload: dict[str, Any],
        *, command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")
        threshold = self._threshold(payload.get("detection_threshold", 0.4))

        # Idempotency check (API-002)
        req_hash = _request_hash(payload)
        replay = self._check_idempotency(command_id, req_hash, "create_project")
        if replay is not None:
            return replay

        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        new_revision = 1  # first revision for a new project

        with self._db._connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, revision, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id, name,
                    str(payload.get("description") or ""),
                    json.dumps(self._strings(payload.get("keywords")), ensure_ascii=False),
                    json.dumps(self._strings(payload.get("team_members")), ensure_ascii=False),
                    json.dumps(payload.get("context") or {}, ensure_ascii=False),
                    threshold,
                    new_revision,
                    now_iso, now_iso,
                ),
            )

            # Change log (DOM-003)
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            project_ref = format_ref("project", project_id)
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.created",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash({"name": name}),
                    json.dumps({"name": name}),
                    now_iso,
                ),
            )

            # Service event (API-004)
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.created",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "name": name},
                refs=[project_ref],
            )

            # Command ledger (API-002)
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.CREATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "create_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def update_project(
        self, principal: Principal, project_id: str, patch: dict[str, Any],
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)

        # Idempotency check
        req_hash = _request_hash({"project_id": project_id, **patch})
        replay = self._check_idempotency(command_id, req_hash, "update_project")
        if replay is not None:
            return replay

        fields: dict[str, Any] = {}
        if "name" in patch:
            name = str(patch["name"] or "").strip()
            if not name:
                raise ValidationError("Project name cannot be empty")
            fields["name"] = name
        if "description" in patch:
            fields["description"] = str(patch["description"] or "")
        if "keywords" in patch:
            fields["keywords"] = self._strings(patch["keywords"])
        if "team_members" in patch:
            fields["team_members"] = self._strings(patch["team_members"])
        if "context" in patch:
            fields["context"] = patch["context"] or {}
        if "detection_threshold" in patch:
            fields["detection_threshold"] = self._threshold(patch["detection_threshold"])

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            # Revision check (API-001)
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1

            # Apply the legacy field updates
            updates: list[str] = []
            params: list[Any] = []
            for key, value in fields.items():
                if key == "name":
                    updates.append("name = ?")
                    params.append(value)
                elif key == "description":
                    updates.append("description = ?")
                    params.append(value)
                elif key == "keywords":
                    updates.append("keywords_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "team_members":
                    updates.append("team_members_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "context":
                    updates.append("context_json = ?")
                    params.append(json.dumps(value, ensure_ascii=False))
                elif key == "detection_threshold":
                    updates.append("detection_threshold = ?")
                    params.append(max(0.0, min(1.0, float(value))))

            updates.append("revision = ?")
            params.append(new_revision)
            updates.append("updated_at = ?")
            params.append(now_iso)
            params.append(project_id)
            if updates:
                conn.execute(
                    f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                    params,
                )

            # Change log
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, _request_hash(fields),
                    json.dumps({"fields": list(fields.keys())}),
                    now_iso,
                ),
            )

            # Event
            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "fields": list(fields.keys())},
                refs=[project_ref],
            )

            # Command
            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "update_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def archive_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "archive"})
        replay = self._check_idempotency(command_id, req_hash, "archive_project")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 1, lifecycle = 'archived', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.archived",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "archived"}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.archived",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.ARCHIVED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "archive_project",
                req_hash, envelope,
            )

        return True

    def restore_project(
        self, principal: Principal, project_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Restore an archived Project (DOM-011).

        If the project is not archived, returns a no_change result
        (API-002's honest reply).
        """
        project = self._require_project(project_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id, "action": "restore"})
        replay = self._check_idempotency(command_id, req_hash, "restore_project")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        if not project.is_archived:
            # Not archived -- no-op per API-002
            with self._db._connection() as conn:
                current_rev = self._get_revision(conn, project_id)
                envelope = CommandResultEnvelope(
                    result_kind=ResultKind.NO_CHANGE,
                    project_id=project_id,
                    project_revision=current_rev,
                )
                self._record_command(
                    conn, cmd_id, project_id, "restore_project",
                    req_hash, envelope,
                )
            result = self._project_payload(project)
            result.update(_envelope_to_dict(envelope))
            return result

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET is_archived = 0, lifecycle = 'active', "
                "revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.restored",
                    project_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"lifecycle": "active"}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.restored",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id},
                refs=[project_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.RESTORED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "restore_project",
                req_hash, envelope,
            )

        result = self._project_payload(self._require_project(project_id))
        result.update(_envelope_to_dict(envelope))
        return result

    def add_resource(
        self, principal: Principal, project_id: str,
        resource_ref: str, payload: dict[str, Any] | None = None,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._require_project(project_id)
        body = payload or {}
        ref_str = qualified_ref(resource_ref)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, **body})
        replay = self._check_idempotency(command_id, req_hash, "add_resource")
        if replay is not None:
            return replay

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

        # The upsert through the repo layer (its own connection/transaction)
        row = self._db.project_relationships.upsert(
            project_id=project_id, resource_ref=ref_str,
            relationship=str(body.get("relationship") or "member"),
            source="manual", confidence=1.0,
        )

        with self._db._connection() as conn:
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.linked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.linked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.LINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "add_resource",
                req_hash, envelope,
            )

        result = row.to_dict()
        result.update(_envelope_to_dict(envelope))
        return result

    def remove_resource(
        self, principal: Principal, project_id: str, resource_ref: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        self._require_project(project_id)
        ref_str = qualified_ref(resource_ref)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "resource_ref": ref_str, "action": "remove"})
        replay = self._check_idempotency(command_id, req_hash, "remove_resource")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

        deleted = self._db.project_relationships.delete(project_id, ref_str)

        with self._db._connection() as conn:
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision,
                    "project.resource.unlinked",
                    ref_str,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"resource_ref": ref_str}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.resource.unlinked",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={"project_id": project_id, "resource_ref": ref_str},
                refs=[project_ref, ref_str],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UNLINKED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(parse_ref(project_ref),),
            )
            self._record_command(
                conn, cmd_id, project_id, "remove_resource",
                req_hash, envelope,
            )

        return deleted

    def associate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Associate a meeting with a project.

        Meeting association event decision: SRS SS10 does NOT define a
        project.meeting.linked event kind.  We emit project.updated with
        the meeting ref in changed_refs/summary, since the association
        is a project mutation (it changes the project's meeting set) but
        is not a resource link (meetings have their own association table).
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "associate"})
        replay = self._check_idempotency(command_id, req_hash, "associate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

        # The legacy repo layer does its own connection
        self._db.projects.associate_meeting_project(
            meeting_id=meeting_id, project_id=project_id,
            source="manual", confidence=1.0,
        )

        with self._db._connection() as conn:
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_associated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_associated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "associate_meeting",
                req_hash, envelope,
            )

        return True

    def disassociate_meeting(
        self, principal: Principal, project_id: str, meeting_id: str,
        *, expected_revision: Optional[int] = None,
        command_id: Optional[str] = None,
    ) -> bool:
        """Disassociate a meeting from a project.

        Same event decision as associate_meeting: project.updated.
        """
        self._require_project(project_id)
        self._require_meeting(meeting_id)

        # Idempotency
        req_hash = _request_hash({"project_id": project_id,
                                  "meeting_id": meeting_id,
                                  "action": "disassociate"})
        replay = self._check_idempotency(command_id, req_hash, "disassociate_meeting")
        if replay is not None:
            return True

        cmd_id = command_id or generate_pcmd_id()
        now_iso = datetime.now().isoformat()
        project_ref = format_ref("project", project_id)
        meeting_ref = format_ref("meeting", meeting_id)

        with self._db._connection() as conn:
            current_rev = self._get_revision(conn, project_id)
            if expected_revision is not None and current_rev != expected_revision:
                raise ConflictError(
                    f"stale revision: expected {expected_revision}, got {current_rev}",
                    code="stale_revision",
                    context={
                        "expected_revision": expected_revision,
                        "current_revision": current_rev,
                    },
                )

            new_revision = current_rev + 1
            conn.execute(
                "UPDATE projects SET revision = ?, updated_at = ? WHERE id = ?",
                (new_revision, now_iso, project_id),
            )

        self._db.projects.disassociate_meeting_project(
            meeting_id=meeting_id, project_id=project_id,
        )

        with self._db._connection() as conn:
            change_id = generate_pchg_id(
                project_id=project_id,
                project_revision=new_revision,
                ordinal=0,
            )
            conn.execute(
                """
                INSERT INTO project_changes (
                    id, project_id, project_revision, change_kind,
                    target_ref, actor_ref, command_id,
                    before_hash, after_hash, summary_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id, project_id, new_revision, "project.updated",
                    meeting_ref,
                    f"principal:{principal.identity}",
                    cmd_id, None, None,
                    json.dumps({"meeting_disassociated": meeting_id}),
                    now_iso,
                ),
            )

            self._ledger.append_in_transaction(
                conn, principal,
                event_type="project.updated",
                producer="ProjectService",
                subject_ref=project_ref,
                source_revision=str(new_revision),
                facts={
                    "project_id": project_id,
                    "meeting_disassociated": meeting_id,
                },
                refs=[project_ref, meeting_ref],
            )

            envelope = CommandResultEnvelope(
                result_kind=ResultKind.UPDATED,
                project_id=project_id,
                project_revision=new_revision,
                changed_refs=(
                    parse_ref(project_ref),
                    parse_ref(meeting_ref),
                ),
            )
            self._record_command(
                conn, cmd_id, project_id, "disassociate_meeting",
                req_hash, envelope,
            )

        return True

    # ── internal helpers ─────────────────────────────────────────────

    def _require_project(self, project_id: str) -> Any:
        project = self._db.projects.get_project(project_id)
        if project is None:
            raise NotFound("project", project_id)
        return project

    def _require_meeting(self, meeting_id: str) -> Any:
        meeting = self._db.meetings.get_meeting(meeting_id)
        if meeting is None:
            raise NotFound("meeting", meeting_id)
        return meeting

    @staticmethod
    def _strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value or []

    @staticmethod
    def _threshold(value: Any) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError("detection_threshold must be between 0 and 1") from exc
        if not 0.0 <= threshold <= 1.0:
            raise ValidationError("detection_threshold must be between 0 and 1")
        return threshold

    @staticmethod
    def _project_payload(project: Any) -> dict[str, Any]:
        return {"id": project.id, "name": project.name, "description": project.description,
                "keywords": project.keywords, "team_members": project.team_members, "context": project.context,
                "detection_threshold": project.detection_threshold, "is_archived": project.is_archived,
                "meeting_count": project.meeting_count, "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()}

    def _get_revision(self, conn: Any, project_id: str) -> int:
        """Read the current revision inside an open transaction."""
        row = conn.execute(
            "SELECT revision FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise NotFound("project", project_id)
        return int(row["revision"])

    def _check_idempotency(
        self, command_id: Optional[str], req_hash: str, command_kind: str,
    ) -> Optional[dict[str, Any]]:
        """API-002: if command_id is given, check for replay or conflict.

        Returns stored result dict on replay, None on new command.
        Raises ConflictError on hash mismatch.
        """
        if command_id is None:
            return None
        existing = self._db.projects.get_project_command(command_id)
        if existing is None:
            return None
        if existing["status"] == "completed" and existing["request_hash"] == req_hash:
            # Replay: return stored result
            if existing["result_json"]:
                return json.loads(existing["result_json"])
            return {"result_kind": "no_change", "project_id": existing["project_id"]}
        if existing["request_hash"] != req_hash:
            raise ConflictError(
                "idempotency conflict: same command_id with different request hash",
                code="idempotency_conflict",
                context={"command_id": command_id},
            )
        # Pending command with same hash -- proceed (could be a retry after crash)
        return None

    def _record_command(
        self,
        conn: Any,
        command_id: str,
        project_id: str,
        command_kind: str,
        request_hash: str,
        envelope: CommandResultEnvelope,
    ) -> None:
        """Record a completed command in the idempotency ledger."""
        now_iso = datetime.now().isoformat()
        result_json = json.dumps(_envelope_to_dict(envelope), ensure_ascii=False)
        conn.execute(
            """
            INSERT INTO project_commands (
                id, project_id, command_kind, request_hash,
                status, result_json, completed_at, created_at
            ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status = 'completed',
                result_json = excluded.result_json,
                completed_at = excluded.completed_at
            """,
            (
                command_id, project_id, command_kind, request_hash,
                result_json, now_iso, now_iso,
            ),
        )
