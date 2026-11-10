"""The owner's engine profile routes, produced from the one contract."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from holdspeak import operations
from holdspeak.access_operations import PROFILE_OPERATIONS
from holdspeak.runtime.composition import db_or
from holdspeak.services.errors import ConflictError, NotFound, ServiceError
from holdspeak.services.model_profile_service import ModelProfileService
from holdspeak.web.operation_routes import operation_router


async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except operations.OperationOwnerRequired:
        return JSONResponse({"error": "Owner access is required", "code": "owner_principal_required"}, status_code=403)
    except operations.OperationRefused as exc:
        if exc.code == "owner_required":
            return JSONResponse({"error": "Owner access is required", "code": "owner_principal_required"}, status_code=403)
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=400)
    except ServiceError as exc:
        if "response" in exc.context:
            return JSONResponse(exc.context["response"], status_code=400)
        status = 404 if isinstance(exc, NotFound) else 409 if isinstance(exc, ConflictError) else int(exc.context.get("status") or 400)
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=status)


def _bare_profiles() -> Any:
    from holdspeak.db import get_database
    return ModelProfileService(db_or(get_database))


def build_model_profiles_router() -> APIRouter:
    # The hub's installed registry; only isolated route tests build a bare target.
    def registry() -> Any:
        return operations.for_runtime(owner_service=_bare_profiles)

    def post(descriptor: Any) -> Any:
        # The old POST boundary requires a JSON object and an explicit body
        # profile_id matching the path. Keep its answer bytes and checks.
        async def call(request: Request, profile_id: str | None = None) -> Any:
            from holdspeak.principals import UNAUTHENTICATED
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            try:
                registry().authorize(principal, descriptor.name)
            except operations.OperationOwnerRequired:
                return JSONResponse({"error": "Owner access is required", "code": "owner_principal_required"}, status_code=403)
            try:
                body = await request.json()
            except ValueError:
                body = None
            if not isinstance(body, dict):
                return JSONResponse({"error": "expected a JSON object"}, status_code=400)
            if profile_id is not None and body.get("profile_id") != profile_id:
                return JSONResponse({"error": "profile_id must match the path"}, status_code=400)
            return await _answer(lambda: registry().invoke(principal, descriptor.name, body, shape="web"),
                                 status=descriptor.http_status)

        if "{profile_id}" in descriptor.http[1]:
            async def endpoint(profile_id: str, request: Request) -> Any:
                return await call(request, profile_id)
        else:
            async def endpoint(request: Request) -> Any:
                return await call(request)
        endpoint.__name__ = descriptor.handler
        return endpoint

    return operation_router(PROFILE_OPERATIONS, registry, _answer, module=__name__,
                            hand_written={row.name: post for row in PROFILE_OPERATIONS if row.http[0] == "POST"})
