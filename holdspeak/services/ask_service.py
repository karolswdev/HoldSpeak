"""Transport-neutral Ask orchestration (HS-123-04)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import asyncio
import time
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..db.core import Database
from ..deployment_revisions import capture_deployment_revision
from ..kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from ..kernel.model import KernelRefused
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal
from ..grounding import (
    GROUNDING_EXPANDS, GROUNDING_MAX_REFS, hydrate_grounding_blocks,
    hydrate_grounding_blocks_detailed, meeting_digest, score_claims,
)
from .errors import ServiceError, ValidationError
from .inference_outcomes import map_inference_outcome

_MATERIAL_CAP = 6000
_ASK_SYSTEM_PROMPT = "You are the desk's AI core. Follow the instruction using the material provided. Be concrete and brief."
ASK_SERVICE_CONTRACT = "holdspeak.ask"
ASK_SERVICE_SCHEMA_VERSION = "1"
ASK_PAYLOAD_SCHEMA_VERSION = 1


@observe_service
class AskService:
    def __init__(self, db: Database, hub_model: Callable[[], str] | None = None,
                 broadcast: Callable[..., None] | None = None,
                 rails_hydrator: Callable[[list[dict[str, Any]], Principal], tuple[list[Any], list[str]]] | None = None, *, observer: PipelineObserver | None = None, broker: Any = None) -> None:
        if broker is None:
            from ..kernel.runtime import _service
            broker = _service()
        if getattr(broker, "database", db) is not db:
            from ..kernel.runtime import _configure
            broker = _configure(db)
        # `hub_model` is RETIRED as a model describer (HS-132-09): it answered the
        # configured meeting placement, which is a different question from "what
        # does the destination this Ask resolved to load". It is still accepted so
        # the transport wiring keeps constructing this service unchanged, and it is
        # consulted NOWHERE — every model name below comes from the resolved
        # destination's own deployment identity.
        self._db, self._hub_model, self._broadcast, self._rails_hydrator, self._broker = db, hub_model or (lambda: ""), broadcast, rails_hydrator, broker
        from ..kernel.ask_projection import register
        register(self._broker.projection_stager)
        self._observer = observer or NullObserver()
        # Cancellation must reach the SAME runner instance whose in-process
        # registry holds the in-flight invocation, across per-request service
        # constructions: the runner is the broker-owned singleton, and the
        # acting principal rides the kernel `_as_principal` context.
        self._runner = self._broker.inference_runner

    def _invoke(self, principal: Principal, request: InvocationRequest, *, publish: Any) -> Any:
        from ..kernel.runtime import _as_principal
        with _as_principal(principal):
            return self._runner.invoke(request, CanonicalPromptAdapter(), publish=publish)

    def list_models(self, principal: Principal) -> list[dict[str, Any]]:
        # HS-130-06: one row PER DESTINATION, never deduped by model name. Id
        # (not name) is the selector, so two destinations serving one model name
        # both appear and are addressable — Ask can never "first-match" hop.
        # HS-132-09: the `this_machine` row names the model THIS destination
        # loads (its deployment identity), never the hub-wide describer. The
        # describer answers the CONFIGURED meeting placement — a cloud model id
        # whenever `intel_provider="cloud"` — while `this_machine` execution is
        # pinned local, so the row advertised a model the destination would
        # never load, and the no-retarget refusal below quoted it back.
        from ..inference_targets import THIS_MACHINE_ID, target_from_profile, this_machine_target
        rows: list[dict[str, Any]] = []
        hub_model = self._destination_model(this_machine_target())
        if hub_model:
            rows.append({"id": THIS_MACHINE_ID, "name": hub_model, "source": "hub", "profile_id": None})
        for profile in self._db.profiles.list():
            # Every row names its destination's deployment identity for the same
            # reason the hub row does — and an on-device destination that names
            # only a `model_file` used to be dropped from the picker entirely
            # while remaining addressable and ready (HS-132-09).
            name = self._destination_model(target_from_profile(profile, self._db))
            if profile.deleted or not name: continue
            row: dict[str, Any] = {"id": profile.id, "name": name, "source": "profile", "profile_id": profile.id}
            node = str(getattr(profile, "node", "") or "")
            if profile.kind == "meshNode" and node:
                from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS
                last = self._db.mesh_relay.worker_last_seen(node)
                age = None if last is None else (datetime.now() - last).total_seconds()
                row.update(node=node, live=age is not None and age <= DEFAULT_LIVENESS_WINDOW_SECONDS,
                           last_seen_seconds=None if age is None else int(age))
            rows.append(row)
        return rows

    @staticmethod
    def _destination_model(target: Any) -> str:
        """The model a destination advertises: its OWN deployment identity.

        One function so the picker row, the no-retarget refusal, and the
        payload's `selected_model` can never disagree about one destination.
        """
        deployment = getattr(target, "deployment", None)
        return str((getattr(deployment, "model", "") if deployment is not None else "") or target.model or "")

    def resolve_grounding(self, principal: Principal, refs: list[str]) -> dict[str, Any]:
        refs = [str(ref).strip() for ref in refs if str(ref).strip()]
        if len(refs) > GROUNDING_MAX_REFS:
            raise ValidationError(f"grounding is capped at {GROUNDING_MAX_REFS}")
        blocks, _, titles, unknown = hydrate_grounding_blocks(self._db, [], [], "summary", qualified_refs=refs)
        if unknown:
            raise ValidationError("grounding ids not on this hub", code="grounding_not_found", context={"unknown_ids": unknown})
        return {"refs": refs, "titles": titles, "chars": sum(len(block) for block in blocks),
                "blocks": [{"ref": ref, "title": title, "chars": len(block)} for ref, title, block in zip(refs, titles, blocks)]}

    async def ask(self, principal: Principal, question: str, grounding: Any = None, *, lens: str = "Ask", context: list[dict[str, Any]] | None = None, model: str | None = None, inference_target_id: str | None = None, profile_id: str | None = None, max_tokens: Any = None, temperature: Any = None, invocation_id: str | None = None, before_physical_dispatch: Any = None, before_compatibility_retry: Any = None) -> dict[str, Any]:
        prompt = str(question or "").strip()
        if not prompt: raise ValidationError("prompt is required")
        lens = str(lens or "Ask").strip() or "Ask"
        material, context_ids, context_titles = self._assemble_material(context or [])
        envelope, grounding_echo = self._grounding(principal, grounding, prompt)
        if grounding_echo:
            context_ids += grounding_echo.pop("_ids"); context_titles += grounding_echo.pop("_titles")
        user_prompt = prompt + ("\n\nMaterial:\n" + material if material else "") + ("\n\nGrounding:\n" + envelope if envelope else "")
        from ..inference_targets import resolve_placement, target_refusal
        placement = resolve_placement(self._db, invocation=(inference_target_id or profile_id) or None)
        target, requested = placement.target, placement.effective_target_id
        ran_profile_id = target.profile_id
        prof = self._db.profiles.get(ran_profile_id) if ran_profile_id else None
        # The model this destination will ACTUALLY load, from the deployment
        # identity readiness checked and execution loads (HS-130-03/HS-132-09) —
        # so the refusal below names the true model and `selected_model` cannot
        # hand the receipt a name no engine on this path will ever report.
        advertised = self._destination_model(target)
        override = str(model or "").strip() or None
        if override and override != advertised:
            offer = advertised or "no model"
            raise ValidationError(f"model {override!r} is not available on destination '{target.name}' (id {requested!r}); it runs {offer!r}. Address the destination that advertises {override!r} by its inference_target_id — Ask does not retarget by model name.", code="model_not_advertised", context={"inference_target_id": requested, "target_name": target.name, "requested_model": override, "available_models": [advertised] if advertised else [], "status": 400})
        if not target.ready:
            raise ServiceError("target_unavailable", target.readiness_reason, context={**target_refusal(target), "status": 409})
        if prof is not None and prof.kind == "meshNode":
            from ..intel.mesh_relay import DEFAULT_LIVENESS_WINDOW_SECONDS
            node = str(getattr(prof, "node", "") or ""); last = self._db.mesh_relay.worker_last_seen(node) if node else None
            age = None if last is None else (datetime.now() - last).total_seconds()
            if age is None or age > DEFAULT_LIVENESS_WINDOW_SECONDS:
                seen = "no worker has ever polled" if age is None else f"last seen {int(age)}s ago"
                raise ValidationError(f"mesh node '{node}' is offline ({seen})")
        # Resolve and persist the immutable deployment before payload construction
        # and ServiceContract hashing. Mutable target state cannot retarget this turn.
        revision = capture_deployment_revision(self._db, target)
        source_text = material + ("\n\n" + envelope if envelope else "")
        payload: dict[str, Any] = {"schema_version": ASK_PAYLOAD_SCHEMA_VERSION, "system_prompt": _ASK_SYSTEM_PROMPT, "user_prompt": user_prompt, "lens": lens, "context_ids": context_ids, "context_titles": context_titles, "grounding": grounding_echo, "source_text": source_text, "temperature": float(temperature) if temperature is not None else None, "max_tokens": int(max_tokens) if max_tokens is not None else None, "deployment_revision": revision.id, "selected_model": advertised}
        invocation_id = str(invocation_id or ("ask_" + uuid.uuid4().hex)).strip()
        if not invocation_id or not invocation_id.replace("_", "").isalnum():
            raise ValidationError("invocation id is invalid", code="ask_invocation_id_invalid")
        self._emit("running", kind="ask", ref="ask", name=lens)
        try:
            outcome = await asyncio.to_thread(
                self._invoke,
                principal,
                InvocationRequest(revision.id, ServiceContract.for_payload(ASK_SERVICE_CONTRACT, ASK_SERVICE_SCHEMA_VERSION, payload), time.time() + 60, payload, invocation_id, before_physical_dispatch=before_physical_dispatch, before_compatibility_retry=before_compatibility_retry),
                publish=self._broker.projection_stager.publisher(invocation_id, "ask-result", lambda output: self._ask_projection(output, payload, target, ran_profile_id, placement.placement_dict())),
            )
        except KernelRefused as exc:
            self._emit("error", kind="ask", ref="ask", name=lens, error=exc.reason)
            raise self._outcome_error(None, exc)
        if outcome.outcome != "succeeded":
            self._emit("error", kind="ask", ref="ask", name=lens, error=outcome.outcome)
            raise self._outcome_error(outcome, None, target=target)
        result = self._broker.projection_stager.finalize(invocation_id)
        if result is None:
            raise ServiceError("projection_not_published", "Ask result is awaiting receipt reconciliation", context={"invocation_id": invocation_id, "operation_id": outcome.operation_id, "receipt": dict(outcome.receipt), "result_ref": outcome.result_ref, "status": 409})
        self._emit("ready", kind="ask", ref="ask", name=lens)
        return dict(result)

    def _ask_projection(self, output: Any, payload: dict[str, Any], target: Any, profile_id: str | None, placement_block: dict[str, Any] | None = None) -> dict[str, Any]:
        dispatched = dict(output) if isinstance(output, dict) else {"output": str(output)}
        answer = str(dispatched["output"])
        provider = str(dispatched.get("provider") or target.deployment.engine)
        selected_model = str(dispatched.get("model") or payload["selected_model"] or target.deployment.model)
        from urllib.parse import urlparse
        egress: dict[str, Any] = {"scope": "local"}
        if target.deployment.boundary == "private_network":
            egress = {"scope": "private_network", "host": urlparse(target.deployment.endpoint).hostname or ""}
        elif target.deployment.boundary in {"cloud", "external_service"}:
            egress = {"scope": "cloud"}
        elif target.kind == "mesh_node":
            egress = {"scope": "mesh", "host": target.deployment.node}
        result: dict[str, Any] = {"output": answer, "lens": payload["lens"], "provider": provider,
                                  "profile_id": profile_id, "inference_target": target.to_dict(),
                                  "actual_placement": target.placement_receipt(provider=provider, model=selected_model),
                                  "egress": egress, "model": selected_model,
                                  "context_ids": list(payload["context_ids"]), "context_titles": list(payload["context_titles"])}
        if placement_block is not None: result["placement"] = placement_block
        if payload["grounding"] is not None: result["grounding"] = payload["grounding"]
        source_text = str(payload["source_text"])
        if source_text.strip(): result["grounding_claims"] = score_claims(answer, source_text)
        return result

    _outcome_error = staticmethod(map_inference_outcome)

    def cancel(self, principal: Principal, invocation_id: str) -> dict[str, str]:
        from ..kernel.runtime import _as_principal
        with _as_principal(principal):
            return {"invocation_id": invocation_id, "disposition": self._runner.cancel(invocation_id)}

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

    def _emit(self, state: str, **frame: Any) -> None:
        if self._broadcast: self._broadcast(state, **frame)
    @staticmethod
    def _provenance(lens: str, prompt: str, ids: list[str], titles: list[str]) -> dict[str, Any]:
        single=len(ids)==1; p={"source_card_id":ids[0] if single else "", "source_card_title":titles[0] if single else f"{len(titles)} items", "via_id":"", "via_name":lens, "via_kind":"ask"}
        if ids: p["context_ids"]=ids
        if titles: p["context_titles"]=titles
        if prompt: p["prompt"]=prompt
        return p
