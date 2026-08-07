"""Control-mode policy inspection and scoped-grant transport adapters."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.authority_service import EvaluationRequest
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.authority")


async def _body(request: Request) -> dict[str, Any] | None:
    try:
        value = await request.json()
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _service_error(exc: ServiceError, *, missing_grant: str | None = None) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.detail}, status_code=400)
    if isinstance(exc, ConflictError):
        return JSONResponse({"error": exc.detail}, status_code=409)
    if isinstance(exc, NotFound):
        return JSONResponse(
            {"error": missing_grant or "Proposed action not found"}, status_code=404
        )
    return JSONResponse({"error": exc.detail}, status_code=400)


def build_authority_router(ctx: WebContext) -> APIRouter:
    service = ctx.authority_service
    if service is None:
        raise RuntimeError("AuthorityService must be supplied at application composition")
    router = APIRouter()

    @router.get("/api/authority/policy")
    async def api_authority_policy(request: Request) -> Any:
        try:
            return JSONResponse(service.get_policy(request.state.principal))
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read authority policy")

    @router.put("/api/authority/control-mode")
    async def api_set_control_mode(request: Request) -> Any:
        body = await _body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(
                service.set_control_mode(
                    request.state.principal, str(body.get("control_mode") or "")
                )
            )
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update control mode")

    @router.post("/api/authority/evaluate")
    async def api_evaluate_operation(request: Request) -> Any:
        body = await _body(request)
        if body is None or not isinstance(body.get("operation"), dict):
            return JSONResponse({"error": "operation object is required"}, status_code=400)
        raw = body["operation"]
        evaluation = EvaluationRequest(
            operation_id=str(raw.get("operation_id") or "preview"),
            family=str(raw.get("family") or ""),
            effect_class=str(raw.get("effect_class") or ""),
            destination=str(raw.get("destination") or ""),
            data_classes=raw.get("data_classes") if isinstance(raw.get("data_classes"), list) else [],
            project_scope=raw.get("project_scope"),
            resource_scope=raw.get("resource_scope"),
            fixed_destination=bool(raw.get("fixed_destination")),
            consequence=str(raw.get("consequence") or "execute_now"),
            grant_id=str(body.get("grant_id") or "").strip(),
            configured_preview=bool(body.get("configured_preview")),
        )
        try:
            return JSONResponse(service.evaluate(request.state.principal, evaluation))
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to evaluate operation")

    @router.get("/api/authority/grants")
    async def api_list_grants(request: Request, actor: str | None = None) -> Any:
        try:
            return JSONResponse(
                {"grants": service.list_grants(request.state.principal, actor)}
            )
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to list grants")

    @router.post("/api/authority/grants")
    async def api_issue_grant(request: Request) -> Any:
        body = await _body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        proposal_id = str(body.get("proposal_id") or "").strip()
        try:
            grant = service.issue_grant(
                request.state.principal,
                proposal_id,
                ttl_seconds=int(body.get("ttl_seconds") or 3600),
                max_uses=int(body.get("max_uses") or 1),
            )
            return JSONResponse({"grant": grant}, status_code=201)
        except ServiceError as exc:
            return _service_error(exc)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to issue grant")

    @router.delete("/api/authority/grants/{grant_id}")
    async def api_revoke_grant(grant_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.revoke_grant(request.state.principal, grant_id))
        except ServiceError as exc:
            return _service_error(exc, missing_grant="Grant not found or already revoked")
        except Exception as exc:
            return error_500(exc, log, "Failed to revoke grant")

    @router.get("/api/authority/grants/{grant_id}/uses")
    async def api_grant_uses(grant_id: str, request: Request) -> Any:
        try:
            uses = service.list_grant_uses(request.state.principal, grant_id)
            return JSONResponse({"grant_id": grant_id, "uses": uses})
        except ServiceError as exc:
            return _service_error(exc, missing_grant="Grant not found")
        except Exception as exc:
            return error_500(exc, log, "Failed to list grant uses")

    return router
