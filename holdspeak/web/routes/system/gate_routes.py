"""HTTP transport for the gate and the principals: produced from ``holdspeak/gate_operations.py``.

One route per declared verb, through ``OperationRegistry.invoke``; the paths
and the answers are the ones the hand-written routes had (parked in
``_parked/gate_routes_20261109.py``). Two routes are hand-written shells over
their rows: ``POST /api/principals/agents`` (its body names ``identity``, a word
the contract refuses as an argument, so the shell passes it as
``agent_identity``) and the decide (the desk's body still carries ``actor``,
which the service never read; the shell drops it).
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....gate_operations import GATE_OPERATIONS
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router

log = get_logger("web.routes.gate")

#: The two principals verbs whose refusal keeps its own shape ({error, detail, ...context}).
_PRINCIPAL_ROWS = ("principals.agent.revoke", "principals.self.revoke")


def _error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.detail}, status_code=400)
    if isinstance(exc, NotFound):
        return JSONResponse({"error": "unknown_proposal"}, status_code=404)
    if isinstance(exc, ConflictError):
        if exc.code == "args_mismatch":
            return JSONResponse({"error": exc.code, **exc.context, "reason": exc.detail}, status_code=409)
        if exc.code == "already_decided":
            return JSONResponse({"error": exc.code, **exc.context}, status_code=409)
        return JSONResponse({"error": exc.code}, status_code=409)
    response = exc.context.get("response")
    if isinstance(response, dict):
        return JSONResponse(response, status_code=int(exc.context.get("status") or 400))
    payload = {"error": exc.code}
    if "operation_id" in exc.context:
        payload["operation_id"] = exc.context["operation_id"] or None
    return JSONResponse(payload, status_code=int(exc.context.get("status") or 400))


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _error(exc)
    except operations.OperationRefused as exc:
        return JSONResponse({"error": exc.detail}, status_code=400)
    except Exception as exc:
        return error_500(exc, log, "The gate call failed")


async def _principal_answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    """A grant revoke the kernel refuses names its code and leaves the credential."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                            status_code=int(exc.context.get("status") or 409))
    except Exception as exc:
        return error_500(exc, log, "The principal call failed")


def build_gate_router(ctx: WebContext) -> APIRouter:
    service = ctx.gate_service
    if service is None:
        raise RuntimeError("GateService must be supplied at application composition")

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, gate_service=lambda: service)

    async def shell(request: Request, name: str, shape: Callable[[dict[str, Any]], dict[str, Any]],
                    status: int) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        if not isinstance(body, dict):
            return JSONResponse({"error": "body must be an object"}, status_code=400)
        principal, args = getattr(request.state, "principal", UNAUTHENTICATED), shape(body)
        return await _answer(lambda: registry().invoke(principal, name, args, shape="web"), status=status)

    def issue(descriptor: Any) -> Callable[..., Awaitable[Any]]:
        async def api_issue_agent_principal(request: Request) -> Any:
            return await shell(request, descriptor.name, lambda body: {"agent_identity": body.get("identity")},
                               descriptor.http_status)
        return api_issue_agent_principal

    def decide(descriptor: Any) -> Callable[..., Awaitable[Any]]:
        async def api_gate_decide(proposal_id: str, request: Request) -> Any:
            # The desk's Approve and Deny still send ``actor``; the service never read
            # it (the decider is the edge's principal), so the shell drops the word.
            return await shell(request, descriptor.name, lambda body: {
                **{k: v for k, v in body.items() if k != "actor"}, "proposal_id": proposal_id}, 200)
        return api_gate_decide

    router = APIRouter()
    mount_router(router, operation_router(
        [op for op in GATE_OPERATIONS if op.name not in _PRINCIPAL_ROWS], registry, _answer,
        module=__name__, hand_written={"principals.agent.issue": issue, "gate.decide": decide}))
    mount_router(router, operation_router(
        [op for op in GATE_OPERATIONS if op.name in _PRINCIPAL_ROWS], registry, _principal_answer, module=__name__))
    return router


def invalidate_held_on_startup(service: Any) -> int:
    """Invalidate pre-restart held proposals and terminalize their kernel rows."""
    flipped, recovered = service.invalidate_held_on_startup()
    if flipped:
        log.info("gate: invalidated %s held proposal(s) on startup; kernel terminalized %s", len(flipped), recovered)
    return len(flipped)
