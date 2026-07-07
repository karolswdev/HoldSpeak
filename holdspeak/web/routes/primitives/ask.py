"""The Ask AI atom on the hub (HSM-16-04, the web parity of HSM-16-09).

Two routes, because keep/bin is the human's judgment:

- ``POST /api/ask`` assembles the lasso'd cards' material FROM THE CANONICAL
  STORE (the grounding is provable, never a client claim), runs the instruction
  through the profile-or-default intel engine, and returns the output with the
  run's honest egress. It persists NOTHING.
- ``POST /api/ask/keep`` persists a kept ask as a run-born artifact wearing the
  SAME provenance wire shape the iPad's kept Ask wears (``structured_json.
  provenance`` with ``via_kind: "ask"``, ask keys only when present; one
  canonical ``sources`` row per card read plus the ask's own via row) — one
  shape, one renderer, every surface.
"""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _new_id, _run_frame

log = get_logger("web.routes.primitives")

# The iPad caps a route's material at 6000 chars (DeskDioramaStage.runRoute);
# the hub mirrors it so the same ask reads the same amount of desk.
_MATERIAL_CAP = 6000

# HSM-15-12: the context envelope. A grounded ask ships REFERENCES and the hub
# hydrates from its own store — it holds the full transcripts, the phone may
# hold truncated copies, and DERP bandwidth stays sane. Bounds are explicit:
# a cut transcript is marked in the block, never trimmed silently.
_GROUNDING_MAX_REFS = 16
_GROUNDING_TRANSCRIPT_CAP = 12_000
_GROUNDING_EXPANDS = ("summary", "full")

_ASK_SYSTEM_PROMPT = (
    "You are the desk's AI core. Follow the instruction using the material "
    "provided. Be concrete and brief."
)


# HS-84-04: the host/badge derivation lives with the resolver now; the alias
# keeps this module's import surface (recipes.py) stable.
from ....intel.providers import endpoint_egress, endpoint_host as _host_of


def _run_egress(ctx: Any, prof: Any, intel: Any) -> tuple[dict[str, Any], str]:
    """The run's HONEST egress badge + model (the 16-09 grammar), ONE derivation.

    A profile run names its endpoint's host. A default cloud run names the
    endpoint the engine ACTUALLY used — `effective_intel_cloud`, so an
    assigned intel profile (HS-84-01) is reported, not the raw legacy config.
    """
    if prof is not None and prof.kind == "meshNode" and getattr(prof, "node", ""):
        return endpoint_egress(node=prof.node), str(prof.model or "")
    if prof is not None and prof.kind == "openAICompatible" and prof.base_url:
        return endpoint_egress(cloud=True, base_url=prof.base_url), str(prof.model or "")
    if getattr(intel, "active_provider", "") == "mesh":
        # the DEFAULT engine is a config-assigned meshNode profile (HS-85-02)
        return endpoint_egress(node=getattr(intel, "node", "")), str(
            getattr(intel, "model_hint", "") or ""
        )
    if intel.active_provider == "cloud":
        from ....config import Config
        from ....intel.providers import effective_intel_cloud

        effective = effective_intel_cloud(Config.load().meeting)
        return endpoint_egress(cloud=True, base_url=effective.base_url), str(effective.model or "")
    from ..sync import _hub_model_name

    return endpoint_egress(cloud=False), _hub_model_name(ctx)


def _meeting_digest(state: Any) -> str:
    """A meeting's summary-level material: intel summary + action items when
    intel exists, else the opening segments (mirrors the iPad's routableText)."""
    parts: list[str] = []
    if state.intel is not None and state.intel.summary:
        parts.append(state.intel.summary)
        items = state.intel.to_dict().get("action_items") or []
        tasks = [str(i.get("task") or i.get("text") or "") for i in items if isinstance(i, dict)]
        tasks = [t for t in tasks if t]
        if tasks:
            parts.append("\n".join(f"- {t}" for t in tasks))
    else:
        parts.append("\n".join(f"{s.speaker}: {s.text}" for s in state.segments[:40]))
    return "\n\n".join(p for p in parts if p)


