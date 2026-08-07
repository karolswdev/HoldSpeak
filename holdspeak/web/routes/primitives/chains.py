"""Chains (crews): CRUD (thin adapter) + the hub run endpoint.

CRUD delegates to PrimitiveService (HS-122-01).
The run endpoint stays in the route layer (story 02/03 territory).
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


def build_chains_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> PrimitiveService:
        from ....db import get_database
        return PrimitiveService(get_database())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/chains")
    async def api_list_chains(request: Request) -> Any:
        try:
            return JSONResponse({"chains": _svc().list_chains(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list chains")

    @router.post("/api/chains")
    async def api_create_chain(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            chain = _svc().create_chain(
                _principal(request),
                chain_id=str(body.get("id") or "") or None,
                name=str(body.get("name") or ""),
                steps=list(body.get("steps") or []),
            )
            return JSONResponse({"chain": chain}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create chain")

    @router.get("/api/chains/{chain_id}")
    async def api_get_chain(chain_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"chain": _svc().get_chain(_principal(request), chain_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get chain")

    @router.put("/api/chains/{chain_id}")
    async def api_update_chain(chain_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            chain = _svc().update_chain(
                _principal(request),
                chain_id,
                name=body.get("name"),
                steps=body.get("steps"),
            )
            return JSONResponse({"chain": chain})
        except NotFound:
            return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update chain")

    @router.delete("/api/chains/{chain_id}")
    async def api_delete_chain(chain_id: str, request: Request) -> Any:
        try:
            _svc().delete_chain(_principal(request), chain_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete chain")

    @router.post("/api/chains/{chain_id}/run")
    async def api_run_chain(chain_id: str, request: Request) -> Any:
        """Run a Chain (crew): each agent in `steps` in sequence, threading output."""
        body = await _json_body(request) or {}
        lifecycle: Optional[RunLifecycle] = None
        try:
            from ....db import get_database
            db = get_database()
            chain = db.chains.get(chain_id)
            if chain is None:
                return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)

            lifecycle = RunLifecycle.begin(
                db, definition_ref=f"sequence:{chain_id}", body=body,
            )

            steps = list(chain.steps or [])
            if not steps:
                invocation = lifecycle.fail(
                    "This Sequence has no Agents. Add one before running.", state="unavailable"
                )
                return JSONResponse(
                    {"error": "This Sequence has no Agents. Add one before running.",
                     "invocation": invocation, "invocation_id": lifecycle.invocation_id}, status_code=409
                )

            agents = []
            for recipe_id in steps:
                agent = db.recipes.get(str(recipe_id))
                if agent is None:
                    error = f"Agent {recipe_id} is unavailable; the Sequence was not run. Repair the Sequence and run it again."
                    invocation = lifecycle.fail(error, state="unavailable")
                    return JSONResponse(
                        {"error": error, "invocation": invocation,
                         "invocation_id": lifecycle.invocation_id}, status_code=409
                    )
                agents.append(agent)

            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ....intel.models import MeetingIntelError
            from ....inference_targets import (
                build_intel_for_target,
                resolve_inference_target,
                target_refusal,
                target_runtime_error,
            )

            target = resolve_inference_target(
                db,
                body.get("inference_target_id")
                or body.get("requested_placement")
                or "this_machine",
            )
            lifecycle.start_attempt(
                destination=target.id,
                target=target,
            )
            if not target.ready:
                invocation = lifecycle.fail(target.readiness_reason, state="unavailable")
                return JSONResponse(
                    {**target_refusal(target), "chain_id": chain_id,
                     "invocation": invocation, "invocation_id": lifecycle.invocation_id},
                    status_code=409,
                )
            intel = build_intel_for_target(target, db)

            _run_frame(ctx, "running", kind="chain", ref=chain_id, name=chain.name or chain_id)
            current_input = str(body.get("input") or "")
            run_steps: list[dict[str, Any]] = []
            for agent in agents:
                user_prompt = _render_user_prompt(
                    agent.user_template, variables or {}, current_input
                )
                if not user_prompt.strip():
                    error = f"Nothing to run for {agent.name or agent.id}; input is retained for Retry."
                    invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                    return JSONResponse(
                        {
                            "error": error,
                            "chain_id": chain_id,
                            "recipe_id": agent.id,
                            "invocation": invocation,
                            "invocation_id": lifecycle.invocation_id,
                        },
                        status_code=400,
                    )
                try:
                    output = await asyncio.to_thread(
                        intel.run_prompt,
                        system_prompt=agent.system_prompt,
                        user_prompt=user_prompt,
                        temperature=float(temperature) if temperature is not None else None,
                        max_tokens=int(max_tokens) if max_tokens is not None else None,
                    )
                except MeetingIntelError as exc:
                    error = target_runtime_error(target, exc)
                    _run_frame(ctx, "error", kind="chain", ref=chain_id,
                               name=chain.name or chain_id, error=error)
                    invocation = lifecycle.fail(error, provider=getattr(intel, "active_provider", None))
                    return JSONResponse(
                        {"error": error, "chain_id": chain_id, "recipe_id": agent.id,
                         "invocation": invocation, "invocation_id": lifecycle.invocation_id},
                        status_code=502,
                    )
                if not str(output or "").strip():
                    error = f"{agent.name or 'Agent'} returned no output; input is retained for Retry."
                    invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                    return JSONResponse({"error": error, "chain_id": chain_id,
                                         "recipe_id": agent.id, "invocation": invocation,
                                         "invocation_id": lifecycle.invocation_id}, status_code=502)
                run_steps.append({
                    "recipe_id": agent.id,
                    "output": output,
                    "provider": intel.active_provider,
                })
                current_input = output

            top_provider = run_steps[-1]["provider"] if run_steps else None

            sources: list[dict[str, str]] = [
                {"source_type": "chain", "source_ref": chain_id}
            ]
            for step in run_steps:
                sources.append(
                    {"source_type": "recipe", "source_ref": str(step["recipe_id"])}
                )
            sources.extend(lifecycle.lineage())

            _run_frame(ctx, "ready", kind="chain", ref=chain_id, name=chain.name or chain_id)
            artifact_id = _persist_run_artifact(
                kind="chain", name=chain.name or chain_id,
                user_input=str(body.get("input") or ""),
                output=run_steps[-1]["output"] if run_steps else "",
                sources=sources,
            )
            if not artifact_id:
                invocation = lifecycle.fail("The result could not be kept as an Artifact.")
                return JSONResponse({"error": invocation["error"], "chain_id": chain_id,
                                     "invocation": invocation,
                                     "invocation_id": lifecycle.invocation_id}, status_code=500)
            invocation = lifecycle.succeed(
                artifact_id, provider=top_provider, model=target.model
            )
            return JSONResponse({
                "chain_id": chain_id,
                "steps": run_steps,
                "output": run_steps[-1]["output"] if run_steps else "",
                "provider": top_provider,
                "sources": sources,
                "artifact_id": artifact_id,
                "result_ref": f"artifact:{artifact_id}",
                "invocation_id": lifecycle.invocation_id,
                "correlation_id": lifecycle.invocation_id,
                "invocation": invocation,
                "inference_target": target.to_dict(),
                "actual_placement": invocation["attempts"][-1]["actual_placement"],
            })
        except Exception as exc:
            if lifecycle is not None:
                try:
                    lifecycle.fail(str(exc))
                except Exception:
                    pass
            return error_500(exc, log, "Failed to run chain")

    return router
