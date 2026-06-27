"""CRUD + run routes for the desk's first-class primitives (Primitive Framework).

The authoring surface the web + iPad ports POST to: Note and Agent (persona) get
full list/create/update/delete here, plus a `run` endpoint that executes a saved
Agent persona against an input through the existing intel/LLM engine, so a
persona authored anywhere is runnable on the hub.

Route table (all snake_case JSON, ISO-8601 UTC `Z` timestamps):

  Notes
    GET    /api/notes                 -> {"notes": [<note>...]}
    POST   /api/notes                 body {title?, body_markdown?, tags?[, id]}
                                       -> {"note": <note>}  (201)
    GET    /api/notes/{id}            -> {"note": <note>} | 404
    PUT    /api/notes/{id}            body {title?, body_markdown?, tags?}
                                       -> {"note": <note>} | 404
    DELETE /api/notes/{id}            -> {"success": true} | 404   (tombstone)

  Agents (personas)
    GET    /api/agents                -> {"agents": [<agent>...]}
    POST   /api/agents                body {name, avatar?, role?, system_prompt?,
                                            user_template?, tools?, kb_id?[, id]}
                                       -> {"agent": <agent>}  (201)
    GET    /api/agents/{id}           -> {"agent": <agent>} | 404
    PUT    /api/agents/{id}           body (same fields as POST) -> {"agent": <agent>} | 404
    DELETE /api/agents/{id}           -> {"success": true} | 404   (tombstone)
    POST   /api/agents/{id}/run       body {input?, variables?, max_tokens?, temperature?}
                                       -> {"agent_id", "output", "provider"} | 404 | 502

  KBs (knowledge bases)
    GET    /api/kbs                   -> {"kbs": [<kb>...]}
    POST   /api/kbs                   body {name, member_ids?[, id]} -> {"kb": <kb>} (201)
    GET    /api/kbs/{id}              -> {"kb": <kb>} | 404
    PUT    /api/kbs/{id}              body {name?, member_ids?} -> {"kb": <kb>} | 404
    DELETE /api/kbs/{id}              -> {"success": true} | 404   (tombstone)

  Chains (crews)
    GET    /api/chains                -> {"chains": [<chain>...]}
    POST   /api/chains                body {name, steps?[, id]} -> {"chain": <chain>} (201)
    GET    /api/chains/{id}           -> {"chain": <chain>} | 404
    PUT    /api/chains/{id}           body {name?, steps?} -> {"chain": <chain>} | 404
    DELETE /api/chains/{id}           -> {"success": true} | 404   (tombstone)

  Workflows
    GET    /api/workflows             -> {"workflows": [<workflow>...]}
    POST   /api/workflows             body {name, prompt?, graph_json?[, id]} -> {"workflow": <workflow>} (201)
    GET    /api/workflows/{id}        -> {"workflow": <workflow>} | 404
    PUT    /api/workflows/{id}        body {name?, prompt?, graph_json?} -> {"workflow": <workflow>} | 404
    DELETE /api/workflows/{id}        -> {"success": true} | 404   (tombstone)

A <note> is NoteRecord.to_dict(); an <agent> is AgentRecord.to_dict(); a <kb> is
KBRecord.to_dict(); a <chain> is ChainRecord.to_dict(); a <workflow> is
WorkflowRecord.to_dict().
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.primitives")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def _json_body(request: Request) -> Optional[dict[str, Any]]:
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _render_user_prompt(template: str, variables: dict[str, Any], user_input: str) -> str:
    """Render an agent's user_template.

    `{input}` is the primary slot for the runtime input; any `{name}` matching a
    provided variable is substituted. Unknown braces are left intact (a missing
    key never raises) so a persona authored elsewhere can't crash the hub.
    """
    if not template:
        return user_input
    mapping = dict(variables or {})
    mapping.setdefault("input", user_input)

    class _Safe(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    try:
        return template.format_map(_Safe(mapping))
    except Exception:
        # A malformed template (e.g. stray brace) → fall back to template + input.
        return f"{template}\n\n{user_input}".strip()


def build_primitives_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    # ── Notes ────────────────────────────────────────────────────────────
    @router.get("/api/notes")
    async def api_list_notes() -> Any:
        try:
            from ...db import get_database
            notes = get_database().notes.list()
            return JSONResponse({"notes": [n.to_dict() for n in notes]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list notes")

    @router.post("/api/notes")
    async def api_create_note(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            note = get_database().notes.upsert(
                note_id=str(body.get("id") or _new_id("note")),
                title=str(body.get("title") or ""),
                body_markdown=str(body.get("body_markdown") or ""),
                tags=list(body.get("tags") or []),
            )
            return JSONResponse({"note": note.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create note")

    @router.get("/api/notes/{note_id}")
    async def api_get_note(note_id: str) -> Any:
        try:
            from ...db import get_database
            note = get_database().notes.get(note_id)
            if note is None:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            return JSONResponse({"note": note.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get note")

    @router.put("/api/notes/{note_id}")
    async def api_update_note(note_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            db = get_database()
            existing = db.notes.get(note_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            note = db.notes.upsert(
                note_id=note_id,
                title=str(body["title"]) if "title" in body else existing.title,
                body_markdown=str(body["body_markdown"]) if "body_markdown" in body else existing.body_markdown,
                tags=list(body["tags"]) if "tags" in body else existing.tags,
            )
            return JSONResponse({"note": note.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update note")

    @router.delete("/api/notes/{note_id}")
    async def api_delete_note(note_id: str) -> Any:
        try:
            from ...db import get_database
            removed = get_database().notes.delete(note_id)
            if not removed:
                return JSONResponse({"error": f"Unknown note: {note_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete note")

    # ── Agents (personas) ────────────────────────────────────────────────
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
        }

    @router.get("/api/agents")
    async def api_list_agents() -> Any:
        try:
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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

            from ...intel.providers import build_configured_meeting_intel
            from ...intel.models import MeetingIntelError

            intel = build_configured_meeting_intel()
            try:
                output = intel.run_prompt(
                    system_prompt=agent.system_prompt,
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                return JSONResponse(
                    {"error": str(exc), "agent_id": agent_id}, status_code=502
                )

            return JSONResponse({
                "agent_id": agent_id,
                "output": output,
                "provider": intel.active_provider,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to run agent")

    # ── KBs (knowledge bases) ─────────────────────────────────────────────
    @router.get("/api/kbs")
    async def api_list_kbs() -> Any:
        try:
            from ...db import get_database
            kbs = get_database().kbs.list()
            return JSONResponse({"kbs": [k.to_dict() for k in kbs]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list kbs")

    @router.post("/api/kbs")
    async def api_create_kb(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "kb name is required"}, status_code=400)
        try:
            from ...db import get_database
            kb = get_database().kbs.upsert(
                kb_id=str(body.get("id") or _new_id("kb")),
                name=str(body.get("name") or ""),
                member_ids=list(body.get("member_ids") or []),
            )
            return JSONResponse({"kb": kb.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create kb")

    @router.get("/api/kbs/{kb_id}")
    async def api_get_kb(kb_id: str) -> Any:
        try:
            from ...db import get_database
            kb = get_database().kbs.get(kb_id)
            if kb is None:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            return JSONResponse({"kb": kb.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get kb")

    @router.put("/api/kbs/{kb_id}")
    async def api_update_kb(kb_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            db = get_database()
            existing = db.kbs.get(kb_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            kb = db.kbs.upsert(
                kb_id=kb_id,
                name=str(body["name"]) if "name" in body else existing.name,
                member_ids=list(body["member_ids"]) if "member_ids" in body else existing.member_ids,
            )
            return JSONResponse({"kb": kb.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update kb")

    @router.delete("/api/kbs/{kb_id}")
    async def api_delete_kb(kb_id: str) -> Any:
        try:
            from ...db import get_database
            removed = get_database().kbs.delete(kb_id)
            if not removed:
                return JSONResponse({"error": f"Unknown kb: {kb_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete kb")

    # ── Chains (crews) ────────────────────────────────────────────────────
    @router.get("/api/chains")
    async def api_list_chains() -> Any:
        try:
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
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
            from ...db import get_database
            removed = get_database().chains.delete(chain_id)
            if not removed:
                return JSONResponse({"error": f"Unknown chain: {chain_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete chain")

    # ── Workflows ─────────────────────────────────────────────────────────
    @router.get("/api/workflows")
    async def api_list_workflows() -> Any:
        try:
            from ...db import get_database
            workflows = get_database().workflows.list()
            return JSONResponse({"workflows": [w.to_dict() for w in workflows]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list workflows")

    @router.post("/api/workflows")
    async def api_create_workflow(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "workflow name is required"}, status_code=400)
        try:
            from ...db import get_database
            workflow = get_database().workflows.upsert(
                workflow_id=str(body.get("id") or _new_id("workflow")),
                name=str(body.get("name") or ""),
                prompt=str(body.get("prompt") or ""),
                graph_json=dict(body.get("graph_json") or {}),
            )
            return JSONResponse({"workflow": workflow.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create workflow")

    @router.get("/api/workflows/{workflow_id}")
    async def api_get_workflow(workflow_id: str) -> Any:
        try:
            from ...db import get_database
            workflow = get_database().workflows.get(workflow_id)
            if workflow is None:
                return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
            return JSONResponse({"workflow": workflow.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get workflow")

    @router.put("/api/workflows/{workflow_id}")
    async def api_update_workflow(workflow_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            db = get_database()
            existing = db.workflows.get(workflow_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
            workflow = db.workflows.upsert(
                workflow_id=workflow_id,
                name=str(body["name"]) if "name" in body else existing.name,
                prompt=str(body["prompt"]) if "prompt" in body else existing.prompt,
                graph_json=dict(body["graph_json"]) if "graph_json" in body else existing.graph_json,
            )
            return JSONResponse({"workflow": workflow.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update workflow")

    @router.delete("/api/workflows/{workflow_id}")
    async def api_delete_workflow(workflow_id: str) -> Any:
        try:
            from ...db import get_database
            removed = get_database().workflows.delete(workflow_id)
            if not removed:
                return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete workflow")

    return router
