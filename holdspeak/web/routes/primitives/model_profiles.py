"""Owner-only Model Library profile authority routes (HS-143-03)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....services.errors import ConflictError, NotFound, ServiceError
from ....services.model_profile_service import ModelProfileService
from ._shared import _json_body


def _error(error: ServiceError) -> JSONResponse:
    if isinstance(error, NotFound):
        status = 404
    elif isinstance(error, ConflictError):
        status = 409
    else:
        status = int(error.context.get("status") or 400)
    return JSONResponse({"error": error.detail, "code": error.code}, status_code=status)


def build_model_profiles_router() -> APIRouter:
    router = APIRouter()

    def _service() -> ModelProfileService:
        from ....db import get_database
        return ModelProfileService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    def _owner_service(request: Request) -> ModelProfileService:
        service = _service()
        # Authorize before inspecting a caller-supplied profile id/body.  This
        # keeps the HTTP edge aligned with the service's owner-first rule.
        service._require_owner(_principal(request))
        return service

    @router.get("/api/model-profiles")
    async def api_list_model_profiles(request: Request) -> Any:
        try:
            service = _owner_service(request)
            return JSONResponse(service.list_profiles(_principal(request)))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/model-profiles")
    async def api_create_model_profile(request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({"profile": service.create_profile(_principal(request), body)}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/model-profiles/{profile_id}")
    async def api_get_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        requested = request.query_params.get("revision")
        try:
            revision = None if requested is None else int(requested)
        except ValueError:
            return JSONResponse({"error": "revision must be an integer"}, status_code=400)
        try:
            return JSONResponse({"profile": service.get_profile(_principal(request), profile_id, revision=revision)})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/model-profiles/{profile_id}/revisions")
    async def api_revise_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if body.get("profile_id") != profile_id:
            return JSONResponse({"error": "profile_id must match the path"}, status_code=400)
        try:
            return JSONResponse({"profile": service.revise_profile(_principal(request), body)}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.delete("/api/model-profiles/{profile_id}")
    async def api_delete_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        raw = request.query_params.get("expected_revision")
        try:
            expected_revision = None if raw is None else int(raw)
        except ValueError:
            return JSONResponse({"error": "expected_revision must be an integer"}, status_code=400)
        try:
            return JSONResponse(service.delete_profile(_principal(request), profile_id, expected_revision=expected_revision))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/model-profiles/{profile_id}/binding")
    async def api_bind_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if body.get("profile_id") != profile_id:
            return JSONResponse({"error": "profile_id must match the path"}, status_code=400)
        try:
            return JSONResponse({"binding": service.bind_profile(_principal(request), body)}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/model-profiles/{profile_id}/probe")
    async def api_probe_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if body.get("profile_id") != profile_id:
            return JSONResponse({"error": "profile_id must match the path"}, status_code=400)
        try:
            return JSONResponse({"observation": service.probe_profile(_principal(request), body)}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.delete("/api/model-profiles/{profile_id}/binding")
    async def api_unbind_model_profile(profile_id: str, request: Request) -> Any:
        try:
            service = _owner_service(request)
        except ServiceError as exc:
            return _error(exc)
        raw = request.query_params.get("expected_binding_revision")
        try:
            expected = None if raw is None else int(raw)
        except ValueError:
            return JSONResponse({"error": "expected_binding_revision must be an integer"}, status_code=400)
        try:
            return JSONResponse(
                service.unbind_profile(
                    _principal(request), profile_id, expected_binding_revision=expected  # type: ignore[arg-type]
                )
            )
        except ServiceError as exc:
            return _error(exc)

    return router
