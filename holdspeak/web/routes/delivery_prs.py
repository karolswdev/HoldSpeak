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
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_prs")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


def build_delivery_prs_router(
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
            from ...delivery import DeliveryRegistry
            from ...delivery.pr_receipts import PrReceiptsService

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

    @router.get("/api/delivery/prs")
    async def api_delivery_prs() -> Any:
        """Cached rows + freshness. Never shells; the only side path
        is the explicitly configured per-source cadence."""
        try:
            def read() -> dict[str, Any]:
                service = _service()
                service.maybe_cadence_refresh(_attempt_story_ids())
                return service.rows_view()

            return await asyncio.to_thread(read)
        except Exception as exc:
            return _classified_500(exc, "pr receipts read failed")

    @router.post("/api/delivery/prs/refresh")
    async def api_delivery_prs_refresh(source_id: Optional[str] = None) -> Any:
        """The manual verb — the one place a poll is asked for."""
        try:
            return await asyncio.to_thread(
                lambda: _service().refresh(source_id, attempt_story_ids=_attempt_story_ids())
            )
        except Exception as exc:
            return _classified_500(exc, "pr receipts refresh failed")

    @router.get("/api/delivery/prs/{source_id}/{number}/diff")
    async def api_delivery_pr_diff(source_id: str, number: int) -> Any:
        try:
            result = await asyncio.to_thread(lambda: _service().diff(source_id, number))
            status = 404 if result.get("status") == "unknown_pr" else 200
            return JSONResponse(result, status_code=status)
        except Exception as exc:
            return _classified_500(exc, "pr diff failed")

    @router.post("/api/delivery/prs/{source_id}/{number}/fetch")
    async def api_delivery_pr_fetch(source_id: str, number: int) -> Any:
        """The explicit egress act the diff absence offers."""
        try:
            result = await asyncio.to_thread(lambda: _service().fetch(source_id, number))
            status = 404 if result.get("status") == "unknown_pr" else 200
            return JSONResponse(result, status_code=status)
        except Exception as exc:
            return _classified_500(exc, "pr fetch failed")

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

    @router.post("/api/delivery/prs/{source_id}/{number}/send-agent")
    async def api_delivery_pr_send_agent(
        source_id: str, number: int, request: Request,
    ) -> Any:
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        context = _service().action_context(source_id, number)
        refused = _available(context, "send_agent")
        if refused:
            return refused
        material = _service().review_material(source_id, number)
        if material.get("status") != "ok":
            return JSONResponse(
                {"error": "diff_unavailable", "reason": material.get("detail") or material.get("status")},
                status_code=409,
            )
        row = context["row"]
        instruction = str(body.get("instruction") or "").strip()
        bounded = (
            f"PR #{number} {row.get('url')}\n"
            f"{instruction}\n\nDiff (bounded):\n{str(material.get('diff') or '')[:1600]}"
        )
        story_id = str(material.get("story_id") or f"PR-{number}")
        launch_request = {
            "agent_profile_id": str(body.get("agent_profile_id") or "claude-default"),
            "source_id": source_id,
            "worktree": {"mode": "existing", "worktree_id": context["worktree_id"]},
            "story_ref": {"project": "holdspeak", "story_id": story_id},
            "session_label": f"hs-pr-{number}-{uuid.uuid4().hex[:6]}",
        }
        try:
            service = delivery_service.default_launch_service()
            result = await asyncio.to_thread(
                service.submit_process_spawn,
                launch_request,
                bounded,
                request.state.principal,
            )
            return JSONResponse(result, status_code=202)
        except Exception as exc:
            reason = getattr(exc, "reason", "process_spawn_failed")
            return JSONResponse({"error": reason, "detail": str(exc)}, status_code=409)

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

    @router.post("/api/delivery/prs/{source_id}/{number}/draft-review")
    async def api_delivery_pr_draft_review(
        source_id: str, number: int, request: Request,
    ) -> Any:
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        context = _service().action_context(source_id, number)
        refused = _available(context, "draft_review")
        if refused:
            return refused
        material = _service().review_material(source_id, number)
        if material.get("status") != "ok":
            return JSONResponse(
                {"error": "diff_unavailable", "reason": material.get("detail") or material.get("status")},
                status_code=409,
            )
        lifecycle = None
        try:
            from ...deployment_revisions import capture_deployment_revision
            from ...inference_targets import resolve_placement
            from ...kernel.inference_runner import InvocationRequest, ServiceContract
            from ...kernel.prompt_adapter import CanonicalPromptAdapter
            from ...kernel.runtime import _as_principal, _service as kernel_service
            from ...db import get_database
            broker = kernel_service(); principal = request.state.principal; db = get_database()
            requested_target_id = str(body.get("inference_target_id") or "this_machine").strip()
            target = resolve_placement(db, invocation=requested_target_id).target
            if not target.ready: return JSONResponse({"error": target.readiness_reason}, status_code=409)
            revision = capture_deployment_revision(db, target); invocation_id = "pr_review_" + uuid.uuid4().hex
            diff_sha256 = __import__("hashlib").sha256(str(material.get("diff") or "").encode()).hexdigest()
            linked_text = "\n\n".join(str(item.get("text") or "") for item in material.get("linked") or [])
            prompt = f"Review PR #{number}. Return a concise GitHub review draft with concrete findings. Do not claim to have posted, approved, merged, or run checks.\n\nLinked story and evidence:\n{linked_text[:48000]}\n\nDiff:\n{str(material.get('diff') or '')[:120000]}"
            parent = broker.parent_run_controller.start(principal, kind="delivery.pr-review-draft", definition_ref=f"pr:{source_id}:{number}", definition_revision=str(material.get("revision") or "unversioned"), input_snapshot={"source_id":source_id,"number":number,"diff_sha256":diff_sha256}, deadline_at=time.time()+300, child_budget=1)
            payload = {"system_prompt":"You are a precise code reviewer. Findings first; cite files and lines when possible.","user_prompt":prompt,"max_tokens":1800,"temperature":None,"source_id":source_id,"number":number,"material_revision":str(material.get("revision") or "unversioned"),"diff_sha256":diff_sha256,"linked_revisions":[str(item.get("revision") or "") for item in material.get("linked") or []]}
            invoke = InvocationRequest(revision.id,ServiceContract.for_payload("holdspeak.delivery-pr-review","1",payload),time.time()+300,payload,invocation_id,parent.operation_id)
            def projection_payload(value: Any) -> dict[str, Any]:
                return {"output":str(dict(value).get("output") or ""),"source_id":source_id,"number":number}
            with _as_principal(principal): outcome = await asyncio.to_thread(broker.inference_runner.invoke,invoke,CanonicalPromptAdapter(),publish=broker.projection_stager.publisher(invocation_id,"delivery-pr-review",projection_payload),parent_context=parent.context)
            if outcome.outcome != "succeeded": broker.parent_run_controller.close(parent.context,outcome.outcome,principal=principal); return JSONResponse({"error":f"inference_{outcome.outcome}"},status_code=409)
            projection=broker.projection_stager.finalize(invocation_id)
            if projection is None:
                if broker.store.receipt(parent.operation_id) is None:
                    broker.parent_run_controller.close(parent.context, "cancelled", principal=principal)
                return JSONResponse({"error": "delivery_pr_review_cancelled"}, status_code=409)
            output=str(projection.get("output") or "")
            lifecycle = None
            artifact_id = str(projection.get("artifact_id") or "")
            if not artifact_id:
                broker.parent_run_controller.close(parent.context, "failed", principal=principal)
                return JSONResponse({"error": "artifact_persistence_failed"}, status_code=500)
            parent_receipt = broker.parent_run_controller.close(parent.context, "succeeded", artifact_id, principal=principal)
            return JSONResponse({"output": output, "artifact_id": artifact_id, "result_ref": f"artifact:{artifact_id}", "invocation_id": invocation_id, "operation_id": parent.operation_id, "invocation": {"operation_id": outcome.operation_id, "deployment_revision": revision.id, "outcome": outcome.outcome, "receipt": dict(outcome.receipt)}, "parent_receipt": dict(parent_receipt)})
        except Exception as exc:
            if lifecycle is not None:
                try:
                    lifecycle.fail(str(exc), state="failed")
                except Exception:
                    pass
            return _classified_500(exc, "pr review draft failed")

    @router.post("/api/delivery/prs/{source_id}/{number}/propose")
    async def api_delivery_pr_propose(
        source_id: str, number: int, request: Request,
    ) -> Any:
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        kind = str(body.get("kind") or "comment")
        verb = "post_status" if kind == "status" else "post_comment"
        context = _service().action_context(source_id, number)
        refused = _available(context, verb)
        if refused:
            return refused
        row = context["row"]
        proposal_id = str(uuid.uuid4())
        if kind == "status":
            preview = str(body.get("description") or "").strip()
            payload = {
                "repo": row.get("repo"), "sha": row.get("head_sha"),
                "state": str(body.get("state") or "pending"),
                "context": str(body.get("context") or "HoldSpeak"),
                "description": preview,
            }
            action = "set_commit_status"
        else:
            preview = str(body.get("body") or "").strip()
            payload = {"repo": row.get("repo"), "number": number, "body": preview}
            action = "comment_pr"
        if not preview:
            return JSONResponse({"error": "proposal_text_required"}, status_code=400)
        from ...kernel.runtime import _service as kernel_service

        broker = kernel_service()
        handle = broker.submit(
            {
                "request_schema": 1,
                "request_id": str(uuid.uuid4()),
                "idempotency_key": f"pr-proposal:{proposal_id}",
                "operation": {"name": "actuator.egress", "version": 1},
                "subject_refs": [f"pr:{source_id}:{number}"],
                "target": {"ref": f"actuator:{proposal_id}"},
                "arguments": {
                    "proposal_id": proposal_id,
                    "origin": "desk",
                    "window_id": f"pr-{source_id}-{number}",
                    "plugin_id": "github_pr_follow",
                    "plugin_version": "1",
                    "target": "github",
                    "action": action,
                    "preview": preview,
                    "payload": payload,
                    "reversible": False,
                    "required_capabilities": ["actuator"],
                },
                "placement": "node:actuator-local",
            },
            request.state.principal,
        )
        status = 409 if handle.get("state") == "refused" else 202
        return JSONResponse({**handle, "proposal_id": proposal_id, "preview": preview, "kind": kind}, status_code=status)

    @router.post("/api/delivery/prs/proposals/{proposal_id}/decide")
    async def api_delivery_pr_decide(proposal_id: str, request: Request) -> Any:
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        decision = str(body.get("decision") or "")
        if decision not in {"approve", "reject"}:
            return JSONResponse({"error": "decision_unknown"}, status_code=400)
        from ...kernel.runtime import _service as kernel_service
        from .actuator_shared import execute_github_proposal, proposal_to_dict

        broker = kernel_service()
        projection = broker.read(
            [f"actuator:{proposal_id}"], "state", "committed", request.state.principal
        )
        objects = projection.get("objects") or []
        if not objects:
            return JSONResponse({"error": "proposal_unknown"}, status_code=404)
        operation = objects[0]["operation"]
        try:
            handle = broker.decide(
                operation["operation_id"], decision, operation["revision"], request.state.principal
            )
        except Exception as exc:
            return JSONResponse({"error": getattr(exc, "reason", "decision_failed")}, status_code=409)
        try:
            proposal = delivery_service.actuator_proposal(proposal_id)
        except Exception:
            return JSONResponse({"error": "proposal_unknown"}, status_code=404)
        if decision == "reject":
            return JSONResponse({**handle, "proposal": proposal_to_dict(proposal)})
        executed = await asyncio.to_thread(
            delivery_service.execute_actuator_proposal,
            execute_github_proposal,
            ctx,
            proposal,
            actor=request.state.principal.identity,
        )
        return JSONResponse({**handle, "proposal": proposal_to_dict(executed)})

    return router
