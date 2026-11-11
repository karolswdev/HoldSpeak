"""PR-receipt routes (HS-104-04).

Read-only rows for registered sources; refresh is the surface verb
(one batched `gh` per source), the diff is local-only with the honest
absence + explicit-fetch offer. Reads never shell out; the cadence
hook runs only for sources whose registry entry explicitly set
`pr_refresh_seconds`. Blocking work runs off the event loop (the
Phase-85 rule); assembly is lazy (the delivery-router precedent).
"""
from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from . import delivery_declared
from ._mount import mount_router

log = get_logger("web.routes.delivery_prs")


def build_delivery_prs_router(ctx: WebContext) -> APIRouter:
    """The PR routes. The reads, the refresh and the fetch are produced from
    their rows (``delivery.prs``, ``delivery.prs_refresh``, ``delivery.pr_diff``,
    ``delivery.pr_fetch``). The handoff, proposal and decision also use declared rows.
    ``draft-review`` stays here: it stages a model result through the engine door.
    The PR cache and its test seams live on ``ctx.delivery_service``."""
    delivery_service = delivery_declared.delivery_of(ctx)
    router = APIRouter()
    mount_router(router, delivery_declared.router(
        ctx, ("delivery.prs", "delivery.prs_refresh", "delivery.pr_diff", "delivery.pr_fetch",
              "delivery.pr_send_agent", "delivery.pr_propose", "delivery.pr_decide"), module=__name__,
    ))

    async def api_delivery_pr_draft_review(
        source_id: str, number: int, request: Request,
    ) -> Any:
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        try:
            from ...kernel.runtime import _service as kernel_service
            from ...principals import PrincipalKind, PrincipalRight

            principal = request.state.principal
            if principal.kind is not PrincipalKind.OWNER or not principal.permits(PrincipalRight.OWNER):
                return JSONResponse({"error": "delivery_pr_review_owner_required"}, status_code=403)
            # E3: the retired per-request engine override is refused by name and
            # sends no PR material anywhere; the assignment names the engine.
            if str(body.get("inference_target_id") or "").strip():
                return JSONResponse({"error": "inference_request_target_override_retired"}, status_code=409)
            status, payload = await asyncio.to_thread(
                delivery_declared.registry_for(ctx)().invoke, principal, "delivery.pr_draft_review",
                {"source_id": source_id, "number": number}, shape="web",
            )
            return JSONResponse(payload, status_code=status)
        except Exception as exc:
            log.error(f"pr review draft failed: {exc}")
            return JSONResponse({"error": "pr review draft failed"}, status_code=500)

    from ...parity_operations import PARITY_OPERATIONS
    from ..operation_routes import operation_router
    mount_router(router, operation_router(
        [d for d in PARITY_OPERATIONS if d.name == "delivery.pr_draft_review"], delivery_declared.registry_for(ctx),
        delivery_declared._answer("delivery.pr_draft_review"), module=__name__,
        hand_written={"delivery.pr_draft_review": lambda d: api_delivery_pr_draft_review}))

    return router

#: The retry kind of a PR review draft; its key is ``<source id>|<number>``.


from ...services.delivery_review import REVIEW_RETRY_KIND, draft_review

def _retry_review(principal: Any, key: str) -> Any:
    """Retry from Needs you: draft the same PR's review again."""
    from ...delivery.pr_receipts import default_pr_receipts
    from ...kernel.runtime import _service as kernel_service
    from ...services import engine_door

    source_id, _, number = key.rpartition("|")
    status, body = draft_review(default_pr_receipts(), kernel_service(), principal, source_id, int(number))
    if status != 200:
        raise engine_door.EngineDoorError("failed", "The review draft did not run")
    return body


def _register_retry() -> None:
    from ...services import engine_door

    engine_door.on_retry(REVIEW_RETRY_KIND, engine_door.RetryKind(
        words="the review draft", object_kind="pr", open_ref=lambda _key: engine_door.ENGINES_REF,
        run=_retry_review,
    ))


_register_retry()

