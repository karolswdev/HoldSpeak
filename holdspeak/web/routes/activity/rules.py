"""Activity project-rule routes — HS-34-02 split of `activity.py`.

`/api/activity/project-rules*` (CRUD + preview + apply). The rule/record payload
shapers and `_model_fields_set` are used only by this group.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import _ActivityProjectRuleRequest
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.activity")


def _model_fields_set(model: Any) -> set[str]:
    fields = getattr(model, "model_fields_set", None)
    if fields is not None:
        return set(fields)
    fields = getattr(model, "__fields_set__", None)
    if fields is not None:
        return set(fields)
    return set()


def _activity_project_rule_payload(rule: Any) -> dict[str, Any]:
    return {
        "id": rule.id,
        "project_id": rule.project_id,
        "project_name": rule.project_name,
        "name": rule.name,
        "enabled": rule.enabled,
        "priority": rule.priority,
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "entity_type": rule.entity_type,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }


def _activity_record_payload(record: Any) -> dict[str, Any]:
    return {
        "id": record.id,
        "source_browser": record.source_browser,
        "source_profile": record.source_profile,
        "url": record.url,
        "title": record.title,
        "domain": record.domain,
        "visit_count": record.visit_count,
        "first_seen_at": record.first_seen_at.isoformat() if record.first_seen_at else None,
        "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "project_id": record.project_id,
    }


def build_rules_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/activity/project-rules")
    async def api_activity_project_rules(include_disabled: bool = True) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            rules = db.activity.list_activity_project_rules(include_disabled=include_disabled)
            return JSONResponse({"rules": [_activity_project_rule_payload(rule) for rule in rules]})
        except Exception as e:
            return error_500(e, log, "Failed to list activity project rules")

    @router.post("/api/activity/project-rules")
    async def api_create_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            rule = db.activity.create_activity_project_rule(
                project_id=payload.project_id or "",
                name=payload.name or "",
                match_type=payload.match_type or "",
                pattern=payload.pattern or "",
                entity_type=payload.entity_type,
                priority=payload.priority if payload.priority is not None else 100,
                enabled=True if payload.enabled is None else payload.enabled,
            )
            return JSONResponse({"rule": _activity_project_rule_payload(rule)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to create activity project rule")

    @router.put("/api/activity/project-rules/{rule_id}")
    async def api_update_activity_project_rule(
        rule_id: str,
        payload: _ActivityProjectRuleRequest,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            fields: dict[str, Any] = {}
            present = _model_fields_set(payload)
            for key in (
                "project_id",
                "name",
                "enabled",
                "priority",
                "match_type",
                "pattern",
                "entity_type",
            ):
                if key in present:
                    fields[key] = getattr(payload, key)
            rule = db.activity.update_activity_project_rule(rule_id, **fields)
            if rule is None:
                return JSONResponse({"error": "activity project rule not found"}, status_code=404)
            return JSONResponse({"rule": _activity_project_rule_payload(rule)})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to update activity project rule")

    @router.delete("/api/activity/project-rules/{rule_id}")
    async def api_delete_activity_project_rule(rule_id: str) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            return JSONResponse({"deleted": db.activity.delete_activity_project_rule(rule_id)})
        except Exception as e:
            return error_500(e, log, "Failed to delete activity project rule")

    @router.post("/api/activity/project-rules/preview")
    async def api_preview_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            matches = db.activity.preview_activity_project_rule(
                project_id=payload.project_id or "",
                match_type=payload.match_type or "",
                pattern=payload.pattern or "",
                entity_type=payload.entity_type,
                limit=50,
            )
            return JSONResponse(
                {
                    "count": len(matches),
                    "matches": [_activity_record_payload(record) for record in matches],
                }
            )
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to preview activity project rule")

    @router.post("/api/activity/project-rules/apply")
    async def api_apply_activity_project_rules(limit: Optional[int] = None) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            updated = db.activity.apply_activity_project_rules(limit=limit)
            return JSONResponse({"updated": updated})
        except Exception as e:
            return error_500(e, log, "Failed to apply activity project rules")

    return router
