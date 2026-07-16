"""Chains (crews): CRUD + the hub run endpoint.

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import (
    RunLifecycle, _json_body, _new_id, _persist_run_artifact, _render_user_prompt,
    _run_frame, capability_descriptor,
)

log = get_logger("web.routes.primitives")


def build_chains_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _payload(db: Any, chain: Any) -> dict[str, Any]:
        missing = [rid for rid in chain.steps if db.recipes.get(str(rid)) is None]
        ready = bool(chain.steps) and not missing
        detail = ""
        if not chain.steps:
            detail = "Add at least one Persona to this linear Sequence."
        elif missing:
            detail = "Missing Personas: " + ", ".join(map(str, missing))
        row = chain.to_dict()
        row["capability"] = capability_descriptor(
            kind="sequence", name=chain.name or chain.id,
            readiness="ready" if ready else "unavailable", detail=detail,
            action_label=f"Run {chain.name or 'Sequence'}",
            support="linear_compatibility",
        )
        return row

    @router.get("/api/chains")
    async def api_list_chains() -> Any:
        try:
            from ....db import get_database
            db = get_database()
            chains = db.chains.list()
            return JSONResponse({"chains": [_payload(db, c) for c in chains]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list chains")

    @router.post("/api/chains")
    async def api_create_chain(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "Sequence name is required"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            chain = db.chains.upsert(
                chain_id=str(body.get("id") or _new_id("chain")),
                name=str(body.get("name") or ""),
                steps=list(body.get("steps") or []),
            )
            return JSONResponse({"chain": _payload(db, chain)}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create chain")

    @router.get("/api/chains/{chain_id}")
    async def api_get_chain(chain_id: str) -> Any:
        try:
            from ....db import get_database
            db = get_database()
            chain = db.chains.get(chain_id)
            if chain is None:
                return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
            return JSONResponse({"chain": _payload(db, chain)})
        except Exception as exc:
            return error_500(exc, log, "Failed to get chain")

    @router.put("/api/chains/{chain_id}")
    async def api_update_chain(chain_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.chains.get(chain_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
            chain = db.chains.upsert(
                chain_id=chain_id,
                name=str(body["name"]) if "name" in body else existing.name,
                steps=list(body["steps"]) if "steps" in body else existing.steps,
            )
            return JSONResponse({"chain": _payload(db, chain)})
        except Exception as exc:
            return error_500(exc, log, "Failed to update chain")

    @router.delete("/api/chains/{chain_id}")
    async def api_delete_chain(chain_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().chains.delete(chain_id)
            if not removed:
                return JSONResponse({"error": f"Unknown Sequence: {chain_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete chain")

    @router.post("/api/chains/{chain_id}/run")
    async def api_run_chain(chain_id: str, request: Request) -> Any:
        """Run a Chain (crew): each agent in `steps` in sequence, threading output.

        Each step loads its AgentRecord, renders its `user_template` against the
        current input (the previous step's output, or the request `input` for the
        first step) + the shared `variables`, and runs it through the same
        persona-run path as `POST /api/recipes/{id}/run`
        (`build_configured_meeting_intel().run_prompt`). 404 if the chain or any
        referenced agent is missing; 502 on the first engine failure (no silent
        empty). Returns the per-step trail plus the last step's output.
        """
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
                    "This Sequence has no Personas. Add one before running.", state="unavailable"
                )
                return JSONResponse(
                    {"error": "This Sequence has no Personas. Add one before running.",
                     "invocation": invocation, "invocation_id": lifecycle.invocation_id}, status_code=409
                )

            # Resolve every agent up front so a missing one 404s before any run.
            agents = []
            for recipe_id in steps:
                agent = db.recipes.get(str(recipe_id))
                if agent is None:
                    error = f"Persona {recipe_id} is unavailable; the Sequence was not run. Repair the Sequence and run it again."
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
                    # off the event loop: a mesh run WAITS on the relay queue,
                    # and THIS loop must serve the worker's claim polls
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
                    error = f"{agent.name or 'Persona'} returned no output; input is retained for Retry."
                    invocation = lifecycle.fail(error, state="empty", provider=getattr(intel, "active_provider", None))
                    return JSONResponse({"error": error, "chain_id": chain_id,
                                         "recipe_id": agent.id, "invocation": invocation,
                                         "invocation_id": lifecycle.invocation_id}, status_code=502)
                run_steps.append({
                    "recipe_id": agent.id,
                    "output": output,
                    "provider": intel.active_provider,
                })
                # Thread this step's output as the next step's input (the pipeline).
                current_input = output

            # Top-level provider = the last step's provider (so the web badge stops
            # reading "provider unknown"); per-step providers are kept on `steps`.
            top_provider = run_steps[-1]["provider"] if run_steps else None

            # Provenance: the chain, plus each step's agent as contributing source.
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

    # ── Workflows ─────────────────────────────────────────────────────────

    return router
