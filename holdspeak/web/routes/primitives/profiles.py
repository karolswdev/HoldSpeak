"""Runtime profiles CRUD (the key never rides the wire).

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.profile_service import ProfileService
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.primitives")


def build_profiles_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _reject_secret(body: dict[str, Any]) -> Optional[JSONResponse]:
        forbidden = sorted(
            key for key in body
            if key.lower().replace("-", "_") in {"api_key", "apikey", "secret", "token"}
        )
        if forbidden:
            return JSONResponse(
                {"error": "InferenceTarget never accepts secret material", "forbidden_fields": forbidden},
                status_code=400,
            )
        return None

    def _svc() -> ProfileService:
        from ....db import get_database, get_observer
        return ProfileService(get_database(), observer=get_observer())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    # HS-134-02: GET /api/profiles retired — the target contract is the only
    # read shape; writes were already rejected (HS-112-01).
    # `/api/inference-targets` is the one write path.
    def _profiles_read_only() -> JSONResponse:
        return JSONResponse(
            {
                "error": "/api/profiles is read-only; write via /api/inference-targets",
                "write_path": "/api/inference-targets",
            },
            status_code=405,
        )

    @router.post("/api/profiles")
    async def api_create_profile(request: Request) -> Any:
        return _profiles_read_only()

    @router.put("/api/profiles/{profile_id}")
    async def api_update_profile(profile_id: str, request: Request) -> Any:
        return _profiles_read_only()

    @router.delete("/api/profiles/{profile_id}")
    async def api_delete_profile(profile_id: str) -> Any:
        return _profiles_read_only()

    @router.get("/api/inference-targets")
    async def api_list_inference_targets(request: Request) -> Any:
        try:
            return JSONResponse(_svc().list_inference_targets(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to list inference targets")

    @router.post("/api/inference-targets/{target_id}/probe")
    async def api_probe_target(target_id: str, request: Request) -> Any:
        """Test this destination without persisting a connection result."""
        try:
            return JSONResponse(_svc().probe_inference_target(_principal(request), target_id))
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to probe inference target")

    @router.post("/api/inference-targets")
    async def api_create_inference_target(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if rejected := _reject_secret(body):
            return rejected
        try:
            target = _svc().create_profile(_principal(request), body)
            return JSONResponse({"inference_target": target}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create inference target")

    @router.get("/api/inference-targets/{target_id}")
    async def api_get_inference_target(target_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_svc().get_inference_target(_principal(request), target_id))
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except ServiceError as exc:
            return JSONResponse({"error": exc.detail}, status_code=int(exc.context.get("status") or 400))
        except Exception as exc:
            return error_500(exc, log, "Failed to get inference target")

    @router.put("/api/inference-targets/{target_id}")
    async def api_update_inference_target(target_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if rejected := _reject_secret(body):
            return rejected
        try:
            target = _svc().update_profile(_principal(request), target_id, body)
            return JSONResponse({"inference_target": target})
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update inference target")

    @router.delete("/api/inference-targets/{target_id}")
    async def api_delete_inference_target(target_id: str, request: Request) -> Any:
        try:
            _svc().delete_profile(_principal(request), target_id)
            return JSONResponse({"success": True})
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown destination: {target_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete inference target")

    # ── KBs (knowledge bases) ─────────────────────────────────────────────

    return router
