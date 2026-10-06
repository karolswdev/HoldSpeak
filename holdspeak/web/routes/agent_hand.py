"""Hand to agent (docs/internal/CONDUCTOR.md, step 2).

``POST /api/agent/hand {kind, id, instruction?, profile?, project_id?}``
(``POST /api/agent/hand/preview``, the same body: the launch sheet's preview,
no side effect; ``GET /api/agent/launches/{launch_id}``: one launch's delivery)
invokes the declared ``agent.hand`` operation (``holdspeak/agent_operations.py``):
one coding agent on one desk item: a grounded brief, a new
worktree, the launch, ``origin_ref`` on the launch and the attempt. The
caller's authenticated principal admits the ``process.spawn`` operation
(its kernel receipt is the launch receipt), the same as the PR send-agent
verb (``delivery_prs.py``). Blocking work runs off the event loop.
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

    return router


__all__ = ["build_agent_hand_router"]
