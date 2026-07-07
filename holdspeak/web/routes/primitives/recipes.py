"""Recipes (user-authored personas): CRUD + the hub run endpoint.

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


def build_recipes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _recipe_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
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

    @router.get("/api/recipes")
    async def api_list_recipes() -> Any:
        try:
            from ....db import get_database
            recipes = get_database().recipes.list()
            return JSONResponse({"recipes": [r.to_dict() for r in recipes]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list recipes")

    @router.post("/api/recipes")
    async def api_create_recipe(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "recipe name is required"}, status_code=400)
        try:
            from ....db import get_database
            recipe = get_database().recipes.upsert(
                recipe_id=str(body.get("id") or _new_id("recipe")),
                **_recipe_fields(body),
            )
            return JSONResponse({"recipe": recipe.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create recipe")

    @router.get("/api/recipes/{recipe_id}")
    async def api_get_recipe(recipe_id: str) -> Any:
        try:
            from ....db import get_database
            recipe = get_database().recipes.get(recipe_id)
            if recipe is None:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)
            return JSONResponse({"recipe": recipe.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get recipe")

    @router.put("/api/recipes/{recipe_id}")
    async def api_update_recipe(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.recipes.get(recipe_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)
            recipe = db.recipes.upsert(recipe_id=recipe_id, **_recipe_fields(body, existing))
            return JSONResponse({"recipe": recipe.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update recipe")

    @router.delete("/api/recipes/{recipe_id}")
    async def api_delete_recipe(recipe_id: str) -> Any:
        try:
            from ....db import get_database
            removed = get_database().recipes.delete(recipe_id)
            if not removed:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete recipe")

    @router.post("/api/recipes/{recipe_id}/run")
    async def api_run_recipe(recipe_id: str, request: Request) -> Any:
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
            recipe = get_database().recipes.get(recipe_id)
            if recipe is None:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)

            user_input = str(body.get("input") or "")
            variables = body.get("variables") if isinstance(body.get("variables"), dict) else {}
            user_prompt = _render_user_prompt(recipe.user_template, variables or {}, user_input)
            if not user_prompt.strip():
                return JSONResponse(
                    {"error": "nothing to run: provide `input` or a recipe user_template"},
                    status_code=400,
                )

            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")

            from ....intel.providers import (
                build_configured_meeting_intel,
                build_meeting_intel_for_profile,
            )
            from ....intel.models import MeetingIntelError

            # Phase 24: run on the recipe's assigned profile when set (its endpoint, key from the
            # hub's secrets), else the hub's configured default.
            ran_profile_id = (recipe.profile_id or "").strip() or None
            if ran_profile_id:
                prof = get_database().profiles.get(ran_profile_id)
                if prof is not None and not prof.deleted:
                    intel = build_meeting_intel_for_profile(
                        kind=prof.kind, base_url=prof.base_url, model=prof.model, profile_id=prof.id,
                    node=getattr(prof, "node", "")
                    )
                else:
                    ran_profile_id = None
                    intel = build_configured_meeting_intel()
            else:
                intel = build_configured_meeting_intel()
            _run_frame(ctx, "running", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)
            try:
                output = intel.run_prompt(
                    system_prompt=recipe.system_prompt,
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                _run_frame(ctx, "error", kind="recipe", ref=recipe_id,
                           name=recipe.name or recipe_id, error=str(exc))
                return JSONResponse(
                    {"error": str(exc), "recipe_id": recipe_id}, status_code=502
                )
            _run_frame(ctx, "ready", kind="recipe", ref=recipe_id, name=recipe.name or recipe_id)

            # Provenance: what produced this output, so a surface that keeps the
            # result as an Artifact can attach lineage ("from <recipe>").
            sources: list[dict[str, str]] = [
                {"source_type": "recipe", "source_ref": recipe_id}
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
                kind="recipe", name=recipe.name or recipe_id,
                user_input=user_input, output=output, sources=sources,
            )
            return JSONResponse({
                "recipe_id": recipe_id,
                "output": output,
                "provider": intel.active_provider,
                "profile_id": ran_profile_id,
                "sources": sources,
                "artifact_id": artifact_id,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to run recipe")

    def _kb_block(db: Any, kb_id: str) -> str:
        """The KB honesty rider (HS-83-02, the 15-12 grammar): real hydrated
        member content, or an explicit marker — never a hint string."""
        from .ask import _context_material

        kb = db.kbs.get(kb_id)
        if kb is None:
            return ""
        name = kb.name or kb_id
        texts: list[str] = []
        for mid in list(getattr(kb, "member_ids", None) or [])[:12]:
            bare = mid.split(":", 1)[1] if ":" in mid else mid
            for kind in ("note", "artifact", "meeting"):
                _, text = _context_material(db, bare, kind, "")
                if text:
                    texts.append(text[:1200])
                    break
        if texts:
            return f"[KB: {name}]\n" + "\n\n".join(texts)
        return f"[KB: {name} — no hydrated members]"

    @router.post("/api/recipes/{recipe_id}/chat")
    async def api_chat_recipe(recipe_id: str, request: Request) -> Any:
        """One conversational turn with a persona (HS-83-02). Persists NOTHING —
        harvest is the human's judgment (`/keep` below).

        The turn's envelope mirrors the iPad's `recipeReply`: the persona's
        standing context (`manual_context` + the KB honesty block), the
        HSM-15-12 grounding refs hydrated from the canonical store, the last
        12 turns, then the question. The role rides the system channel (the
        transport-correct seat for `run_prompt`); everything else is the same
        block grammar.
        """
        body = await _json_body(request) or {}
        question = str(body.get("question") or "").strip()
        if not question:
            return JSONResponse({"error": "question is required"}, status_code=400)
        try:
            from ....db import get_database
            from ....intel.models import MeetingIntelError
            from ....intel.providers import (
                build_configured_meeting_intel,
                build_meeting_intel_for_profile,
            )
            from .ask import (
                _GROUNDING_EXPANDS, _GROUNDING_MAX_REFS, _hydrate_grounding, _run_egress,
            )

            db = get_database()
            recipe = db.recipes.get(recipe_id)
            if recipe is None:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)
            name = recipe.name or recipe_id

            blocks: list[str] = []
            ctx_parts: list[str] = []
            if (recipe.manual_context or "").strip():
                ctx_parts.append(recipe.manual_context)
            if recipe.kb_id:
                kb_text = _kb_block(db, recipe.kb_id)
                if kb_text:
                    ctx_parts.append(kb_text)
            if ctx_parts:
                blocks.append("[CONTEXT]\n" + "\n\n".join(ctx_parts))

            # HSM-15-12 grounding — the SAME wire and refusal grammar as /api/ask.
            grounding = body.get("grounding")
            context_ids: list[str] = []
            context_titles: list[str] = []
            grounding_echo = None
            if grounding is not None:
                if not isinstance(grounding, dict):
                    return JSONResponse({"error": "grounding must be an object"}, status_code=400)
                raw_m = grounding.get("meeting_ids")
                raw_a = grounding.get("artifact_ids")
                meeting_ids = [str(x).strip() for x in raw_m if str(x).strip()] if isinstance(raw_m, list) else []
                artifact_ids = [str(x).strip() for x in raw_a if str(x).strip()] if isinstance(raw_a, list) else []
                expand = str(grounding.get("expand") or "summary").strip() or "summary"
                if expand not in _GROUNDING_EXPANDS:
                    return JSONResponse(
                        {"error": f"expand {expand!r} is not one of {list(_GROUNDING_EXPANDS)}"},
                        status_code=400,
                    )
                if len(meeting_ids) + len(artifact_ids) > _GROUNDING_MAX_REFS:
                    return JSONResponse(
                        {"error": f"grounding is capped at {_GROUNDING_MAX_REFS} refs"},
                        status_code=400,
                    )
                g_blocks, g_ids, g_titles, unknown = _hydrate_grounding(
                    db, meeting_ids, artifact_ids, expand
                )
                if unknown:
                    return JSONResponse(
                        {"error": "grounding ids not on this hub", "unknown_ids": unknown},
                        status_code=400,
                    )
                if g_blocks:
                    blocks.append("[GROUNDING]\n" + "\n\n".join(g_blocks))
                context_ids += g_ids
                context_titles += g_titles
                grounding_echo = {
                    "meeting_ids": meeting_ids, "artifact_ids": artifact_ids,
                    "expand": expand, "titles": g_titles,
                }

            history = body.get("history") if isinstance(body.get("history"), list) else []
            window = [h for h in history if isinstance(h, dict)][-12:]
            if window:
                convo = "\n".join(
                    ("User: " if str(h.get("role")) == "you" else f"{name}: ") + str(h.get("text") or "")
                    for h in window
                )
                blocks.append("[CONVERSATION SO FAR]\n" + convo)
            blocks.append("[USER]\n" + question[:6000] + f"\n\nReply as {name}.")

            ran_profile_id = (recipe.profile_id or "").strip() or None
            prof = db.profiles.get(ran_profile_id) if ran_profile_id else None
            if prof is not None and not prof.deleted:
                intel = build_meeting_intel_for_profile(
                    kind=prof.kind, base_url=prof.base_url, model=prof.model, profile_id=prof.id,
                    node=getattr(prof, "node", "")
                )
            else:
                ran_profile_id = None
                prof = None
                intel = build_configured_meeting_intel()

            system_prompt = (recipe.system_prompt or "").strip() or f"You are {name}, a helpful assistant."
            _run_frame(ctx, "running", kind="recipe", ref=recipe_id, name=name)
            try:
                output = intel.run_prompt(
                    system_prompt=system_prompt,
                    user_prompt="\n\n".join(blocks),
                )
            except MeetingIntelError as exc:
                _run_frame(ctx, "error", kind="recipe", ref=recipe_id, name=name, error=str(exc))
                return JSONResponse({"error": str(exc), "recipe_id": recipe_id}, status_code=502)
            _run_frame(ctx, "ready", kind="recipe", ref=recipe_id, name=name)

            # The turn's HONEST egress — the 16-09 grammar, the same ONE
            # derivation as /api/ask (HS-84-04).
            egress, model = _run_egress(ctx, prof, intel)

            payload: dict[str, Any] = {
                "recipe_id": recipe_id,
                "output": output,
                "provider": intel.active_provider,
                "profile_id": ran_profile_id,
                "egress": egress,
                "model": model,
                "context_ids": context_ids,
                "context_titles": context_titles,
            }
            if grounding_echo is not None:
                payload["grounding"] = grounding_echo
            return JSONResponse(payload)
        except Exception as exc:
            return error_500(exc, log, "Failed to chat with recipe")

    @router.post("/api/recipes/{recipe_id}/keep")
    async def api_keep_recipe_reply(recipe_id: str, request: Request) -> Any:
        """Harvest one chat reply onto the desk — the run-born artifact the
        run route mints, minted only when the human says keep."""
        body = await _json_body(request) or {}
        output = str(body.get("output") or "")
        if not output.strip():
            return JSONResponse({"error": "output is required"}, status_code=400)
        try:
            from ....db import get_database
            recipe = get_database().recipes.get(recipe_id)
            if recipe is None:
                return JSONResponse({"error": f"Unknown recipe: {recipe_id}"}, status_code=404)
            artifact_id = _persist_run_artifact(
                kind="recipe", name=recipe.name or recipe_id,
                user_input=str(body.get("question") or ""),
                output=output,
                sources=[{"source_type": "recipe", "source_ref": recipe_id}],
            )
            if not artifact_id:
                return JSONResponse({"error": "keep failed"}, status_code=500)
            return JSONResponse({"artifact_id": artifact_id}, status_code=201)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep chat reply")

    # ── Runtime profiles (Phase 24) ───────────────────────────────────────
    # SHAPE ONLY over the API. The api key never rides a profile body; it lives in
    # the hub's secrets (env: HOLDSPEAK_PROFILE_<ID>_KEY) and is joined at run time.

    return router
