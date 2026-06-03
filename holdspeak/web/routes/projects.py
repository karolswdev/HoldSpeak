"""Project KB / association routes (HS-26-05).

Project CRUD, meeting<->project association, per-project summary / action-items /
artifacts, the cross-meeting briefings timeline, and a meeting's project list.
Handlers move verbatim (`self._project_detector` -> `ctx.project_detector`).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projects")


def build_projects_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/projects/{project_id}/briefings")
    async def api_list_project_briefings(
        project_id: str,
        limit: int = 50,
    ) -> Any:
        """HS-13-09: per-project meeting_context timeline.

        Returns every meeting_context briefing whose
        `value.project_id` matches, ordered newest first.
        The /history Projects-tab panel walks this for the
        cross-meeting narrative.
        """
        from ...db import get_database

        try:
            clean_limit = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            clean_limit = 50
        try:
            db = get_database()
            if db.projects.get_project(project_id) is None:
                return JSONResponse(
                    {"error": f"Unknown project: {project_id}"},
                    status_code=404,
                )
            annotations = db.activity.list_activity_annotations(
                source_connector_id="meeting_context",
                annotation_type="meeting_context_briefing",
                limit=max(clean_limit * 4, 100),
            )
            rows = []
            for ann in annotations:
                if not isinstance(ann.value, dict):
                    continue
                if ann.value.get("project_id") != project_id:
                    continue
                rows.append(
                    {
                        "id": ann.id,
                        "title": ann.title,
                        "value": ann.value,
                        "created_at": ann.created_at.isoformat(),
                        "updated_at": ann.updated_at.isoformat(),
                    }
                )
                if len(rows) >= clean_limit:
                    break
            return JSONResponse(
                {"project_id": project_id, "briefings": rows}
            )
        except Exception as e:
            return error_500(e, log, "Failed to list project briefings")

    @router.get("/api/projects")
    async def api_list_projects(include_archived: bool = False) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            projects = db.projects.list_projects(include_archived=include_archived)
            return JSONResponse({
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "keywords": p.keywords,
                        "team_members": p.team_members,
                        "context": p.context,
                        "detection_threshold": p.detection_threshold,
                        "is_archived": p.is_archived,
                        "meeting_count": p.meeting_count,
                        "created_at": p.created_at.isoformat(),
                        "updated_at": p.updated_at.isoformat(),
                    }
                    for p in projects
                ]
            })
        except Exception as e:
            return error_500(e, log, "Failed to list projects")

    @router.post("/api/projects")
    async def api_create_project(payload: dict[str, Any]) -> Any:
        try:
            import uuid
            from ...db import get_database
            db = get_database()
            name = str(payload.get("name") or "").strip()
            if not name:
                return JSONResponse(
                    {"success": False, "error": "Project name is required"},
                    status_code=400,
                )
            project_id = f"proj-{uuid.uuid4().hex[:12]}"
            keywords = payload.get("keywords") or []
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            team_members = payload.get("team_members") or []
            if isinstance(team_members, str):
                team_members = [m.strip() for m in team_members.split(",") if m.strip()]
            threshold = float(payload.get("detection_threshold", 0.4))
            if not (0.0 <= threshold <= 1.0):
                return JSONResponse(
                    {"success": False, "error": "detection_threshold must be between 0 and 1"},
                    status_code=400,
                )
            db.projects.create_project(
                project_id=project_id,
                name=name,
                description=str(payload.get("description") or ""),
                keywords=keywords,
                team_members=team_members,
                context=payload.get("context") or {},
                detection_threshold=threshold,
            )
            # Reload detector
            if ctx.project_detector is not None:
                ctx.project_detector.reload_projects(
                    db.projects.get_all_projects_for_detector()
                )
            project = db.projects.get_project(project_id)
            return JSONResponse({
                "success": True,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "keywords": project.keywords,
                    "team_members": project.team_members,
                    "context": project.context,
                    "detection_threshold": project.detection_threshold,
                    "is_archived": project.is_archived,
                    "meeting_count": project.meeting_count,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                } if project else None,
            })
        except Exception as e:
            log.error(f"Failed to create project: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/projects/{project_id}")
    async def api_get_project(project_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            project = db.projects.get_project(project_id)
            if not project:
                return JSONResponse({"error": "Project not found"}, status_code=404)
            return JSONResponse({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "keywords": project.keywords,
                "team_members": project.team_members,
                "context": project.context,
                "detection_threshold": project.detection_threshold,
                "is_archived": project.is_archived,
                "meeting_count": project.meeting_count,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            })
        except Exception as e:
            return error_500(e, log, "Failed to get project")

    @router.patch("/api/projects/{project_id}")
    async def api_update_project(project_id: str, payload: dict[str, Any]) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            existing = db.projects.get_project(project_id)
            if not existing:
                return JSONResponse(
                    {"success": False, "error": "Project not found"},
                    status_code=404,
                )
            update_fields: dict[str, Any] = {}
            if "name" in payload:
                name = str(payload["name"]).strip()
                if not name:
                    return JSONResponse(
                        {"success": False, "error": "Project name cannot be empty"},
                        status_code=400,
                    )
                update_fields["name"] = name
            if "description" in payload:
                update_fields["description"] = str(payload["description"] or "")
            if "keywords" in payload:
                kw = payload["keywords"]
                if isinstance(kw, str):
                    kw = [k.strip() for k in kw.split(",") if k.strip()]
                update_fields["keywords"] = kw
            if "team_members" in payload:
                tm = payload["team_members"]
                if isinstance(tm, str):
                    tm = [m.strip() for m in tm.split(",") if m.strip()]
                update_fields["team_members"] = tm
            if "context" in payload:
                update_fields["context"] = payload["context"] or {}
            if "detection_threshold" in payload:
                threshold = float(payload["detection_threshold"])
                if not (0.0 <= threshold <= 1.0):
                    return JSONResponse(
                        {"success": False, "error": "detection_threshold must be between 0 and 1"},
                        status_code=400,
                    )
                update_fields["detection_threshold"] = threshold
            if update_fields:
                db.projects.update_project(project_id, **update_fields)
            # Reload detector
            if ctx.project_detector is not None:
                ctx.project_detector.reload_projects(
                    db.projects.get_all_projects_for_detector()
                )
            updated = db.projects.get_project(project_id)
            return JSONResponse({
                "success": True,
                "project": {
                    "id": updated.id,
                    "name": updated.name,
                    "description": updated.description,
                    "keywords": updated.keywords,
                    "team_members": updated.team_members,
                    "context": updated.context,
                    "detection_threshold": updated.detection_threshold,
                    "is_archived": updated.is_archived,
                    "meeting_count": updated.meeting_count,
                    "created_at": updated.created_at.isoformat(),
                    "updated_at": updated.updated_at.isoformat(),
                } if updated else None,
            })
        except Exception as e:
            log.error(f"Failed to update project: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.delete("/api/projects/{project_id}")
    async def api_archive_project(project_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            existing = db.projects.get_project(project_id)
            if not existing:
                return JSONResponse(
                    {"success": False, "error": "Project not found"},
                    status_code=404,
                )
            db.projects.update_project(project_id, is_archived=True)
            if ctx.project_detector is not None:
                ctx.project_detector.reload_projects(
                    db.projects.get_all_projects_for_detector()
                )
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to archive project: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/projects/{project_id}/meetings")
    async def api_project_meetings(
        project_id: str, limit: int = 50, offset: int = 0
    ) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            meetings = db.projects.get_project_meetings(project_id, limit=limit, offset=offset)
            return JSONResponse({"meetings": meetings})
        except Exception as e:
            return error_500(e, log, "Failed to get project meetings")

    @router.post("/api/projects/{project_id}/meetings/{meeting_id}")
    async def api_associate_meeting(project_id: str, meeting_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            db.projects.associate_meeting_project(
                meeting_id=meeting_id,
                project_id=project_id,
                source="manual",
                confidence=1.0,
            )
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to associate meeting: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.delete("/api/projects/{project_id}/meetings/{meeting_id}")
    async def api_disassociate_meeting(project_id: str, meeting_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            db.projects.disassociate_meeting_project(
                meeting_id=meeting_id,
                project_id=project_id,
            )
            return JSONResponse({"success": True})
        except Exception as e:
            log.error(f"Failed to disassociate meeting: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @router.get("/api/meetings/{meeting_id}/projects")
    async def api_meeting_projects(meeting_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            projects = db.projects.get_meeting_projects(meeting_id)
            return JSONResponse({"projects": projects})
        except Exception as e:
            return error_500(e, log, "Failed to get meeting projects")

    @router.get("/api/projects/{project_id}/summary")
    async def api_project_summary(project_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            summary = db.projects.get_project_summary(project_id)
            return JSONResponse(summary)
        except Exception as e:
            return error_500(e, log, "Failed to get project summary")

    @router.get("/api/projects/{project_id}/action-items")
    async def api_project_action_items(project_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            items = db.projects.get_project_action_items(project_id)
            return JSONResponse({
                "action_items": [
                    {
                        "id": ai.id,
                        "task": ai.task,
                        "owner": ai.owner,
                        "due": ai.due,
                        "status": ai.status,
                        "review_state": ai.review_state,
                        "source_timestamp": ai.source_timestamp,
                        "meeting_id": ai.meeting_id,
                        "meeting_title": ai.meeting_title,
                        "meeting_date": ai.meeting_date.isoformat(),
                        "created_at": ai.created_at.isoformat(),
                        "completed_at": ai.completed_at.isoformat() if ai.completed_at else None,
                        "reviewed_at": ai.reviewed_at.isoformat() if ai.reviewed_at else None,
                    }
                    for ai in items
                ]
            })
        except Exception as e:
            return error_500(e, log, "Failed to get project action items")

    @router.get("/api/projects/{project_id}/artifacts")
    async def api_project_artifacts(project_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            artifacts = db.projects.get_project_artifacts(project_id)
            return JSONResponse({
                "artifacts": [
                    {
                        "id": a.id,
                        "meeting_id": a.meeting_id,
                        "artifact_type": a.artifact_type,
                        "title": a.title,
                        "body_markdown": a.body_markdown,
                        "confidence": a.confidence,
                        "status": a.status,
                        "plugin_id": a.plugin_id,
                        "created_at": a.created_at.isoformat(),
                    }
                    for a in artifacts
                ]
            })
        except Exception as e:
            return error_500(e, log, "Failed to get project artifacts")

    return router
