"""Authenticated decision-record reads and owner lifecycle gestures (HS-109-01)."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse

from ...principals import (
    PrincipalKind,
    PrincipalRight,
    UNAUTHENTICATED,
    refusal,
)
from ..context import WebContext


def _authority_refusal(request: Request, right: PrincipalRight) -> Optional[JSONResponse]:
    principal = getattr(request.state, "principal", UNAUTHENTICATED)
    if principal.permits(right):
        return None
    status = 401 if principal.kind is PrincipalKind.NONE else 403
    return JSONResponse(refusal(principal, right), status_code=status)


def build_decisions_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter(prefix="/api/decisions", tags=["decisions"])

    @router.get("")
    async def list_decisions(
        request: Request,
        project_id: Optional[str] = None,
        project_key: Optional[str] = None,
        meeting_id: Optional[str] = None,
        lifecycle: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Any:
        denied = _authority_refusal(request, PrincipalRight.READ)
        if denied is not None:
            return denied
        if project_id and project_key and project_id != project_key:
            return JSONResponse(
                {"error": "project_id and project_key must name the same project"},
                status_code=400,
            )
        try:
            from ...db import get_database

            rows = get_database().decisions.list(
                project_key=project_key or project_id,
                meeting_id=meeting_id,
                lifecycle=lifecycle,
                limit=limit,
                offset=offset,
            )
            return JSONResponse(
                {
                    "decisions": [row.to_dict() for row in rows],
                    "page": {
                        "offset": max(0, int(offset)),
                        "limit": max(1, min(int(limit), 500)),
                        "count": len(rows),
                    },
                }
            )
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    @router.get("/{decision_id}")
    async def get_decision(decision_id: str, request: Request) -> Any:
        denied = _authority_refusal(request, PrincipalRight.READ)
        if denied is not None:
            return denied
        from ...db import get_database

        result = get_database().decisions.get_with_lineage(decision_id)
        if result is None:
            return JSONResponse({"error": "decision_not_found"}, status_code=404)
        return JSONResponse(result)

    def _owner(request: Request) -> Optional[JSONResponse]:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        if principal.kind is PrincipalKind.OWNER and principal.permits(PrincipalRight.OWNER):
            return None
        status = 401 if principal.kind is PrincipalKind.NONE else 403
        return JSONResponse(refusal(principal, PrincipalRight.OWNER), status_code=status)

    def _transition_response(
        decision_id: str,
        request: Request,
        action: str,
        superseded_by: Optional[str] = None,
    ) -> JSONResponse:
        denied = _owner(request)
        if denied is not None:
            return denied
        from ...db import get_database
        from ...db.decisions import DecisionTransitionRefused

        db = get_database()
        principal = request.state.principal
        try:
            if action == "accept":
                receipt = db.decisions.accept(decision_id, actor=principal.identity)
            elif action == "reject":
                receipt = db.decisions.reject(decision_id, actor=principal.identity)
            else:
                receipt = db.decisions.supersede(
                    decision_id,
                    str(superseded_by or "").strip(),
                    actor=principal.identity,
                )
        except KeyError:
            return JSONResponse({"error": "decision_not_found"}, status_code=404)
        except DecisionTransitionRefused as exc:
            return JSONResponse(
                {
                    "error": exc.code,
                    "current_lifecycle": exc.current,
                    "action": exc.action,
                    "detail": str(exc),
                },
                status_code=409,
            )
        record = db.decisions.get(decision_id)
        return JSONResponse(
            {
                "decision": record.to_dict() if record else None,
                "receipt": receipt.to_dict(),
            }
        )

    @router.post("/{decision_id}/accept")
    async def accept_decision(decision_id: str, request: Request) -> Any:
        return _transition_response(decision_id, request, "accept")

    @router.post("/{decision_id}/reject")
    async def reject_decision(decision_id: str, request: Request) -> Any:
        return _transition_response(decision_id, request, "reject")

    @router.post("/{decision_id}/supersede")
    async def supersede_decision(
        decision_id: str,
        request: Request,
        payload: dict[str, Any] = Body(default={}),
    ) -> Any:
        return _transition_response(
            decision_id,
            request,
            "supersede",
            str(payload.get("superseded_by") or ""),
        )

    return router
