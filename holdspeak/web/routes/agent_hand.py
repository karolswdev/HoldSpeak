"""Hand to agent (docs/internal/CONDUCTOR.md, step 2).

``POST /api/agent/hand {kind, id, instruction?, profile?, project_id?}``
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
