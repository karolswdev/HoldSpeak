"""Hand to agent (docs/internal/CONDUCTOR.md, step 2).

``POST /api/agent/hand {kind, id, instruction?, profile?, project_id?}``
(``POST /api/agent/hand/preview``, the same body: the launch sheet's preview,
no side effect; ``GET /api/agent/launches/{launch_id}``: one launch's delivery;
``GET /api/agent/launches/{launch_id}/lane``: the launch lane, PHILO-14 C0)
invokes the declared ``agent.hand`` operation (``holdspeak/agent_operations.py``):
one coding agent on one desk item: a grounded brief, a new
worktree, the launch, ``origin_ref`` on the launch and the attempt. The
caller's authenticated principal admits the ``process.spawn`` operation
(its kernel receipt is the launch receipt), the same as the PR send-agent
verb (``delivery_prs.py``). Blocking work runs off the event loop.

PHILO-15 16: ``GET /api/projects/{project_id}/repository`` (the Project's
registered repository, cloned or not) and ``POST`` of the same path
(``project.repository.register``, owner only, one receipt).
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import Principal, PrincipalKind
from ...services.errors import ServiceError
from ..context import WebContext

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
    }


def build_agent_hand_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _ops() -> Any:
        from ... import operations
        from ...services.agent_hand_service import default_agent_hand_service

        return operations.for_context(
            ctx,
            agent_hand_service=lambda: default_agent_hand_service(
                delivery_service=getattr(ctx, "delivery_service", None)
            ),
        )

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
        status = 202 if result.get("status") == "launched" else 409
        return JSONResponse(result, status_code=status)

    @router.post("/api/agent/hand/preview")
    async def api_agent_hand_preview(request: Request) -> Any:
        """The launch sheet's preview (K3): the brief, the repository and
        the branch Hand to agent would use, with no side effect. Owner only."""
        from ...services.agent_hand_preview import preview_hand
        from ...services.agent_hand_service import default_agent_hand_service

        try:
            body = await request.json()
        except Exception:
            body = None
        body = body if isinstance(body, dict) else {}
        kind, item_id = str(body.get("kind") or "").strip(), str(body.get("id") or "").strip()
        if not kind or not item_id:
            return JSONResponse({"error": "item_required"}, status_code=400)
        principal = getattr(
            request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
        )
        # The service object only: its launch driver getter is never called
        # (it binds and reconciles); the preview reads the driver's files.
        service = getattr(ctx, "agent_hand_service", None) or default_agent_hand_service(
            delivery_service=getattr(ctx, "delivery_service", None)
        )

        def run() -> Any:
            return preview_hand(
                service, principal, kind, item_id,
                instruction=body.get("instruction"), profile=body.get("profile"),
                project_id=body.get("project_id"), reads=getattr(ctx, "agent_hand_reads", None),
            )

        try:
            result = await asyncio.to_thread(run)
        except ServiceError as exc:
            payload = dict(exc.context)
            status = int(payload.pop("status", 409))
            return JSONResponse(
                {"error": exc.code, "code": exc.code, "detail": exc.detail, **payload}, status_code=status
            )
        except Exception as exc:
            log.error(f"agent hand preview failed: {exc}")
            return JSONResponse({"error": "agent_hand_preview_failed"}, status_code=500)
        return JSONResponse(result)

    @router.get("/api/agent/launches/{launch_id}")
    async def api_agent_launch(launch_id: str) -> Any:
        """One launch's delivery, read from the launch ledger (no driver, no
        reconcile): the launch sheet's receipt follows it until the brief is
        sent, held or refused."""
        from ...services.agent_hand_preview import LaunchReads

        reads = getattr(ctx, "agent_hand_reads", None) or LaunchReads()
        record = await asyncio.to_thread(lambda: reads.launcher()._ledger.get(launch_id))
        if not record:
            return JSONResponse({"error": "launch_unknown", "code": "launch_unknown"}, status_code=404)
        return JSONResponse({
            key: record.get(key)
            for key in ("launch_id", "state", "instruction_state", "trust_state", "failure", "profile_id")
        } | {"profile": record.get("profile_id")})

    @router.get("/api/agent/launches/{launch_id}/lane")
    async def api_agent_launch_lane(launch_id: str, after: int = 0, limit: int = 200) -> Any:
        """One launch's lane (PHILO-14 C0): the launch with its brief, the
        follow-through with the PR checks, the current wait with its draft,
        the session's events (paged: ``?after=<event id>&limit=``), the gated
        calls, the answers typed, the attempt's state changes, the worktree's
        commits and files, and the usage. Owner only (the edge default).
        Reads only (``services.launch_lane``)."""
        from ...db import get_database
        from ...services.agent_hand_preview import LaunchReads
        from ...services.launch_lane import launch_lane

        reads = getattr(ctx, "agent_hand_reads", None) or LaunchReads()

        def run() -> Any:
            return launch_lane(
                launch_id, db=get_database(), reads=reads,
                after=max(0, int(after)), limit=max(1, min(int(limit), 1000)),
                control=lane_control,
            )

        try:
            lane = await asyncio.to_thread(run)
        except Exception as exc:
            log.error(f"launch lane failed: {exc}")
            return JSONResponse({"error": "launch_lane_failed"}, status_code=500)
        if lane is None:
            return JSONResponse({"error": "launch_unknown", "code": "launch_unknown"}, status_code=404)
        return JSONResponse(lane)

    @router.post("/api/agent/launches/{launch_id}/deliver")
    async def api_agent_deliver(launch_id: str, request: Request) -> Any:
        """Deliver the held brief of an existing launch (after a restart, a
        hook install or a refused send): resume on the launch, no relaunch."""
        from ...services.agent_hand_service import default_agent_hand_service

        principal = getattr(
            request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
        )
        service = getattr(ctx, "agent_hand_service", None) or default_agent_hand_service(
            delivery_service=getattr(ctx, "delivery_service", None)
        )
        try:
            result = await asyncio.to_thread(service.resume, principal, launch_id)
        except ServiceError as exc:
            payload = dict(exc.context)
            status = int(payload.pop("status", 409))
            return JSONResponse(
                {"error": exc.code, "code": exc.code, "detail": exc.detail, **payload}, status_code=status
            )
        return JSONResponse(result, status_code=202)

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

    return router


__all__ = ["build_agent_hand_router"]
