"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/delivery_prs.py``: POST /api/delivery/prs/launches/{launch_id}/input.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""PR-receipt routes (HS-104-04).

Read-only rows for registered sources; refresh is the surface verb
(one batched `gh` per source), the diff is local-only with the honest
absence + explicit-fetch offer. Reads never shell out; the cadence
hook runs only for sources whose registry entry explicitly set
`pr_refresh_seconds`. Blocking work runs off the event loop (the
Phase-85 rule); assembly is lazy (the delivery-router precedent).
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext

log = get_logger("web.routes.delivery_prs")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


def _legacy_review_matches(
    broker: Any, identity: str, linked_text: str, linked_revisions: list[str],
) -> bool:
    """A review admitted under the pre-story *identity* with this same story.

    Before 2026-10-05 the identity left the linked story out, so such a run
    stored the story only in its admitted prompt. It replays (one artifact, no
    model call) only when that prompt holds this exact story text and the same
    story revisions; an edited story is a new run.
    """
    operation_id = "delivery-pr-review:" + __import__("hashlib").sha256(identity.encode()).hexdigest()
    try:
        prior = broker.inference_adoption_service.admitted_payload(operation_id)
    except Exception:  # no adoption store: nothing was admitted before
        return False
    if not prior:
        return False
    block = f"Linked story and evidence:\n{linked_text[:48000]}\n\nDiff:\n"
    return (
        block in str(prior.get("user_prompt") or "")
        and list(prior.get("linked_revisions") or []) == linked_revisions
    )


def parked_build_delivery_prs_router(
    ctx: WebContext,
    *,
    service: Any = None,
    attempts_service: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    runner: Any = None,
) -> APIRouter:
    delivery_service = ctx.delivery_service
    if delivery_service is None:
        raise RuntimeError("DeliveryService must be supplied at application composition")
    router = APIRouter()
    holder: dict[str, Any] = {"service": service, "attempts": attempts_service}

    def _service() -> Any:
        if holder["service"] is None:
            from ....delivery import DeliveryRegistry
            from ....delivery.pr_receipts import PrReceiptsService, default_pr_receipts

            if registry_path is None and map_path is None and runner is None:
                # Production: the cache the Heartbeat sweep refreshes.
                holder["service"] = default_pr_receipts()
            else:
                registry = DeliveryRegistry(registry_path, map_path=map_path)
                holder["service"] = PrReceiptsService(registry, runner=runner)
        return holder["service"]

    def _attempt_story_ids() -> list[str]:
        """Story ids from the durable Work attempts — the heuristic
        correlation input. Best-effort: an empty list only means no
        heuristic labels, never a failure."""
        try:
            if holder["attempts"] is not None:
                rows = holder["attempts"].list()
            else:
                rows = delivery_service.list_work_attempts()
            ids = []
            for row in rows:
                story_id = getattr(row, "story_id", None) or (
                    row.get("story_id") if isinstance(row, dict) else None
                )
                if story_id:
                    ids.append(str(story_id))
            return sorted(set(ids))
        except Exception:
            return []

    def _available(context: dict[str, Any], verb: str) -> Optional[JSONResponse]:
        if context.get("status") != "ok":
            return JSONResponse({"error": "unknown_pr"}, status_code=404)
        availability = ((context.get("row") or {}).get("verbs") or {}).get(verb) or {}
        if not availability.get("available"):
            return JSONResponse(
                {"error": "verb_unavailable", "verb": verb,
                 "reason": availability.get("reason") or "unavailable"},
                status_code=409,
            )
        return None

    @router.post("/api/delivery/prs/launches/{launch_id}/input")
    async def api_delivery_pr_launch_input(launch_id: str, request: Request) -> Any:
        """Send bounded follow-up text to the exact spawned PR agent.

        This is intentionally not a fourth visible verb: it is the transport
        leg used by the in-place agent conversation, and remains a child
        ``process.input`` of the running ``process.spawn`` operation.
        """
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        text = str(body.get("text") or "").strip()
        if not text or len(text) > 1600:
            return JSONResponse({"error": "input_invalid"}, status_code=400)
        service = delivery_service.default_launch_service()
        record = service.launch_record(launch_id)
        if record is None:
            return JSONResponse({"error": "launch_unknown"}, status_code=404)
        target = record.get("target") or {}
        try:
            result = await asyncio.to_thread(
                service._commands.submit_process_input,
                {
                    "node_id": str(record.get("node_id") or "local"),
                    "target_id": target.get("target_id"),
                    "target_generation": target.get("target_generation"),
                    "operation": {"family": "coder_steering", "verb": "terminal.text"},
                    "payload": {
                        "text": text,
                        "submit": True,
                        "session_key": record.get("session"),
                        "agent": str(record.get("profile_id") or "agent"),
                    },
                    "parent_operation_id": str(record.get("operation_id") or ""),
                },
                request.state.principal,
            )
            return JSONResponse(result, status_code=202)
        except Exception as exc:
            reason = getattr(exc, "reason", "process_input_failed")
            return JSONResponse({"error": reason, "detail": str(exc)}, status_code=409)

    return router
