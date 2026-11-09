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
import uuid
from typing import Any, Optional

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
    ``delivery.pr_fetch``). Four verbs stay written here: ``send-agent``
    spawns an agent, ``propose`` and ``decide`` post to GitHub through the
    kernel, and ``draft-review`` is a model call through the engine door.
    The PR cache and its test seams live on ``ctx.delivery_service``."""
    delivery_service = delivery_declared.delivery_of(ctx)
    router = APIRouter()
    mount_router(router, delivery_declared.router(
        ctx, ("delivery.prs", "delivery.prs_refresh", "delivery.pr_diff", "delivery.pr_fetch"), module=__name__,
    ))

    def _service() -> Any:
        return delivery_service.pr_receipts()

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

    @router.post("/api/delivery/prs/{source_id}/{number}/draft-review")
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
                draft_review, _service(), kernel_service(), principal, source_id, number,
            )
            return JSONResponse(payload, status_code=status)
        except Exception as exc:
            log.error(f"pr review draft failed: {exc}")
            return JSONResponse({"error": "pr review draft failed"}, status_code=500)

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

#: The retry kind of a PR review draft; its key is ``<source id>|<number>``.
REVIEW_RETRY_KIND = "delivery.review"


def draft_review(service: Any, broker: Any, principal: Any, source_id: str, number: int) -> tuple[int, dict[str, Any]]:
    """Draft one PR review on the engine assigned to ``delivery.pr_review_draft``,
    through the engine door; ``(status, body)`` for the route (and for Retry)."""
    from ...services import engine_door

    context = service.action_context(source_id, number)
    if context.get("status") != "ok":
        return 404, {"error": "unknown_pr"}
    availability = ((context.get("row") or {}).get("verbs") or {}).get("draft_review") or {}
    if not availability.get("available"):
        return 409, {"error": "verb_unavailable", "verb": "draft_review",
                     "reason": availability.get("reason") or "unavailable"}
    material = service.review_material(source_id, number)
    if material.get("status") != "ok":
        return 409, {"error": "diff_unavailable", "reason": material.get("detail") or material.get("status")}
    try:
        engine = engine_door.engine_for(broker, "delivery.pr_review_draft")
    except engine_door.EngineDoorError:
        return 409, {"error": "delivery_pr_review_draft_refused", "reason": "inference_no_engine"}
    material_revision = str(material.get("revision") or "unversioned")
    diff_sha256 = hashlib.sha256(str(material.get("diff") or "").encode()).hexdigest()
    linked = material.get("linked") or []
    linked_text = "\n\n".join(str(item.get("text") or "") for item in linked)
    prompt = (
        f"Review PR #{number}. Return a concise GitHub review draft with concrete findings. "
        "Do not claim to have posted, approved, merged, or run checks.\n\n"
        f"Linked story and evidence:\n{linked_text[:48000]}\n\n"
        f"Diff:\n{str(material.get('diff') or '')[:120000]}"
    )

    def review_memory() -> Any:
        """Decisions and notes on the PR's subject (title, branch, story).

        The diff and the story are already in the prompt.
        """
        from ...db import get_database
        from ...services.memory_grounding import memory_for

        row = context.get("row") or {}
        return memory_for(
            "delivery.pr_review_draft",
            get_database(),
            query=" ".join(str(part or "") for part in (
                row.get("title"), row.get("head_ref"), material.get("story_id"),
            )),
        )

    payload = engine_door.with_memory(
        broker, engine,
        {
            "system_prompt": "You are a precise code reviewer. Findings first; cite files and lines when possible.",
            "user_prompt": prompt,
            "max_tokens": 1800,
            "temperature": None,
            "source_id": source_id,
            "number": number,
            "material_revision": material_revision,
            "diff_sha256": diff_sha256,
            "linked_revisions": [str(item.get("revision") or "") for item in linked],
        },
        review_memory,
        reserved_output_tokens=1800,
    )

    def projection(value: Any) -> dict[str, Any]:
        text = value.get("output") if isinstance(value, dict) else value
        return {"output": str(text or ""), "source_id": source_id, "number": number}

    try:
        answer = engine_door.run(
            broker, principal, "delivery.pr_review_draft", payload,
            engine=engine, deadline=300, stage=("delivery-pr-review", projection),
            retry=(REVIEW_RETRY_KIND, f"{source_id}|{number}"),
        )
    except engine_door.EngineDoorError as exc:
        return 409, {
            "error": "delivery_pr_review_draft_refused",
            "reason": "inference_" + (exc.outcome or exc.code),
            "operation_id": exc.operation_id,
        }
    published = answer.published if isinstance(answer.published, dict) else {}
    output = str(published.get("output") or "")
    artifact_id = str(published.get("artifact_id") or "")
    if not artifact_id or not output.strip():
        return 409, {"error": "delivery_pr_review_draft_refused"}
    return 200, {
        "output": output,
        "artifact_id": artifact_id,
        "result_ref": f"artifact:{artifact_id}",
        "invocation_id": answer.invocation_id,
        # The runner's kernel operation is the review's one receipt.
        "operation_id": answer.operation_id,
        "invocation": {"operation_id": answer.operation_id, "outcome": "succeeded"},
        "placement": {"source": "owner_assignment", "egress": {"scope": engine_door.egress_of(broker, answer.engine)}},
    }


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

