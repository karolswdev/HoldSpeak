"""Read-only capability run receipts for retry, inspection, and return."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives.invocations")


def recover_inference_on_startup() -> list[str]:
    """Project hub-killed, actually claimed inference attempts as unknown."""
    from ....db import get_database
    from ....kernel.runtime import _service
    from ....principals import Principal, PrincipalKind

    database, broker = get_database(), _service()
    claimed = [
        item for item in broker.store.operations_in_state("claimed")
        if item["name"] == "inference.run"
    ]
    recovered = database.capability_invocations.recover_running_unknown(
        [item["native_id"] for item in claimed]
    )
    for operation in claimed:
        if operation["native_id"] in recovered:
            node = Principal(PrincipalKind.NODE, operation["claimed_by"])
            broker.receipt(
                operation["operation_id"], "indeterminate",
                f"invocation:{operation['native_id']}", node,
            )
    return recovered


def build_invocations_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.get("/api/invocations")
    async def api_list_invocations(limit: int = 100) -> Any:
        try:
            from ....db import get_database
            rows = get_database().capability_invocations.list(limit=limit)
            return JSONResponse({"invocations": [row.to_dict() for row in rows]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list capability invocations")

    @router.get("/api/invocations/{invocation_id}")
    async def api_get_invocation(invocation_id: str) -> Any:
        try:
            from ....db import get_database
            row = get_database().capability_invocations.get(invocation_id)
            if row is None:
                return JSONResponse({"error": f"Unknown invocation: {invocation_id}"}, status_code=404)
            return JSONResponse({"invocation": row.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get capability invocation")

    @router.post("/api/invocations/{invocation_id}/cancel")
    async def api_cancel_invocation(invocation_id: str, request: Request) -> Any:
        """Submit, claim, and receipt an owner cancellation signal."""
        try:
            import uuid

            from ....db import get_database
            from ....kernel.runtime import _service
            from ....principals import Principal, PrincipalKind

            db = get_database()
            broker = _service()
            parent = broker.store.operation_for_native(invocation_id)
            if parent is None or parent["name"] != "inference.run":
                return JSONResponse({"error": f"Unknown inference run: {invocation_id}"}, status_code=404)
            signal_id = "cancel_" + uuid.uuid4().hex
            principal = getattr(
                request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
            )
            handle = broker.submit(
                {
                    "request_schema": 1, "request_id": signal_id,
                    "idempotency_key": signal_id,
                    "operation": {"name": "inference.cancel", "version": 1},
                    "parent_operation_id": parent["operation_id"],
                    "target": {}, "arguments": {
                        "invocation_id": invocation_id, "signal_id": signal_id,
                        "reason": "owner_cancelled",
                    },
                },
                principal,
            )
            if handle["state"] == "refused":
                return JSONResponse(handle, status_code=409)
            handle = broker.decide(
                handle["operation_id"], "approve", handle["revision"],
                principal,
            )
            node = Principal(
                PrincipalKind.NODE, str(parent["placement"]).removeprefix("node:")
            )
            claimed = broker.claim(node, signal_id)
            if not claimed["operations"]:
                return JSONResponse({"error": "cancellation claim failed"}, status_code=409)
            invocation = db.capability_invocations.cancel(invocation_id)
            receipt = broker.receipt(
                handle["operation_id"], "succeeded", f"invocation:{invocation_id}", node
            )
            return JSONResponse(
                {
                    "invocation": invocation.to_dict(),
                    "operation_id": handle["operation_id"], "receipt": receipt,
                },
                status_code=202,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel capability invocation")

    return router
