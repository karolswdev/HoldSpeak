"""HTTP transport for application settings (HS-123-03)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, ValidationError
from ....services.settings_service import SettingsService
from ...context import WebContext
from ...runtime_support import error_500
from .settings_secrets import register_settings_secret_routes

log = get_logger("web.routes.system")


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _service(ctx: WebContext) -> SettingsService:
    if not isinstance(ctx.settings_service, SettingsService):
        raise RuntimeError("SettingsService was not supplied at application composition")
    return ctx.settings_service


def build_settings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/settings")
    async def api_get_settings(request: Request) -> Any:
        try:
            from ....plugins.dictation.runtime_counters import get_counters, get_session_status

            payload = _service(ctx).get_settings(_principal(request))
            # Runtime fields are read-only enrichment, retained verbatim from the
            # previous HTTP response rather than becoming persisted service state.
            payload["_runtime_status"] = {
                "counters": get_counters(),
                "session": get_session_status(),
            }
            return JSONResponse(payload)
        except Exception as exc:
            return error_500(exc, log, "Failed to load settings")

    @router.put("/api/settings")
    async def api_update_settings(payload: dict[str, Any], request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).update_settings(_principal(request), payload))
        except ConflictError as exc:
            # HS-130-07: a stale partial-tree write. Reject with 409 and hand
            # back the current revision so the client can reload + reconcile.
            return JSONResponse(
                {
                    "success": False,
                    "error": exc.detail,
                    "revision": exc.context.get("revision", ""),
                },
                status_code=409,
            )
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error("Failed to update settings: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.get("/api/settings/hub")
    async def api_settings_hub(request: Request) -> Any:
        """HS-170-04: settings hub row facts.

        One read returning the seven module rows' state tokens from existing
        services. Counts are integers; the face applies the zero law.
        """
        try:
            from ....config import Config
            from ....services.model_library_service import ModelLibraryApplicationService
            from ....services.inference_assignment_service import InferenceAssignmentService

            config = Config.load()
            p = _principal(request)

            # Models: engines from the model library summary, groups from
            # the assignments summary.
            engines = 0
            groups_set = 0
            default_set = False
            if ctx.model_library_service is not None:
                try:
                    lib = ctx.model_library_service.get_library(p)
                    summary = lib.get("summary", {})
                    engines = summary.get("ready_count", 0)
                except Exception:
                    pass
            if ctx.inference_assignment_service is not None:
                try:
                    asn = ctx.inference_assignment_service.assignment_summary(p)
                    rows = asn.get("rows", [])
                    for row in rows:
                        if row.get("id") == "global":
                            default_set = row.get("status") == "assigned"
                        elif row.get("status") == "assigned":
                            groups_set += 1
                except Exception:
                    pass

            # Connections: count provider connections.
            connected = 0
            try:
                from ....db import get_database
                conns = get_database().automations.list_provider_connections()
                connected = len(conns)
            except Exception:
                pass

            # Voice: pipeline live + target.
            voice_live = config.dictation.pipeline.enabled
            voice_target = config.dictation.pipeline.target_profile_override or "auto"

            # Meetings: intelligence enabled.
            intel_on = config.meeting.intel_enabled

            # Rhythm: count active cadence loops.
            loops = 0
            if ctx.cadence_service is not None:
                try:
                    loop_list = ctx.cadence_service.list_loops(p)
                    loops = len(loop_list.get("loops", []))
                except Exception:
                    pass

            # Sounds.
            sounds_on = config.ui.desk_sounds

            # System.
            mesh_on = bool(getattr(config.mesh, "device_name", ""))

            # Posture.
            posture = config.control_mode

            # writtenAt: the settings file's last write.
            written_at = None
            try:
                from ....config import CONFIG_FILE
                import os
                if CONFIG_FILE.exists():
                    written_at = os.path.getmtime(CONFIG_FILE)
            except Exception:
                pass

            return JSONResponse({
                "models": {
                    "engines": engines,
                    "groupsSet": groups_set,
                    "defaultSet": default_set,
                },
                "connections": {"connected": connected},
                "voice": {"live": voice_live, "target": voice_target},
                "meetings": {"intelligence": intel_on},
                "rhythm": {"loops": loops},
                "sounds": {"on": sounds_on},
                "system": {"host": "THIS DEVICE", "mesh": mesh_on},
                "posture": posture,
                "writtenAt": written_at,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to load settings hub")

    register_settings_secret_routes(router, ctx)
    return router
