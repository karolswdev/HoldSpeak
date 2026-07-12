"""ControlMode policy inspection and scoped Grant management (HS-92-08)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.authority")


async def _body(request: Request) -> dict[str, Any] | None:
    try:
        value = await request.json()
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def build_authority_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.get("/api/authority/policy")
    async def api_authority_policy() -> Any:
        from ...config import Config
        from ...operation_policy import (
            HARD_INVARIANTS,
            INITIAL_FAMILIES,
            POLICY_CONTRACT_VERSION,
            POLICY_VERSION,
        )
        from ...product_language import control_mode_label, PRODUCT_LANGUAGE

        mode = Config.load().control_mode
        return JSONResponse(
            {
                "version": POLICY_CONTRACT_VERSION,
                "policy_version": POLICY_VERSION,
                "control_mode": mode,
                "control_mode_label": control_mode_label(mode),
                "control_mode_description": (
                    PRODUCT_LANGUAGE.control_mode_description(mode)
                ),
                "applies_to": "future_operations_only",
                "source": "config",
                "precedence": [
                    "hard_invariants",
                    "revocation",
                    "scoped_grant",
                    "control_mode",
                    "feature_default",
                ],
                "hard_invariants": list(HARD_INVARIANTS),
                "supported_families": sorted(INITIAL_FAMILIES),
                "unsupported_family_behavior": "refused",
            }
        )

    @router.put("/api/authority/control-mode")
    async def api_set_control_mode(request: Request) -> Any:
        body = await _body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        from ...product_language import (
            ProductLanguageError,
            control_mode_label,
            control_mode_wire,
        )

        try:
            requested = control_mode_wire(str(body.get("control_mode") or ""))
        except ProductLanguageError:
            return JSONResponse(
                {"error": "Control mode must be Secure, Normal, or YOLO."},
                status_code=400,
            )
        try:
            from ...config import Config

            config = Config.load()
            previous = config.control_mode
            config.control_mode = requested
            config.save()
            from ...db import get_database

            revoked = (
                get_database().actuators.revoke_active_grants(
                    reason="control_mode_changed"
                )
                if previous != requested
                else 0
            )
            return JSONResponse(
                {
                    "control_mode": requested,
                    "control_mode_label": control_mode_label(requested),
                    "previous_control_mode": previous,
                    "previous_control_mode_label": control_mode_label(previous),
                    "applies_to": "future_operations_only",
                    "source": "config",
                    "revoked_grants": revoked,
                }
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to update control mode")

    @router.post("/api/authority/evaluate")
    async def api_evaluate_operation(request: Request) -> Any:
        body = await _body(request)
        if body is None or not isinstance(body.get("operation"), dict):
            return JSONResponse(
                {"error": "operation object is required"}, status_code=400
            )
        try:
            from ...config import Config
            from ...operation_policy import describe_operation, resolve_policy

            raw = body["operation"]
            operation = describe_operation(
                operation_id=str(raw.get("operation_id") or "preview"),
                family=str(raw.get("family") or ""),
                effect_class=str(raw.get("effect_class") or ""),
                actor=str(raw.get("actor") or "owner"),
                destination=str(raw.get("destination") or ""),
                data_classes=raw.get("data_classes")
                if isinstance(raw.get("data_classes"), list)
                else [],
                project_scope=raw.get("project_scope"),
                resource_scope=raw.get("resource_scope"),
                fixed_destination=bool(raw.get("fixed_destination")),
                consequence=str(raw.get("consequence") or "execute_now"),
            )
            grant = None
            grant_id = str(body.get("grant_id") or "").strip()
            if grant_id:
                from ...db import get_database

                row = get_database().actuators.get_grant(grant_id)
                grant = row.to_dict() if row else None
            decision = resolve_policy(
                operation,
                mode=Config.load().control_mode,
                source="config",
                grant=grant,
                configured_preview=bool(body.get("configured_preview")),
            )
            return JSONResponse(
                {"operation": operation.to_dict(), "policy": decision.to_dict()}
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to evaluate operation")

    @router.get("/api/authority/grants")
    async def api_list_grants(actor: str | None = None) -> Any:
        try:
            from ...db import get_database

            rows = get_database().actuators.list_grants(actor=actor)
            return JSONResponse({"grants": [row.to_dict() for row in rows]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list grants")

    @router.post("/api/authority/grants")
    async def api_issue_grant(request: Request) -> Any:
        """Issue only from an existing fixed-destination proposal.

        This makes “newly discovered destination” structurally impossible: the
        exact normalized destination and scopes come from the durable proposal.
        """
        body = await _body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        proposal_id = str(body.get("proposal_id") or "").strip()
        actor = str(body.get("actor") or "owner").strip() or "owner"
        try:
            from ...config import Config
            from ...db import get_database
            from ...operation_policy import operation_for_proposal

            db = get_database()
            proposal = db.actuators.get_proposal(proposal_id)
            if proposal is None:
                return JSONResponse(
                    {"error": "Proposed action not found"}, status_code=404
                )
            operation = operation_for_proposal(proposal, actor=actor)
            if not operation.fixed_destination:
                return JSONResponse(
                    {
                        "error": "Grants may only bind an already configured fixed destination"
                    },
                    status_code=409,
                )
            control_mode = Config.load().control_mode
            if control_mode == "yolo":
                return JSONResponse(
                    {
                        "error": "YOLO uses the captured posture for eligible configured operations. Use Secure or Normal to issue a bounded grant."
                    },
                    status_code=409,
                )
            grant = db.actuators.issue_grant(
                actor=operation.actor,
                operation_family=operation.family,
                effect_class=operation.effect_class,
                destination=operation.destination,
                data_classes=list(operation.data_classes),
                project_scope=operation.project_scope,
                resource_scope=operation.resource_scope,
                ttl_seconds=int(body.get("ttl_seconds") or 3600),
                max_uses=int(body.get("max_uses") or 1),
                control_mode=control_mode,
            )
            return JSONResponse({"grant": grant.to_dict()}, status_code=201)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to issue grant")

    @router.delete("/api/authority/grants/{grant_id}")
    async def api_revoke_grant(grant_id: str) -> Any:
        try:
            from ...db import get_database

            if not get_database().actuators.revoke_grant(grant_id):
                return JSONResponse(
                    {"error": "Grant not found or already revoked"}, status_code=404
                )
            return JSONResponse(
                {"success": True, "grant_id": grant_id, "state": "revoked"}
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to revoke grant")

    @router.get("/api/authority/grants/{grant_id}/uses")
    async def api_grant_uses(grant_id: str) -> Any:
        try:
            from ...db import get_database

            db = get_database()
            if db.actuators.get_grant(grant_id) is None:
                return JSONResponse({"error": "Grant not found"}, status_code=404)
            return JSONResponse(
                {
                    "grant_id": grant_id,
                    "uses": db.actuators.list_grant_uses(grant_id),
                }
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to list grant uses")

    return router
