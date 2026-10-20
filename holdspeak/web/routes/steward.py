"""HS-163-04: Project Steward routes -- runs on HTTP.

POST /api/projects/{id}/steward/runs       -- run_once (async boundary; immediate-id)
GET  /api/projects/{id}/steward/runs       -- list runs
GET  /api/steward/runs/{run_id}            -- pollable state (phase, steps, receipts)
POST /api/steward/runs/{run_id}/stop       -- STW-003 on the wire
GET  /api/projects/{id}/steward/policy     -- get steward policy
PUT  /api/projects/{id}/steward/policy     -- update steward policy
POST /api/projects/{id}/steward/trigger    -- HS-167-02: evaluate_due + run_due NOW

Parse-and-serialize ONLY; the service owns logic.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...room_operations import STEWARD_POLICY_FIELDS
from ...services.errors import NotFound, ServiceError, ValidationError
from ...services.steward_serialization_service import (
    _serialize_policy,
    _serialize_run,
    _serialize_runs,
    _serialize_step,
    _serialize_steps,
)
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields, service_refusal

log = get_logger("web.routes.steward")


def _request_hash(payload: dict[str, Any]) -> str:
    """Deterministic hash for idempotency (mirrors project_update_service)."""
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def build_steward_router(ctx: WebContext) -> APIRouter:
    """PHILO-9-02: every steward route reaches its declared operation (``holdspeak/room_operations.py``).

    The run, stop, the policy write, the trigger and a nudge's send are
    admitted: one kernel operation with one terminal receipt each (the run's
    and the trigger's written when their work ends); the reads and a
    nudge's dismissal are not.
    """
    router = APIRouter(tags=["steward"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> Any:
        return operations.for_context(ctx)

    def refused_by(exc: ServiceError, default_status: int = 409) -> JSONResponse:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        if isinstance(exc, NotFound):
            return JSONResponse({"code": exc.code, "message": exc.detail, **refusal_fields(exc)}, status_code=404)
        return service_refusal(exc, default_status=default_status)

    # ── POST /api/projects/{project_id}/steward/runs ───────────────
    # The beat, section 2: the pending handle -- run_id AND operation_id at
    # once; the operation is non-terminal while the run works.

    @router.post("/api/projects/{project_id}/steward/runs")
    async def api_start_steward_run(project_id: str, request: Request) -> Any:
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "project.run_steward", optional=True)
        if refused is not None:
            return refused
        try:
            result, _kernel = ops().invoke_receipted(p, "project.run_steward", {
                "project_id": project_id, "watermark": body.get("watermark"),
                "command_id": body.get("command_id"),
            })
            return JSONResponse(result)
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            return refused_by(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start steward run")

    # ── GET /api/projects/{project_id}/steward/runs ────────────────

    @router.get("/api/projects/{project_id}/steward/runs")
    async def api_list_steward_runs(
        project_id: str, request: Request,
        state: str | None = None,
        limit: int = 100,
    ) -> Any:
        try:
            svc = ctx.project_steward_service
            runs = svc._db.steward_runs.list_runs(
                project_id, state=state, limit=limit,
            )
            return JSONResponse({"runs": _serialize_runs(runs)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list steward runs")

    # ── GET /api/steward/runs/{run_id} ─────────────────────────────
    # Pollable state: phase, steps, receipts, the run's operation and its receipt.

    @router.get("/api/steward/runs/{run_id}")
    async def api_get_steward_run(run_id: str, request: Request) -> Any:
        try:
            return JSONResponse(ops().invoke(principal(request), "project.get_steward_run", {"run_id": run_id}))
        except NotFound:
            return JSONResponse(
                {"code": "not_found", "message": f"Unknown steward run: {run_id}"},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get steward run")

    # ── POST /api/steward/runs/{run_id}/stop ───────────────────────
    # STW-003 on the wire, admitted: the stop flag and the stop's receipt.

    @router.post("/api/steward/runs/{run_id}/stop")
    async def api_stop_steward_run(run_id: str, request: Request) -> Any:
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "project.stop_steward", optional=True)
        if refused is not None:
            return refused
        try:
            result, kernel = ops().invoke_receipted(p, "project.stop_steward", {
                "run_id": run_id, "command_id": body.get("command_id")})
            return JSONResponse({**result, **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            if isinstance(exc, NotFound) and kernel_refusal(exc) is None:
                return JSONResponse({"code": "not_found", "message": f"Unknown steward run: {run_id}",
                                     **refusal_fields(exc)}, status_code=404)
            return refused_by(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to stop steward run")

    # ── GET /api/projects/{project_id}/steward/policy ──────────────

    @router.get("/api/projects/{project_id}/steward/policy")
    async def api_get_steward_policy(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(ops().invoke(principal(request), "project.configure_steward",
                                             {"project_id": project_id}))
        except NotFound:
            return JSONResponse({"policy": None})
        except Exception as exc:
            return error_500(exc, log, "Failed to get steward policy")

    # ── PUT /api/projects/{project_id}/steward/policy ──────────────
    # Admitted (a policy write changes authority); the write, its
    # configure_operation_id and the receipt commit in ONE transaction.

    @router.put("/api/projects/{project_id}/steward/policy")
    async def api_put_steward_policy(project_id: str, request: Request) -> Any:
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "project.configure_steward")
        if refused is not None:
            return refused
        try:
            args = {"project_id": project_id, **{key: body.get(key) for key in STEWARD_POLICY_FIELDS}}
            if body.get("command_id"):
                args["command_id"] = body.get("command_id")  # a retry reaches the same operation (ruling B)
            result, kernel = ops().invoke_receipted(p, "project.configure_steward", args)
            return JSONResponse({**result, **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "validation_error", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ValidationError as exc:
            return JSONResponse({"success": False, "code": "validation_error", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            return refused_by(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update steward policy")

    # ── POST /api/steward/trigger ──────────────────────────────────
    # HS-167-02 + PHILO-9-02: admitted; returns the pending handle at once,
    # and its one receipt is written when its runs end (the beat, section 4).

    @router.post("/api/steward/trigger")
    async def api_trigger_steward(request: Request) -> Any:
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "project.steward.trigger", optional=True)
        if refused is not None:
            return refused
        try:
            result, _kernel = ops().invoke_receipted(p, "project.steward.trigger",
                                                     {"command_id": body.get("command_id")})
            return JSONResponse(result)
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            return refused_by(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to trigger steward")

    # ── HS-173-04: Nudge routes ──────────────────────────────────────

    @router.get("/api/projects/{project_id}/nudges")
    async def api_list_nudges(project_id: str, request: Request, state: str | None = None) -> Any:
        try:
            nudges = ops().invoke(principal(request), "steward.nudges", {"project_id": project_id, "state": state})
            return JSONResponse({"nudges": nudges})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "validation", "message": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to list nudges")

    @router.post("/api/nudges/{step_id}/send")
    async def api_send_nudge(step_id: str, request: Request) -> Any:
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "nudge.send", optional=True)
        if refused is not None:
            return refused
        try:
            from starlette.concurrency import run_in_threadpool

            # PHILO-10-02 GATE 2: the gh child runs off the event loop.
            result, kernel = await run_in_threadpool(
                ops().invoke_receipted, p, "nudge.send", {"step_id": step_id, "text": str(body.get("text", "") or "")})
            return JSONResponse({"success": True, **result, **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            context = {k: v for k, v in exc.context.items() if k not in {"status", "operation_id", "receipt"}}
            return JSONResponse({"success": False, "error": exc.code, "code": exc.code, "message": exc.detail,
                                 **context, **refusal_fields(exc)},
                                status_code=int(exc.context.get("status") or 409))
        except Exception as exc:
            return error_500(exc, log, "Failed to send nudge")

    @router.post("/api/nudges/{step_id}/dismiss")
    async def api_dismiss_nudge(step_id: str, request: Request) -> Any:
        try:
            result = ops().invoke(principal(request), "nudge.dismiss", {"step_id": step_id})
            if "error" in result:
                status = 404 if result["error"] == "nudge_not_found" else 409
                return JSONResponse(
                    {"success": False, **result}, status_code=status,
                )
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to dismiss nudge")

    return router
