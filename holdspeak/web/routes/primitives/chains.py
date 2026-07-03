"""Chains (crews): CRUD + the hub run endpoint.

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives")
from ._shared import _json_body, _new_id, _persist_run_artifact, _render_user_prompt, _run_frame, canonical_source_type


def build_chains_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/chains")
    async def api_list_chains() -> Any:
        try:
            from ....db import get_database
            chains = get_database().chains.list()
            return JSONResponse({"chains": [c.to_dict() for c in chains]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list chains")

    @router.post("/api/chains")
    async def api_create_chain(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "chain name is required"}, status_code=400)
        try:
            from ....db import get_database
            chain = get_database().chains.upsert(
                chain_id=str(body.get("id") or _new_id("chain")),
                name=str(body.get("name") or ""),
                steps=list(body.get("steps") or []),
            )
            return JSONResponse({"chain": chain.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create chain")

    @router.get("/api/chains/{chain_id}")
    async def api_get_chain(chain_id: str) -> Any:
        try:
            from ....db import get_database
            chain = get_database().chains.get(chain_id)
            if chain is None:
                return JSONResponse({"error": f"Unknown chain: {chain_id}"}, status_code=404)
            return JSONResponse({"chain": chain.to_dict()})
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
                return JSONResponse({"error": f"Unknown chain: {chain_id}"}, status_code=404)
            chain = db.chains.upsert(
                chain_id=chain_id,
                name=str(body["name"]) if "name" in body else existing.name,
                steps=list(body["steps"]) if "steps" in body else existing.steps,
            )
            return JSONResponse({"chain": chain.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update chain")

    @router.delete("/api/chains/{chain_id}")
    async def api_delete_chain(chain_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().chains.delete(chain_id)
            if not removed:
                return JSONResponse({"error": f"Unknown chain: {chain_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete chain")

    @router.post("/api/chains/{chain_id}/run")
    async def api_run_chain(chain_id: str, request: Request) -> Any:
        """Run a Chain (crew): each agent in `steps` in sequence, threading output.

        Each step loads its AgentRecord, renders its `user_template` against the
        current input (the previous step's output, or the request `input` for the
        first step) + the shared `variables`, and runs it through the same
        persona-run path as `POST /api/agents/{id}/run`
        (`build_configured_meeting_intel().run_prompt`). 404 if the chain or any
        referenced agent is missing; 502 on the first engine failure (no silent
        empty). Returns the per-step trail plus the last step's output.
        """
        body = await _json_body(request) or {}
        try:
            from ....db import get_database
            db = get_database()
            chain = db.chains.get(chain_id)
            if chain is None:
                return JSONResponse({"error": f"Unknown chain: {chain_id}"}, status_code=404)

            steps = list(chain.steps or [])
            if not steps:
                return JSONResponse(
                    {"error": f"chain {chain_id} has no steps to run"}, status_code=400
                )

            # Resolve every agent up front so a missing one 404s before any run.
            agents = []
            for agent_id in steps:
                agent = db.agents.get(str(agent_id))
                if agent is None:
                    return JSONResponse(
                        {"error": f"Unknown agent in chain: {agent_id}"}, status_code=404
                    )
                agents.append(agent)

            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ....intel.providers import build_configured_meeting_intel
            from ....intel.models import MeetingIntelError

            intel = build_configured_meeting_intel()

            _run_frame(ctx, "running", kind="chain", ref=chain_id, name=chain.name or chain_id)
            current_input = str(body.get("input") or "")
            run_steps: list[dict[str, Any]] = []
            for agent in agents:
                user_prompt = _render_user_prompt(
                    agent.user_template, variables or {}, current_input
                )
                if not user_prompt.strip():
                    return JSONResponse(
                        {
                            "error": (
                                f"nothing to run for step {agent.id}: provide `input` "
                                "or an agent user_template"
                            ),
                            "chain_id": chain_id,
                            "agent_id": agent.id,
                        },
                        status_code=400,
                    )
                try:
                    output = intel.run_prompt(
                        system_prompt=agent.system_prompt,
                        user_prompt=user_prompt,
                        temperature=float(temperature) if temperature is not None else None,
                        max_tokens=int(max_tokens) if max_tokens is not None else None,
                    )
                except MeetingIntelError as exc:
                    _run_frame(ctx, "error", kind="chain", ref=chain_id,
                               name=chain.name or chain_id, error=str(exc))
                    return JSONResponse(
                        {"error": str(exc), "chain_id": chain_id, "agent_id": agent.id},
                        status_code=502,
                    )
                run_steps.append({
                    "agent_id": agent.id,
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
                    {"source_type": "agent", "source_ref": str(step["agent_id"])}
                )

            _run_frame(ctx, "ready", kind="chain", ref=chain_id, name=chain.name or chain_id)
            artifact_id = _persist_run_artifact(
                kind="chain", name=chain.name or chain_id,
                user_input=str(body.get("input") or ""),
                output=run_steps[-1]["output"] if run_steps else "",
                sources=sources,
            )
            return JSONResponse({
                "chain_id": chain_id,
                "steps": run_steps,
                "output": run_steps[-1]["output"] if run_steps else "",
                "provider": top_provider,
                "sources": sources,
                "artifact_id": artifact_id,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to run chain")

    # ── Workflows ─────────────────────────────────────────────────────────

    return router