def _context_material(db: Any, cid: str, kind: str, title: str) -> tuple[str, str]:
    """One lasso'd card's (title, routable text) from the canonical store.

    Mirrors the iPad's ``routableText`` per kind; a card the hub cannot load
    contributes its title honestly instead of failing the whole ask.
    """
    kind = str(kind or "").strip().lower()
    try:
        if kind == "note":
            note = db.notes.get(cid)
            if note is not None and not getattr(note, "deleted", False):
                return (note.title or title or cid, str(note.body_markdown or ""))
        elif kind == "artifact":
            art = db.plugins.get_artifact(cid)
            if art is not None:
                return (art.title or title or cid, str(art.body_markdown or ""))
        elif kind == "meeting":
            state = db.meetings.get_meeting(cid)
            if state is not None:
                return (state.title or title or cid, _meeting_digest(state))
        elif kind == "kb":
            kb = db.kbs.get(cid)
            if kb is not None and not getattr(kb, "deleted", False):
                members = list(getattr(kb, "member_ids", None) or [])
                return (kb.name or title or cid, "\n".join(f"- {m}" for m in members))
    except Exception as exc:
        log.debug(f"ask context {kind}:{cid} unavailable: {exc}")
    return (title or cid, "")


def _assemble_material(db: Any, context: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
    """The joined material block + the (ids, titles) lineage actually read."""
    blocks: list[str] = []
    ids: list[str] = []
    titles: list[str] = []
    for entry in context:
        if not isinstance(entry, dict):
            continue
        cid = str(entry.get("id") or "").strip()
        if not cid:
            continue
        kind = str(entry.get("kind") or "")
        hint = str(entry.get("title") or "")
        resolved_title, text = _context_material(db, cid, kind, hint)
        ids.append(cid)
        titles.append(resolved_title)
        blocks.append(f"## {resolved_title}\n{text}" if text else f"## {resolved_title}")
    return ("\n\n".join(blocks))[:_MATERIAL_CAP], ids, titles


def _runnable_models(ctx: WebContext, db: Any) -> list[dict[str, Any]]:
    """The hub's runnable allow-list (HS-83-03) — ONE derivation shared by the
    ask route's model-override check and ``GET /api/models``: the hub's own
    configured model, then each non-deleted profile's model. Deduped by name
    (the hub's own row wins), so no client discovers capability by provoking
    the 400."""
    from ..sync import _hub_model_name

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    hub_model = _hub_model_name(ctx)
    if hub_model:
        rows.append({"name": hub_model, "source": "hub", "profile_id": None})
        seen.add(hub_model)
    for p in db.profiles.list():
        name = str(p.model or "")
        if p.deleted or not name or name in seen:
            continue
        rows.append({"name": name, "source": "profile", "profile_id": p.id})
        seen.add(name)
    return rows


def _hydrate_grounding(
    db: Any, meeting_ids: list[str], artifact_ids: list[str], expand: str
) -> tuple[list[str], list[str], list[str], list[str]]:
    """The envelope's hub half: (blocks, ids, titles, unknown_ids).

    Each block wears the provenance header the iPad's assembler wears —
    ``[MEETING: <title> — <date>]`` / ``[ARTIFACT: <title> — <meeting>]`` —
    one envelope shape across on-device, endpoint, and desktop runs. An id
    the hub does not hold is returned as unknown (the caller refuses loudly;
    grounding is never a best-effort claim)."""
    blocks: list[str] = []
    ids: list[str] = []
    titles: list[str] = []
    unknown: list[str] = []
    for mid in meeting_ids:
        try:
            state = db.meetings.get_meeting(mid)
        except Exception:
            state = None
        if state is None:
            unknown.append(mid)
            continue
        title = state.title or mid
        day = ""
        try:
            day = state.started_at.date().isoformat()
        except Exception:
            day = ""
        header = f"[MEETING: {title} — {day}]" if day else f"[MEETING: {title}]"
        if expand == "full" and state.segments:
            text = "\n".join(f"{s.speaker}: {s.text}" for s in state.segments)
            if len(text) > _GROUNDING_TRANSCRIPT_CAP:
                text = (
                    text[:_GROUNDING_TRANSCRIPT_CAP]
                    + f"\n[transcript cut at {_GROUNDING_TRANSCRIPT_CAP} chars]"
                )
        else:
            text = _meeting_digest(state)
        blocks.append(f"{header}\n{text}" if text else header)
        ids.append(mid)
        titles.append(title)
    for aid in artifact_ids:
        try:
            art = db.plugins.get_artifact(aid)
        except Exception:
            art = None
        if art is None:
            unknown.append(aid)
            continue
        of = ""
        if art.meeting_id:
            try:
                parent = db.meetings.get_meeting(art.meeting_id)
                of = (parent.title or "") if parent is not None else ""
            except Exception:
                of = ""
        title = art.title or aid
        header = f"[ARTIFACT: {title} — {of}]" if of else f"[ARTIFACT: {title}]"
        body = str(art.body_markdown or "")
        blocks.append(f"{header}\n{body}" if body else header)
        ids.append(aid)
        titles.append(title)
    return blocks, ids, titles, unknown


def _ask_provenance(
    *, lens: str, prompt: str, context_ids: list[str], context_titles: list[str]
) -> dict[str, Any]:
    """The structured provenance object, byte-shaped like the iPad's
    ``OutputRecord.provenanceJSON`` (DeskRecords.swift): ask keys ride only
    when present, so nothing here can disturb the golden recipe/chain shape."""
    single = len(context_ids) == 1
    source_title = context_titles[0] if single else f"{len(context_titles)} items"
    prov: dict[str, Any] = {
        "source_card_id": context_ids[0] if single else "",
        "source_card_title": source_title,
        "via_id": "",
        "via_name": lens,
        "via_kind": "ask",
    }
    if context_ids:
        prov["context_ids"] = context_ids
    if context_titles:
        prov["context_titles"] = context_titles
    if prompt:
        prov["prompt"] = prompt
    return prov


def build_ask_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/models")
    async def api_list_models() -> Any:
        """The runnable allow-list (HS-83-03): what a `model` override on
        `/api/ask` would accept — the hub's own model + its profiles' models.
        The SAME derivation the ask route's refusal names, so no client ever
        discovers capability by provoking the 400."""
        try:
            from ....db import get_database

            return JSONResponse({"models": _runnable_models(ctx, get_database())})
        except Exception as exc:
            return error_500(exc, log, "Failed to list models")

    @router.post("/api/ask")
    async def api_ask(request: Request) -> Any:
        """Run an instruction over lasso'd context. Persists nothing."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "prompt is required"}, status_code=400)
        lens = str(body.get("lens") or "Ask").strip() or "Ask"
        context = body.get("context") if isinstance(body.get("context"), list) else []
        try:
            from ....db import get_database
            from ....intel.models import MeetingIntelError
            from ....intel.providers import (
                build_configured_meeting_intel,
                build_meeting_intel_for_profile,
            )

            db = get_database()
            material, context_ids, context_titles = _assemble_material(db, context)

            # HSM-15-12: hydrate the grounding refs from the canonical store.
            grounding = body.get("grounding")
            grounding_echo: Optional[dict[str, Any]] = None
            envelope = ""
            if grounding is not None:
                if not isinstance(grounding, dict):
                    return JSONResponse(
                        {"error": "grounding must be an object"}, status_code=400
                    )
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
                blocks, g_ids, g_titles, unknown = _hydrate_grounding(
                    db, meeting_ids, artifact_ids, expand
                )
                if unknown:
                    return JSONResponse(
                        {"error": "grounding ids not on this hub", "unknown_ids": unknown},
                        status_code=400,
                    )
                envelope = "\n\n".join(blocks)
                context_ids += g_ids
                context_titles += g_titles
                grounding_echo = {
                    "meeting_ids": meeting_ids,
                    "artifact_ids": artifact_ids,
                    "expand": expand,
                    "titles": g_titles,
                }

            user_prompt = prompt + ("\n\nMaterial:\n" + material if material else "")
            if envelope:
                user_prompt += "\n\nGrounding:\n" + envelope

            # Phase 24: run on the requested profile when set (its endpoint, the
            # key from the hub's secrets), else the hub's configured default.
            ran_profile_id: Optional[str] = str(body.get("profile_id") or "").strip() or None
            prof = None
            if ran_profile_id:
                prof = db.profiles.get(ran_profile_id)
                if prof is None or prof.deleted:
                    ran_profile_id = None
                    prof = None

            # HSM-15-11: a manifest-bounded model override — "run THIS model on
            # the hub". The allow-list is what the hub can actually run: its own
            # configured model + its profiles' models. A model some OTHER node
            # pushed a manifest for is not runnable here and refuses loudly.
            override = str(body.get("model") or "").strip() or None
            if override:
                from ..sync import _hub_model_name

                hub_model = _hub_model_name(ctx)
                profiles = [p for p in db.profiles.list() if not p.deleted]
                if prof is not None and (prof.model or "") == override:
                    pass  # the requested profile already runs it
                elif (by_model := next((p for p in profiles if (p.model or "") == override), None)) is not None:
                    prof, ran_profile_id = by_model, by_model.id
                elif override == hub_model:
                    prof, ran_profile_id = None, None  # the hub's own engine IS this model
                else:
                    allowed = sorted({r["name"] for r in _runnable_models(ctx, db)})
                    return JSONResponse(
                        {"error": f"model {override!r} is not runnable on this hub",
                         "allowed_models": allowed},
                        status_code=400,
                    )

            if prof is not None:
                intel = build_meeting_intel_for_profile(
                    kind=prof.kind, base_url=prof.base_url, model=prof.model, profile_id=prof.id,
                    node=getattr(prof, "node", "")
                )
            else:
                intel = build_configured_meeting_intel()

            max_tokens = body.get("max_tokens")
            temperature = body.get("temperature")
            _run_frame(ctx, "running", kind="ask", ref="ask", name=lens)
            try:
                output = intel.run_prompt(
                    system_prompt=_ASK_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=float(temperature) if temperature is not None else None,
                    max_tokens=int(max_tokens) if max_tokens is not None else None,
                )
            except MeetingIntelError as exc:
                _run_frame(ctx, "error", kind="ask", ref="ask", name=lens, error=str(exc))
                return JSONResponse({"error": str(exc)}, status_code=502)
            _run_frame(ctx, "ready", kind="ask", ref="ask", name=lens)

            # The run's HONEST egress (the 16-09 grammar: state where THIS run
            # went, never the app default) — the one derivation (HS-84-04).
            egress, model = _run_egress(ctx, prof, intel)

            payload: dict[str, Any] = {
                "output": output,
                "lens": lens,
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
            return error_500(exc, log, "Failed to run ask")

    @router.post("/api/ask/keep")
    async def api_ask_keep(request: Request) -> Any:
        """Persist a kept ask — the same artifact the iPad's Keep mints."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        output = str(body.get("output") or "")
        if not output.strip():
            return JSONResponse({"error": "output is required"}, status_code=400)
        lens = str(body.get("lens") or "Ask").strip() or "Ask"
        prompt = str(body.get("prompt") or "")
        context = body.get("context") if isinstance(body.get("context"), list) else []
        context_ids = [str(e.get("id") or "") for e in context if isinstance(e, dict) and e.get("id")]
        context_titles = [
            str(e.get("title") or e.get("id") or "")
            for e in context
            if isinstance(e, dict) and e.get("id")
        ]
        try:
            from ....db import get_database

            prov = _ask_provenance(
                lens=lens, prompt=prompt,
                context_ids=context_ids, context_titles=context_titles,
            )
            # The canonical sources rows (iPad `provenanceSources`): every card
            # the ask read, plus its own via row.
            sources = [
                {"source_type": "card", "source_ref": t} for t in (context_titles or [prov["source_card_title"]])
            ] + [{"source_type": "ask", "source_ref": lens}]

            artifact_id = _new_id("artifact")
            get_database().plugins.record_artifact(
                artifact_id=artifact_id,
                meeting_id="",
                artifact_type="plugin_output",
                title=lens,
                body_markdown=output,
                structured_json={
                    "lens": lens,
                    "source": prov["source_card_title"],
                    "provenance": prov,
                },
                confidence=1.0,
                status="draft",
                plugin_id="web.desk",
                plugin_version="0",
                sources=sources,
            )
            return JSONResponse({"artifact_id": artifact_id}, status_code=201)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep ask")

    return router
