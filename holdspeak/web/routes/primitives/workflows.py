"""Workflows: CRUD (thin adapter) + the graph-aware hub run endpoint.

CRUD delegates to PrimitiveService (HS-122-01).
The run endpoint stays in the route layer — it owns ctx, WebSocket
broadcast, and the inference lifecycle (story 02/03 territory).
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.primitive_service import NotFound, PrimitiveService, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import (
    RunLifecycle, _json_body, _new_id, _persist_run_artifact, _render_user_prompt,
    _run_frame, capability_descriptor,
)

log = get_logger("web.routes.primitives")


def build_workflows_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database
        return PrimitiveService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/workflows")
    async def api_list_workflows(request: Request) -> Any:
        try:
            return JSONResponse({"workflows": _svc().list_workflows(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list workflows")

    @router.post("/api/workflows")
    async def api_create_workflow(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            workflow = _svc().create_workflow(
                _principal(request),
                workflow_id=str(body.get("id") or "") or None,
                name=str(body.get("name") or ""),
                prompt=str(body.get("prompt") or ""),
                graph_json=dict(body.get("graph_json") or {}),
            )
            return JSONResponse({"workflow": workflow}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create workflow")

    @router.get("/api/workflows/{workflow_id}")
    async def api_get_workflow(workflow_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"workflow": _svc().get_workflow(_principal(request), workflow_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get workflow")

    @router.put("/api/workflows/{workflow_id}")
    async def api_update_workflow(workflow_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            workflow = _svc().update_workflow(
                _principal(request),
                workflow_id,
                name=body.get("name"),
                prompt=body.get("prompt"),
                graph_json=body.get("graph_json"),
            )
            return JSONResponse({"workflow": workflow})
        except NotFound:
            return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update workflow")

    @router.delete("/api/workflows/{workflow_id}")
    async def api_delete_workflow(workflow_id: str, request: Request) -> Any:
        try:
            _svc().delete_workflow(_principal(request), workflow_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete workflow")

    @router.post("/api/workflows/{workflow_id}/run")
    async def api_run_workflow(workflow_id: str, request: Request) -> Any:
        """Run a Workflow.

        The Workbench saves a workflow as either a freeform `prompt` or a node
        graph (`graph_json`). Execution order:

        1. **Linear graph.** If the workflow has a `graph_json` that is an
           unambiguous single chain of LLM-call / prompt / pass-through nodes (no
           branch / forEach / while / sequence / fan-out), run the nodes in
           topological order, threading each node's output into the next node's
           input through the same engine path personas use. The per-node trail is
           returned as `steps`.
        2. **Prompt.** If the workflow has no graph and has a `prompt`, run it through
           the engine with an empty system prompt rendered against `{input}` +
           `variables`.
        3. **Unsupported graph.** If the graph contains control flow / fan-out the
           hub cannot execute, refuse it before Run. It is never lowered to a prompt;
           the exact graph remains available to a capable Workbench host.

        404 if the workflow is missing; 502 on engine failure (no silent empty).
        Returns `{workflow_id, output, provider}` (+ optional `steps`, `warning`,
        and a `sources` lineage array).
        """
        body = await _json_body(request) or {}
        lifecycle: Optional[RunLifecycle] = None
        try:
            from ....db import get_database
            db = get_database()
            workflow = db.workflows.get(workflow_id)
            if workflow is None:
                return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)

            lifecycle = RunLifecycle.begin(
                db, definition_ref=f"workflow:{workflow_id}", body=body,
            )

            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            user_input = str(body.get("input") or "")
            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ....intel.models import MeetingIntelError
            from ....inference_targets import (
                build_intel_for_target,
                resolve_inference_target,
                target_refusal,
                target_runtime_error,
            )
            from ..workflow_graph import (
                apply_pure_transform,
                build_node_prompt,
                linearize,
                on_node_error,
                resolved_failure_policy,
                _MODEL_KINDS,
                _PURE_TRANSFORM_KINDS,
            )

            sources: list[dict[str, str]] = [
                {"source_type": "workflow", "source_ref": workflow_id}
            ]
            wf_name = workflow.name or workflow_id
            target = resolve_inference_target(
                db,
                body.get("inference_target_id")
                or body.get("requested_placement")
                or "this_machine",
            )
            if not target.ready:
                lifecycle.start_attempt(destination=target.id, target=target)
                invocation = lifecycle.fail(target.readiness_reason, state="unavailable")
                return JSONResponse(
                    {**target_refusal(target), "workflow_id": workflow_id,
                     "invocation": invocation, "invocation_id": lifecycle.invocation_id},
                    status_code=409,
                )

            plan = linearize(workflow.graph_json) if workflow.graph_json else None
            if plan is not None and not plan.linearizable:
                error = (
                    "This Workflow is unavailable on this host: " + plan.reason
                    + ". Open it in a compatible Workbench; it was not lowered to a prompt."
                )
                invocation = lifecycle.fail(error, state="unavailable")
                return JSONResponse(
                    {"error": error, "workflow_id": workflow_id,
                     "support": "unsupported_graph", "invocation": invocation,
                     "invocation_id": lifecycle.invocation_id},
                    status_code=409,
                )

            _run_frame(ctx, "running", kind="workflow", ref=workflow_id, name=wf_name)
            if plan is not None and plan.linearizable:
                current = _render_user_prompt("", variables or {}, user_input)
                intel = build_intel_for_target(target, db)
                lifecycle.start_attempt(
                    destination=target.id,
                    target=target,
                )
                run_steps: list[dict[str, Any]] = []
                ran_a_model_op = False
                for gnode in plan.ordered:
                    if gnode.kind in _MODEL_KINDS:
                        node_prompt = build_node_prompt(gnode, current)
                        if not node_prompt.strip():
                            continue
                        try:
                            out = await asyncio.to_thread(
                                intel.run_prompt,
                                system_prompt="",
                                user_prompt=node_prompt,
                                temperature=float(temperature) if temperature is not None else None,
                                max_tokens=int(max_tokens) if max_tokens is not None else None,
                            )
                        except MeetingIntelError as exc:
                            error = target_runtime_error(target, exc)
                            handled = on_node_error(gnode, current)
                            if handled is None:
                                _run_frame(ctx, "error", kind="workflow",
                                           ref=workflow_id, name=wf_name,
                                           error=error)
                                invocation = lifecycle.fail(
                                    error, provider=getattr(intel, "active_provider", None)
                                )
                                return JSONResponse(
                                    {"error": error, "workflow_id": workflow_id,
                                     "node_id": gnode.id,
                                     "failure_policy": resolved_failure_policy(gnode),
                                     "invocation": invocation,
                                     "invocation_id": lifecycle.invocation_id},
                                    status_code=502,
                                )
                            current = handled
                            run_steps.append({
                                "node_id": gnode.id,
                                "kind": gnode.kind,
                                "output": current,
                                "provider": None,
                                "failure_policy": resolved_failure_policy(gnode),
                                "runs_on": gnode.runs_on,
                                "status": (
                                    "skipped"
                                    if resolved_failure_policy(gnode) == "skip"
                                    else "fell_back"
                                ),
                                "error": error,
                            })
                            continue
                        current = out
                        ran_a_model_op = True
                        run_steps.append({
                            "node_id": gnode.id,
                            "kind": gnode.kind,
                            "output": out,
                            "provider": intel.active_provider,
                            "failure_policy": resolved_failure_policy(gnode),
                            "runs_on": gnode.runs_on,
                            "status": "ok",
                        })
                    elif gnode.kind in _PURE_TRANSFORM_KINDS:
                        current = apply_pure_transform(gnode, current)
                        run_steps.append({
                            "node_id": gnode.id,
                            "kind": gnode.kind,
                            "output": current,
                            "provider": None,
                            "failure_policy": resolved_failure_policy(gnode),
                            "runs_on": gnode.runs_on,
                            "status": "ok",
                        })

                if not run_steps:
                    error = (
                        "Nothing executable ran; the Workflow input is retained for Retry."
                    )
                    invocation = lifecycle.fail(error, state="empty")
                    return JSONResponse(
                        {
                            "error": error,
                            "workflow_id": workflow_id,
                            "invocation": invocation,
                            "invocation_id": lifecycle.invocation_id,
                        },
                        status_code=400,
                    )

                if not str(current or "").strip():
                    error = "Workflow returned no output; the input is retained for Retry."
                    _run_frame(ctx, "error", kind="workflow", ref=workflow_id, name=wf_name, error=error)
                    invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                    return JSONResponse({"error": error, "workflow_id": workflow_id,
                                         "invocation": invocation,
                                         "invocation_id": lifecycle.invocation_id}, status_code=502)

                sources.extend(lifecycle.lineage())
                _run_frame(ctx, "ready", kind="workflow", ref=workflow_id, name=wf_name)
                artifact_id = _persist_run_artifact(
                    kind="workflow", name=workflow.name or workflow_id,
                    user_input=str(body.get("input") or ""),
                    output=str(current or ""), sources=sources,
                )
                if not artifact_id:
                    invocation = lifecycle.fail("The result could not be kept as an Artifact.")
                    return JSONResponse({"error": invocation["error"], "workflow_id": workflow_id,
                                         "invocation": invocation,
                                         "invocation_id": lifecycle.invocation_id}, status_code=500)
                invocation = lifecycle.succeed(
                    artifact_id,
                    provider=getattr(intel, "active_provider", None),
                    model=target.model,
                )
                return JSONResponse({
                    "workflow_id": workflow_id,
                    "output": current,
                    "provider": intel.active_provider if ran_a_model_op else None,
                    "steps": run_steps,
                    "sources": sources,
                    "artifact_id": artifact_id,
                    "result_ref": f"artifact:{artifact_id}",
                    "invocation_id": lifecycle.invocation_id,
                    "correlation_id": lifecycle.invocation_id,
                    "invocation": invocation,
                    "inference_target": target.to_dict(),
                    "actual_placement": invocation["attempts"][-1]["actual_placement"],
                })

            prompt = str(workflow.prompt or "").strip()

            user_prompt = _render_user_prompt(prompt, variables or {}, user_input)
            if not user_prompt.strip():
                error = "This Workflow has no runnable graph or prompt; its input is retained."
                invocation = lifecycle.fail(error, state="unavailable")
                return JSONResponse(
                    {
                        "error": error,
                        "workflow_id": workflow_id,
                        "invocation": invocation,
                        "invocation_id": lifecycle.invocation_id,
                    },
                    status_code=409,
                )

            intel = build_intel_for_target(target, db)
            lifecycle.start_attempt(
                destination=target.id,
                target=target,
            )
            try:
                output = await asyncio.to_thread(
                    intel.run_prompt,
                    system_prompt="",
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                error = target_runtime_error(target, exc)
                _run_frame(ctx, "error", kind="workflow", ref=workflow_id,
                           name=wf_name, error=error)
                invocation = lifecycle.fail(error, provider=getattr(intel, "active_provider", None))
                return JSONResponse(
                    {"error": error, "workflow_id": workflow_id,
                     "invocation": invocation,
                     "invocation_id": lifecycle.invocation_id}, status_code=502
                )

            if not str(output or "").strip():
                error = "Workflow returned no output; the input is retained for Retry."
                _run_frame(ctx, "error", kind="workflow", ref=workflow_id, name=wf_name, error=error)
                invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                return JSONResponse({"error": error, "workflow_id": workflow_id,
                                     "invocation": invocation,
                                     "invocation_id": lifecycle.invocation_id}, status_code=502)

            sources.extend(lifecycle.lineage())
            _run_frame(ctx, "ready", kind="workflow", ref=workflow_id, name=wf_name)
            artifact_id = _persist_run_artifact(
                kind="workflow", name=workflow.name or workflow_id,
                user_input=str(body.get("input") or ""),
                output=output, sources=sources,
            )
            if not artifact_id:
                invocation = lifecycle.fail("The result could not be kept as an Artifact.")
                return JSONResponse({"error": invocation["error"], "workflow_id": workflow_id,
                                     "invocation": invocation,
                                     "invocation_id": lifecycle.invocation_id}, status_code=500)
            invocation = lifecycle.succeed(
                artifact_id,
                provider=getattr(intel, "active_provider", None),
                model=target.model,
            )
            result: dict[str, Any] = {
                "workflow_id": workflow_id,
                "output": output,
                "provider": intel.active_provider,
                "sources": sources,
                "artifact_id": artifact_id,
                "result_ref": f"artifact:{artifact_id}",
                "invocation_id": lifecycle.invocation_id,
                "correlation_id": lifecycle.invocation_id,
                "invocation": invocation,
                "inference_target": target.to_dict(),
                "actual_placement": invocation["attempts"][-1]["actual_placement"],
            }
            return JSONResponse(result)
        except Exception as exc:
            if lifecycle is not None:
                try:
                    lifecycle.fail(str(exc))
                except Exception:
                    pass
            return error_500(exc, log, "Failed to run workflow")

    return router
