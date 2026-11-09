"""Hand to an agent session (docs/internal/CONDUCTOR.md, step 2).

``POST /api/agent/hand {kind, id, instruction?, profile?, project_id?}``
invokes the declared ``agent.hand`` operation (``holdspeak/agent_operations.py``):
one coding agent on one desk item: a grounded brief, a new
worktree, the launch, ``origin_ref`` on the launch and the attempt. The
caller's authenticated principal admits the ``process.spawn`` operation
(its kernel receipt is the launch receipt), the same as the PR send-agent
verb (``delivery_prs.py``). Blocking work runs off the event loop. The
preview, one launch's delivery and lane, and the launch verbs are produced
from ``agent_operations.LAUNCH_OPERATIONS``.

PHILO-15 16: ``GET /api/projects/{project_id}/repository`` (the Project's
registered repository, cloned or not) and ``POST`` of the same path
(``project.repository.register``, owner only, one receipt).
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...agent_operations import LAUNCH_OPERATIONS
from ._mount import mount_router
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import Principal, PrincipalKind
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router

log = get_logger("web.routes.agent_hand")

#: Refusals that mean "the item or its Project is not ready", not a failure.
_NOT_FOUND = frozenset({"item_unknown"})


def lane_control(key: str) -> dict[str, Any]:
    """PHILO-14 C2: how the lane may act on its own session now: the Control
    mode, the session's pane grant, and whether the steer policy lets the
    owner type without one (a registered pane in YOLO: ``direct``). The same
    resolver the steer route uses (``steering_policy``)."""
    from ...config import Config

    mode = Config.load().control_mode
    if not key:
        return {"mode": mode, "armed": False, "direct": False, "expires_in_seconds": None}
    from ... import coder_steering
    from ...agent_context import list_agent_sessions
    from .system.coder_steering_support import active_policy_grant, canonical_pane_id, steering_policy

    session = next(
        (s for s in list_agent_sessions() if f"{s.agent}:{s.session_id}" == key), None
    )
    grant = active_policy_grant(key)
    target = coder_steering.resolve_pane_target(session) if session is not None else None
    pane_id = canonical_pane_id(target) or (canonical_pane_id(grant.get("pane_id")) if grant else None)
    _operation, policy = steering_policy(
        key, pane_id, operation_kind="type_text", data_classes=("typed_text",),
        registered=pane_id is not None, grant=grant,
    )
    direct = policy.get("outcome") == "allowed" and policy.get("authority_basis") == "control_posture"
    return {
        "mode": mode,
        "armed": grant is not None,
        "direct": bool(direct),
        "expires_in_seconds": grant.get("expires_in_seconds") if grant else None,
        "pane": bool(target),
        # PHILO-15 B46: the registered pane the steer names, so a YOLO steer
        # from the lane passes the registered-destination rule.
        "pane_id": pane_id,
    }


def build_agent_hand_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> Any:
        from ... import operations
        from ...services.agent_hand_service import default_agent_hand_service

        registry = operations.for_context(
            ctx,
            agent_hand_service=lambda: default_agent_hand_service(
                delivery_service=getattr(ctx, "delivery_service", None)
            ),
        )
        # The launch reads (a test's stand-in, else the defaults) and the
        # lane's steering resolver, on the one service the rows are bound to.
        bind = getattr(registry.target("agent.hand"), "bind_reads", None)  # a test's stand-in may not have it
        if bind is not None:
            bind(getattr(ctx, "agent_hand_reads", None), lane_control)
        return registry

    @router.post("/api/agent/hand")
    async def api_agent_hand(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        body = body if isinstance(body, dict) else {}
        if not str(body.get("kind") or "").strip() or not str(body.get("id") or "").strip():
            return JSONResponse({"error": "item_required"}, status_code=400)
        principal = getattr(
            request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
        )
        try:
            ops = _ops()

            def run() -> Any:
                return ops.invoke(principal, "agent.hand", body)

            result = await asyncio.to_thread(run)
        except ServiceError as exc:
            payload = dict(exc.context)
            status = int(payload.pop("status", 409))
            return JSONResponse(
                {"error": exc.code, "code": exc.code, "detail": exc.detail, **payload}, status_code=status
            )
        except Exception as exc:
            reason = getattr(exc, "reason", None) or getattr(exc, "code", None)
            if reason is None:
                log.error(f"agent hand failed: {exc}")
                return JSONResponse({"error": "agent_hand_failed"}, status_code=500)
            status = 404 if reason in _NOT_FOUND else (400 if reason == "invalid_arguments" else 409)
            return JSONResponse({"error": reason, "code": reason, "detail": str(exc)}, status_code=status)
        status = 202 if result.get("status") in ("launched", "queued") else 409
        return JSONResponse(result, status_code=status)

    # ── PHILO-15 16 (B38): a Project knows its repository ──────────────

    @router.get("/api/projects/{project_id}/repository")
    async def api_project_repository(project_id: str) -> Any:
        """The Project's registered repository, CLONED or not, and the
        repositories its Room watches (the drawer's Get Info and Register).
        Owner only (the edge default); reads only."""
        from ...services.agent_hand_preview import LaunchReads

        reads = getattr(ctx, "agent_hand_reads", None) or LaunchReads()
        principal = Principal(PrincipalKind.OWNER, "owner-session")

        def run() -> Any:
            # The one service instance the register operation is bound to.
            service = _ops().target("project.repository.register")
            return service.repository_state(principal, project_id, registry=reads.registry())

        try:
            return JSONResponse(await asyncio.to_thread(run))
        except Exception as exc:
            log.error(f"project repository read failed: {exc}")
            return JSONResponse({"error": "project_repository_failed"}, status_code=500)

    @router.post("/api/projects/{project_id}/repository")
    async def api_register_project_repository(project_id: str, request: Request) -> Any:
        """``project.repository.register``: the owner's press names the
        Project's repository (owner/name). One admitted kernel operation, one
        receipt; nothing is cloned until the first hand."""
        from ...operations import OperationRefused
        from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields, service_refusal

        name = "project.repository.register"
        principal = getattr(request.state, "principal", None) or Principal(PrincipalKind.OWNER, "owner-session")
        registry = _ops()
        data, refused = await body_or_refusal(request, registry, principal, name)
        if refused is not None:
            return refused
        args = {"project_id": project_id, "repository": data.get("repository")}
        if data.get("command_id"):
            args["command_id"] = data.get("command_id")

        def run() -> JSONResponse:
            try:
                result, kernel = registry.invoke_receipted(principal, name, args)
                return JSONResponse({**result, **kernel_fields(kernel)})
            except OperationRefused as exc:
                return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                                     "message": exc.detail, **refusal_fields(exc)}, status_code=400)
            except ServiceError as exc:
                if (answer := kernel_refusal(exc)) is not None:
                    return answer
                return service_refusal(exc)

        return await asyncio.to_thread(run)

    # 2026-11-08 (one contract): the launch verbs are produced from their
    # declared rows (``agent_operations.LAUNCH_OPERATIONS``) through the
    # registry; 2026-11-09: the preview, the launch's delivery, Re-brief, Take
    # back and Deliver too. The lane reads the reads and the steering resolver
    # ``_ops`` binds on the service, never arguments.
    mount_router(router, operation_router(
        LAUNCH_OPERATIONS, _ops, lambda fn, status=200: _answer(fn, status=status), module=__name__,
    ))
    return router


async def _answer(fn: Any, *, status: int = 200, name: str = "") -> JSONResponse:
    """The launch verbs' envelope: the answer, else ``{error, code, detail}``
    and the refusal's own fields (``status``, ``reason``, the record), at the
    status the hand-written routes answered with."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        payload = dict(exc.context)
        http = payload.pop("http", None)
        if http is None and isinstance(payload.get("status"), int):
            http = payload.pop("status")
        return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail, **payload},
                            status_code=int(http or 409))
    except OperationRefused as exc:
        return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail}, status_code=400)
    except Exception as exc:
        log.error(f"{name or 'agent launch verb'} failed: {exc}")
        return JSONResponse({"error": "agent_launch_failed"}, status_code=500)


__all__ = ["build_agent_hand_router"]
