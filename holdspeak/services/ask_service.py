"""Transport-neutral Ask orchestration (HS-123-04)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..db.core import Database
from ..principals import Principal
from ..grounding import (
    GROUNDING_EXPANDS, GROUNDING_MAX_REFS, hydrate_grounding_blocks,
    hydrate_grounding_blocks_detailed, meeting_digest, score_claims,
)
from .errors import ServiceError, ValidationError

_MATERIAL_CAP = 6000
_ASK_SYSTEM_PROMPT = "You are the desk's AI core. Follow the instruction using the material provided. Be concrete and brief."


@observe_service
class AskService:
    def __init__(self, db: Database, hub_model: Callable[[], str] | None = None,
                 broadcast: Callable[..., None] | None = None,
                 rails_hydrator: Callable[[list[dict[str, Any]], Principal], tuple[list[Any], list[str]]] | None = None, *, observer: PipelineObserver | None = None) -> None:
        self._db, self._hub_model, self._broadcast, self._rails_hydrator = db, hub_model or (lambda: ""), broadcast, rails_hydrator
        self._observer = observer or NullObserver()

    def list_models(self, principal: Principal) -> list[dict[str, Any]]:
        rows, seen = [], set()
        hub_model = self._hub_model()
        if hub_model:
            rows.append({"name": hub_model, "source": "hub", "profile_id": None}); seen.add(hub_model)
        for profile in self._db.profiles.list():
            name = str(profile.model or "")
            if profile.deleted or not name or name in seen: continue
            row: dict[str, Any] = {"name": name, "source": "profile", "profile_id": profile.id}
            node = str(getattr(profile, "node", "") or "")
            if profile.kind == "meshNode" and node:
                from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS
                last = self._db.mesh_relay.worker_last_seen(node)
                age = None if last is None else (datetime.now() - last).total_seconds()
                row.update(node=node, live=age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS,
                           last_seen_seconds=None if age is None else int(age))
            rows.append(row); seen.add(name)
        return rows

    def resolve_grounding(self, principal: Principal, refs: list[str]) -> dict[str, Any]:
        refs = [str(ref).strip() for ref in refs if str(ref).strip()]
        if len(refs) > GROUNDING_MAX_REFS:
            raise ValidationError(f"grounding is capped at {GROUNDING_MAX_REFS}")
        blocks, _, titles, unknown = hydrate_grounding_blocks(self._db, [], [], "summary", qualified_refs=refs)
        if unknown:
            raise ValidationError("grounding ids not on this hub", code="grounding_not_found", context={"unknown_ids": unknown})
        return {"refs": refs, "titles": titles, "chars": sum(len(block) for block in blocks),
                "blocks": [{"ref": ref, "title": title, "chars": len(block)} for ref, title, block in zip(refs, titles, blocks)]}

    async def ask(self, principal: Principal, question: str, grounding: Any = None, *, lens: str = "Ask", context: list[dict[str, Any]] | None = None, model: str | None = None, inference_target_id: str | None = None, profile_id: str | None = None, max_tokens: Any = None, temperature: Any = None) -> dict[str, Any]:
        prompt = str(question or "").strip()
        if not prompt: raise ValidationError("prompt is required")
        lens = str(lens or "Ask").strip() or "Ask"
        material, context_ids, context_titles = self._assemble_material(context or [])
        envelope, grounding_echo = self._grounding(principal, grounding, prompt)
        if grounding_echo:
            context_ids += grounding_echo.pop("_ids"); context_titles += grounding_echo.pop("_titles")
        user_prompt = prompt + ("\n\nMaterial:\n" + material if material else "") + ("\n\nGrounding:\n" + envelope if envelope else "")
        from ..inference_targets import build_intel_for_target, resolve_inference_target, target_refusal, target_runtime_error
        requested = str(inference_target_id or profile_id or "this_machine").strip()
        target = resolve_inference_target(self._db, requested)
        ran_profile_id = target.profile_id
        prof = self._db.profiles.get(ran_profile_id) if ran_profile_id else None
        override = str(model or "").strip() or None
        if override:
            if prof is not None and (prof.model or "") == override: pass
            elif (by_model := next((p for p in self._db.profiles.list() if not p.deleted and (p.model or "") == override), None)) is not None:
                prof, ran_profile_id, target = by_model, by_model.id, resolve_inference_target(self._db, by_model.id)
            elif override == self._hub_model():
                prof, ran_profile_id, target = None, None, resolve_inference_target(self._db, "this_machine")
            else: raise ValidationError(f"model {override!r} is not runnable on this hub", context={"allowed_models": sorted({r['name'] for r in self.list_models(principal)})})
        if not target.ready: raise ServiceError("target_unavailable", target.readiness_reason, context={**target_refusal(target), "status": 409})
        if prof is not None and prof.kind == "meshNode":
            from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS
            node = str(getattr(prof, "node", "") or ""); last = self._db.mesh_relay.worker_last_seen(node) if node else None
            age = None if last is None else (datetime.now() - last).total_seconds()
            if age is None or age > DEFAULT_LIVENESS_WINDOW_SECONDS:
                seen = "no worker has ever polled" if age is None else f"last seen {int(age)}s ago"
                raise ValidationError(f"mesh node '{node}' is offline ({seen})")
        intel = build_intel_for_target(target, self._db)
        self._emit("running", kind="ask", ref="ask", name=lens)
        try:
            output = await asyncio.to_thread(intel.run_prompt, system_prompt=_ASK_SYSTEM_PROMPT, user_prompt=user_prompt, temperature=float(temperature) if temperature is not None else None, max_tokens=int(max_tokens) if max_tokens is not None else None)
        except Exception as exc:
            from ..intel.models import MeetingIntelError
            if isinstance(exc, MeetingIntelError):
                error = target_runtime_error(target, exc); self._emit("error", kind="ask", ref="ask", name=lens, error=error)
                raise ServiceError("inference_failed", error, context={"inference_target": target.to_dict(), "alternate_target_id": "this_machine", "status": 502}) from exc
            raise
        self._emit("ready", kind="ask", ref="ask", name=lens)
        egress, selected_model = self._egress(prof, intel)
        payload: dict[str, Any] = {"output": output, "lens": lens, "provider": intel.active_provider, "profile_id": ran_profile_id, "inference_target": target.to_dict(), "actual_placement": target.placement_receipt(provider=intel.active_provider, model=selected_model), "egress": egress, "model": selected_model, "context_ids": context_ids, "context_titles": context_titles}
        if grounding_echo is not None: payload["grounding"] = grounding_echo
        source_text = material + ("\n\n" + envelope if envelope else "")
        if source_text.strip(): payload["grounding_claims"] = score_claims(output, source_text)
        return payload

    def keep(self, principal: Principal, output: str, sources: list[dict[str, Any]], *, lens: str = "Ask", prompt: str = "", grounding: Any = None) -> dict[str, Any]:
        if not str(output or "").strip(): raise ValidationError("output is required")
        from ..db.relationships import qualified_ref
        exact_refs: list[str] = []
        aliases = {"kb":"knowledge", "directory":"zone", "recipe":"persona", "chain":"sequence"}
        context_ids, context_titles = [], []
        for entry in sources:
            if not isinstance(entry, dict): continue
            if entry.get("id"): context_ids.append(str(entry["id"])); context_titles.append(str(entry.get("title") or entry["id"]))
            candidate = str(entry.get("ref") or "").strip()
            if not candidate and entry.get("kind") and entry.get("id"): candidate = f"{aliases.get(str(entry['kind']), str(entry['kind']))}:{entry['id']}"
            if candidate:
                try: exact_refs.append(qualified_ref(candidate))
                except ValueError as exc: raise ValidationError(str(exc)) from exc
        for candidate in (grounding or {}).get("refs", []) if isinstance(grounding, dict) else []:
            try: exact_refs.append(qualified_ref(candidate))
            except ValueError as exc: raise ValidationError(str(exc)) from exc
        exact_refs = list(dict.fromkeys(exact_refs))
        if exact_refs:
            *_, stale = hydrate_grounding_blocks(self._db, [], [], "summary", qualified_refs=exact_refs)
            if stale: raise ServiceError("grounding_changed", "grounding changed or was deleted before Keep", context={"unknown_ids": stale, "status": 409})
        axes = {ref: {"zone_id": (p.directory_id if (p := self._db.directory_memberships.get(ref)) else None), "knowledge_ids": [r.knowledge_id for r in self._db.knowledge_memberships.list_for_resource(ref)], "project_ids": [r.project_id for r in self._db.project_relationships.list_for_resource(ref)]} for ref in exact_refs}
        prov = self._provenance(lens, prompt, context_ids, context_titles)
        artifact_id = "artifact_" + __import__("uuid").uuid4().hex[:12]
        canonical = [{"source_type": ref.split(":", 1)[0], "source_ref": ref} for ref in exact_refs] or [{"source_type":"card", "source_ref": title} for title in (context_titles or [prov["source_card_title"]])]
        canonical.append({"source_type":"ask", "source_ref":lens})
        self._db.plugins.record_artifact(artifact_id=artifact_id, meeting_id="", artifact_type="plugin_output", title=lens, body_markdown=output, structured_json={"lens":lens,"source":prov["source_card_title"],"provenance":prov,"qualified_refs":exact_refs,"relationship_snapshot":axes}, confidence=1.0, status="draft", plugin_id="web.desk", plugin_version="0", sources=canonical)
        return {"artifact_id": artifact_id}

    def _assemble_material(self, context: list[dict[str, Any]]) -> tuple[str, list[str], list[str]]:
        blocks=[]; ids=[]; titles=[]
        for entry in context:
            if not isinstance(entry, dict) or not (cid := str(entry.get("id") or "").strip()): continue
            title, text = self._context_material(cid, str(entry.get("kind") or ""), str(entry.get("title") or "")); ids.append(cid); titles.append(title); blocks.append(f"## {title}\n{text}" if text else f"## {title}")
        return "\n\n".join(blocks)[:_MATERIAL_CAP], ids, titles

    def _context_material(self, cid: str, kind: str, title: str) -> tuple[str, str]:
        try:
            if kind.lower() == "note" and (x := self._db.notes.get(cid)) is not None and not x.deleted: return x.title or title or cid, str(x.body_markdown or "")
            if kind.lower() == "artifact" and (x := self._db.plugins.get_artifact(cid)) is not None: return x.title or title or cid, str(x.body_markdown or "")
            if kind.lower() == "meeting" and (x := self._db.meetings.get_meeting(cid)) is not None: return x.title or title or cid, meeting_digest(x)
            if kind.lower() == "kb" and (x := self._db.kbs.get(cid)) is not None and not x.deleted: return x.name or title or cid, "\n".join(f"- {m}" for m in (x.member_ids or []))
        except Exception: pass
        return title or cid, ""

    def _grounding(self, principal: Principal, grounding: Any, prompt: str) -> tuple[str, dict[str, Any] | None]:
        if grounding is None: return "", None
        if not isinstance(grounding, dict): raise ValidationError("grounding must be an object")
        vals = lambda key: [str(x).strip() for x in grounding.get(key, []) if str(x).strip()] if isinstance(grounding.get(key), list) else []
        meeting_ids, artifact_ids, refs = vals("meeting_ids"), vals("artifact_ids"), vals("refs"); rails = [x for x in grounding.get("rails", []) if isinstance(x, dict)] if isinstance(grounding.get("rails"), list) else []
        expand = str(grounding.get("expand") or "summary").strip() or "summary"
        if expand not in GROUNDING_EXPANDS: raise ValidationError(f"expand {expand!r} is not one of {list(GROUNDING_EXPANDS)}")
        if len(meeting_ids)+len(artifact_ids)+len(refs)+len(rails) > GROUNDING_MAX_REFS: raise ValidationError(f"grounding is capped at {GROUNDING_MAX_REFS}")
        blocks, ids, titles, hydration = hydrate_grounding_blocks_detailed(self._db, meeting_ids, artifact_ids, expand, qualified_refs=refs, query=prompt)
        unknown=list(hydration.unknown)
        if rails and self._rails_hydrator:
            rblocks, runknown = self._rails_hydrator(rails, principal); unknown += runknown
            for b in rblocks: blocks.append(f"[{b.kind.replace('rails:', 'RAILS ').upper()}: {b.title} — {b.subtitle}]\n{b.text}" if b.text else f"[{b.kind.replace('rails:', 'RAILS ').upper()}: {b.title} — {b.subtitle}]"); ids.append(b.ref); titles.append(b.title)
        if unknown: raise ValidationError("grounding ids not on this hub", code="grounding_not_found", context={"unknown_ids": unknown})
        echo: dict[str, Any] = {"meeting_ids":meeting_ids,"artifact_ids":artifact_ids,"expand":expand,"titles":titles,"source_refs":hydration.source_refs,"selection":hydration.selection,"matched_count":hydration.matched_count,"overflow_count":hydration.overflow_count,"_ids":ids,"_titles":titles}
        if refs: echo["refs"] = refs
        if rails: echo["rails"] = rails
        return "\n\n".join(blocks), echo

    def _egress(self, profile: Any, intel: Any) -> tuple[dict[str, Any], str]:
        from ..intel.providers import endpoint_egress
        if profile is not None and profile.kind == "meshNode" and getattr(profile,"node",""): return endpoint_egress(node=profile.node), str(profile.model or "")
        if profile is not None and profile.kind == "openAICompatible" and profile.base_url: return endpoint_egress(cloud=True, base_url=profile.base_url), str(profile.model or "")
        if getattr(intel,"active_provider","") == "mesh": return endpoint_egress(node=getattr(intel,"node","")), str(getattr(intel,"model_hint","") or "")
        if getattr(intel,"active_provider","") == "cloud":
            from ..config import Config
            from ..intel.providers import effective_intel_cloud
            effective=effective_intel_cloud(Config.load().meeting); return endpoint_egress(cloud=True, base_url=effective.base_url), str(effective.model or "")
        return endpoint_egress(cloud=False), self._hub_model()
    def _emit(self, state: str, **frame: Any) -> None:
        if self._broadcast: self._broadcast(state, **frame)
    @staticmethod
    def _provenance(lens: str, prompt: str, ids: list[str], titles: list[str]) -> dict[str, Any]:
        single=len(ids)==1; p={"source_card_id":ids[0] if single else "", "source_card_title":titles[0] if single else f"{len(titles)} items", "via_id":"", "via_name":lens, "via_kind":"ask"}
        if ids: p["context_ids"]=ids
        if titles: p["context_titles"]=titles
        if prompt: p["prompt"]=prompt
        return p
