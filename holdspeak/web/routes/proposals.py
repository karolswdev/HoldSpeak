"""HS-172-03: Follow-through proposal transport adapters.

Routes:
  GET  /api/meetings/{id}/follow-through-proposals - list proposals for a meeting
  GET  /api/meetings/{id}/outcome-review  - HS-200-12: the review face's projection
  GET  /api/projects/{id}/proposals       - list proposals for a project
  POST /api/proposals/{id}/confirm        - confirm a proposal (idempotent)
  POST /api/proposals/{id}/edit           - HS-200-12: amend a proposed row in place
  POST /api/meetings/{id}/proposals/accept-reviewed - HS-200-12: confirm the eligible rows
  POST /api/proposals/{id}/dismiss        - dismiss a proposal (idempotent)
  POST /api/proposals/{id}/defer          - PHILO-15 08: hide from Needs until tomorrow
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse

from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...project_operations import PROJECT_OPERATIONS
from ...principals import UNAUTHENTICATED
from ...services.proposal_bridge_service import ProposalBridgeService
from ..context import WebContext
from ..operation_routes import ContractRefusal, _invoke
from ..runtime_support import error_500
from ._mount import mount_router
from ._produced import produced

log = get_logger("web.routes.proposals")
_service_lock = threading.Lock()


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _service(ctx: WebContext) -> ProposalBridgeService:
    with _service_lock:
        service = getattr(ctx, "proposal_bridge_service", None)
        if service is not None:
            return service
        from ...db import get_database
        service = ProposalBridgeService(get_database())
        ctx.proposal_bridge_service = service  # type: ignore[attr-defined]
        return service


def _status(result: dict[str, Any]) -> int:
    """404 for a missing proposal; 409 for one already decided the other way."""
    return 409 if result.get("code") in {
        "confirmed",
        "dismissed",
        "meeting_deleted",
        "meeting_parked",
    } else 404


def _answer(what: str, *, wrap: bool = True, missing: int | None = None) -> Any:
    """A produced proposal route's envelope: the service answers a refusal as
    ``{error, code}`` (it does not raise), so the status is read from it."""

    async def answer(fn: Any, *, status: int = 200) -> JSONResponse:
        try:
            result = await run_in_threadpool(fn)
        except ContractRefusal as exc:
            return JSONResponse({"success": False, "error": exc.detail, "code": exc.code}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, what)
        if isinstance(result, dict) and "error" in result:
            code = missing or _status(result)
            return JSONResponse({"success": False, **result} if missing is None or wrap else
                                {"success": False, "error": result["error"]}, status_code=code)
        return JSONResponse({"success": True, **result} if wrap else result, status_code=status)

    return answer


def _edit(registry: Any, answer: Any) -> Any:
    """The edit route: the web names the person ``owner``; the contract refuses
    that word as an argument (AUTHORITY_FIELDS), so the route passes it as ``who``."""

    def build(descriptor: Any) -> Any:
        async def api_edit_proposal(proposal_id: str, request: Request) -> Any:
            try:
                body = await request.json()
            except Exception:
                body = None
            body = dict(body) if isinstance(body, dict) else {}
            if "owner" in body:
                body["who"] = body.pop("owner")
            args = {**body, "proposal_id": proposal_id}
            who = _principal(request)
            return await answer(lambda: _invoke(registry, who, descriptor.name, args))

        return api_edit_proposal

    return build


def build_proposal_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["proposals"])

    # 2026-11-09 (ops/projects): the review, accept-reviewed, the project's
    # list, edit, restore and defer are produced from their declared rows
    # (``project_operations.py``); confirm, dismiss and the meeting's list
    # keep their handlers (their MCP twins are proposal.confirm, proposal.dismiss
    # and meeting.proposals).
    def registry() -> Any:
        return operations.for_context(ctx, proposal_bridge_service=lambda: _service(ctx))

    answers = {
        "project.proposals": _answer("Failed to list project proposals", wrap=False),
        "meeting.outcome_review": _answer("Failed to read the meeting review", wrap=False, missing=404),
        "meeting.accept_reviewed": _answer("Failed to accept the reviewed proposals", missing=404),
        "proposal.edit": _answer("Failed to edit proposal", wrap=False),
        "proposal.restore": _answer("Failed to restore proposal"),
        "proposal.defer": _answer("Failed to defer proposal"),
    }
    mount_router(router, produced(ctx, [d for d in PROJECT_OPERATIONS if d.service == "proposal_bridge_service"],
                                  answers, module=__name__, hand_written={"proposal.edit": _edit(registry, answers["proposal.edit"])},
                                  proposal_bridge_service=lambda: _service(ctx)))

    @router.get("/api/meetings/{meeting_id}/follow-through-proposals")
    def api_meeting_proposals(
        meeting_id: str,
        request: Request,
        state: Optional[str] = None,
    ) -> Any:
        try:
            proposals = _service(ctx).list_meeting_proposals(meeting_id, state=state)
            return JSONResponse({"meeting_id": meeting_id, "proposals": proposals})
        except Exception as exc:
            return error_500(exc, log, "Failed to list meeting proposals")

    @router.post("/api/proposals/{proposal_id}/confirm")
    def api_confirm_proposal(
        proposal_id: str,
        request: Request,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        try:
            result = _service(ctx).confirm_proposal(
                _principal(request),
                proposal_id,
                text=body.get("text"),
                owner=body.get("owner"),
                due=body.get("due"),
            )
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to confirm proposal")

    @router.post("/api/proposals/{proposal_id}/dismiss")
    def api_dismiss_proposal(
        proposal_id: str,
        request: Request,
    ) -> Any:
        try:
            result = _service(ctx).dismiss_proposal(_principal(request), proposal_id)
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to dismiss proposal")

    return router
