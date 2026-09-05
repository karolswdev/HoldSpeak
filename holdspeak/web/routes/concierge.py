"""Concierge routes (HS-170-03).

GET  /api/concierge/detect    -- every engine found
POST /api/concierge/propose   -- the seven groups with proposed engines
POST /api/concierge/probe     -- one-token probe for an engine
POST /api/concierge/apply     -- write the assignment set
POST /api/concierge/download  -- start a preset download
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import UNAUTHENTICATED, PrincipalKind
from ...services.errors import ConflictError, ServiceError
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger

log = get_logger("web.routes.concierge")


def _safe_error(exc: ServiceError) -> JSONResponse:
    ctx = exc.context or {}
    status = int(ctx.get("status", 400))
    if isinstance(exc, ConflictError) and status < 400:
        status = 409
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def build_concierge_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/concierge", tags=["concierge"])

    def _owner(request: Request) -> None:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "concierge_owner_required",
                "Owner access is required.",
                context={"status": 403},
            )

    @router.get("/detect")
    async def get_detect(request: Request) -> Any:
        try:
            _owner(request)
            from ...services.concierge_service import detect

            setup_svc = ctx.inference_setup_service
            db = None
            if setup_svc is not None:
                db = setup_svc._db

            if db is None:
                return JSONResponse(
                    {"code": "concierge_unavailable", "message": "Database is not available."},
                    status_code=503,
                )

            from pathlib import Path
            home = setup_svc._home_provider() if setup_svc is not None else Path.home()

            result = detect(db=db, home=home)
            return JSONResponse(result)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to detect engines")

    @router.post("/propose")
    async def post_propose(request: Request) -> Any:
        try:
            _owner(request)
            from ...services.concierge_service import detect, propose

            setup_svc = ctx.inference_setup_service
            db = None
            if setup_svc is not None:
                db = setup_svc._db

            if db is None:
                return JSONResponse(
                    {"code": "concierge_unavailable", "message": "Database is not available."},
                    status_code=503,
                )

            from pathlib import Path
            home = setup_svc._home_provider() if setup_svc is not None else Path.home()

            detection = detect(db=db, home=home)
            result = propose(engines=detection["engines"])
            return JSONResponse(result)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to propose engine set")

    @router.post("/probe")
    async def post_probe(request: Request) -> Any:
        try:
            _owner(request)
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError(
                    "concierge_probe_invalid",
                    "Expected a JSON object.",
                    context={"status": 400},
                )

            engine_id = body.get("engineId")
            generate = bool(body.get("generate", False))

            if not engine_id or not isinstance(engine_id, str):
                raise ServiceError(
                    "concierge_probe_invalid",
                    "engineId is required.",
                    context={"status": 400},
                )

            from ...services.concierge_service import detect, probe

            setup_svc = ctx.inference_setup_service
            db = None
            if setup_svc is not None:
                db = setup_svc._db

            if db is None:
                return JSONResponse(
                    {"code": "concierge_unavailable", "message": "Database is not available."},
                    status_code=503,
                )

            from pathlib import Path
            home = setup_svc._home_provider() if setup_svc is not None else Path.home()

            detection = detect(db=db, home=home)
            engine = None
            for e in detection["engines"]:
                if e["id"] == engine_id:
                    engine = e
                    break

            if engine is None:
                raise ServiceError(
                    "concierge_engine_not_found",
                    f"Engine '{engine_id}' not found.",
                    context={"status": 404},
                )

            result = probe(engine=engine, generate=generate)
            return JSONResponse(result)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to probe engine")

    @router.post("/apply")
    async def post_apply(request: Request) -> Any:
        try:
            _owner(request)
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError(
                    "concierge_apply_invalid",
                    "Expected a JSON object.",
                    context={"status": 400},
                )

            rows = body.get("rows")
            if not isinstance(rows, list):
                raise ServiceError(
                    "concierge_apply_invalid",
                    "rows is required.",
                    context={"status": 400},
                )

            from ...services.concierge_service import apply, detect

            setup_svc = ctx.inference_setup_service
            assignment_svc = ctx.inference_assignment_service
            db = None
            if setup_svc is not None:
                db = setup_svc._db

            if db is None or assignment_svc is None:
                return JSONResponse(
                    {"code": "concierge_unavailable", "message": "Required services are not available."},
                    status_code=503,
                )

            from pathlib import Path
            home = setup_svc._home_provider() if setup_svc is not None else Path.home()

            detection = detect(db=db, home=home)
            principal = request.state.principal

            result = apply(
                rows=rows,
                engines=detection["engines"],
                assignment_service=assignment_svc,
                principal=principal,
                db=db,
            )
            return JSONResponse(result)
        except ConflictError as exc:
            return _safe_error(exc)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to apply engine set")

    @router.post("/download")
    async def post_download(request: Request) -> Any:
        try:
            _owner(request)
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError(
                    "concierge_download_invalid",
                    "Expected a JSON object.",
                    context={"status": 400},
                )

            preset_id = body.get("presetId")
            if not preset_id or not isinstance(preset_id, str):
                raise ServiceError(
                    "concierge_download_invalid",
                    "presetId is required.",
                    context={"status": 400},
                )

            from ...services.concierge_service import download
            from ...inference_setup_catalog import (
                packaged_catalog_envelope_json,
                verify_catalog_envelope,
            )
            from datetime import datetime, timezone

            model_lib_svc = ctx.model_library_service
            if model_lib_svc is None:
                return JSONResponse(
                    {"code": "concierge_unavailable", "message": "Model library is not available."},
                    status_code=503,
                )

            now = datetime.now(timezone.utc)
            envelope_json = packaged_catalog_envelope_json()
            catalog = verify_catalog_envelope(envelope_json, now=now)
            catalog_revision = catalog["catalog_revision"]

            principal = request.state.principal
            result = download(
                preset_id=preset_id,
                model_library_service=model_lib_svc,
                principal=principal,
                catalog_revision=catalog_revision,
            )
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start download")

    return router


__all__ = ["build_concierge_router"]
