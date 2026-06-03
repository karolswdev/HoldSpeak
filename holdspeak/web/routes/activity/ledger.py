"""Activity-ledger routes — HS-34-02 split of `activity.py`.

`/api/activity/status`, `records` (get/delete), `refresh`, `settings`,
`domains` (post/delete) — the local activity-intelligence ledger basics.
`_activity_status_payload` is used only by this group (status/refresh/settings/
domains/records-delete all return a fresh status), so it lives here.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _ActivityDomainRuleRequest,
    _ActivitySettingsRequest,
)
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.activity")


def _activity_status_payload() -> dict[str, Any]:
    from ....activity_history import discover_browser_history_sources
    from ....db import get_database

    db = get_database()
    settings = db.activity.get_activity_privacy_settings()
    rules = db.activity.list_activity_domain_rules()
    checkpoints = db.activity.list_activity_import_checkpoints()
    checkpoint_payload = [
        {
            "source_browser": checkpoint.source_browser,
            "source_profile": checkpoint.source_profile,
            "source_path_hash": checkpoint.source_path_hash,
            "last_visit_raw": checkpoint.last_visit_raw,
            "last_imported_at": checkpoint.last_imported_at.isoformat() if checkpoint.last_imported_at else None,
            "last_error": checkpoint.last_error,
            "enabled": checkpoint.enabled,
        }
        for checkpoint in checkpoints
    ]
    discovered = [
        {
            "source_browser": source.source_browser,
            "source_profile": source.source_profile,
            "source_path_hash": source.source_path_hash,
            "readable": source.path.is_file(),
            "enabled": bool(source.enabled and settings["enabled"]),
        }
        for source in discover_browser_history_sources()
    ]
    return {
        "settings": settings,
        "sources": discovered,
        "checkpoints": checkpoint_payload,
        "domain_rules": rules,
        "record_count": len(db.activity.list_activity_records(limit=5000)),
    }


def build_ledger_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/activity/status")
    async def api_activity_status() -> Any:
        try:
            return JSONResponse(_activity_status_payload())
        except Exception as e:
            return error_500(e, log, "Failed to read activity status")

    @router.get("/api/activity/records")
    async def api_activity_records(
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> Any:
        try:
            from ....activity_context import build_activity_context
            from ....db import get_database

            db = get_database()
            bundle = build_activity_context(
                db=db,
                project_id=project_id,
                limit=limit,
                refresh=False,
            ).to_dict()
            records = bundle["records"]
            if domain:
                clean_domain = domain.strip().lower()
                records = [record for record in records if record.get("domain") == clean_domain]
            if entity_type:
                clean_type = entity_type.strip().lower()
                records = [record for record in records if record.get("entity_type") == clean_type]
            bundle["records"] = records
            return JSONResponse(bundle)
        except Exception as e:
            return error_500(e, log, "Failed to read activity records")

    @router.post("/api/activity/refresh")
    async def api_activity_refresh() -> Any:
        try:
            from ....activity_history import import_browser_history
            from ....db import get_database

            db = get_database()
            results = import_browser_history(db=db)
            return JSONResponse(
                {
                    "results": [
                        {
                            "source_browser": result.source_browser,
                            "source_profile": result.source_profile,
                            "source_path_hash": result.source_path_hash,
                            "imported_count": result.imported_count,
                            "checkpoint_raw": result.checkpoint_raw,
                            "enabled": result.enabled,
                            "error": result.error,
                        }
                        for result in results
                    ],
                    "status": _activity_status_payload(),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to refresh activity")

    @router.put("/api/activity/settings")
    async def api_activity_settings(payload: _ActivitySettingsRequest) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            settings = db.activity.update_activity_privacy_settings(
                enabled=payload.enabled,
                retention_days=payload.retention_days,
            )
            return JSONResponse({"settings": settings, "status": _activity_status_payload()})
        except Exception as e:
            return error_500(e, log, "Failed to update activity settings")

    @router.post("/api/activity/domains")
    async def api_activity_domain_rule(payload: _ActivityDomainRuleRequest) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            rule = db.activity.upsert_activity_domain_rule(
                domain=payload.domain,
                action=payload.action,
            )
            return JSONResponse({"rule": rule, "status": _activity_status_payload()})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to update activity domain rule")

    @router.delete("/api/activity/domains/{domain}")
    async def api_delete_activity_domain_rule(domain: str) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            deleted = db.activity.delete_activity_domain_rule(domain)
            return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
        except Exception as e:
            return error_500(e, log, "Failed to delete activity domain rule")

    @router.delete("/api/activity/records")
    async def api_delete_activity_records(
        domain: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Any:
        try:
            from ....db import get_database

            db = get_database()
            deleted = db.activity.delete_activity_records(domain=domain, project_id=project_id)
            return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
        except Exception as e:
            return error_500(e, log, "Failed to delete activity records")

    return router
