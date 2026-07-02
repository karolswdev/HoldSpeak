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
    POST   /api/agents/{id}/run       body {input?, variables?, source_ref?, max_tokens?, temperature?}
                                       -> {"agent_id", "output", "provider", "sources"} | 404 | 502
                                       (sources lineage: [{source_type:"agent", source_ref:<id>}
                                        (+ {source_type:"input", source_ref} if source_ref given)])

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
    POST   /api/chains/{id}/run       body {input?, variables?, max_tokens?, temperature?}
                                       -> {"chain_id", "steps":[{agent_id, output, provider}...],
                                           "output", "provider", "sources"} | 400 | 404 | 502
                                       (runs each agent in `steps` in sequence, threading
                                        output -> next input; top-level `provider` is the last
                                        step's; `sources` is [{chain}, {agent}...] lineage)

  Workflows
    GET    /api/workflows             -> {"workflows": [<workflow>...]}
    POST   /api/workflows             body {name, prompt?, graph_json?[, id]} -> {"workflow": <workflow>} (201)
    GET    /api/workflows/{id}        -> {"workflow": <workflow>} | 404
    PUT    /api/workflows/{id}        body {name?, prompt?, graph_json?} -> {"workflow": <workflow>} | 404
    DELETE /api/workflows/{id}        -> {"success": true} | 404   (tombstone)
    POST   /api/workflows/{id}/run    body {input?, variables?, max_tokens?, temperature?}
                                       -> {"workflow_id", "output", "provider", "sources"
                                           [, "steps"][, "warning"]} | 400 | 404 | 502
                                       (runs a LINEAR `graph_json` node chain in order when one
                                        is present + linearizable [-> `steps`]; else runs
                                        `prompt`; a non-linearizable graph is refused with an
                                        honest `warning`, never a guessed order)

  Directories (the canonical organization container; the iPad's "zone")
    GET    /api/directories             -> {"directories": [<directory + member_ids[]>...]}
    POST   /api/directories             body {name, parent_id?[, id]} -> {"directory": <directory>} (201)
    GET    /api/directories/{id}        -> {"directory": <directory>, "member_ids": [primitive_id...],
                                           "members": [<member>...]} | 404
    PUT    /api/directories/{id}        body {name?, parent_id?} -> {"directory": <directory>} | 404
    DELETE /api/directories/{id}        -> {"success": true} | 404   (tombstone)

  Directory membership (the synced `primitive_id -> directory_id` filing map;
  supersedes the legacy `hs.desk.filed` / iPad `filed` maps)
    GET    /api/directories/{dir_id}/members
                                        -> {"directory_id", "members": [<member>...]}
    PUT    /api/directories/{dir_id}/members/{primitive_id}
                                        -> {"membership": <member>} (file; idempotent re-file)
    DELETE /api/directories/{dir_id}/members/{primitive_id}
                                        -> {"success": true} | 404   (unfile; tombstone)

A <note> is NoteRecord.to_dict(); an <agent> is AgentRecord.to_dict(); a <kb> is
KBRecord.to_dict(); a <chain> is ChainRecord.to_dict(); a <workflow> is
WorkflowRecord.to_dict(); a <directory> is DirectoryRecord.to_dict(); a <member>
is DirectoryMembershipRecord.to_dict().
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


# ── Run-response provenance: the canonical `source_type` vocabulary ──────────
#
# Every primitive `run` endpoint here returns a `sources` lineage list whose
# entries are `{"source_type": <canonical>, "source_ref": <id>}`. The hub is the
# canonical authority for this vocabulary. The pinned set (and what each means):
#
#   "agent"    — a saved Agent persona that produced/contributed to the output
#   "input"    — the run's input record (e.g. a meeting_id passed as source_ref)
#   "chain"    — the Chain (crew) a run executed
#   "workflow" — the Workflow a run executed
#
# A future change to any of these literals is a wire contract break for every
# surface that attaches lineage; `test_run_response_source_type_vocab_is_pinned`
# guards them.
#
# Aliases (tolerated, non-breaking): the iPad authoring port historically emits
# "card" for an input source (its canvas card == an input record). We accept that
# synonym and fold it to the canonical "input" via `canonical_source_type` so
# lineage from either surface lands on one stored vocabulary; nothing is rejected.
CANONICAL_SOURCE_TYPES: frozenset[str] = frozenset(
    {"agent", "input", "chain", "workflow"}
)

# iPad / authoring-port synonyms → the canonical hub value (additive, tolerant).
_SOURCE_TYPE_ALIASES: dict[str, str] = {"card": "input"}


def canonical_source_type(raw: Any) -> str:
    """Fold a raw `source_type` to the canonical hub vocabulary.

    Canonical values pass through unchanged; known aliases (the iPad "card")
    map to their canonical form. Anything else is returned lowercased + stripped
    untouched (non-breaking: we never reject an unknown lineage tag, we just
    don't claim it is canonical).
    """
    val = str(raw or "").strip().lower()
    return _SOURCE_TYPE_ALIASES.get(val, val)


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


def _persist_run_artifact(
    *,
    kind: str,
    name: str,
    user_input: str,
    output: str,
    sources: list[dict[str, str]],
) -> Optional[str]:
    """Persist a run's output as a run-born artifact (v6, Phase 74).

    The result enters the ONE artifact store — it syncs, lands on the desk,
    and shows in the iPad's artifact review — instead of evaporating with
    the HTTP response. A persistence failure never eats a successful run:
    log and return None.
    """
    try:
        from ...db import get_database

        artifact_id = _new_id("artifact")
        head = " ".join(user_input.split())[:48]
        title = f"{name}: {head}" if head else f"{name} run"
        get_database().plugins.record_artifact(
            artifact_id=artifact_id,
            meeting_id="",
            artifact_type="run_output",
            title=title,
            body_markdown=str(output or ""),
            status="draft",
            plugin_id=f"{kind}_run",
            plugin_version="1",
            sources=sources,
        )
        return artifact_id
    except Exception as exc:
        log.error(f"Failed to persist run artifact: {exc}")
        return None


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
            "profile_id": (pick("profile_id", existing.profile_id if existing else None) or None),
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

            from ...intel.providers import (
                build_configured_meeting_intel,
                build_meeting_intel_for_profile,
            )
            from ...intel.models import MeetingIntelError

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
    def _profile_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "kind": str(pick("kind", existing.kind if existing else "onDevice")),
            "model_file": str(pick("model_file", existing.model_file if existing else "")),
            "base_url": str(pick("base_url", existing.base_url if existing else "")),
            "model": str(pick("model", existing.model if existing else "")),
            "context_limit": int(pick("context_limit", existing.context_limit if existing else 16384)),
            "requires_key": bool(pick("requires_key", existing.requires_key if existing else False)),
        }

    @router.get("/api/profiles")
    async def api_list_profiles() -> Any:
        try:
            from ...db import get_database
            return JSONResponse({"profiles": [p.to_dict() for p in get_database().profiles.list()]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list profiles")

    @router.post("/api/profiles")
    async def api_create_profile(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "profile name is required"}, status_code=400)
        try:
            from ...db import get_database
            profile = get_database().profiles.upsert(
                profile_id=str(body.get("id") or _new_id("profile")),
                **_profile_fields(body),
            )
            return JSONResponse({"profile": profile.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create profile")

    @router.get("/api/profiles/{profile_id}")
    async def api_get_profile(profile_id: str) -> Any:
        try:
            from ...db import get_database
            profile = get_database().profiles.get(profile_id)
            if profile is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get profile")

    @router.put("/api/profiles/{profile_id}")
    async def api_update_profile(profile_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            db = get_database()
            existing = db.profiles.get(profile_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            profile = db.profiles.upsert(profile_id=profile_id, **_profile_fields(body, existing))
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update profile")

    @router.delete("/api/profiles/{profile_id}")
    async def api_delete_profile(profile_id: str) -> Any:
        try:
            from ...db import get_database
            if not get_database().profiles.delete(profile_id):
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete profile")

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
            from ...db import get_database
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

            from ...intel.providers import build_configured_meeting_intel
            from ...intel.models import MeetingIntelError

            intel = build_configured_meeting_intel()

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
        2. **Prompt.** Otherwise, if the workflow has a `prompt`, run it through
           the engine with an empty system prompt rendered against `{input}` +
           `variables`.
        3. **Refused graph fallback.** If the graph contains control flow / fan-out
           we cannot linearize (and there's no/empty prompt), we DO NOT guess an
           order — we run the prompt fallback and return an honest `warning`
           naming why the graph could not run.

        Per-node provenance: the iPad Blueprint carries a per-node `failure_policy`
        (retryThenQueue / fallbackOnDevice / skip) and a `runs_on` model preference
        (auto / onDevice / endpoint). The linearizer now carries both, and each
        linear `steps` entry surfaces the node's resolved `failure_policy` and
        `runs_on` so the trail is honest about what was requested. On a model-op
        error the hub honours a faithful subset of the failure policy: `skip` and
        `fallbackOnDevice` carry the input through unchanged and continue the chain
        (the step's `status` records which), while `retryThenQueue` / unset surface
        the error as a 502 (no silent empty).

        NOT yet applied on the hub (carried + surfaced honestly, not enforced):
        `runs_on` does not pin a node to a specific provider — the hub runs every
        model op on its single configured provider, so `runs_on` is reported but the
        target is not switched per node. `retryThenQueue` does not retry-with-backoff
        or park/queue the run (the hub has no run queue); it fails fast. `fallbackOnDevice`
        has no separate on-device fallback to swap to on the hub, so it degrades to
        carrying the input through rather than re-running on another model. Full
        per-node target routing and queue/park semantics live on the iPad runner
        (`WorkflowRunner` / `BlueprintInterpreter`) and the mesh (HSM-15).

        404 if the workflow is missing; 502 on engine failure (no silent empty).
        Returns `{workflow_id, output, provider}` (+ optional `steps`, `warning`,
        and a `sources` lineage array).
        """
        body = await _json_body(request) or {}
        try:
            from ...db import get_database
            db = get_database()
            workflow = db.workflows.get(workflow_id)
            if workflow is None:
                return JSONResponse({"error": f"Unknown workflow: {workflow_id}"}, status_code=404)

            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            user_input = str(body.get("input") or "")
            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ...intel.providers import build_configured_meeting_intel
            from ...intel.models import MeetingIntelError
            from .workflow_graph import (
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

            # ── 1) Try the linear graph runner ─────────────────────────────
            warning: Optional[str] = None
            plan = linearize(workflow.graph_json) if workflow.graph_json else None
            if plan is not None and plan.linearizable:
                # Seed the chain with the rendered request input (variables applied).
                current = _render_user_prompt("", variables or {}, user_input)
                intel = build_configured_meeting_intel()
                run_steps: list[dict[str, Any]] = []
                ran_a_model_op = False
                for gnode in plan.ordered:
                    if gnode.kind in _MODEL_KINDS:
                        node_prompt = build_node_prompt(gnode, current)
                        if not node_prompt.strip():
                            continue
                        try:
                            out = intel.run_prompt(
                                system_prompt="",
                                user_prompt=node_prompt,
                                temperature=float(temperature) if temperature is not None else None,
                                max_tokens=int(max_tokens) if max_tokens is not None else None,
                            )
                        except MeetingIntelError as exc:
                            # Honour a faithful subset of the node's failure policy:
                            # `skip` / `fallbackOnDevice` carry the input through and
                            # continue; `retryThenQueue` / unset surface the error.
                            handled = on_node_error(gnode, current)
                            if handled is None:
                                return JSONResponse(
                                    {"error": str(exc), "workflow_id": workflow_id,
                                     "node_id": gnode.id,
                                     "failure_policy": resolved_failure_policy(gnode)},
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
                                "error": str(exc),
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
                    # pass-through nodes (entry/source/merge/output) carry `current`.

                if not run_steps:
                    return JSONResponse(
                        {
                            "error": (
                                "nothing to run: the graph linearized but produced "
                                "no executable steps; provide `input` or node prompts"
                            ),
                            "workflow_id": workflow_id,
                        },
                        status_code=400,
                    )

                artifact_id = _persist_run_artifact(
                    kind="workflow", name=workflow.name or workflow_id,
                    user_input=str(body.get("input") or ""),
                    output=str(current or ""), sources=sources,
                )
                return JSONResponse({
                    "workflow_id": workflow_id,
                    "output": current,
                    "provider": intel.active_provider if ran_a_model_op else None,
                    "steps": run_steps,
                    "sources": sources,
                    "artifact_id": artifact_id,
                })

            # ── 2/3) Prompt path (+ honest warning if a graph was refused) ──
            prompt = str(workflow.prompt or "").strip()
            if plan is not None and not plan.linearizable:
                # The graph exists but we won't guess an order for it. Be honest.
                warning = (
                    "graph execution skipped (" + plan.reason + "); "
                    "ran the prompt fallback"
                )

            user_prompt = _render_user_prompt(prompt, variables or {}, user_input)
            if not user_prompt.strip():
                return JSONResponse(
                    {
                        "error": (
                            "nothing to run: the workflow has no runnable graph and "
                            "no prompt; provide `input` or a prompt"
                        ),
                        "workflow_id": workflow_id,
                    },
                    status_code=400,
                )

            intel = build_configured_meeting_intel()
            try:
                output = intel.run_prompt(
                    system_prompt="",
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                return JSONResponse(
                    {"error": str(exc), "workflow_id": workflow_id}, status_code=502
                )

            result: dict[str, Any] = {
                "workflow_id": workflow_id,
                "output": output,
                "provider": intel.active_provider,
                "sources": sources,
                "artifact_id": _persist_run_artifact(
                    kind="workflow", name=workflow.name or workflow_id,
                    user_input=str(body.get("input") or ""),
                    output=output, sources=sources,
                ),
            }
            if warning:
                result["warning"] = warning
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to run workflow")

    # ── Directories (the canonical organization container; iPad "zone") ────
    @router.get("/api/directories")
    async def api_list_directories() -> Any:
        try:
            from ...db import get_database
            db = get_database()
            directories = db.directories.list()
            out = []
            for d in directories:
                item = d.to_dict()
                members = db.directory_memberships.list_for_directory(d.id)
                item["member_ids"] = [m.primitive_id for m in members]
                out.append(item)
            return JSONResponse({"directories": out})
        except Exception as exc:
            return error_500(exc, log, "Failed to list directories")

    @router.post("/api/directories")
    async def api_create_directory(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "directory name is required"}, status_code=400)
        try:
            from ...db import get_database
            directory = get_database().directories.upsert(
                directory_id=str(body.get("id") or _new_id("dir")),
                name=str(body.get("name") or ""),
                parent_id=(body.get("parent_id") or None),
            )
            return JSONResponse({"directory": directory.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create directory")

    @router.get("/api/directories/{directory_id}")
    async def api_get_directory(directory_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            directory = db.directories.get(directory_id)
            if directory is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            members = db.directory_memberships.list_for_directory(directory_id)
            return JSONResponse({
                "directory": directory.to_dict(),
                "member_ids": [m.primitive_id for m in members],
                "members": [m.to_dict() for m in members],
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to get directory")

    @router.put("/api/directories/{directory_id}")
    async def api_update_directory(directory_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database
            db = get_database()
            existing = db.directories.get(directory_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            directory = db.directories.upsert(
                directory_id=directory_id,
                name=str(body["name"]) if "name" in body else existing.name,
                parent_id=(body["parent_id"] or None) if "parent_id" in body else existing.parent_id,
            )
            return JSONResponse({"directory": directory.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update directory")

    @router.delete("/api/directories/{directory_id}")
    async def api_delete_directory(directory_id: str) -> Any:
        try:
            from ...db import get_database
            removed = get_database().directories.delete(directory_id)
            if not removed:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete directory")

    # ── Directory membership (the synced filing map; supersedes `filed`) ───
    @router.get("/api/directories/{directory_id}/members")
    async def api_list_directory_members(directory_id: str) -> Any:
        try:
            from ...db import get_database
            db = get_database()
            if db.directories.get(directory_id) is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            members = db.directory_memberships.list_for_directory(directory_id)
            return JSONResponse({
                "directory_id": directory_id,
                "members": [m.to_dict() for m in members],
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to list directory members")

    @router.put("/api/directories/{directory_id}/members/{primitive_id}")
    async def api_file_member(directory_id: str, primitive_id: str) -> Any:
        """File a primitive into a directory (idempotent; a re-file moves it).

        Membership is keyed by `primitive_id` (a primitive lives in one
        directory), so PUTting the same primitive elsewhere overwrites the edge.
        """
        try:
            from ...db import get_database
            db = get_database()
            if db.directories.get(directory_id) is None:
                return JSONResponse({"error": f"Unknown directory: {directory_id}"}, status_code=404)
            membership = db.directory_memberships.upsert(
                primitive_id=primitive_id,
                directory_id=directory_id,
            )
            return JSONResponse({"membership": membership.to_dict()})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to file directory member")

    @router.delete("/api/directories/{directory_id}/members/{primitive_id}")
    async def api_unfile_member(directory_id: str, primitive_id: str) -> Any:
        """Unfile a primitive from a directory (tombstone).

        404 if the primitive isn't currently filed into THIS directory.
        """
        try:
            from ...db import get_database
            db = get_database()
            existing = db.directory_memberships.get(primitive_id)
            if existing is None or existing.directory_id != directory_id:
                return JSONResponse(
                    {"error": f"{primitive_id} is not filed in {directory_id}"},
                    status_code=404,
                )
            db.directory_memberships.delete(primitive_id)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to unfile directory member")

    return router
