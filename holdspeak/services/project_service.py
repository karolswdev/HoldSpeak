"""Transport-neutral project and relationship operations (HS-123-05)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import uuid
from typing import Any

from ..db.core import Database
from ..db.relationships import qualified_ref
from ..meeting_aftercare import compute_project_since_last_meeting
from ..principals import Principal
from .errors import NotFound, ValidationError


@observe_service
class ProjectService:
    """The durable project boundary; routes only parse and serialize."""

    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    def list_projects(self, principal: Principal, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        return [self._project_payload(project) for project in self._db.projects.list_projects(
            include_archived=bool(filters.get("include_archived", False))
        )]

    def create_project(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ValidationError("Project name is required")
        threshold = self._threshold(payload.get("detection_threshold", 0.4))
        project_id = f"proj-{uuid.uuid4().hex[:12]}"
        self._db.projects.create_project(
            project_id=project_id, name=name,
            description=str(payload.get("description") or ""),
            keywords=self._strings(payload.get("keywords")),
            team_members=self._strings(payload.get("team_members")),
            context=payload.get("context") or {}, detection_threshold=threshold,
        )
        return self._project_payload(self._require_project(project_id))

    def get_project(self, principal: Principal, project_id: str) -> dict[str, Any]:
        return self._project_payload(self._require_project(project_id))

    def update_project(self, principal: Principal, project_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        self._require_project(project_id)
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
        if fields:
            self._db.projects.update_project(project_id, **fields)
        return self._project_payload(self._require_project(project_id))

    def archive_project(self, principal: Principal, project_id: str) -> bool:
        self._require_project(project_id)
        self._db.projects.update_project(project_id, is_archived=True)
        return True

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

    def add_resource(self, principal: Principal, project_id: str, resource_ref: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._require_project(project_id)
        body = payload or {}
        row = self._db.project_relationships.upsert(
            project_id=project_id, resource_ref=qualified_ref(resource_ref),
            relationship=str(body.get("relationship") or "member"), source="manual", confidence=1.0,
        )
        return row.to_dict()

    def remove_resource(self, principal: Principal, project_id: str, resource_ref: str) -> bool:
        self._require_project(project_id)
        return self._db.project_relationships.delete(project_id, qualified_ref(resource_ref))

    def list_resource_relationships(self, principal: Principal, resource_ref: str) -> dict[str, Any]:
        ref = qualified_ref(resource_ref)
        placement = self._db.directory_memberships.get(ref)
        return {"resource_ref": ref, "zone": placement.to_dict() if placement else None,
                "knowledge": [row.to_dict() for row in self._db.knowledge_memberships.list_for_resource(ref)],
                "projects": [row.to_dict() for row in self._db.project_relationships.list_for_resource(ref)],
                "explanations": {"zone": "Where this object lives; exactly one Zone or the Desk root.",
                                 "knowledge": "Reusable collections this object informs; membership does not move it.",
                                 "projects": "Work this object supports; a relationship does not file or copy it."}}

    def associate_meeting(self, principal: Principal, project_id: str, meeting_id: str) -> bool:
        self._require_project(project_id)
        self._require_meeting(meeting_id)
        self._db.projects.associate_meeting_project(meeting_id=meeting_id, project_id=project_id, source="manual", confidence=1.0)
        return True

    def disassociate_meeting(self, principal: Principal, project_id: str, meeting_id: str) -> bool:
        self._require_project(project_id)
        self._require_meeting(meeting_id)
        self._db.projects.disassociate_meeting_project(meeting_id=meeting_id, project_id=project_id)
        return True

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
