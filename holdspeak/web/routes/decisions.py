"""Authenticated decision-record reads and owner lifecycle gestures (HS-109-01)."""
from __future__ import annotations

import asyncio
import time
import uuid
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


def _kernel_service() -> Any:
    from ...kernel.runtime import _service

    return _service()


async def _generate_with_model(db: Any, target: Any, prompt: str) -> tuple[str, Any]:
    from ...inference_targets import build_intel_for_target

    intel = build_intel_for_target(target, db)
    output = await asyncio.to_thread(
        intel.run_prompt,
        system_prompt=(
            "Draft one concise artifact from the accepted decision. Preserve the "
            "decision's meaning. Return Markdown only and do not invent approval."
        ),
        user_prompt=prompt,
        max_tokens=1200,
    )
    return str(output or "").strip(), intel


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
        # Authored Desk ADRs use the Desk primitive policy; the legacy
        # meeting-memory projection keeps its established read authority.
        is_desk_read = not any((project_id, project_key, meeting_id, lifecycle))
        if not is_desk_read:
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

            db = get_database()
            # HS-113-08: unqualified Desk reads address authored ADRs. The
            # established Project Memory API always supplies a query/filter and
            # remains a read-only view of meeting-derived decision memory.
            if not any((project_key, project_id, meeting_id, lifecycle)):
                rows = db.desk_decisions.list(limit=limit)
                return JSONResponse({"decisions": [row.to_dict() for row in rows]})
            rows = db.decisions.list(
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
        from ...db import get_database

        db = get_database()
        desk_decision = db.desk_decisions.get(decision_id)
        if desk_decision is not None:
            return JSONResponse({"decision": desk_decision.to_dict()})
        denied = _authority_refusal(request, PrincipalRight.READ)
        if denied is not None:
            return denied
        result = db.decisions.get_with_lineage(decision_id)
        if result is None:
            return JSONResponse({"error": "decision_not_found"}, status_code=404)
        return JSONResponse(result)

    @router.get("/{decision_id}/moment")
    async def get_decision_moment(decision_id: str, request: Request) -> Any:
        denied = _authority_refusal(request, PrincipalRight.READ)
        if denied is not None:
            return denied
        from ...db import get_database

        repository = get_database().decisions
        decision = repository.get(decision_id)
        if decision is None:
            return JSONResponse({"error": "decision_not_found"}, status_code=404)
        moment = repository.resolve_decision_moment(decision_id)
        if moment is None:
            return JSONResponse(
                {"error": "decision_moment_unavailable", "decision_id": decision_id},
                status_code=404,
            )
        return JSONResponse(
            {
                "decision_id": decision.id,
                "provenance_label": decision.provenance_label,
                "moment": moment.to_dict(),
            }
        )

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
        from ...db import get_database

        desk_decision = get_database().desk_decisions.get(decision_id)
        if desk_decision is not None:
            successor = get_database().desk_decisions.supersede(
                decision_id, "decision_" + uuid.uuid4().hex[:12]
            )
            return JSONResponse({"decision": successor.to_dict()}, status_code=201)
        return _transition_response(
            decision_id,
            request,
            "supersede",
            str(payload.get("superseded_by") or ""),
        )

    def _promotion_refusal(exc: Exception) -> JSONResponse:
        from ...db.decisions import DecisionPromotionRefused

        if isinstance(exc, KeyError):
            return JSONResponse({"error": "decision_not_found"}, status_code=404)
        if isinstance(exc, DecisionPromotionRefused):
            return JSONResponse(
                {"error": exc.code, "decision_id": exc.decision_id, "detail": exc.detail},
                status_code=409,
            )
        return JSONResponse({"error": str(exc)}, status_code=400)

    @router.post("/{decision_id}/promote/{artifact_type}")
    async def promote_decision(
        decision_id: str, artifact_type: str, request: Request
    ) -> Any:
        denied = _owner(request)
        if denied is not None:
            return denied
        from ...db import get_database

        db = get_database()
        try:
            receipt = db.decisions.promote(
                decision_id,
                artifact_type,
                actor=request.state.principal.identity,
            )
        except (KeyError, ValueError) as exc:
            return _promotion_refusal(exc)
        artifact = db.plugins.get_artifact(receipt.artifact_id)
        decision = db.decisions.get(decision_id)
        return JSONResponse(
            {
                "decision": decision.to_dict() if decision else None,
                "artifact": artifact.to_dict() if artifact else None,
                "receipt": receipt.to_dict(),
            }
        )

    @router.post("/{decision_id}/promote/{artifact_type}/draft-with-model")
    async def draft_promoted_decision_with_model(
        decision_id: str,
        artifact_type: str,
        request: Request,
        payload: dict[str, Any] = Body(default={}),
    ) -> Any:
        denied = _owner(request)
        if denied is not None:
            return denied
        from ...db import get_database
        from ...inference_targets import resolve_inference_target, target_refusal
        from .primitives._shared import RunLifecycle

        db = get_database()
        try:
            decision = db.decisions.assert_promotable(decision_id)
            # Also validate the requested artifact kind before asking admission.
            from ...db.decisions import derive_promoted_artifact_id

            derive_promoted_artifact_id(decision_id, artifact_type)
        except (KeyError, ValueError) as exc:
            return _promotion_refusal(exc)

        requested_target_id = str(
            payload.get("inference_target_id") or "this_machine"
        ).strip()
        invocation_id = "invocation_" + uuid.uuid4().hex
        broker = _kernel_service()
        handle = broker.submit(
            {
                "request_schema": 1,
                "request_id": str(uuid.uuid4()),
                "idempotency_key": invocation_id,
                "operation": {"name": "inference.run", "version": 1},
                "target": {},
                "arguments": {
                    "invocation_id": invocation_id,
                    "definition_ref": "program:decision-promotion-v1",
                    "definition_revision": "1",
                    "grounding_refs": [
                        {"ref": f"decision:{decision.id}", "revision": decision.updated_at},
                        {
                            "ref": f"meeting:{decision.source_meeting_id}",
                            "revision": decision.decided_at,
                        },
                    ],
                    "requested_target_id": requested_target_id,
                    "deadline_at": time.time() + 300.0,
                    "input_snapshot": {
                        "decision_id": decision.id,
                        "artifact_type": str(artifact_type).strip().lower(),
                    },
                },
            },
            request.state.principal,
        )
        if handle.get("state") == "refused":
            return JSONResponse(handle, status_code=409)
        try:
            handle = broker.decide(
                handle["operation_id"],
                "approve",
                handle["revision"],
                request.state.principal,
            )
        except Exception as exc:
            return JSONResponse(
                {"error": getattr(exc, "reason", "inference_admission_failed"), "detail": str(exc)},
                status_code=409,
            )

        lifecycle = RunLifecycle(
            db,
            invocation_id,
            "program:decision-promotion-v1",
            operation_id=handle["operation_id"],
            broker=broker,
        )
        target = resolve_inference_target(db, requested_target_id)
        try:
            lifecycle.start_attempt(destination=target.id, target=target)
            if not target.ready:
                invocation = lifecycle.fail(target.readiness_reason, state="unavailable")
                return JSONResponse(
                    {**target_refusal(target), "invocation": invocation}, status_code=409
                )
            prompt = (
                f"Artifact type: {str(artifact_type).strip().lower()}\n"
                f"Decision: {decision.text}\n"
                f"Rationale: {decision.rationale or 'Not recorded'}\n"
                f"Decided at: {decision.decided_at}\n"
                f"Meeting: {decision.source_meeting_id}"
            )
            output, intel = await _generate_with_model(db, target, prompt)
            if not output:
                invocation = lifecycle.fail("model_returned_empty_output", state="empty")
                return JSONResponse(
                    {"error": "model_returned_empty_output", "invocation": invocation},
                    status_code=409,
                )
            receipt = db.decisions.promote(
                decision.id,
                artifact_type,
                actor=request.state.principal.identity,
                body_markdown=output,
                review_status="draft",
                model_assisted=True,
            )
            invocation = lifecycle.succeed(
                receipt.artifact_id,
                provider=getattr(intel, "active_provider", None),
                model=target.model,
            )
            artifact = db.plugins.get_artifact(receipt.artifact_id)
            return JSONResponse(
                {
                    "decision": decision.to_dict(),
                    "artifact": artifact.to_dict() if artifact else None,
                    "receipt": receipt.to_dict(),
                    "operation_id": handle["operation_id"],
                    "invocation_id": invocation_id,
                    "invocation": invocation,
                    "inference_target": target.to_dict(),
                }
            )
        except Exception as exc:
            try:
                lifecycle.fail(str(exc))
            except Exception:
                pass
            if isinstance(exc, (KeyError, ValueError)):
                return _promotion_refusal(exc)
            return JSONResponse(
                {"error": "decision_promotion_generation_failed", "detail": str(exc)},
                status_code=500,
            )

    return router
