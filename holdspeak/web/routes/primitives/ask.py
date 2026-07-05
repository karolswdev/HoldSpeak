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

_ASK_SYSTEM_PROMPT = (
    "You are the desk's AI core. Follow the instruction using the material "
    "provided. Be concrete and brief."
)


def _host_of(base_url: Any) -> str:
    """The bare host a cloud run egresses to (never a full URL in a badge)."""
    raw = str(base_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "//" in raw else f"//{raw}")
    return parsed.hostname or ""


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
                return (state.title or title or cid, "\n\n".join(p for p in parts if p))
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
            user_prompt = prompt + ("\n\nMaterial:\n" + material if material else "")

            # Phase 24: run on the requested profile when set (its endpoint, the
            # key from the hub's secrets), else the hub's configured default.
            ran_profile_id: Optional[str] = str(body.get("profile_id") or "").strip() or None
            prof = None
            if ran_profile_id:
                prof = db.profiles.get(ran_profile_id)
                if prof is None or prof.deleted:
                    ran_profile_id = None
                    prof = None
            if prof is not None:
                intel = build_meeting_intel_for_profile(
                    kind=prof.kind, base_url=prof.base_url, model=prof.model, profile_id=prof.id
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
            # went, never the app default). A profile run names its endpoint's
            # host; a default run reports what the engine actually used.
            if prof is not None and prof.kind == "openAICompatible" and prof.base_url:
                egress: dict[str, Any] = {"scope": "cloud", "host": _host_of(prof.base_url)}
                model = str(prof.model or "")
            elif intel.active_provider == "cloud":
                from ....config import Config

                meeting_cfg = Config.load().meeting
                egress = {"scope": "cloud", "host": _host_of(meeting_cfg.intel_cloud_base_url) or "api.openai.com"}
                model = str(meeting_cfg.intel_cloud_model or "")
            else:
                from ..sync import _hub_model_name

                egress = {"scope": "local"}
                model = _hub_model_name(ctx)

            return JSONResponse({
                "output": output,
                "lens": lens,
                "provider": intel.active_provider,
                "profile_id": ran_profile_id,
                "egress": egress,
                "model": model,
                "context_ids": context_ids,
                "context_titles": context_titles,
            })
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
