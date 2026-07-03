"""Agents (personas): CRUD + the hub run endpoint.

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


def build_agents_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _agent_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "avatar": str(pick("avatar", existing.avatar if existing else "")),
            "role": str(pick("role", existing.role if existing else "")),
            "system_prompt": str(pick("system_prompt", existing.system_prompt if existing else "")),
            "user_template": str(pick("user_template", existing.user_template if existing else "")),
            "tools": list(pick("tools", existing.tools if existing else [])),
            "kb_id": (pick("kb_id", existing.kb_id if existing else None) or None),
            "profile_id": (pick("profile_id", existing.profile_id if existing else None) or None),
            "manual_context": str(pick("manual_context", existing.manual_context if existing else "")),
            "use_zone_context": bool(pick("use_zone_context", existing.use_zone_context if existing else False)),
        }

    @router.get("/api/agents")
    async def api_list_agents() -> Any:
        try:
            from ....db import get_database
            agents = get_database().agents.list()
            return JSONResponse({"agents": [a.to_dict() for a in agents]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list agents")

    @router.post("/api/agents")
    async def api_create_agent(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "agent name is required"}, status_code=400)
        try:
            from ....db import get_database
            agent = get_database().agents.upsert(
                agent_id=str(body.get("id") or _new_id("agent")),
                **_agent_fields(body),
            )
            return JSONResponse({"agent": agent.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create agent")

    @router.get("/api/agents/{agent_id}")
    async def api_get_agent(agent_id: str) -> Any:
        try:
            from ....db import get_database
            agent = get_database().agents.get(agent_id)
            if agent is None:
                return JSONResponse({"error": f"Unknown agent: {agent_id}"}, status_code=404)
            return JSONResponse({"agent": agent.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get agent")

    @router.put("/api/agents/{agent_id}")
    async def api_update_agent(agent_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.agents.get(agent_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown agent: {agent_id}"}, status_code=404)
            agent = db.agents.upsert(agent_id=agent_id, **_agent_fields(body, existing))
            return JSONResponse({"agent": agent.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update agent")

    @router.delete("/api/agents/{agent_id}")
    async def api_delete_agent(agent_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().agents.delete(agent_id)
            if not removed:
                return JSONResponse({"error": f"Unknown agent: {agent_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete agent")

    @router.post("/api/agents/{agent_id}/run")
    async def api_run_agent(agent_id: str, request: Request) -> Any:
        """Run a saved persona against an input through the intel/LLM engine.

        Builds the messages from the persona's `system_prompt` + rendered
        `user_template` and runs them through `build_configured_meeting_intel()`
        (so the user's configured provider/endpoint is honoured). A model/endpoint
        failure surfaces as a 502 with the engine's message — no silent empty
        output.
        """
        body = await _json_body(request) or {}
        try:
            from ....db import get_database
            agent = get_database().agents.get(agent_id)
            if agent is None:
                return JSONResponse({"error": f"Unknown agent: {agent_id}"}, status_code=404)

            user_input = str(body.get("input") or "")
            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            user_prompt = _render_user_prompt(agent.user_template, variables or {}, user_input)
            if not user_prompt.strip():
                return JSONResponse(
                    {"error": "nothing to run: provide `input` or an agent user_template"},
                    status_code=400,
                )

            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ....intel.providers import (
                build_configured_meeting_intel,
                build_meeting_intel_for_profile,
            )
            from ....intel.models import MeetingIntelError

            # Phase 24: run on the agent's assigned profile when set (its endpoint, key from the
            # hub's secrets), else the hub's configured default.
            ran_profile_id = (agent.profile_id or "").strip() or None
            if ran_profile_id:
                prof = get_database().profiles.get(ran_profile_id)
                if prof is not None and not prof.deleted:
                    intel = build_meeting_intel_for_profile(
                        kind=prof.kind, base_url=prof.base_url, model=prof.model, profile_id=prof.id
                    )
                else:
                    ran_profile_id = None
                    intel = build_configured_meeting_intel()
            else:
                intel = build_configured_meeting_intel()
            _run_frame(ctx, "running", kind="agent", ref=agent_id, name=agent.name or agent_id)
            try:
                output = intel.run_prompt(
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                _run_frame(ctx, "error", kind="agent", ref=agent_id,
                           name=agent.name or agent_id, error=str(exc))
                return JSONResponse(
                    {"error": str(exc), "agent_id": agent_id}, status_code=502
                )
            _run_frame(ctx, "ready", kind="agent", ref=agent_id, name=agent.name or agent_id)

            # Provenance: what produced this output, so a surface that keeps the
            # result as an Artifact can attach lineage ("from <agent>").
            sources: list[dict[str, str]] = [
                {"source_type": "agent", "source_ref": agent_id}
            ]
            provided_ref = str(body.get("source_ref") or "").strip()
            if provided_ref:
                # The input source is canonical "input"; if a caller (e.g. the
                # iPad) hands us its own source_type we fold it to the canonical
                # vocab (its "card" → "input"), defaulting to "input" when unset.
                provided_type = body.get("source_type")
                input_type = (
                    canonical_source_type(provided_type) if provided_type else "input"
                )
                sources.append({"source_type": input_type, "source_ref": provided_ref})

            artifact_id = _persist_run_artifact(
                kind="agent", name=agent.name or agent_id,
                user_input=user_input, output=output, sources=sources,
            )
            return JSONResponse({
                "agent_id": agent_id,
                "output": output,
                "provider": intel.active_provider,
                "profile_id": ran_profile_id,
                "sources": sources,
                "artifact_id": artifact_id,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to run agent")

    # ── Runtime profiles (Phase 24) ───────────────────────────────────────
    # SHAPE ONLY over the API. The api key never rides a profile body; it lives in
    # the hub's secrets (env: HOLDSPEAK_PROFILE_<ID>_KEY) and is joined at run time.

    return router
